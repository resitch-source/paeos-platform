# PAEOS — Deployment Runbook (v1.0.0)

Operational steps to deploy PAEOS. This runbook is documentation only; it does
**not** trigger a deployment. A production deployment or production database
migration is a gated action (controller gates #6/#7) and requires explicit human
approval before execution.

## 1. Prerequisites
- PostgreSQL 16 with PostGIS 3.4 available.
- A **non-superuser** database role for the application (so Row-Level Security is
  enforced — superusers bypass RLS).
- Python 3.11 runtime for the backend; a static host/CDN for the built frontend.

## 2. Configuration (environment variables, `PAEOS_` prefix)
Set at minimum:
- `PAEOS_ENVIRONMENT=production`
- `PAEOS_JWT_SECRET=<strong random secret>` (must not be the default)
- `PAEOS_DATABASE_URL=postgresql+psycopg://<user>:<pass>@<host>:5432/<db>`
  (must not use the default local credentials)
- Optional: `PAEOS_RATE_LIMIT_ENABLED=true`, `PAEOS_RATE_LIMIT_PER_MINUTE=<n>`
- Optional: `PAEOS_BUILD_SHA=<git sha>` (surfaced by `/api/v1/info`)

Startup calls `Settings.assert_production_safe()`, which refuses to boot in
production with the default JWT secret, debug mode on, or default DB credentials.

## 3. Database migration
- Review pending migrations, then apply: `alembic upgrade head`.
- Migrations are additive and forward-only; the current head is `0013`.
- **Gate #7:** applying migrations to a production database requires approval.

## 4. Launch & verify
- Start the API (e.g. `uvicorn paeos_fx.main:app`).
- Liveness: `GET /api/v1/health` → `{"status":"ok"}`.
- Readiness: `GET /api/v1/ready` → verifies database connectivity.
- Build info: `GET /api/v1/info` → version, environment, build SHA, phases.

## 5. Tenant onboarding
- Provision the first tenant and admin via `provision_tenant(...)`
  (`paeos_fx.platform.onboarding_service`), which seeds the permission catalog,
  the `TENANT_ADMIN` role, and the first admin user.

## 6. Rollback
- Roll back the application to the previous released image/tag.
- Database: prefer forward-fix migrations. A destructive `alembic downgrade` in
  production is a gated action (#1/#7) — do not run it without approval and a
  verified backup.

## 7. Backups
- Ensure automated backups are configured and **restores are tested** before
  go-live (see `GO_LIVE_CHECKLIST.md`).
