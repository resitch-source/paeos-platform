# PAEOS — Architecture

## Layered architecture (strict)

```
Client (React SPA)
      │  HTTPS / JSON
      ▼
API layer (FastAPI, /api/v1)          ── auth, validation, tenant middleware
      ▼
Domain services                       ── business rules, transactions
      ▼
Repositories                          ── data access, tenant-scoped
      ▼
PostgreSQL 16 + PostGIS (RLS)         ── storage, spatial, isolation
```

No layer may bypass the one below it. AI, simulation, and integration flows all
enter through the API/domain-service layer — never straight into the database.

## PAEOS-FX platform capabilities

Horizontal framework packages under `backend/paeos_fx/`:

- **core** — configuration, DB session, security (hash/JWT), errors, logging,
  request/tenant context, pagination, value classification.
- **db** — declarative base with naming conventions, base mixins (UUID PK,
  timestamps, audit fields, tenant_id, soft-delete, optimistic version).
- **platform/tenancy** — tenant model, request→session tenant binding, RLS.
- **platform/iam** — users, roles, permissions, memberships, RBAC checks.
- **platform/audit** — immutable audit log service.
- **platform/events** — in-process event bus + transactional outbox.
- **platform/workflow** — reusable state-machine engine.
- **platform/approval** — configurable approval chains.
- **platform/rules** — declarative rule evaluation.
- **platform/jobs** — Celery task framework + tenant-aware context.
- **platform/notifications** — channel-abstract notifications.
- **platform/documents** — file/document service (pluggable storage).
- **platform/search** — search abstraction (Postgres FTS default).
- **platform/numbering** — gap-safe per-tenant document numbering.
- **platform/uom** — units of measure + dimensional conversion.
- **platform/currency** — money type + FX-rate interface.
- **platform/i18n** — localization (en + fil), timezone.
- **platform/masterdata** — generic versioned reference-data framework.

## Future-phase interfaces (minimum stable interfaces only)

- **interfaces/ai** — guarded AI tool contract (no direct DB access).
- **interfaces/simulation** — simulation engine contract with provenance envelope.
- **interfaces/digital_twin** — twin state/telemetry contract.
- **interfaces/integration** — inbound/outbound adapter contract.

These contain contracts and guardrails only. No crop/livestock/MES/marketplace
logic exists at the foundation.

## Multi-tenancy & security

- Every tenant-owned table has a non-null `tenant_id`.
- RLS policies restrict rows to the current `app.tenant_id`.
- Request middleware resolves the tenant and sets the DB session variable inside
  the transaction; no query runs without tenant context for tenant-owned data.
- Passwords hashed with Argon2; JWT for stateless auth; standard security
  headers and input validation at the API edge.

## Observability

Structured JSON logging with correlation and tenant IDs, Prometheus-style
metrics interface, OpenTelemetry tracing hooks, health/readiness endpoints.
