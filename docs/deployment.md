# Deployment

See PRODUCT_SPEC.md §23 and §33 for requirements.

**Note (post M0–M4 vetting):** Current stack supports full M2 UI + M3/M4 transcript/ingestion. Use the README "How to test locally" section for milestone-specific acceptance verification.

## Quick local

```bash
cp .env.example .env
docker compose up --build
```

## Production notes (future)

- Use a real reverse proxy (nginx / caddy)
- Persistent volumes for postgres + data/
- Secrets management for AI keys (never in image)
- Regular DB + uploads backups
- Consider read replicas or connection pooling later
