# AGENTS.md

You are building Private Podcast Archive Copilot, a private AI archive search and content intelligence system for podcast and video creators.

## Highest Priorities

1. Preserve user/customer data privacy.
2. Maintain workspace isolation.
3. Produce source-grounded answers with citations.
4. Prefer simple, testable implementation over clever abstractions.
5. Keep LLM/provider code behind interfaces.
6. Do not overbuild features outside the current milestone.

## Coding Rules

- Use TypeScript for frontend.
- Use Python for backend.
- Use FastAPI for API.
- Use PostgreSQL with pgvector.
- Use SQLAlchemy and Alembic for database models/migrations.
- Use Pydantic for request/response schemas.
- Use Docker Compose for local development.
- Add tests for core parsing, chunking, retrieval, and API behavior.
- Never hardcode API keys.
- Use `.env.example` for required environment variables.
- Do not put generated files, local uploads, or secrets into git.

## Architecture Rules

- All customer data must be scoped by workspace_id.
- All AI model calls must go through provider abstraction services.
- Embedding generation must be replaceable.
- Chat model generation must be replaceable.
- Ingestion should be restartable and idempotent where practical.
- Do not assume one transcript format; normalize all formats into transcript_segments.
- Every chunk should map back to source transcript segments and timestamp ranges.
- Every answer should be capable of showing citations.

## UX Rules

- Build a clean SaaS interface.
- Prioritize dashboard, show detail, episode detail, transcript viewer, search, chat, and exports.
- Do not use fake data unless clearly labeled as sample data.
- Show ingestion status and errors clearly.
- Make copy/export actions obvious.

## Development Workflow

- Start complex work in plan mode.
- Before implementing a feature, describe the files to change.
- Keep diffs small.
- After changes, run tests or explain why tests could not be run.
- Prefer incremental milestones.
