# Contributing to PAEOS

PAEOS is developed under the **PAEOS Build Controller** (see `CLAUDE.md` and
`docs/CONTROLLER.md`). Every change flows through a governed, phase-gated
pipeline. This document is the practical guide for contributors.

## 1. Ground rules

- **Never skip a phase.** Work belongs to exactly one phase (see
  `PROJECT_STATUS.md`). Do not implement future-phase functionality; if a future
  dependency is required, add only the minimum stable interface.
- **No fabrication.** Every engineering/agricultural/financial/sensor/AI value
  must carry a classification (`UNKNOWN | ASSUMPTION | ESTIMATE | SIMULATION |
  MEASURED | VALIDATED`). See `paeos_fx.core.classification`.
- **No secrets in the repo.** Use `.env` (git-ignored) and `.env.example` for
  documentation. The pre-commit secret guard will block accidental commits.
- **Respect tenant isolation.** Every tenant-owned entity carries `tenant_id`
  and is covered by Row-Level Security. Add negative isolation tests for new
  tenant-owned tables.

## 2. Development setup

```bash
./scripts/dev_setup.sh          # venv + install + lint + tests
# or
make venv && make check
```

Backend: Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16 + PostGIS.
Frontend: React 18 + TypeScript + Vite. Full stack: `make up` (Docker).

## 3. Branching model

- `main` — integration branch; always releasable (see `docs/BRANCHING.md`).
- Working branches: `claude/<topic>` or `phase-<n>/<topic>`.
- Keep branches focused on a single phase deliverable.

## 4. Commit conventions

- Imperative subject line, ≤ 72 chars (e.g. `Add numbering service`).
- Explain the *why* in the body when non-obvious.
- Reference the phase and, if applicable, the ADR.

## 5. Pull requests

- Fill in `.github/pull_request_template.md` completely, including the
  Definition-of-Done checklist (`docs/DEFINITION_OF_DONE.md`).
- CI must be green: ruff, mypy, unit tests, integration + tenant-isolation
  tests (PostGIS), frontend build.
- Gated changes (security boundaries, tenant isolation, auth, financial logic,
  destructive migrations, production deploys) require explicit human approval
  and must be called out in the PR.

## 6. Quality gates (run locally before pushing)

```bash
make lint          # ruff
make typecheck     # mypy
make test          # pytest
pre-commit run --all-files
```

## 7. Migrations

- Additive and non-destructive by default (`alembic revision`).
- Never hand-edit generated files that tooling owns.
- Destructive or production migrations are gated — do not run them without
  approval.

## 8. Definition of Done

A change is done only when it satisfies every item in
`docs/DEFINITION_OF_DONE.md`.
