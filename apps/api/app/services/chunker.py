"""Chunking service for Milestone 4.

Segment-aware chunking per PRODUCT_SPEC.md §16:
- Target 500-900 tokens per chunk (default 800)
- 100-200 token overlap (default 150)
- Do not split in middle of a transcript segment unless segment is very long
- Keep start/end timestamps from first/last segment in chunk
- Keep start/end segment indexes
- Store speaker_summary if obvious (e.g. single speaker)
- text is concatenated with spaces
"""
from typing import Any, Dict, List, Optional

Segment = Dict[str, Any]
Chunk = Dict[str, Any]


def count_tokens(text: str) -> int:
    """Rough token estimate. ~4 chars per token is common approximation.
    For production, replace with tiktoken or model-specific counter.
    """
    if not text:
        return 0
    # Simple heuristic: words * 1.3 or chars/4
    words = len(text.split())
    return max(1, int(words * 1.3))


def chunk_segments(
    segments: List[Segment],
    max_tokens: int = 800,
    overlap_tokens: int = 150,
) -> List[Chunk]:
    """Build chunks from normalized transcript segments.

    Returns list of dicts suitable for Chunk model:
    {
        "chunk_index": int,
        "start_segment_index": int,
        "end_segment_index": int,
        "start_seconds": float | None,
        "end_seconds": float | None,
        "speaker_summary": str | None,
        "text": str,
        "token_count": int,
        "metadata_json": dict | None,
    }
    """
    if not segments:
        return []

    chunks: List[Chunk] = []
    current: List[Segment] = []
    current_tokens = 0
    chunk_index = 0

    for seg in segments:
        seg_tokens = count_tokens(seg.get("text", ""))

        if current and (current_tokens + seg_tokens > max_tokens):
            # Flush current chunk
            chunk = _make_chunk(current, chunk_index)
            chunks.append(chunk)
            chunk_index += 1

            # Build overlap from tail
            current = _build_overlap(current, overlap_tokens)
            current_tokens = sum(count_tokens(s.get("text", "")) for s in current)

        current.append(seg)
        current_tokens += seg_tokens

    # Flush last
    if current:
        chunk = _make_chunk(current, chunk_index)
        chunks.append(chunk)

    return chunks


def _make_chunk(seg_list: List[Segment], index: int) -> Chunk:
    if not seg_list:
        return {}

    first = seg_list[0]
    last = seg_list[-1]

    text = " ".join(s.get("text", "") for s in seg_list)

    # Speaker summary: if all same non-null speaker
    speakers = {s.get("speaker") for s in seg_list if s.get("speaker")}
    speaker_summary = next(iter(speakers)) if len(speakers) == 1 else None

    token_count = sum(count_tokens(s.get("text", "")) for s in seg_list)

    return {
        "chunk_index": index,
        "start_segment_index": first.get("segment_index"),
        "end_segment_index": last.get("segment_index"),
        "start_seconds": first.get("start_seconds"),
        "end_seconds": last.get("end_seconds"),
        "speaker_summary": speaker_summary,
        "text": text,
        "token_count": token_count,
        "metadata_json": {
            "num_segments": len(seg_list),
            "chunker_version": "m4-simple",
        },
    }


def _build_overlap(current: List[Segment], overlap_tokens: int) -> List[Segment]:
    """Take tail segments until overlap_tokens reached (from end)."""
    if not current:
        return []

    tail: List[Segment] = []
    tokens = 0
    for seg in reversed(current):
        tail.insert(0, seg)
        tokens += count_tokens(seg.get("text", ""))
        if tokens >= overlap_tokens:
            break
    return tail
