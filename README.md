# m10-i10 — Multi-Service Docker Compose Stack

A four-service RAG stack: FastAPI + Next.js + Neo4j + Weaviate.
One command brings everything up.

## Services

| Service  | Port | Description          |
|----------|------|----------------------|
| neo4j    | 7687 / 7474 | Graph database |
| weaviate | 8080 | Vector store         |
| api      | 8000 | FastAPI RAG backend  |
| web      | 3000 | Next.js frontend     |

## Prerequisites

- Docker Desktop running
- Git

## Quickstart

### 1. Clone the repo

```bash
git clone https://github.com/<team-fork>/m10-i10-team-N.git
cd m10-i10-team-N
```

### 2. Set up environment

```bash
cp .env.example .env
```

Open `.env` and replace `<password>` with your chosen password.
Make sure `NEO4J_AUTH` and `NEO4J_PASSWORD` use the **same** value.

### 3. Start the stack

```bash
docker compose up -d --build
```

### 4. Wait for all services to be healthy

```bash
bash scripts/healthcheck_stack.sh
```

Or check manually:

```bash
docker compose ps
```

Expected healthy order: neo4j → weaviate → api → web
The api may take up to 3-5 min on first boot (downloads spaCy + flan-t5-base).

### 5. Seed the databases

Run both from the **repo root**:

```bash
bash scripts/seed_neo4j.sh
bash scripts/seed_weaviate.sh
```

### 6. Test the API

```bash
curl -X POST http://localhost:8000/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I prep ginger for stir-fry?"}'
```

Expected: HTTP 200 with `answer`, `citations`, and `confidence` fields.

### 7. Open the browser

Navigate to: http://localhost:3000/rag

Type: `Find Sichuan recipes that use ginger` and click Submit.
You should see a cited answer rendered on the page.

### 8. Teardown

```bash
docker compose down -v
```

The `-v` flag removes the named volumes (neo4j_data, weaviate_data).
Re-running steps 3-5 starts fresh.

## Team

See `TEAM.md` for role assignments and contribution summary.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'api'` | Make sure `build.context: .` in docker-compose.yml |
| Neo4j healthcheck fails | Check NEO4J_AUTH matches NEO4J_PASSWORD in .env |
| Weaviate never healthy | Uses `wget` not `curl` — do not change the healthcheck |
| API stuck starting | Normal on cold boot — wait up to 5 min for model download |
| seed script not found | Run scripts from repo root, not from inside scripts/ |