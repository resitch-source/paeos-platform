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

## ADR-0011 — Versioning & changelog
- **Decision:** Semantic Versioning (`MAJOR.MINOR.PATCH`); Keep a Changelog
  format in `CHANGELOG.md`; phase completions tagged `phase-<n>-complete`. The
  Foundation baseline is `0.1.0`.
- **Status:** ACCEPTED (Phase 0).

## ADR-0012 — Branch protection stance
- **Decision:** Branch-protection rules for `main` (require PR + green CI,
  disallow force-push/deletion, review for gated changes) are documented as
  recommendations in `docs/BRANCHING.md`. They are applied by a repository
  admin, not by automated/controller work, because changing branch protection
  is outside the automated action scope.
- **Status:** ACCEPTED (Phase 0). Enforcement pending repo-admin action.

## ADR-0014 — Inventory transactional core & procurement financial scope
- **Decision:** All stock changes route through a single central
  `InventoryService` (movements are signed ledger entries; stock level = sum of
  movements; negative stock blocked unless explicitly allowed). Procurement is
  scoped to suppliers + purchase orders + receipt + line pricing only. Monetary
  values use the Foundation `Money` type (integer minor units); prices/quantities
  are caller-supplied and stored exactly. No GL, tax engine, discounts, or
  payments. Warehouses are non-geographic (link to org units) so the transactional
  core is fully testable without PostGIS.
- **Status:** ACCEPTED (Phase 6). Financial transaction logic approved under
  gate #12 for this scope; broader finance is deferred to a later phase.

## ADR-0013 — SessionStart hook
- **Decision:** A synchronous `SessionStart` hook provisions the backend venv
  in Claude Code on the web so tests/linters are runnable. Remote-only,
  idempotent. Effective for sessions after it lands on the default branch.
- **Status:** ACCEPTED (Phase 0).

## ADR-0015 — Enablement scope (training, support, expert marketplace) & fee boundary
- **Decision:** Phase 9 adds three enablement domains on the existing Foundation
  engines, with no new framework code: (a) **Training** — a course catalog and
  learner enrollments driven by the state-machine engine; completion is a
  recorded transition, with no scoring/competency/certificate engine (nothing
  about attainment is fabricated). (b) **Technical support** — tickets with a
  state-machine lifecycle and threaded comments; caller-supplied priorities; no
  SLA automation and no external communication channels (deferred to Phase 12).
  (c) **Expert marketplace** — an expert directory and client engagements with an
  agreed fee. Expert rate cards and engagement fees are exact `Money` amounts
  (integer minor units), caller-supplied; there is **no** payment, invoicing, AR,
  GL, tax, or settlement logic, and no fabricated expert ratings/scores. All six
  tables are tenant-owned (RLS) and non-geometric (fully testable without
  PostGIS).
- **Status:** ACCEPTED (Phase 9). Financial transaction logic (fees/rates)
  approved under gate #12 for this bounded scope; broader finance remains
  deferred.

## ADR-0016 — AI-agent advisory scope & safety-chain instantiation
- **Decision:** Phase 10 instantiates (does not alter) the Foundation AI-safety
  chain `AI → Authorized Tool → Domain Service → Business Validation →
  Transaction → Audit Log`. Concrete agents reach data ONLY through
  permission-checked, READ-ONLY `AuthorizedTool`s dispatched by the Foundation
  `ToolRegistry`; the AI is never given a database handle. Agents are
  deterministic (no LLM/model provider is wired) and produce advisory
  `AiRecommendation`s that are persisted, classified, carry assumptions, and set
  `requires_human_approval=True`. Recommendations are NEVER auto-applied:
  accepting one records a human decision and executes nothing, mutating no domain
  data. No mutating or safety-critical/machinery tool is registered, so the AI
  cannot change state or actuate equipment (gates #13/#14 upheld; no security
  boundary changed, so gate #8 is not triggered). Both tables (`agent_run`,
  `ai_recommendation`) are tenant-owned (RLS) and non-geometric.
- **Status:** ACCEPTED (Phase 10). LLM/model-provider wiring and any
  AI-initiated action remain deferred/gated.
