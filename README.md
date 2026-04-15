# LLMOps Platform

**DevOps for LLM Applications** — the same discipline of testing, monitoring, and safe deployment that software teams use for code, applied to prompts and AI behavior.

Teams building LLM-powered applications hit a wall when they move from prototype to production. Prompts get managed through Slack messages and Google Docs. A "small tweak" improves one use case but silently breaks three others. Costs spiral because every query — even simple FAQs — goes to the most expensive model. When users report bad responses, nobody can trace what happened. And every prompt change goes to 100% of traffic with no safety net.

This platform solves all of that. It gives AI/ML teams a unified interface to **version and A/B test prompts**, **run automated and human evaluations**, **route queries to the cheapest model that can handle them**, **trace every LLM call in production**, and **deploy changes safely through eval-gated CI/CD pipelines with canary rollouts**.

```
Prompt Edit → Run Evals → Quality Gate → Canary (10%) → Monitor → Full Rollout
```

---

## What Problems Does It Solve?

| Problem | Without This Platform | With This Platform |
|---------|----------------------|-------------------|
| **Prompt Chaos** | Prompts live in Slack, Docs, and local files. Nobody knows what's in production or how to roll back. | Version-controlled prompts with full history, diff views, and one-click rollback. |
| **Silent Quality Regressions** | A prompt tweak breaks edge cases that nobody catches until users complain. | Eval suites run on every change and block deployment if quality drops below thresholds. |
| **Uncontrolled Costs** | Every query uses the most expensive model. A $15/M-token model answers simple FAQs. | Intelligent routing sends simple queries to cheaper models. Cost dashboards show spend per app. |
| **No Production Visibility** | When something goes wrong, there's no trace of which prompt, model, or parameters were used. | Full request traces with latency, tokens, cost, and quality signals for every LLM call. |
| **Risky Deployments** | Prompt changes go straight to 100% of traffic. If it breaks, every user is affected. | Canary rollouts start at 10%, auto-rollback on quality degradation, gradual ramp to 100%. |

---

## Who Is It For?

- **AI/ML Engineers** — Build and iterate on prompts, write eval datasets, configure model routing, monitor production quality
- **Prompt Engineers / AI Product Managers** — Design prompt strategies, run A/B tests, review eval results, decide which version ships
- **Engineering Managers** — High-level visibility into cost trends, quality scores, and error rates across AI applications
- **Human Evaluators** — Domain experts who rate LLM responses for quality during evaluation campaigns

---

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

## Real-World Scenarios

**Improving a support bot's prompt** — An engineer adds conciseness instructions. Automated eval runs 200 test questions: relevance unchanged, conciseness +30%, but factuality dropped 5% on complex queries. They adjust the prompt, re-run eval (all green), and deploy via canary. The regression never reaches users.

**Investigating a cost spike** — A manager gets a budget alert: "Product Search" spend is up 40%. The cost dashboard shows tokens-per-request doubled on Wednesday. Drilling into traces reveals a verbose system message was added. They optimize it and costs drop back down — caught in hours, not at the monthly invoice.

**A/B testing response styles** — A prompt engineer tests bullet-point vs. paragraph answers with a 50/50 split. After 1,000 requests, bullet-points score +0.4 on helpfulness (statistically significant). One click promotes the winner to production.

**Catching a regression automatically** — An engineer pushes a prompt change. The CI/CD pipeline runs evals and detects factuality dropped from 4.2 to 3.6 — below the 3.8 threshold. Deployment is blocked automatically with a link to the failing test cases.

---

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

## Scope — What This Does NOT Do

- Does not host or serve LLM applications — it manages prompts, evals, and observability for apps running elsewhere
- Does not train or fine-tune models — it works with pre-trained models via their APIs
- Does not replace LLM providers (OpenAI, Anthropic, etc.) — it sits between your app and the provider
- Does not manage application code or business logic — only the LLM-specific layer (prompts, model selection, evaluation)

## License

MIT
