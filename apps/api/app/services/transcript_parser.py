"""Transcript parser service for Milestone 3.

Implements normalization per PRODUCT_SPEC.md §15:
- All formats -> list of {"segment_index": int, "speaker": str|None, "start_seconds": float|None, "end_seconds": float|None, "text": str}
- Supported: JSON (array of objects), CSV (flexible headers), plain text (paragraphs), basic VTT/SRT.
- Rules: trim, collapse spaces, preserve original text as much as possible, no hallucinated timestamps, warnings instead of silent failure.
- Speaker defaults to None or "Unknown" if missing.
"""
import csv
import io
import json
import re
from typing import Any
from uuid import UUID

from ..config import UPLOADS_DIR  # not used here


Segment = dict[str, Any]


def _normalize_text(text: str) -> str:
    """Collapse repeated whitespace, strip."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text.strip())
    return text


def _parse_time_to_seconds(t: str | float | None) -> float | None:
    """Parse common time formats to seconds float. Supports HH:MM:SS, MM:SS, SS, or numeric."""
    if t is None:
        return None
    if isinstance(t, (int, float)):
        return float(t)
    t = str(t).strip()
    if not t:
        return None
    # numeric
    try:
        return float(t)
    except ValueError:
        pass
    # HH:MM:SS or MM:SS or MM:SS.mmm
    parts = re.split(r"[:.]", t)
    try:
        if len(parts) == 4:  # HH:MM:SS.mmm or similar
            h, m, s, ms = map(float, parts[:4])
            return h * 3600 + m * 60 + s + ms / 1000
        if len(parts) == 3:
            h, m, s = map(float, parts)
            return h * 3600 + m * 60 + s
        if len(parts) == 2:
            m, s = map(float, parts)
            return m * 60 + s
        if len(parts) == 1:
            return float(parts[0])
    except Exception:
        return None
    return None


def _parse_json(data: list[dict] | Any) -> tuple[list[Segment], list[str]]:
    warnings: list[str] = []
    segments: list[Segment] = []
    if not isinstance(data, list):
        warnings.append("JSON root must be an array of segment objects.")
        return segments, warnings

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            warnings.append(f"Segment {i} is not an object, skipped.")
            continue
        # flexible keys
        speaker = item.get("speaker") or item.get("speaker_name") or None
        start = item.get("start") or item.get("start_time") or item.get("timestamp") or item.get("start_seconds")
        end = item.get("end") or item.get("end_time") or item.get("end_seconds")
        text = item.get("text") or item.get("content") or item.get("transcript") or ""
        text = _normalize_text(str(text))

        start_sec = _parse_time_to_seconds(start)
        end_sec = _parse_time_to_seconds(end)

        if not text:
            warnings.append(f"Segment {i} has empty text, skipped.")
            continue

        segments.append({
            "segment_index": len(segments),
            "speaker": speaker if speaker else None,
            "start_seconds": start_sec,
            "end_seconds": end_sec,
            "text": text,
        })

    if not segments:
        warnings.append("No valid segments found in JSON.")
    return segments, warnings


def _parse_csv(text: str) -> tuple[list[Segment], list[str]]:
    warnings: list[str] = []
    segments: list[Segment] = []
    try:
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            warnings.append("CSV has no header row.")
            return segments, warnings

        # map possible header names (case insensitive)
        headers_lower = {h.lower().strip(): h for h in reader.fieldnames}

        def get_val(row: dict, *keys: str) -> str | None:
            for k in keys:
                if k in headers_lower:
                    return row.get(headers_lower[k])
            return None

        for i, row in enumerate(reader):
            speaker = get_val(row, "speaker", "speaker_name", "name")
            start = get_val(row, "start", "start_time", "timestamp", "start_seconds")
            end = get_val(row, "end", "end_time", "end_seconds")
            text = get_val(row, "text", "content", "transcript", "line") or ""

            text = _normalize_text(text)
            if not text:
                warnings.append(f"Row {i} has empty text, skipped.")
                continue

            start_sec = _parse_time_to_seconds(start)
            end_sec = _parse_time_to_seconds(end)

            segments.append({
                "segment_index": len(segments),
                "speaker": speaker if speaker else None,
                "start_seconds": start_sec,
                "end_seconds": end_sec,
                "text": text,
            })
    except Exception as e:
        warnings.append(f"CSV parse error: {e}")

    if not segments:
        warnings.append("No valid segments found in CSV.")
    return segments, warnings


def _parse_plain_text(text: str) -> tuple[list[Segment], list[str]]:
    warnings: list[str] = []
    segments: list[Segment] = []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [line.strip() for line in text.splitlines() if line.strip()]

    for i, para in enumerate(paragraphs):
        text_norm = _normalize_text(para)
        if not text_norm:
            continue
        segments.append({
            "segment_index": len(segments),
            "speaker": None,
            "start_seconds": None,
            "end_seconds": None,
            "text": text_norm,
        })

    if not segments:
        warnings.append("No paragraphs found in plain text transcript.")
    else:
        warnings.append("Plain text transcript: timestamps and speakers unavailable (approximated by paragraphs).")
    return segments, warnings


def _parse_vtt_or_srt(text: str, is_vtt: bool = False) -> tuple[list[Segment], list[str]]:
    """Basic VTT/SRT cue parser. Supports simple cues with optional speaker."""
    warnings: list[str] = []
    segments: list[Segment] = []
    # Remove WEBVTT header and NOTE
    text = re.sub(r"^WEBVTT.*?\n\n", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"^NOTE.*?\n\n", "", text, flags=re.IGNORECASE | re.DOTALL)

    # Split into cues (blank line separated)
    cues = re.split(r"\n\s*\n", text.strip())
    idx = 0
    for cue in cues:
        lines = [l.strip() for l in cue.splitlines() if l.strip()]
        if not lines:
            continue
        # optional cue id or number
        if re.match(r"^\d+$", lines[0]) or (is_vtt and lines[0].startswith("cue")):
            lines = lines[1:]
        if not lines:
            continue
        # timestamp line
        ts_line = lines[0]
        time_match = re.search(
            r"(\d{1,2}:)?(\d{1,2}:)?(\d{1,2}(?:\.\d+)?)\s*-->\s*(\d{1,2}:)?(\d{1,2}:)?(\d{1,2}(?:\.\d+)?)",
            ts_line,
        )
        if not time_match:
            continue
        start_str = time_match.group(0).split("-->")[0].strip()
        end_str = time_match.group(0).split("-->")[1].strip()
        start_sec = _parse_time_to_seconds(start_str)
        end_sec = _parse_time_to_seconds(end_str)

        # remaining lines = text (+ optional speaker like <v Speaker> or Speaker: )
        text_lines = lines[1:]
        full_text = " ".join(text_lines)
        speaker = None
        # simple speaker detection
        speaker_match = re.match(r"^<v\s+([^>]+)>\s*(.*)$", full_text, re.IGNORECASE)
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            full_text = speaker_match.group(2).strip()
        else:
            speaker_match = re.match(r"^([^:]+):\s*(.*)$", full_text)
            if speaker_match:
                speaker = speaker_match.group(1).strip()
                full_text = speaker_match.group(2).strip()

        text_norm = _normalize_text(full_text)
        if not text_norm:
            continue

        segments.append({
            "segment_index": idx,
            "speaker": speaker,
            "start_seconds": start_sec,
            "end_seconds": end_sec,
            "text": text_norm,
        })
        idx += 1

    if not segments:
        warnings.append("No cues parsed from VTT/SRT.")
    return segments, warnings


def parse_transcript(
    file_bytes: bytes, filename: str, mime_type: str | None = None
) -> tuple[list[Segment], list[str]]:
    """
    Main entry point. Returns (segments, warnings).
    Detects format from extension or mime.
    """
    warnings: list[str] = []
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    content = file_bytes.decode("utf-8", errors="replace")

    if ext == "json" or (mime_type and "json" in mime_type):
        try:
            data = json.loads(content)
            return _parse_json(data)
        except Exception as e:
            warnings.append(f"JSON decode error: {e}")
            return [], warnings

    if ext in ("csv", "tsv") or (mime_type and ("csv" in mime_type or "text/plain" in mime_type and ext in ("csv", "tsv"))):
        return _parse_csv(content)

    if ext in ("vtt", "srt") or (mime_type and ("text/vtt" in mime_type or "application/x-subrip" in mime_type)):
        is_vtt = ext == "vtt"
        segs, warns = _parse_vtt_or_srt(content, is_vtt=is_vtt)
        return segs, warns + warns  # warnings from parser

    # default plain text
    if ext in ("txt", "text") or not ext or (mime_type and "text/plain" in mime_type):
        return _parse_plain_text(content)

    # fallback
    warnings.append(f"Unsupported format for {filename} (ext={ext}, mime={mime_type}). Treating as plain text.")
    segs, plain_warns = _parse_plain_text(content)
    return segs, warnings + plain_warns


def segments_to_db_rows(segments: list[Segment], episode_id: UUID, transcript_file_id: UUID | None, workspace_id: UUID) -> list[dict]:
    """Convert normalized segments to dicts ready for TranscriptSegment(**row)."""
    rows = []
    for i, seg in enumerate(segments):
        rows.append({
            "workspace_id": workspace_id,
            "episode_id": episode_id,
            "transcript_file_id": transcript_file_id,
            "segment_index": i,  # ensure sequential
            "speaker": seg.get("speaker"),
            "start_seconds": seg.get("start_seconds"),
            "end_seconds": seg.get("end_seconds"),
            "text": seg.get("text", ""),
        })
    return rows
