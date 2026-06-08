"""Episodes API (M2 full CRUD + M3/M4 transcript/ingest).

Includes full CRUD per PRODUCT_SPEC §14.4:
- GET/POST /shows/{show_id}/episodes
- GET/PATCH/DELETE /episodes/{episode_id}

Plus transcript upload, segments, parse, ingest (M3/M4).

Follows PRODUCT_SPEC §14.4, §14.5, §7.4-7.5.
Storage uses UPLOADS_DIR from config, organized by workspace/episode.
No full auth yet (relies on DEV_AUTH_BYPASS / future workspace scoping in queries).
"""
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from ..config import UPLOADS_DIR, AI_EMBEDDING_PROVIDER, AI_EMBEDDING_MODEL
from ..database import get_db
from ..models import Episode, Show, TranscriptFile, TranscriptSegment, Chunk, Embedding, IngestionJob
from ..schemas.episodes import (
    EpisodeCreate,
    EpisodeUpdate,
    EpisodeResponse,
    EpisodeListResponse,
)
from ..schemas.transcript import (
    TranscriptFileUploadResponse,
    TranscriptSegmentsListResponse,
    TranscriptSegmentResponse,
    ParseTranscriptRequest,
)
from ..services.transcript_parser import parse_transcript, segments_to_db_rows
from ..services.chunker import chunk_segments
from ..services.embedding import get_embedding_provider

router = APIRouter(prefix="/episodes", tags=["episodes"])


def _sanitize_filename(name: str) -> str:
    """Basic safe filename (no path traversal, limited chars)."""
    name = os.path.basename(name)
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    if len(name) > 100:
        name = name[:50] + "_" + name[-45:]
    return name


def _get_episode_or_404(episode_id: UUID, db: Session) -> Episode:
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    return ep


def _get_show_or_404(show_id: UUID, db: Session) -> Show:
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return show


def _save_upload_file(upload: UploadFile, episode: Episode) -> tuple[str, int]:
    """Save original file under UPLOADS_DIR/{workspace_id}/{episode_id}/ and return (storage_path, size)."""
    uploads_root = Path(UPLOADS_DIR)
    target_dir = uploads_root / str(episode.workspace_id) / str(episode.id)
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _sanitize_filename(upload.filename or "transcript.txt")
    dest = target_dir / safe_name

    # If exists, append unique suffix (MVP)
    if dest.exists():
        stem, suffix = os.path.splitext(safe_name)
        dest = target_dir / f"{stem}_{UUID(int=os.urandom(8).hex()[:16]).hex[:8]}{suffix}"

    size = 0
    with dest.open("wb") as f:
        # chunked for safety
        while True:
            chunk = upload.file.read(1024 * 1024)  # 1MB
            if not chunk:
                break
            f.write(chunk)
            size += len(chunk)

    upload.file.close()
    # relative storage path for DB (portable)
    rel_path = str(dest.relative_to(uploads_root))
    return rel_path, size


