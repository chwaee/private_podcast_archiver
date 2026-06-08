#!/bin/bash
set -e

echo "==> Running Alembic migrations..."
alembic upgrade head

echo "==> Seeding demo data (idempotent)..."
python scripts/seed_sample_data.py || echo "Seed script completed (or skipped)."

echo "==> Starting Uvicorn (reload enabled for dev)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
