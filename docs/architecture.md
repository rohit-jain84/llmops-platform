# LLMOps Platform - Architecture

## Overview

The LLMOps Platform follows a layered architecture with clear separation between the API layer, service/business logic layer, and data layer. All infrastructure runs in Docker containers orchestrated by Docker Compose.

## System Architecture

```
                     +------------------+
                     |   React Frontend |
                     |  (Vite SPA :3000)|
                     +--------+---------+
                              |
                              | REST API
                              v
                +-------------+---------------+
                |       FastAPI Backend        |
                |         (:8000)              |
                |  +--------+  +-----------+   |
                |  | API    |  | Services  |   |
                |  | Routes |->| (business |   |
                |  |  (v1)  |  |  logic)   |   |
                |  +--------+  +-----------+   |
                +---+-----+------+----+--------+
                    |     |      |    |
       +------------+  +--+--+ +-+----+---+  +----------+
       |               |     | |          |  |          |
+------+------+  +-----+--+ +--+------+ +--+------+ +--+------+
|  PostgreSQL |  | Redis  | | Qdrant  | | LangFuse| | LLM APIs|
|  (data)     |  | (cache | | (vector | | (traces)| | (OpenAI |
|             |  |  queue)| |  cache) | |         | | Claude) |
+-------------+  +--------+ +---------+ +---------+ +---------+
                    |
             +------+------+
             | Celery      |
             | Workers     |
             +------+------+
                    |
     +--------------+--------------+
     |              |              |
+----+----+  +------+-----+  +-----+------+
| OTel    |  | Prometheus |  | Grafana    |
|Collector|->|  (metrics) |->| (dashboards|
|         |  +------------+  |  :3002)    |
+----+----+                  +-----+------+
     |                             |
+----+----+                        |
| Tempo   |  <---------------------+
| (traces)|
+---------+
```

## Key Architectural Patterns

- **API -> Service -> Repository**: Routes handle HTTP concerns, services contain business logic, SQLAlchemy handles data access.
- **Gateway Pattern**: The `/gateway/chat` endpoint acts as a proxy handling routing, caching, experiment splitting, tracing, and LLM calls.
- **Event-driven Background Processing**: Celery handles long-running eval runs, canary progression, and periodic budget checks.
- **Dual Tracing**: LangFuse for LLM-specific traces; OpenTelemetry for infrastructure traces exported to Grafana Tempo.

## Services (12 Docker Containers)

| Service | Port | Purpose |
|---------|------|---------|
| backend | 8000 | FastAPI REST API |
| celery-worker | - | Background task processing |
| celery-beat | - | Periodic task scheduling |
| frontend | 3000 | React SPA |
| postgres | 5432 | Primary database |
| redis | 6379 | Cache, queue broker |
| qdrant | 6333 | Vector DB for semantic cache |
| langfuse | 3001 | LLM tracing |
| otel-collector | 4317 | OpenTelemetry collector |
| prometheus | 9090 | Metrics storage |
| grafana | 3002 | Dashboards |
| tempo | 3200 | Distributed tracing |

## Technology Stack

**Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Celery, litellm, LangFuse, Jinja2, sentence-transformers

**Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Shadcn/ui, TanStack Query, Recharts, Monaco Editor, Zustand

**Infrastructure**: PostgreSQL 16, Redis 7, Qdrant, Grafana + Prometheus + Tempo, OpenTelemetry
