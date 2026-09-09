# PAEOS — Production Hardening Checklist (Phase 12)

This checklist accompanies the Phase 12 hardening work. It documents deployment
controls; the application enforces the code-level items via
`Settings.assert_production_safe()` at startup. Nothing here changes the
authentication architecture, tenant isolation (RLS), or any existing security
boundary — the additions are defense-in-depth and are disabled by default.

## Secrets & configuration
- All secrets come from `PAEOS_*` environment variables; none are hardcoded
  (`core/config.py`). `.env.example` documents required variables.
- `assert_production_safe()` refuses to boot in `production` when:
  - `PAEOS_JWT_SECRET` is left at the insecure default;
  - debug mode is on;
  - `PAEOS_DATABASE_URL` still uses the default local credentials.
- Rotate `PAEOS_JWT_SECRET` on a schedule; keep it out of version control.

## Database
- Connect the application as a **non-superuser** role so PostgreSQL Row-Level
  Security is enforced (superusers bypass RLS). RLS is `ENABLE`d **and** `FORCE`d
  on every tenant-owned table (see migrations).
- Take regular backups and test restores; keep migrations forward-only in prod.

## Transport & headers
- Terminate TLS at the edge; enable HSTS there (`Strict-Transport-Security`).
- The app sets `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
  and `Cache-Control: no-store` on every response (`api/middleware.py`).

## Rate limiting
- An additive, **opt-in** fixed-window limiter is available
  (`core/ratelimit.py`, wired in `main.py`). Enable with
  `PAEOS_RATE_LIMIT_ENABLED=true` and tune `PAEOS_RATE_LIMIT_PER_MINUTE`.
- The in-memory limiter is per-process; front it with a distributed limiter
  (e.g. Redis) behind a load balancer for multi-instance deployments.

## Integrations / IoT
- Inbound messages are recorded idempotently
  (`(tenant_id, system, idempotency_key)` unique) so external systems can retry
  safely. Ingestion is **records-only** — no autonomous machinery control.
- No outbound adapter is wired: the default adapter **refuses to fabricate** a
  delivery. Configure a concrete adapter per deployment.

## Auditing & observability
- Domain mutations are written to the audit log via the domain-service layer.
- Every request carries an `X-Correlation-ID` for log correlation.
