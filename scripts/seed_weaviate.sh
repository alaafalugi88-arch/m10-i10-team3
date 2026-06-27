#!/usr/bin/env bash
# Run from repo root: bash scripts/seed_weaviate.sh
set -euo pipefail

echo "▶ Seeding Weaviate (runs inside api container)..."
docker compose exec -T api python seed_weaviate.py

echo "✅ Weaviate seeded. (~10-45s depending on cache)"