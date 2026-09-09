# PAEOS 1.0.0 — Release Notes

PAEOS (Philippine Agriculture Enterprise Operating System) 1.0.0 completes the
locked FX→13 roadmap. This is a factual summary of what the platform delivers;
see `CHANGELOG.md` for per-phase detail.

## Highlights
- **Multi-tenant, secure by design.** PostgreSQL Row-Level Security (ENABLE +
  FORCE) on every tenant-owned table, JWT authentication, RBAC permission
  catalog, and a full audit trail. The application runs as a non-superuser role
  so RLS cannot be bypassed.
- **Provenance & no-fabrication.** Every quantitative value is classified
  (UNKNOWN/ASSUMPTION/ESTIMATE/SIMULATION/MEASURED/VALIDATED); simulations carry
  a full CalculationRecord. No agronomic, financial, sensor, or AI values are
  invented.
- **Central services, never bypassed.** All stock changes route through the
  single audited InventoryService; monetary amounts use the exact integer-minor
  `Money` type (no floats).

## What's included (FX → Phase 13)
- **Foundation + Enterprise Core:** config, DB/RLS, IAM/RBAC, audit, events,
  workflow, approval, currency, master-data; auth, tenant onboarding, org units.
- **Agriculture:** crop/soil master data + PostGIS farms/parcels; crop
  production with the GDD simulation engine; livestock/poultry; fisheries.
- **Operations:** inventory + procurement; processing/MES with an advisory
  coconut-oil digital twin; marketplace/trading/logistics.
- **Enablement:** training, technical support, and an expert marketplace.
- **Intelligence & simulation:** advisory AI agents (guarded read-only tools,
  human-decided) and AgriSim optimization (EOQ, allocation) with advisory twin
  projections.
- **Platform:** IoT/integration ingestion (idempotent, records-only), additive
  security hardening, and this commercialization/deployment release surface.

## Safety posture
- AI is advisory and tool-mediated; it never holds direct database access and
  never auto-applies a recommendation.
- No autonomous machinery control exists; any control channel routes through a
  human-approval guard and performs no actuation.
- Financial scope is exact pricing via `Money` only — no payments, GL, or tax.

## Operating
- New public endpoints: `GET /api/v1/info` (version/phases/build), alongside the
  existing `/health`, `/ready`, and `/meta`.
- Deploy per `DEPLOYMENT_RUNBOOK.md`; verify against `GO_LIVE_CHECKLIST.md` and
  `PRODUCTION_HARDENING.md`.

## Known limitations / deferred
- No live external integration adapters are wired (the default adapter refuses to
  fabricate a delivery); the in-memory rate limiter is per-process.
- Pricing/billing is a business decision and is not implemented (see
  `COMMERCIALIZATION.md`).
