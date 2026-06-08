#!/usr/bin/env bash
set -euo pipefail

echo "==> Private Podcast Archive Copilot (Milestone 0)"
echo "==> Starting Docker Compose stack (db + api + worker + web)..."

docker compose up --build

# Note: Ctrl-C to stop. For clean reset use ./scripts/reset_db.sh
