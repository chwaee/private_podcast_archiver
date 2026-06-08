# Deployment (M0)

See PRODUCT_SPEC.md §23 and §33 for requirements.

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
