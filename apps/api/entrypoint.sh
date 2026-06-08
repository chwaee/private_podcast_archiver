#!/bin/bash
set -e

echo "==> Initializing database schema directly from SQLAlchemy models (early from-scratch dev mode)"
echo "    (Migrations via Alembic are available for future schema evolution; see alembic/)"
python -c '
import os
import sys
from sqlalchemy import text
sys.path.insert(0, "/app")
from app.database import engine, Base
print("Ensuring vector extension (for embeddings)...")
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    conn.commit()
print("Creating all tables if they do not exist...")
Base.metadata.create_all(bind=engine)
print("Schema ready.")
'

echo "==> Seeding demo data if needed (idempotent)..."
python scripts/seed_sample_data.py || echo "Seed completed or skipped."

echo "==> Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
