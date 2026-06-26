#!/usr/bin/env bash
# Polls until all 4 services are healthy
set -euo pipefail

SERVICES=("neo4j" "weaviate" "api" "web")
TIMEOUT=600
ELAPSED=0

echo "⏳ Waiting for all services to be healthy..."

while true; do
  ALL_HEALTHY=true
  for svc in "${SERVICES[@]}"; do
    STATUS=$(docker compose ps --format json | \
             python3 -c "import sys,json; data=sys.stdin.read(); \
             rows=[json.loads(l) for l in data.splitlines() if l]; \
             match=[r for r in rows if '$svc' in r.get('Name','')]; \
             print(match[0].get('Health','unknown') if match else 'missing')")
    if [ "$STATUS" != "healthy" ]; then
      echo "  ⏸ $svc → $STATUS"
      ALL_HEALTHY=false
    else
      echo "  ✅ $svc → healthy"
    fi
  done

  if $ALL_HEALTHY; then
    echo "🎉 All services healthy!"
    break
  fi

  sleep 10
  ELAPSED=$((ELAPSED + 10))
  if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "❌ Timeout after ${TIMEOUT}s"
    docker compose ps
    exit 1
  fi
done