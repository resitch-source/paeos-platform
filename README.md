# PAEOS — Philippine Agriculture Enterprise Operating System

PAEOS is a multi-tenant enterprise operating system for Philippine agriculture,
built in strictly sequential phases on top of the **PAEOS-FX Foundation**.

> **Current state:** PAEOS-FX Foundation framework (horizontal substrate only).
> No domain phase (Phase 0+) has started. See `PROJECT_STATUS.md`.

## Architecture (locked)

```
PAEOS-FX FOUNDATION
  → PHASE 0  — Project Governance
  → PHASE 1  — Enterprise Core
  → PHASE 2  — Agriculture Master Data + GIS
  → PHASE 3  — Crop Production + Crop Simulation
  → PHASE 4  — Livestock + Poultry
  → PHASE 5  — Fisheries + Aquaculture
  → PHASE 6  — Inventory + Procurement + Warehouse
  → PHASE 7  — Processing + MES + Coconut Oil Digital Twin
  → PHASE 8  — Marketplace + Trading + Logistics
  → PHASE 9  — Training + Technical Support + Expert Marketplace
  → PHASE 10 — AgriIntelligence / AI Agents
  → PHASE 11 — AgriSim + Optimization + Digital Twins
  → PHASE 12 — IoT + Integrations + Security + Production Hardening
  → PHASE 13 — Commercialization + Customer Deployment
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
backend/     FastAPI application + PAEOS-FX platform framework
frontend/    React + TypeScript application shell
infra/        docker-compose + local dev environment
docs/         Architecture, foundation, and controller documentation
scripts/      Developer helper scripts
.github/      CI/CD workflows
```

## Quick start (development)

```bash
# Backend (local venv)
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest

# Full stack (Docker)
cd infra
docker compose up --build
```

See `docs/FOUNDATION.md` for the complete foundation reference and
`docs/CONTROLLER.md` for the automated development controller.

## Governance

This project is developed under the **PAEOS Build Controller**. Every phase
runs a fixed DISCOVER → PLAN → APPROVE → IMPLEMENT → TEST → ... → COMMIT
pipeline with mandatory human approval gates. See `CLAUDE.md`.
