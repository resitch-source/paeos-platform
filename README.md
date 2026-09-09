# PAEOS — Philippine Agriculture Enterprise Operating System

PAEOS is a multi-tenant enterprise operating system for Philippine agriculture,
built in strictly sequential phases on top of the **PAEOS-FX Foundation**.

> **Current state:** **v1.0.0 — complete.** The full roadmap (PAEOS-FX Foundation
> through Phase 13) is delivered and merged. Multi-tenant (PostgreSQL RLS),
> JWT/RBAC, full audit, provenance/no-fabrication throughout, a central inventory
> service, exact `Money` pricing, advisory-only AI, and a click-through web UI.
> See `PROJECT_STATUS.md`, `CHANGELOG.md`, and `docs/RELEASE_NOTES_1.0.0.md`.

## Architecture (locked) — all phases COMPLETE

```
PAEOS-FX FOUNDATION                                              ✓ COMPLETE
  → PHASE 0  — Project Governance                                ✓ COMPLETE
  → PHASE 1  — Enterprise Core                                   ✓ COMPLETE
  → PHASE 2  — Agriculture Master Data + GIS                     ✓ COMPLETE
  → PHASE 3  — Crop Production + Crop Simulation                 ✓ COMPLETE
  → PHASE 4  — Livestock + Poultry                              ✓ COMPLETE
  → PHASE 5  — Fisheries + Aquaculture                          ✓ COMPLETE
  → PHASE 6  — Inventory + Procurement + Warehouse              ✓ COMPLETE
  → PHASE 7  — Processing + MES + Coconut Oil Digital Twin      ✓ COMPLETE
  → PHASE 8  — Marketplace + Trading + Logistics                ✓ COMPLETE
  → PHASE 9  — Training + Technical Support + Expert Marketplace ✓ COMPLETE
  → PHASE 10 — AgriIntelligence / AI Agents                     ✓ COMPLETE
  → PHASE 11 — AgriSim + Optimization + Digital Twins           ✓ COMPLETE
  → PHASE 12 — IoT + Integrations + Security + Prod Hardening   ✓ COMPLETE
  → PHASE 13 — Commercialization + Customer Deployment          ✓ COMPLETE
```

**Locked rule:** Never skip a phase. Never silently start another phase.
Future-phase dependencies are satisfied only by a *minimum stable interface*.

## Technology stack

| Layer            | Choice                                   |
|------------------|------------------------------------------|
| Backend          | Python 3.11+ / FastAPI                    |
| ORM / migrations | SQLAlchemy 2.x / Alembic                  |
| Database         | PostgreSQL 16 + PostGIS 3.4               |
| Async jobs       | Celery + Redis                            |
| Frontend         | React 18 + TypeScript + Vite              |
| Containers       | Docker + docker-compose (dev)             |
| CI/CD            | GitHub Actions                            |

## Repository layout

```
backend/     FastAPI application + PAEOS-FX platform framework (+ scripts/)
frontend/    React + TypeScript web app (login, dashboard, inventory, sales)
infra/        docker-compose local dev stack
docs/         Architecture, deployment, testing, and release documentation
.github/      CI/CD workflows
```

## Quick start (run & test in a browser)

Requires Docker + Docker Compose. Full instructions: `docs/TESTING.md`.

```bash
# 1. Backend + PostgreSQL/PostGIS + Redis (runs migrations on start)
cd infra && docker compose up --build

# 2. Seed a demo tenant + admin (in another terminal)
docker compose exec api python -m scripts.seed_demo

# 3. Web UI
cd frontend && npm ci && npm run dev        # http://localhost:5173
```

Then sign in with the demo credentials — tenant `farm`, `admin@demofarm.ph`,
`supersecret123` — and click through Inventory and Sales Orders. The full API
is browsable and testable at **http://localhost:8000/docs** (Swagger UI), and
build info is at `GET /api/v1/info`.

Backend-only (no Docker):

```bash
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest                                       # unit + (DB-gated) integration
```

## Deployment

See `docs/DEPLOYMENT_RUNBOOK.md` and `docs/GO_LIVE_CHECKLIST.md`. Production
deployment and production database migrations are gated actions requiring
explicit human approval.

## Governance

This project was developed under the **PAEOS Build Controller**: every phase ran
a fixed DISCOVER → PLAN → APPROVE → IMPLEMENT → TEST → … → COMMIT pipeline with
mandatory human approval gates. See `CLAUDE.md`, `PROGRESS.md`, and
`DECISIONS.md` (ADR-0001…0019).
