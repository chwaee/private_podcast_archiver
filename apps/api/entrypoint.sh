#!/bin/bash
set -e

# Force the correct DATABASE_URL for the container (in case the user's .env has localhost from local dev).
# Compose sets it, but this makes it robust even if .env is loaded.
export DATABASE_URL="postgresql+psycopg://postgres:postgres@db:5432/podcast_copilot"

echo "==> Initializing database schema directly from SQLAlchemy models (early from-scratch dev mode)"
echo "    (Migrations via Alembic are available for future schema evolution; see alembic/)"
python init_db.py

echo "==> Seeding demo data if needed (idempotent)..."
python scripts/seed_sample_data.py || echo "Seed completed or skipped."

echo "==> Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
