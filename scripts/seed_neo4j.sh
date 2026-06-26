#!/usr/bin/env bash
# Run from repo root: bash scripts/seed_neo4j.sh
set -euo pipefail

source .env

echo "▶ Seeding Neo4j from seed.cypher..."
docker compose exec -T neo4j cypher-shell \
  -u "$NEO4J_USER" \
  -p "$NEO4J_PASSWORD" \
  < seed.cypher

echo "✅ Neo4j seeded successfully."