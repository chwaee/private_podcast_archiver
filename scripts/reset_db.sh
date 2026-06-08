#!/usr/bin/env bash
set -euo pipefail

echo "WARNING: This will stop containers and DELETE the database volume (all data lost)."
read -r -p "Are you sure? Type 'yes' to continue: " confirm
if [[ "$confirm" != "yes" ]]; then
  echo "Aborted."
  exit 1
fi

echo "Bringing stack down and removing volumes..."
docker compose down -v

echo "Done. Next 'docker compose up --build' or ./scripts/dev_start.sh will start fresh."
