#!/usr/bin/env python3
"""Initialize the database schema directly from models.

Used by the entrypoint for early from-scratch development so that
`docker compose up -d --build` is sufficient (no manual migrations).

This is equivalent to the initial Alembic migration at this stage of the project.
"""
import os
import sys

# Ensure we can import the app package when run from /app in the container
# (the volume mount puts the api code at /app, so "app/" package is at /app/app)
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

from sqlalchemy import text

from app.database import engine, Base

print("Ensuring vector extension (for embeddings)...")
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    conn.commit()

print("Creating all tables if they do not exist...")
Base.metadata.create_all(bind=engine)
print("Schema ready.")
