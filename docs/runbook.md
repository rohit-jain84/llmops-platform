# LLMOps Platform - Operational Runbook

## Quick Start

```bash
# Clone and start
git clone <repo-url>
cd llmops-platform
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose up -d

# Run database migrations
docker compose exec backend alembic upgrade head

# Seed demo data
docker compose exec backend python scripts/seed_data.py
```

## Service URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| LangFuse | http://localhost:3001 |
| Grafana | http://localhost:3002 |
| Prometheus | http://localhost:9090 |

## Common Operations

### Run Evaluation
```bash
curl -X POST http://localhost:8000/api/v1/eval/runs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"prompt_version_id": "<uuid>", "dataset_id": "<uuid>"}'
```

### Create A/B Experiment
```bash
curl -X POST http://localhost:8000/api/v1/experiments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": "<uuid>",
    "name": "Test v2 vs v3",
    "variants": [
      {"prompt_version_id": "<v2-uuid>", "traffic_pct": 50, "label": "control"},
      {"prompt_version_id": "<v3-uuid>", "traffic_pct": 50, "label": "variant_a"}
    ]
  }'
```

### Send Request Through Gateway
```bash
curl -X POST http://localhost:8000/api/v1/gateway/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": "<uuid>",
    "prompt_template_id": "<uuid>",
    "variables": {"query": "How do I reset my password?"}
  }'
```

## Troubleshooting

### Database Connection Issues
```bash
docker compose logs postgres
docker compose exec postgres pg_isready -U llmops
```

### Celery Worker Issues
```bash
docker compose logs celery-worker
docker compose exec celery-worker celery -A app.workers.celery_app inspect active
```

### Redis Issues
```bash
docker compose exec redis redis-cli ping
docker compose exec redis redis-cli info memory
```

### Qdrant Issues
```bash
curl http://localhost:6333/collections
```

## Monitoring Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| High Error Rate | >5% for 5 min | Check backend logs, verify LLM API keys |
| High Latency | p99 >10s for 5 min | Check LLM provider status, review model routing |
| Quality Regression | Eval score drops | Review recent prompt changes, check canary deployments |
| Budget Exceeded | >100% threshold | Review routing rules, check for traffic spikes |
| Cache Miss Spike | Hit ratio <20% | Verify Qdrant health, check collection configuration |

## Backup & Recovery

### Database Backup
```bash
docker compose exec postgres pg_dump -U llmops llmops > backup.sql
```

### Database Restore
```bash
docker compose exec -T postgres psql -U llmops llmops < backup.sql
```
