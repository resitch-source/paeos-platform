# PAEOS — Progress Log

## 2026-09-05 — PAEOS-FX Foundation
- Repository inspected: confirmed greenfield (unborn Git repo, 0 files).
- G1 Foundation Plan produced and **approved**.
- Foundation framework implemented (sections A–AF), horizontal substrate only:
  - Repo scaffolding, governance docs, `.gitignore`, licensing placeholder.
  - Backend package `paeos_fx` (FastAPI): core config, DB base/mixins,
    security, errors, logging, context, pagination, value classification.
  - Platform engines: tenancy (RLS), IAM/RBAC, audit, events (+outbox),
    workflow, approval, rules, jobs, notifications, documents, search,
    numbering, UoM, currency, i18n, master-data framework.
  - Future-phase interfaces: AI (guarded tool contract), simulation,
    digital twin, integration.
  - API v1 + health/readiness, error handling, structured observability.
  - Alembic baseline migration (extensions, platform schema, base tables, RLS).
  - Test suite: unit (pure engines) + integration/RLS (DB-gated).
  - Frontend shell (React + TS + Vite).
  - Docker dev environment, Makefile, CI workflow.

_Detailed test/quality/security results recorded in the phase report._

Foundation released, committed (`d87de56`), and pushed to
`claude/paeos-repo-inspection-t9kf9j`.

## 2026-09-05 — Phase 0 — Project Governance
- Added contribution/workflow docs: `CONTRIBUTING.md`,
  `docs/DEFINITION_OF_DONE.md`, `docs/BRANCHING.md`, `docs/VERSIONING.md`.
- Added policy docs: `SECURITY.md`, `CODE_OF_CONDUCT.md`.
- Added GitHub templates: `CODEOWNERS`, `pull_request_template.md`,
  issue templates (bug/feature/config).
- Added change tracking: `CHANGELOG.md`.
- Added developer tooling: `.pre-commit-config.yaml` (ruff, ruff-format,
  mypy, secret/large-file guards) and a `precommit` Make target.
- Added SessionStart hook (`.claude/`) so Claude Code web sessions provision
  the backend venv; validated hook, linter, and a test run through it.
- Updated governance ledgers and ADRs (ADR-0011 versioning, ADR-0012 branch
  protection stance).
- No application code, DB, or future-phase changes.

Released, committed (`ec3b22a`), and pushed.

## 2026-09-05 — Phase 1 — Enterprise Core
- Reusable domain-service + tenant-repository layer (defense-in-depth tenant
  filtering on top of RLS).
- Authentication implementing approved JWT design: `POST /auth/login`
  (tenant_slug + email + password), `GET /auth/me`; permission-embedding tokens.
- Request authorization pipeline (`api/deps.py`): JWT → execution context,
  `require_permission`, RLS-bound tenant session.
- Tenant onboarding/seeding: permission catalog, `TENANT_ADMIN` role, first
  admin user, platform-tenant bootstrap.
- IAM admin (users/roles/permission grants) + organizational units
  (`org_unit`, hierarchical, non-geographic) with audited services + REST APIs.
- Migration `0002_enterprise_core` (additive: org_unit + RLS).
- Tests: 5 auth/RBAC guard unit tests; 5 integration tests (onboarding, auth,
  RBAC, CRUD, tenant isolation) validated on PostgreSQL 16.
- ruff + mypy clean; 49 unit tests pass. No GIS/agriculture/future-phase work.
