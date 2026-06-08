"""Minimal Episode + Transcript API for Milestone 3.

Includes:
- Basic episode retrieval (to support upload UI)
- POST /episodes/{episode_id}/transcript-files (multipart upload + immediate parse + segment storage)
- GET /episodes/{episode_id}/segments
- POST /episodes/{episode_id}/parse-transcript (re-parse if needed)

Follows PRODUCT_SPEC §14.5 and §7.4-7.5.
Storage uses UPLOADS_DIR from config, organized by workspace/episode.
No full auth yet (relies on DEV_AUTH_BYPASS / future workspace scoping in queries).
"""
import os
import re
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from ..config import UPLOADS_DIR
from ..database import get_db
from ..models import Episode, TranscriptFile, TranscriptSegment
from ..schemas.transcript import (
    TranscriptFileUploadResponse,
    TranscriptSegmentsListResponse,
    TranscriptSegmentResponse,
    ParseTranscriptRequest,
)
from ..services.transcript_parser import parse_transcript, segments_to_db_rows

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


# Minimal episode helpers to support M3 UI without full M2
@router.get("/{episode_id}")
def get_episode(episode_id: UUID, db: Session = Depends(get_db)):
    ep = _get_episode_or_404(episode_id, db)
    return {
        "id": str(ep.id),
        "title": ep.title,
        "episode_number": ep.episode_number,
        "ingestion_status": ep.ingestion_status,
        "show_id": str(ep.show_id),
        "workspace_id": str(ep.workspace_id),
    }
