# LLMOps Platform

A comprehensive platform for managing the complete lifecycle of AI/LLM applications — from prompt engineering and A/B testing to automated evaluation, cost optimization, and deployment with canary rollouts.

## Features

### Prompt Management
- Version-controlled prompt templates with Jinja2 syntax
- Monaco-based editor with `{{variable}}` highlighting
- Side-by-side diff comparison between versions
- Tag management (production, staging, experimental)
- Interactive playground for testing prompts

### A/B Testing
- Create experiments with multiple prompt variants
- Configurable traffic splitting
- Real-time results with statistical significance (Welch's t-test)
- Automatic winner detection and promotion

### Evaluation Framework
- **5 built-in evaluators**: Factuality, Relevance, Safety, Format Compliance, Latency
- Extensible evaluator registry with `BaseEvaluator` interface
- Golden and adversarial dataset management
- Human evaluation campaigns with blind rating interface
- Automated eval runs via Celery workers

### LLM Gateway
- Unified proxy endpoint (`POST /gateway/chat`)
- **Semantic caching** with Qdrant + sentence-transformers
- **Intelligent model routing** based on complexity, keywords, and custom rules
- Integrated tracing via LangFuse
- Full request logging with token/cost tracking

### Cost Optimization
- Real-time cost analytics by application, model, and time period
- Budget alerts with configurable thresholds
- Cost forecasting based on 7/30 day trends
- Model routing for cost reduction (route simple queries to cheaper models)

### Observability
- **Dual tracing**: LangFuse for LLM traces, OpenTelemetry for infrastructure
- 3 pre-built Grafana dashboards (LLM Overview, Cost Analytics, Quality Trends)
- Custom OTel metrics (request duration, tokens, cost, cache hit ratio, eval scores)
- Configurable alerting rules

### CI/CD & Deployments
- Eval-gated deployment pipeline (GitHub Actions)
- Automated canary rollouts (10% → 25% → 50% → 100%)
- Automatic rollback on quality degradation
- Full deployment audit trail

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Celery |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Shadcn/ui |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 |
| Vector DB | Qdrant |
| LLM | litellm (OpenAI, Anthropic, 100+ providers) |
| Tracing | LangFuse + OpenTelemetry |
| Monitoring | Grafana + Prometheus + Tempo |
| Infra | Docker Compose (12 services) |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) OpenAI/Anthropic API keys for LLM features

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd llmops-platform

# Copy environment file
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)

# Start all services
docker compose up -d

# Run database migrations
docker compose exec backend alembic upgrade head

# Seed demo data
docker compose exec backend python scripts/seed_data.py
```

### Access

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API Docs** | http://localhost:8000/docs |
| **LangFuse** | http://localhost:3001 |
| **Grafana** | http://localhost:3002 |

### Demo Credentials
- Admin: `admin@llmops.dev` / `admin123`
- Engineer: `engineer@llmops.dev` / `engineer123`
- Evaluator: `evaluator@llmops.dev` / `evaluator123`

## Project Structure

```
llmops-platform/
├── docker-compose.yml          # 12 services
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app factory
│   │   ├── config.py           # Pydantic Settings
│   │   ├── database.py         # Async DB session
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response DTOs
│   │   ├── api/v1/             # Route handlers
│   │   ├── services/           # Business logic layer
│   │   ├── evaluators/         # Eval metric implementations
│   │   ├── workers/            # Celery tasks
│   │   ├── middleware/         # Auth, OTel
│   │   └── telemetry/          # OTel SDK setup
│   └── tests/
├── frontend/
│   └── src/
│       ├── api/                # Typed API client
│       ├── hooks/              # React Query hooks
│       ├── stores/             # Zustand stores
│       ├── components/         # UI components
│       └── pages/              # Route pages
├── grafana/provisioning/       # Pre-built dashboards
├── prometheus/                 # Metrics config
├── otel-collector/             # Trace pipeline
├── tempo/                      # Trace storage
├── scripts/                    # Seed data, sample eval
├── docs/                       # Architecture, runbook
└── .github/workflows/          # CI + eval-gated deploy
```

## API Overview

All endpoints under `/api/v1/`. Authentication via JWT Bearer token.

| Category | Key Endpoints |
|----------|--------------|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Applications | `GET/POST /applications` |
| Prompts | CRUD templates/versions, tagging, rollback, diff, render |
| Experiments | Create, start/stop, live results, promote winner |
| Evaluations | Datasets, eval runs, human eval campaigns |
| Cost | Analytics, forecasting, budget alerts |
| Deployments | Create, promote (canary), rollback |
| Gateway | `POST /gateway/chat` — unified LLM proxy |
| CI/CD | `POST /cicd/trigger-eval`, `GET /cicd/eval-status/{id}` |

Full API documentation available at http://localhost:8000/docs when running.

## Observability Dashboards

The platform ships with 3 pre-built Grafana dashboards accessible at `http://localhost:3002` after `docker compose up`:

### LLM Overview Dashboard
- **Request volume** — Requests per minute across all applications and models
- **Latency distribution** — P50/P95/P99 response times (histogram)
- **Error rate** — Failed requests as % of total, broken down by error type
- **Cache hit ratio** — Semantic cache effectiveness over time
- **Active experiments** — Currently running A/B tests with traffic splits

### Cost Analytics Dashboard
- **Daily/weekly/monthly spend** — Stacked by model (GPT-4o, GPT-4o-mini, Claude Sonnet, etc.)
- **Cost per application** — Which apps consume the most budget
- **Token usage trends** — Input vs. output tokens over time
- **Budget utilization** — Current spend vs. configured budget alerts (80%, 100% thresholds)
- **Routing savings** — Estimated cost saved by model routing (cheaper model for simple queries)

### Quality Trends Dashboard
- **Evaluation scores over time** — Factuality, relevance, safety, and format compliance
- **Per-version comparison** — Side-by-side quality metrics for prompt versions
- **Human eval agreement** — Inter-rater consistency for human evaluation campaigns
- **Deployment health** — Canary rollout stages with quality gates

> To view dashboards: run `docker compose up -d`, then open http://localhost:3002 (default credentials: admin/admin).

## License

MIT
