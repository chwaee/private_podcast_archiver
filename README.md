# Private Podcast Archive Copilot

Private AI archive search, RAG, transcript intelligence, and content repurposing platform for podcasters, YouTubers, and media teams with large back catalogs.

**Core promise:** “Ask your podcast archive anything and get reliable answers with episode-level and timestamp-level citations.”

This is a **private-by-default** system. All data is isolated by workspace. Designed for local / private-cloud / VPS deployments first.

## Current Status

**Milestone 0 – Repo and Foundations** (complete)

- Monorepo skeleton (Next.js web + FastAPI api + worker + PostgreSQL + pgvector)
- Docker Compose for local dev/pilot
- FastAPI `/api/health`
- Next.js app shell with sidebar + dashboard placeholder
- SQLAlchemy + Alembic skeleton (no models/migrations yet — see M1)
- AGENTS.md, .env.example, scripts
- No auth, no data models, no ingestion, no RAG yet (per spec)

See [PRODUCT_SPEC.md](./PRODUCT_SPEC.md) for the full product design, DB schema, API contracts, prompts, and milestone plan.

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

## Next Milestones (high level)

M1: Core data models + migrations + seed  
M2: Shows & Episodes UI/CRUD  
M3: Transcript upload + parsing  
M4: Chunking + embeddings + ingestion jobs  
M5: Semantic search  
M6: Archive chat (RAG + citations)  
M7: Content exports (quote packs, clip ideas, etc.)  
M8: Pilot hardening

See PRODUCT_SPEC.md §26 for detailed acceptance criteria.

## License

Internal / pilot use. See future for distribution.
