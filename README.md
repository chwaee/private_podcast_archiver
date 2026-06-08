# Private Podcast Archive Copilot

Private AI archive search, RAG, transcript intelligence, and content repurposing platform for podcasters, YouTubers, and media teams with large back catalogs.

**Core promise:** “Ask your podcast archive anything and get reliable answers with episode-level and timestamp-level citations.”

This is a **private-by-default** system. All data is isolated by workspace. Designed for local / private-cloud / VPS deployments first.

## Current Status

**Milestones 0–4 complete** (M2 implemented via dedicated catch-up pass after initial jump to M3/M4 for feature dependencies; all prior work vetted for acceptance criteria).

- **M0 (Repo & Foundations)**: Full monorepo (Next.js + FastAPI + worker), Docker Compose (pgvector), `/api/health`, Next.js shell + sidebar, SQLAlchemy/Alembic skeleton, AGENTS.md, scripts, .env.example.
- **M1 (Core Data Model)**: All entities (users, workspaces, shows, episodes, transcripts, chunks, embeddings, jobs, chats, citations, exports), initial Alembic migration, seed (demo ws/show/episode with fixed IDs), model tests with workspace isolation.
- **M2 (Show & Episode UI)**: Full API CRUD for shows (list/create/get/patch under workspaces) + episodes (list/create/get/patch/delete under shows). Frontend: /shows list+create, /shows/[id] detail+episodes+create form, /episodes/[id] full detail page with tabs (Overview, Transcript [M3], Chunks [M4], etc.). Navigation updated; episode appears under show.
- **M3 (Transcript Upload & Parsing)**: Upload endpoint + parser (JSON/CSV/TXT/VTT/SRT per spec), file storage, normalized segment storage, transcript viewer UI with search/speaker/timestamps/warnings. Sample JSON works.
- **M4 (Chunking & Embeddings)**: Segment-aware chunker, embedding provider abstraction (Fake + OpenAI-compatible), ingestion workflow (/ingest creates chunks + embeddings + IngestionJob, sets status=indexed).

All acceptance criteria from PRODUCT_SPEC.md §26 have been reviewed and addressed (see "Milestone Vetting" below). M3/M4 features are integrated into the M2 episode detail UI.

See [PRODUCT_SPEC.md](./PRODUCT_SPEC.md) for full design, DB schema, API contracts, and detailed criteria.

## Getting Started (Docker Compose)

```bash
# 1. Environment
cp .env.example .env
# Edit .env as needed (AI provider keys, etc.). For pure local dev with no external calls, defaults + DEV_AUTH_BYPASS are sufficient for M0.

# 2. Start everything
docker compose up --build

# Or use the helper
./scripts/dev_start.sh
```

- Web UI: http://localhost:3000
- API: http://localhost:8000 (FastAPI docs at /docs)
- Health: http://localhost:8000/api/health
- DB: localhost:5432 (postgres/postgres/podcast_copilot) — exposed for debugging only

To stop and clean volumes (reset DB):

```bash
./scripts/reset_db.sh
```

## Development Notes

- All customer data queries **must** filter by workspace_id (enforced from M1 onward).
- AI providers are abstracted (see later milestones).
- Keep changes minimal and testable.
- Follow the AGENTS.md rules strictly.

## Project Structure (per spec §11)

```
apps/
  web/          # Next.js (TypeScript)
  api/          # FastAPI + SQLAlchemy + Alembic
packages/
  shared/       # Future shared types
data/           # uploads/ exports/ sample/ (gitignored)
scripts/        # dev helpers
docs/           # architecture, deployment, etc.
```

## Milestone Vetting & Testing (Current as of this update)

We performed a full back-audit of M0–M4 acceptance criteria (per PRODUCT_SPEC.md §26) using code review, syntax/build checks, model simulation, parser execution against sample data, and UI/API path verification. No running full Docker stack in this environment (use the commands below for end-to-end).

**M0 Acceptance**:
- `docker compose up` starts services (config validated repeatedly).
- `/api/health` returns `{"status":"ok","version":"0.1.0"}`.
- Web loads (dashboard + full pages now).

**M1 Acceptance**:
- Migrations apply (0001_initial_models.py creates all tables).
- `seed_sample_data.py` creates demo workspace/show/episode (fixed IDs for testing; uses models + commit).
- Backend tests (`test_models.py`) create/query entities + demonstrate workspace isolation (e.g., queries on ws_a don't see ws_b data).

**M2 Acceptance**:
- Create show: UI form at /shows (POST /api/shows/workspaces/.../shows) + API.
- Create episode: Form in /shows/[showId] (POST /api/episodes/shows/.../episodes) + API.
- Episode appears under show: Listed in show detail page (GET /api/episodes/shows/...).

**M3 Acceptance**:
- JSON sample uploads: Endpoint + storage in episodes.py + transcript_parser.py.
- Segments display with speaker + timestamp: In /episodes/[id] Transcript tab (searchable table).
- Parser warnings: Returned on upload (e.g., plain text note); tested with sample.

**M4 Acceptance**:
- Ingestion creates chunks: chunker.py + /ingest workflow.
- Embeddings stored: embedding.py (providers) + Embedding rows.
- Job status = indexed + episode.ingestion_status updated.

**How to test locally (recommended after vetting):**
```bash
cp .env.example .env
docker compose up --build -d db   # or full stack
docker compose run --rm api alembic upgrade head
docker compose run --rm api python scripts/seed_sample_data.py
# Then:
# - Visit http://localhost:3000/shows (create show/episode)
# - Open episode detail → upload data/sample/sample_episode_transcript.json
# - Run ingestion → check Chunks tab + status
# - API: curl http://localhost:8000/api/health ; use /docs for interactive
docker compose run --rm api pytest -q apps/api/app/tests/ --tb=line
```

**Automated checks performed**:
- Web: `npm run build` (all routes including new /shows, /shows/[id], /episodes/[id]).
- Python: `py_compile` on all core files (main, routers, services, models, tests, seed).
- Parser: Direct execution on sample JSON → 4 segments, no warnings for valid input.
- Model/seed logic: AST + string checks for create paths and isolation tests.

Gaps fixed during this vetting pass:
- Outdated README (now documents M0–M4 + testing).
- M2 was previously incomplete (full catch-up implemented with proper pages + CRUD before this audit).
- Minor: Added chunks listing endpoint for UI tab; ensured forms call correct integrated endpoints.
- Documentation now emphasizes sequential testing of acceptance criteria.

## Next Milestones (high level)

M5: Semantic search  
M6: Archive chat (RAG + citations)  
M7: Content exports (quote packs, clip ideas, etc.)  
M8: Pilot hardening

See PRODUCT_SPEC.md §26 for detailed acceptance criteria. (All prior milestones now vetted and documented.)

## License

Internal / pilot use. See future for distribution.
