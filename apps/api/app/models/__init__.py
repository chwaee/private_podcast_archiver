"""SQLAlchemy models for Private Podcast Archive Copilot.

All definitions follow PRODUCT_SPEC.md §13 exactly (field names, types,
nullability, defaults, unique constraints, indexes, and the overall entity list).

Base is re-exported from the M0 database setup so that models inherit the
same declarative base. All customer data tables include workspace_id scoping.

Vector column for embeddings requires the pgvector package (added in M1).
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Date,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    Index,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from ..database import Base  # M0 Base; all models must inherit from it and carry workspace_id


# -----------------------------------------------------------------------------
# Core identity & isolation
# -----------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships (convenience)
    shows: Mapped[List["Show"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    members: Mapped[List["WorkspaceMember"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String, default="admin", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="members")


# -----------------------------------------------------------------------------
# Content hierarchy (show -> episode)
# -----------------------------------------------------------------------------

class Show(Base):
    __tablename__ = "shows"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rss_feed_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    default_language: Mapped[str] = mapped_column(String, default="en")
    default_timezone: Mapped[str] = mapped_column(String, default="UTC")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_workspace_show_slug"),
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="shows")
    episodes: Mapped[List["Episode"]] = relationship(
        back_populates="show", cascade="all, delete-orphan"
    )


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    show_id: Mapped[UUID] = mapped_column(ForeignKey("shows.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    episode_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    publish_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ingestion_status: Mapped[str] = mapped_column(String, default="not_started")
    indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    show: Mapped["Show"] = relationship(back_populates="episodes")
    transcript_files: Mapped[List["TranscriptFile"]] = relationship(
        back_populates="episode", cascade="all, delete-orphan"
    )
    transcript_segments: Mapped[List["TranscriptSegment"]] = relationship(
        back_populates="episode", cascade="all, delete-orphan"
    )
    chunks: Mapped[List["Chunk"]] = relationship(
        back_populates="episode", cascade="all, delete-orphan"
    )
    ingestion_jobs: Mapped[List["IngestionJob"]] = relationship(
        back_populates="episode", cascade="all, delete-orphan"
    )


# -----------------------------------------------------------------------------
# Transcripts
# -----------------------------------------------------------------------------

class TranscriptFile(Base):
    __tablename__ = "transcript_files"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    episode_id: Mapped[UUID] = mapped_column(ForeignKey("episodes.id"), nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parser_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    episode: Mapped["Episode"] = relationship(back_populates="transcript_files")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    episode_id: Mapped[UUID] = mapped_column(ForeignKey("episodes.id"), nullable=False)
    transcript_file_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("transcript_files.id"), nullable=True
    )
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_seconds: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 3), nullable=True)
    end_seconds: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 3), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("episode_id", "segment_index", name="uq_episode_segment"),
        Index("ix_transcript_segments_workspace", "workspace_id"),
        Index("ix_transcript_segments_episode", "episode_id"),
        Index("ix_transcript_segments_start", "start_seconds"),
        Index("ix_transcript_segments_speaker", "speaker"),
    )

    episode: Mapped["Episode"] = relationship(back_populates="transcript_segments")


# -----------------------------------------------------------------------------
# Retrieval units (chunking + embeddings)
# -----------------------------------------------------------------------------

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    episode_id: Mapped[UUID] = mapped_column(ForeignKey("episodes.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_segment_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_segment_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    start_seconds: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 3), nullable=True)
    end_seconds: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 3), nullable=True)
    speaker_summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("episode_id", "chunk_index", name="uq_episode_chunk"),
        Index("ix_chunks_workspace", "workspace_id"),
        Index("ix_chunks_episode", "episode_id"),
        Index("ix_chunks_start", "start_seconds"),
    )

    episode: Mapped["Episode"] = relationship(back_populates="chunks")
    embedding: Mapped[Optional["Embedding"]] = relationship(
        back_populates="chunk", uselist=False, cascade="all, delete-orphan"
    )


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    chunk_id: Mapped[UUID] = mapped_column(ForeignKey("chunks.id"), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1024), nullable=False)  # 1024 matches .env.example default
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_embeddings_workspace", "workspace_id"),
    )

    chunk: Mapped["Chunk"] = relationship(back_populates="embedding")


# -----------------------------------------------------------------------------
# Background jobs
# -----------------------------------------------------------------------------

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    episode_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("episodes.id"), nullable=True)
    job_type: Mapped[str] = mapped_column(String, nullable=False)  # parse_transcript | chunk_episode | embed_episode | full_ingestion
    status: Mapped[str] = mapped_column(String, default="queued", nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    episode: Mapped[Optional["Episode"]] = relationship(back_populates="ingestion_jobs")


# -----------------------------------------------------------------------------
# Chat & exports (RAG outputs)
# -----------------------------------------------------------------------------

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    filters_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="chat_session", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    chat_session_id: Mapped[UUID] = mapped_column(ForeignKey("chat_sessions.id"), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # user | assistant | system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chat_session: Mapped["ChatSession"] = relationship(back_populates="messages")


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)  # chat_message | export | manual
    source_id: Mapped[Optional[UUID]] = mapped_column(String, nullable=True)  # generic id of the generating object
    episode_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("episodes.id"), nullable=True)
    chunk_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("chunks.id"), nullable=True)
    transcript_segment_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("transcript_segments.id"), nullable=True
    )
    start_seconds: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 3), nullable=True)
    end_seconds: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 3), nullable=True)
    label: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Export(Base):
    __tablename__ = "exports"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    export_type: Mapped[str] = mapped_column(String, nullable=False)  # episode_summary | quote_pack | clip_ideas | newsletter_draft | topic_brief
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_scope_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# Re-export Base for convenience (matches the expectation in alembic/env.py and tests)
# from ..database import Base  (already imported above)
