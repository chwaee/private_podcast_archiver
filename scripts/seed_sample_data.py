#!/usr/bin/env python3
"""M1 seed script.

Creates a demo workspace + show + episode so the system has something
to look at after `alembic upgrade head`.

Intended to be run from inside the API container (or with the package on PYTHONPATH)
after the database is up and migrations applied.

Usage (example inside container):
    python scripts/seed_sample_data.py
"""
import os
import sys

# Make the app package importable.
# Supports:
# - Running from project root (traditional)
# - Running from inside container where scripts/ is mounted at /app/scripts and the api package at /app/app
script_dir = os.path.dirname(os.path.abspath(__file__))
candidates = [
    os.path.abspath(os.path.join(script_dir, "..", "apps", "api")),  # classic layout
    "/app",                                                          # container: api code mounted at /app, scripts at /app/scripts
    os.getcwd(),
    os.path.abspath(os.path.join(script_dir, "..")),
]
for candidate in candidates:
    if os.path.exists(os.path.join(candidate, "app", "database.py")):
        sys.path.insert(0, candidate)
        break
else:
    # fallback
    sys.path.insert(0, os.path.abspath(os.path.join(script_dir, "..", "apps", "api")))

from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal
from app.models import Workspace, Show, Episode

# Fixed demo IDs for M3 testing (upload + transcript viewer)
DEMO_WORKSPACE_ID = UUID("11111111-1111-1111-1111-111111111111")
DEMO_SHOW_ID = UUID("22222222-2222-2222-2222-222222222222")
DEMO_EPISODE_ID = UUID("33333333-3333-3333-3333-333333333333")


def main() -> None:
    print("Private Podcast Archive Copilot — seed_sample_data.py (M1)")

    # Use a fresh session
    with Session(engine) as session:
        # Idempotency guard: if a demo workspace already exists, do nothing.
        existing = session.query(Workspace).filter_by(slug="demo").first()
        if existing:
            print(f"Demo workspace already exists (id={existing.id}). Nothing to do.")
            return

        ws = Workspace(
            id=DEMO_WORKSPACE_ID,
            name="Demo Workspace",
            slug="demo",
            description="Seeded by M1 seed script for local development and testing.",
        )
        session.add(ws)
        session.flush()

        show = Show(
            id=DEMO_SHOW_ID,
            workspace_id=ws.id,
            name="The Canadian Investor",
            slug="canadian-investor",
            description="A long-running finance podcast.",
            default_language="en",
        )
        session.add(show)
        session.flush()

        ep = Episode(
            id=DEMO_EPISODE_ID,
            workspace_id=ws.id,
            show_id=show.id,
            title="The Biggest Financial Mistake I Ever Made",
            episode_number="427",
            description="Host discusses a personal lesson about yield chasing.",
            publish_date=None,
            ingestion_status="not_started",
        )
        session.add(ep)

        session.commit()

        print("✅ Seeded:")
        print(f"   Workspace: {ws.name} (slug={ws.slug}, id={ws.id})")
        print(f"   Show:      {show.name} (slug={show.slug}, id={show.id})")
        print(f"   Episode:   {ep.title} (id={ep.id})")
        print("You can now add a transcript and run ingestion (M3/M4).")


if __name__ == "__main__":
    main()

