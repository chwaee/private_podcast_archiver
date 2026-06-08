"""Initial core data models.

Revision ID: 0001
Revises: 
Create Date: 2026-06-08

This migration creates all tables from PRODUCT_SPEC.md §13 using the
SQLAlchemy models defined in M1. It is the first migration (no previous
schema in a fresh database).

Includes:
- All listed entities with exact columns, types, nullability
- Primary keys (UUID), foreign keys, unique constraints, indexes
- JSONB columns
- pgvector Vector column for embeddings (requires extension + pgvector package)
- Reasonable server defaults for timestamps

Run via: alembic upgrade head   (inside the api container after DB is up)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure the vector extension exists (the pgvector Docker image enables it,
    # but this is idempotent and safe).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- workspaces ---
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False, unique=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- workspace_members ---
    op.create_table(
        "workspace_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="admin"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )

    # --- shows ---
    op.create_table(
        "shows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("website_url", sa.String(), nullable=True),
        sa.Column("rss_feed_url", sa.String(), nullable=True),
        sa.Column("default_language", sa.String(), nullable=False, server_default="en"),
        sa.Column("default_timezone", sa.String(), nullable=False, server_default="UTC"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workspace_id", "slug", name="uq_workspace_show_slug"),
    )
    op.create_index("ix_shows_workspace", "shows", ["workspace_id"])

    # --- episodes ---
    op.create_table(
        "episodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("show_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shows.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("episode_number", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("publish_date", sa.Date(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("audio_url", sa.String(), nullable=True),
        sa.Column("video_url", sa.String(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("ingestion_status", sa.String(), nullable=False, server_default="not_started"),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_episodes_workspace", "episodes", ["workspace_id"])
    op.create_index("ix_episodes_show", "episodes", ["show_id"])

    # --- transcript_files ---
    op.create_table(
        "transcript_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("episodes.id"), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("parser_type", sa.String(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- transcript_segments ---
    op.create_table(
        "transcript_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("episodes.id"), nullable=False),
        sa.Column("transcript_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transcript_files.id"), nullable=True),
        sa.Column("segment_index", sa.Integer(), nullable=False),
        sa.Column("speaker", sa.String(), nullable=True),
        sa.Column("start_seconds", sa.Numeric(10, 3), nullable=True),
        sa.Column("end_seconds", sa.Numeric(10, 3), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("episode_id", "segment_index", name="uq_episode_segment"),
    )
    op.create_index("ix_transcript_segments_workspace", "transcript_segments", ["workspace_id"])
    op.create_index("ix_transcript_segments_episode", "transcript_segments", ["episode_id"])
    op.create_index("ix_transcript_segments_start", "transcript_segments", ["start_seconds"])
    op.create_index("ix_transcript_segments_speaker", "transcript_segments", ["speaker"])

    # --- chunks ---
    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("episodes.id"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("start_segment_index", sa.Integer(), nullable=True),
        sa.Column("end_segment_index", sa.Integer(), nullable=True),
        sa.Column("start_seconds", sa.Numeric(10, 3), nullable=True),
        sa.Column("end_seconds", sa.Numeric(10, 3), nullable=True),
        sa.Column("speaker_summary", sa.String(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("episode_id", "chunk_index", name="uq_episode_chunk"),
    )
    op.create_index("ix_chunks_workspace", "chunks", ["workspace_id"])
    op.create_index("ix_chunks_episode", "chunks", ["episode_id"])
    op.create_index("ix_chunks_start", "chunks", ["start_seconds"])

    # --- embeddings (vector) ---
    op.create_table(
        "embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=False, unique=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(1024), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_embeddings_workspace", "embeddings", ["workspace_id"])

    # --- ingestion_jobs ---
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("episodes.id"), nullable=True),
        sa.Column("job_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="queued"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- chat_sessions ---
    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("filters_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- chat_messages ---
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("chat_session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_sessions.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- citations ---
    op.create_table(
        "citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("episodes.id"), nullable=True),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=True),
        sa.Column("transcript_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("transcript_segments.id"), nullable=True),
        sa.Column("start_seconds", sa.Numeric(10, 3), nullable=True),
        sa.Column("end_seconds", sa.Numeric(10, 3), nullable=True),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- exports ---
    op.create_table(
        "exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("export_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("source_scope_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("exports")
    op.drop_table("citations")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("ingestion_jobs")
    op.drop_table("embeddings")
    op.drop_table("chunks")
    op.drop_table("transcript_segments")
    op.drop_table("transcript_files")
    op.drop_table("episodes")
    op.drop_table("shows")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
    op.drop_table("users")
    # We intentionally do not drop the vector extension on downgrade.