@router.post("/{episode_id}/transcript-files", response_model=TranscriptFileUploadResponse)
async def upload_transcript_file(
    episode_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload original transcript file, parse immediately, store segments."""
    episode = _get_episode_or_404(episode_id, db)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Save original
    storage_path, file_size = _save_upload_file(file, episode)

    # Create TranscriptFile record
    tf = TranscriptFile(
        workspace_id=episode.workspace_id,
        episode_id=episode.id,
        original_filename=file.filename,
        storage_path=storage_path,
        mime_type=file.content_type,
        file_size_bytes=file_size,
        parser_type="auto",
    )
    db.add(tf)
    db.flush()

    # Read back for parsing (MVP - small files)
    full_path = Path(UPLOADS_DIR) / storage_path
    file_bytes = full_path.read_bytes()

    segments, warnings = parse_transcript(
        file_bytes, file.filename, file.content_type
    )

    if not segments:
        # still keep the file record
        episode.ingestion_status = "transcript_uploaded"
        db.commit()
        return TranscriptFileUploadResponse(
            transcript_file_id=tf.id,
            episode_id=episode.id,
            status="uploaded",
            original_filename=file.filename,
            warnings=warnings or ["No segments could be parsed from file."],
        )

    # Insert segments
    rows = segments_to_db_rows(
        segments, episode.id, tf.id, episode.workspace_id
    )
    db.bulk_insert_mappings(TranscriptSegment, rows)

    # Update episode
    episode.ingestion_status = "parsed"
    db.commit()

    return TranscriptFileUploadResponse(
        transcript_file_id=tf.id,
        episode_id=episode.id,
        status="parsed",
        original_filename=file.filename,
        warnings=warnings,
    )


@router.get("/{episode_id}/segments", response_model=TranscriptSegmentsListResponse)
def list_segments(
    episode_id: UUID,
    db: Session = Depends(get_db),
    limit: int = 500,
    offset: int = 0,
):
    """List normalized transcript segments for an episode (for viewer)."""
    episode = _get_episode_or_404(episode_id, db)

    q = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.episode_id == episode.id)
        .order_by(TranscriptSegment.segment_index)
        .offset(offset)
        .limit(limit)
    )
    segs = q.all()

    return TranscriptSegmentsListResponse(
        episode_id=episode.id,
        segments=[TranscriptSegmentResponse.model_validate(s) for s in segs],
        total=len(segs),
    )


@router.post("/{episode_id}/parse-transcript", response_model=dict)
def parse_transcript_endpoint(
    episode_id: UUID,
    req: ParseTranscriptRequest = ...,
    db: Session = Depends(get_db),
):
    """Re-parse from the latest transcript file (MVP: re-runs parser on stored original)."""
    episode = _get_episode_or_404(episode_id, db)

    tf = (
        db.query(TranscriptFile)
        .filter(TranscriptFile.episode_id == episode.id)
        .order_by(TranscriptFile.created_at.desc())
        .first()
    )
    if not tf:
        raise HTTPException(status_code=404, detail="No transcript file found for episode")

    full_path = Path(UPLOADS_DIR) / tf.storage_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Stored transcript file missing on disk")

    file_bytes = full_path.read_bytes()
    segments, warnings = parse_transcript(
        file_bytes, tf.original_filename, tf.mime_type
    )

    if req.force_reprocess:
        # delete old segments for this file
        db.query(TranscriptSegment).filter(
            TranscriptSegment.transcript_file_id == tf.id
        ).delete()

    if segments:
        rows = segments_to_db_rows(segments, episode.id, tf.id, episode.workspace_id)
        db.bulk_insert_mappings(TranscriptSegment, rows)
        episode.ingestion_status = "parsed"
    else:
        episode.ingestion_status = "transcript_uploaded"

    db.commit()

    return {
        "episode_id": str(episode.id),
        "segments_parsed": len(segments),
        "warnings": warnings,
        "status": episode.ingestion_status,
    }


# M2: Full episode CRUD (integrated with existing M3/M4 endpoints)
@router.get("/shows/{show_id}/episodes", response_model=EpisodeListResponse)
def list_episodes_for_show(
    show_id: UUID,
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
):
    """List episodes under a show (M2)."""
    _get_show_or_404(show_id, db)
    query = (
        db.query(Episode)
        .filter(Episode.show_id == show_id)
        .order_by(Episode.created_at.desc())
    )
    total = query.count()
    eps = query.offset(offset).limit(limit).all()
    return EpisodeListResponse(
        episodes=[EpisodeResponse.model_validate(e) for e in eps],
        total=total,
    )


@router.post("/shows/{show_id}/episodes", response_model=EpisodeResponse, status_code=status.HTTP_201_CREATED)
def create_episode(
    show_id: UUID,
    ep_in: EpisodeCreate,
    db: Session = Depends(get_db),
):
    """Create episode under show (M2)."""
    show = _get_show_or_404(show_id, db)
    ep = Episode(
        workspace_id=show.workspace_id,
        show_id=show_id,
        **ep_in.model_dump(),
    )
    db.add(ep)
    db.commit()
    db.refresh(ep)
    return EpisodeResponse.model_validate(ep)


@router.get("/{episode_id}", response_model=EpisodeResponse)
def get_episode(episode_id: UUID, db: Session = Depends(get_db)):
    """Get episode detail (M2 + used by M3/M4)."""
    ep = _get_episode_or_404(episode_id, db)
    return EpisodeResponse.model_validate(ep)


@router.patch("/{episode_id}", response_model=EpisodeResponse)
def update_episode(
    episode_id: UUID,
    ep_in: EpisodeUpdate,
    db: Session = Depends(get_db),
):
    """Update episode (M2)."""
    ep = _get_episode_or_404(episode_id, db)
    update_data = ep_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ep, field, value)
    db.commit()
    db.refresh(ep)
    return EpisodeResponse.model_validate(ep)


@router.delete("/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_episode(episode_id: UUID, db: Session = Depends(get_db)):
    """Delete episode (M2). Cascades to transcripts/chunks via model."""
    ep = _get_episode_or_404(episode_id, db)
    db.delete(ep)
    db.commit()
    return None


@router.get("/{episode_id}/chunks")
def list_chunks(episode_id: UUID, db: Session = Depends(get_db), limit: int = 50):
    """List chunks for episode (M4 support for detail page)."""
    ep = _get_episode_or_404(episode_id, db)
    chunks = (
        db.query(Chunk)
        .filter(Chunk.episode_id == ep.id)
        .order_by(Chunk.chunk_index)
        .limit(limit)
        .all()
    )
    return {
        "episode_id": str(ep.id),
        "chunks": [
            {
                "id": str(c.id),
                "chunk_index": c.chunk_index,
                "start_seconds": float(c.start_seconds) if c.start_seconds else None,
                "end_seconds": float(c.end_seconds) if c.end_seconds else None,
                "speaker_summary": c.speaker_summary,
                "text": c.text[:300] + ("..." if len(c.text) > 300 else ""),
                "token_count": c.token_count,
            }
            for c in chunks
        ],
    }


# =============================================================================
# M4: Chunking + Embeddings + Ingestion
# =============================================================================

@router.post("/{episode_id}/ingest")
def ingest_episode(
    episode_id: UUID,
    force_reprocess: bool = False,
    db: Session = Depends(get_db),
):
    """Trigger full ingestion for an episode: chunking + embeddings.
    Updates episode.ingestion_status to 'indexed' on success.
    Creates IngestionJob record.
    For MVP runs synchronously (later offload to worker).
    """
    episode = _get_episode_or_404(episode_id, db)

    # Check if we have segments
    seg_count = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.episode_id == episode.id)
        .count()
    )
    if seg_count == 0:
        raise HTTPException(
            status_code=400, detail="No transcript segments found. Upload transcript first."
        )

    if episode.ingestion_status == "indexed" and not force_reprocess:
        return {"episode_id": str(episode.id), "status": "already_indexed", "message": "Use force_reprocess=true to re-ingest."}

    # Create job
    job = IngestionJob(
        workspace_id=episode.workspace_id,
        episode_id=episode.id,
        job_type="full_ingestion",
        status="running",
        progress_percent=10,
    )
    db.add(job)
    db.flush()

    try:
        # Fetch segments ordered
        segments = (
            db.query(TranscriptSegment)
            .filter(TranscriptSegment.episode_id == episode.id)
            .order_by(TranscriptSegment.segment_index)
            .all()
        )
        seg_dicts = [
            {
                "segment_index": s.segment_index,
                "speaker": s.speaker,
                "start_seconds": float(s.start_seconds) if s.start_seconds is not None else None,
                "end_seconds": float(s.end_seconds) if s.end_seconds is not None else None,
                "text": s.text,
            }
            for s in segments
        ]

        # 1. Chunk
        job.progress_percent = 30
        db.commit()
        chunk_dicts = chunk_segments(seg_dicts)

        # Delete old chunks/embeddings if reprocess
        if force_reprocess:
            old_chunk_ids = [c.id for c in db.query(Chunk).filter(Chunk.episode_id == episode.id).all()]
            if old_chunk_ids:
                db.query(Embedding).filter(Embedding.chunk_id.in_(old_chunk_ids)).delete()
            db.query(Chunk).filter(Chunk.episode_id == episode.id).delete()

        # Insert chunks
        chunk_models = []
        for cd in chunk_dicts:
            ch = Chunk(
                workspace_id=episode.workspace_id,
                episode_id=episode.id,
                chunk_index=cd["chunk_index"],
                start_segment_index=cd["start_segment_index"],
                end_segment_index=cd["end_segment_index"],
                start_seconds=cd["start_seconds"],
                end_seconds=cd["end_seconds"],
                speaker_summary=cd["speaker_summary"],
                text=cd["text"],
                token_count=cd["token_count"],
                metadata_json=cd.get("metadata_json"),
            )
            db.add(ch)
            chunk_models.append(ch)
        db.flush()  # get IDs

        # 2. Embed
        job.progress_percent = 60
        db.commit()
        provider = get_embedding_provider()
        texts = [c.text for c in chunk_models]
        vectors = provider.embed_texts(texts)

        for ch, vec in zip(chunk_models, vectors):
            emb = Embedding(
                workspace_id=episode.workspace_id,
                chunk_id=ch.id,
                provider=AI_EMBEDDING_PROVIDER,
                model=AI_EMBEDDING_MODEL or getattr(provider, "model", "fake"),
                dimensions=len(vec),
                embedding=vec,
            )
            db.add(emb)

        # Finalize
        episode.ingestion_status = "indexed"
        episode.indexed_at = datetime.now(timezone.utc)
        job.status = "succeeded"
        job.progress_percent = 100
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "episode_id": str(episode.id),
            "status": "indexed",
            "chunks_created": len(chunk_models),
            "job_id": str(job.id),
        }

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)[:500]
        db.commit()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
