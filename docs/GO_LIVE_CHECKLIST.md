# PAEOS — Go-Live Checklist (v1.0.0)

Complete every item before a customer go-live. Items marked (gated) are
controller-gated actions requiring explicit human approval to execute.

## Security & configuration
- [ ] `PAEOS_JWT_SECRET` set to a strong, rotated secret (not the default).
- [ ] `PAEOS_ENVIRONMENT=production` and debug disabled.
- [ ] `PAEOS_DATABASE_URL` uses dedicated, non-default credentials.
- [ ] Application connects as a **non-superuser** role (RLS enforced).
- [ ] Rate limiting enabled at the edge and/or `PAEOS_RATE_LIMIT_ENABLED=true`.
- [ ] TLS terminated at the edge with HSTS; security headers verified.
- [ ] Secret-handling review passed (no secrets in code or VCS).
- See `PRODUCTION_HARDENING.md` for the full control list.

## Data & migrations
- [ ] `alembic upgrade head` applied to the target database (gated #7).
- [ ] Row-Level Security present on all tenant-owned tables (verified).
- [ ] Automated backups configured; a restore has been **tested**.

## Application health
- [ ] `/api/v1/health`, `/api/v1/ready`, `/api/v1/info` all return expected data.
- [ ] `PAEOS_BUILD_SHA` set so the deployed build is identifiable.
- [ ] Structured logs and correlation IDs flowing to the log sink.

## Tenancy
- [ ] First tenant provisioned; admin credentials delivered securely.
- [ ] Tenant-isolation smoke test passed (Tenant A cannot see Tenant B).

## Operational readiness
- [ ] On-call and incident process defined.
- [ ] Rollback procedure rehearsed (see `DEPLOYMENT_RUNBOOK.md`).
- [ ] Production deployment approved (gate #6) before cut-over.
