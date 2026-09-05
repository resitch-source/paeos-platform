# PAEOS — Architecture Decision Record (ADR)

Decisions are immutable once recorded. Changes are appended as new entries.

## ADR-0001 — Backend stack
- **Decision:** Python 3.11+ with FastAPI, SQLAlchemy 2.x, Alembic.
- **Status:** ACCEPTED (G1 approval, proposed defaults).
- **Rationale:** Strong async web framework, mature ORM/migrations, first-class
  typing, good fit for AI/simulation integration and GIS via GeoAlchemy2.

## ADR-0002 — Database
- **Decision:** PostgreSQL 16 + PostGIS 3.4. UUID PKs, FKs, constraints,
  indexes, timestamps, audit fields, migration versioning.
- **Status:** ACCEPTED (mandated by controller rules).

## ADR-0003 — Multi-tenancy model
- **Decision:** Shared database, shared schema, mandatory `tenant_id` on every
  tenant-owned entity, enforced by PostgreSQL Row-Level Security (RLS) bound to
  a per-request `app.tenant_id` session variable.
- **Status:** ACCEPTED (G1 approval, proposed default).
- **Note:** This is a security boundary. Any change requires approval gates
  #8/#9. Negative isolation tests are mandatory.

## ADR-0004 — Authentication architecture
- **Decision:** JWT bearer tokens (access) with Argon2 password hashing;
  pluggable auth provider interface. Foundation ships the framework; concrete
  identity federation is deferred to later phases behind the same interface.
- **Status:** ACCEPTED (G1 approval, proposed default).
- **Note:** Auth architecture changes require approval gate #10.

## ADR-0005 — Default branch
- **Decision:** `main` as the default integration branch.
- **Status:** ACCEPTED (proposed default). Feature work occurs on
  `claude/*` branches per the build controller.

## ADR-0006 — License
- **Decision:** Proprietary — All Rights Reserved (placeholder).
- **Status:** ASSUMPTION — pending explicit confirmation of the licensing model.
  Recorded so no accidental open-source grant is implied.

## ADR-0007 — Async jobs & cache
- **Decision:** Celery workers with Redis broker/result backend; Redis for
  cache and transient queues.
- **Status:** ACCEPTED (G1 approval, proposed default).

## ADR-0008 — Search
- **Decision:** PostgreSQL full-text search behind a pluggable search interface;
  external engine (e.g. OpenSearch) deferred behind the same interface.
- **Status:** ACCEPTED (G1 approval, proposed default).

## ADR-0009 — Value fabrication policy
- **Decision:** All domain/engineering/financial/sensor/AI values carry a
  classification (`UNKNOWN | ASSUMPTION | ESTIMATE | SIMULATION | MEASURED |
  VALIDATED`). Calculations record inputs, units, model, assumptions, reference,
  result, model version, validation status.
- **Status:** ACCEPTED (mandated by controller rules).

## ADR-0010 — AI safety chain
- **Decision:** AI access is mediated: AI → Authorized Tool → Domain Service →
  Business Validation → Transaction → Audit Log. No direct DB access for AI.
- **Status:** ACCEPTED (mandated by controller rules).
