"""Pydantic schemas for Shows (M2)."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class ShowBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    website_url: Optional[str] = None
    rss_feed_url: Optional[str] = None
    default_language: str = "en"
    default_timezone: str = "UTC"


class ShowCreate(ShowBase):
    pass


class ShowUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    rss_feed_url: Optional[str] = None
    default_language: Optional[str] = None
    default_timezone: Optional[str] = None


class ShowResponse(ShowBase):
    id: UUID
    workspace_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShowListResponse(BaseModel):
    shows: List[ShowResponse]
    total: int
