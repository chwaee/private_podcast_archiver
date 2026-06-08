"""Pydantic schemas for Episodes (M2) + extensions for M3/M4."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel

from .transcript import TranscriptSegmentResponse  # reuse


class EpisodeBase(BaseModel):
    title: str
    episode_number: Optional[str] = None
    description: Optional[str] = None
    publish_date: Optional[date] = None
    source_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    duration_seconds: Optional[int] = None


class EpisodeCreate(EpisodeBase):
    pass


class EpisodeUpdate(BaseModel):
    title: Optional[str] = None
    episode_number: Optional[str] = None
    description: Optional[str] = None
    publish_date: Optional[date] = None
    source_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    duration_seconds: Optional[int] = None


class EpisodeResponse(EpisodeBase):
    id: UUID
    workspace_id: UUID
    show_id: UUID
    ingestion_status: str
    indexed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EpisodeListResponse(BaseModel):
    episodes: List[EpisodeResponse]
    total: int


# For detail page, include related counts or minimal
class EpisodeDetailResponse(EpisodeResponse):
    transcript_segments_count: int = 0
    chunks_count: int = 0
