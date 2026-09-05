# PAEOS-FX Backend

FastAPI application + the PAEOS-FX platform framework.

## Layout

```
paeos_fx/
  core/         config, db session, security, errors, logging, context, pagination
  db/           declarative base, mixins, session (RLS), model registry
  platform/     tenancy, iam, audit, events, workflow, approval, rules, jobs,
                notifications, documents, search, numbering, uom, currency,
                i18n, masterdata
  interfaces/   ai, simulation, digital_twin, integration  (contracts only)
  api/          FastAPI app, middleware, error handlers, v1 router
migrations/     Alembic environment + baseline migration
tests/          unit (no DB) + integration/RLS (DB-gated)
```

## Setup

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Run

```bash
uvicorn paeos_fx.main:app --reload
# Docs at http://localhost:8000/docs
```

## Test

```bash
pytest                 # unit tests always run
# Integration + tenant-isolation tests run only when a live DB is available:
PAEOS_TEST_DATABASE_URL=postgresql+psycopg://paeos:paeos@localhost:5432/paeos pytest -m integration
```

## Migrations

```bash
alembic upgrade head       # apply baseline (creates platform schema + RLS)
alembic downgrade -1       # revert (development only)
```

Migrations are additive/non-destructive by policy. Destructive operations
require human approval per the build controller.
