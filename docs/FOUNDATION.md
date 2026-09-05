# PAEOS-FX Foundation Reference

The foundation is the horizontal framework every phase builds on. It contains no
domain logic. Future phases are represented only by minimum stable interfaces.

## Capability map (A–AF)

| # | Capability | Module(s) | Notes |
|---|------------|-----------|-------|
| A | Repository | root files, `.gitignore`, `LICENSE` | governance + hygiene |
| B | Package structure | `paeos_fx/` | core / db / platform / interfaces / api |
| C | Database foundation | `db/base.py`, `db/mixins.py`, migration | UUID PK, audit, versioning |
| D | Multi-tenancy | `platform/tenancy.py`, `db/session.py`, RLS | fail-closed isolation |
| E | IAM / RBAC | `platform/iam.py` | users, roles, permissions |
| F | Configuration | `core/config.py` | env + tenant settings + flags |
| G | Master data | `platform/masterdata.py` | versioned, effective-dated pattern |
| H | Workflow | `platform/workflow.py` | state-machine engine |
| I | Approval | `platform/approval.py` | configurable chains |
| J | Rules | `platform/rules.py` | declarative, safe evaluation |
| K | Events | `platform/events.py` | in-process bus + outbox |
| L | Background jobs | `platform/jobs.py` | Celery (optional extra) |
| M | Notifications | `platform/notifications.py` | channel-abstract |
| N | Documents/files | `platform/documents.py` | pluggable storage |
| O | Search | `platform/search.py` | backend-agnostic |
| P | Numbering | `platform/numbering.py` | gap-safe per-tenant |
| Q | Units of measure | `platform/uom.py` | dimensional conversion |
| R | Currency | `platform/currency.py` | integer minor units; FX interface |
| S | Localization | `platform/i18n.py` | en + fil, Asia/Manila |
| T | Audit | `platform/audit.py` | append-only |
| U | API foundation | `api/`, `main.py` | v1, health, meta, pagination |
| V | Error handling | `core/errors.py`, `api/errors.py` | envelope + correlation id |
| W | Observability | `core/logging.py` | structured logs, metrics interface |
| X | AI interface | `interfaces/ai.py` | guarded tool chain |
| Y | Simulation interface | `interfaces/simulation.py` | provenance envelope |
| Z | Digital-twin interface | `interfaces/digital_twin.py` | inert control (gated) |
| AA | Integration | `interfaces/integration.py` | adapter/mapper contracts |
| AB | Security | `core/security.py`, middleware, RLS | Argon2, JWT, headers |
| AC | Testing | `tests/` | unit + integration/RLS |
| AD | Frontend | `frontend/` | React+TS shell |
| AE | Docker/dev | `infra/`, `backend/Dockerfile` | compose stack |
| AF | CI/CD | `.github/workflows/ci.yml` | lint/type/test/build |

## Tenant isolation (how it works)

1. A request resolves its tenant; `db.session.tenant_session(tenant_id)` opens a
   session and executes `set_config('app.tenant_id', <uuid>, true)` inside the
   transaction.
2. Every tenant-owned table has RLS `ENABLE`d and `FORCE`d, with a
   `tenant_isolation` policy: `USING`/`WITH CHECK`
   `tenant_id::text = current_setting('app.tenant_id', true)`.
3. With no tenant set, the comparison yields no match — **fail-closed** (zero
   rows), never a leak.
4. The application connects as a **non-superuser** role, because superusers
   bypass RLS. This is validated by the tenant-isolation test suite.

## No-fabrication policy

Values carry a `Classification` (`UNKNOWN | ASSUMPTION | ESTIMATE | SIMULATION |
MEASURED | VALIDATED`). Simulation/engineering results must be produced as a
`CalculationRecord` capturing inputs, units, formula/model, assumptions,
reference, result, model version, and validation status.

## AI safety chain

`AI → AuthorizedTool → Domain Service → Business Validation → Transaction →
Audit Log`. The `ToolRegistry` refuses unknown tools, enforces the required
permission, and blocks safety-critical tools without an approved control
context. AI has no direct database access.
