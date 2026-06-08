"""Pydantic schemas for Milestone 3 transcript features."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, Field


class TranscriptFileUploadResponse(BaseModel):
    transcript_file_id: UUID
    episode_id: UUID
    status: str = "uploaded"
    original_filename: str
    warnings: List[str] = []


class TranscriptSegmentResponse(BaseModel):
    id: UUID
    segment_index: int
    speaker: Optional[str] = None
    start_seconds: Optional[Decimal] = None
    end_seconds: Optional[Decimal] = None
    text: str

    class Config:
        from_attributes = True


class TranscriptSegmentsListResponse(BaseModel):
    episode_id: UUID
    segments: List[TranscriptSegmentResponse]
    total: int


class ParseTranscriptRequest(BaseModel):
    force_reprocess: bool = False
