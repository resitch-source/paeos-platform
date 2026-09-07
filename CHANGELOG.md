# Changelog

All notable changes to PAEOS are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **Phase 11 — AgriSim + Optimization + Digital Twins:**
  - Optimization engines behind the Foundation `SimulationEngine` contract:
    Economic Order Quantity (`EOQ = √(2·D·S/H)`, Harris 1913) and closed-form
    proportional allocation. Parameters are caller-supplied; no coefficients are
    fabricated.
  - An engine registry exposing GDD (Phase 3), mass-balance (Phase 7), EOQ, and
    allocation uniformly, plus a scenario runner that executes any named model
    and persists the full `CalculationRecord` (classified SIMULATION).
  - New standalone `scenario_run` table (no cropping-cycle FK → non-geometric and
    testable on any PostgreSQL), with an optional `subject_ref`. Digital-twin
    what-if projections are ADVISORY forward runs recorded as scenario runs — no
    actuation and no new control path (machinery control stays `guard_control`-
    gated and unimplemented).
  - Services + REST endpoints (list engines, run scenario, project twin, list
    runs); permission catalog extended (`agrisim.*`; no actuation permission by
    design) and granted to TENANT_ADMIN. ADR-0017 records the scope.
  - Migration `0012_agrisim_optimization` (additive: 1 table + RLS, no geometry).
  - Tests: EOQ math (hand-verified) + allocation exactness + provenance +
    registry lookup/guards (unit); EOQ/mass-balance scenario persistence,
    advisory twin projection, and tenant isolation (integration, any PostgreSQL).
- **Phase 10 — AgriIntelligence / AI Agents:**
  - Instantiates the Foundation AI-safety chain (`AI → Authorized Tool → Domain
    Service → Business Validation → Transaction → Audit Log`) with concrete,
    tenant-scoped agents. Agents reach data ONLY through permission-checked,
    read-only `AuthorizedTool`s dispatched by the Foundation `ToolRegistry`; the
    AI never receives a database handle. No mutating or safety-critical/machinery
    tool is registered (gates #13/#14 upheld) and no security boundary changes.
  - Deterministic advisory agents (low-stock, open-orders) over authorized-tool
    outputs; each emits `AIRecommendation`s that are classified, carry
    assumptions, and set `requires_human_approval=True`. No LLM/model provider is
    wired and nothing is fabricated.
  - Recommendations are persisted (`agent_run`, `ai_recommendation`) with a
    human-decision lifecycle (proposed→accepted/rejected/superseded). Accepting a
    recommendation records a decision and executes nothing — the AI flow mutates
    no domain data.
  - Services + REST endpoints (run agent, list recommendations, decide);
    permission catalog extended (`ai.*`; no mutating/actuating AI permission by
    design) and granted to TENANT_ADMIN. ADR-0016 records the scope.
  - Migration `0011_agri_intelligence` (additive: 2 tables + RLS, no geometry).
  - Tests: agent logic + recommendation lifecycle + a safety assertion that the
    registry exposes no mutating/safety-critical tool (unit); agent end-to-end
    via the guarded registry with persistence, a permission-denied guard, and
    tenant isolation (integration, any PostgreSQL).
- **Phase 9 — Training + Technical Support + Expert Marketplace:**
  - Training: a course catalog and learner enrollments with a state-machine
    lifecycle (enrolled→in_progress→completed/withdrawn). Completion is a
    recorded transition — no scoring, competency, or certificate engine (nothing
    about learner attainment is fabricated).
  - Technical support: tickets with a state-machine lifecycle
    (open→in_progress→resolved→closed, plus reopen/cancel), caller-supplied
    priorities, and threaded comments. Pure workflow + audit — no SLA automation
    and no external communication channels.
  - Expert marketplace (financial, approval gate #12): an expert directory and
    client engagements with a lifecycle
    (requested→accepted→delivered→closed/cancelled) and an agreed fee via the
    Foundation `Money` type (integer minor units). Expert rate cards and fees are
    caller-supplied and exact; no payment/AR/GL/tax/settlement logic and no
    fabricated ratings.
  - Services + REST endpoints (courses, enrollments, tickets + comments/assign,
    expert profiles, engagements + fee/transitions); permission catalog extended
    (training.*/support.*/experts.*) and granted to TENANT_ADMIN. ADR-0015
    records the scope and fee boundary.
  - Migration `0010_training_support_experts` (additive: 6 tables + RLS, no
    geometry).
  - Tests: enrollment/ticket/engagement lifecycle transitions + guards (unit);
    course→enrollment, ticket flow with comments, engagement lifecycle + fee, and
    tenant isolation (integration, any PostgreSQL).
- **Phase 8 — Marketplace + Trading + Logistics:**
  - Customers, marketplace listings, and sales orders with a state-machine
    lifecycle (draft→confirmed→fulfilled→closed/cancelled) and exact monetary
    line pricing (Money, integer minor units). Fulfilling an order posts stock
    OUT THROUGH the central InventoryService (fails closed on insufficient
    stock). Financial scope is line pricing only — no tax/GL/payments.
  - Logistics: shipments with a lifecycle (planned→dispatched→delivered),
    tracking records only — no external carrier integration.
  - Services + REST endpoints (customers, listings, orders + lines/totals/
    transitions/fulfill, shipments); permission catalog extended and granted to
    TENANT_ADMIN.
  - Migration `0009_marketplace_trading_logistics` (additive: 5 tables + RLS,
    no geometry).
  - Tests: order-total math + lifecycle transitions (unit); order lifecycle +
    fulfilment via the central inventory service, shipment flow, and tenant
    isolation (integration, any PostgreSQL).
- **Phase 7 — Processing + MES + Coconut Oil Digital Twin:**
  - Manufacturing execution: process definitions (recipes with tenant-defined
    input/output quantities), production runs with a lifecycle, and quality
    checks. Completing a run consumes inputs and produces outputs THROUGH the
    central `InventoryService` (fails closed on insufficient stock).
  - Coconut-oil digital twin (ADVISORY, non-actuating): processing assets +
    telemetry, twin state derived from the latest readings, and a transparent
    mass-balance simulation (`output = input × yield_fraction`, both
    caller-supplied) recorded with a `CalculationRecord` classified SIMULATION.
  - SAFETY: no autonomous machinery-control path exists; the twin's control
    channel routes only through `guard_control` (refuses without human approval)
    and performs no actuation. No coefficients or equipment specs are fabricated.
  - Services + REST endpoints (recipes, runs, quality, assets/telemetry, twin
    state, mass-balance simulation); permission catalog extended (no
    machinery-control permission by design) and granted to TENANT_ADMIN.
  - Migration `0008_processing_mes` (additive: 7 tables + RLS, no geometry).
  - Tests: mass-balance math + provenance and the safety control-guard (unit);
    production run consume/produce via central inventory, telemetry twin state,
    and tenant isolation (integration).
- **Phase 6 — Inventory + Procurement + Warehouse:**
  - Central `InventoryService` — the single authorized, audited path for stock
    changes: item master, warehouses/storage locations, stock levels, and a
    signed stock-movement ledger; movements, transfers, and a negative-stock
    guard.
  - Procurement (financial, approval gate #12): suppliers and purchase orders
    with a state-machine lifecycle (draft→submitted→approved→received/cancelled)
    and line pricing via the Foundation `Money` type (integer minor units).
    Receiving a PO posts stock IN through the central inventory service; no
    tax/GL/payment logic. Prices/quantities are caller-supplied and exact.
  - Services + REST endpoints for items, warehouses, movements/transfers, stock
    queries, suppliers, purchase orders (+ lines, totals, transitions, receive);
    permission catalog extended and granted to TENANT_ADMIN.
  - Migration `0007_inventory_procurement` (additive: 8 tables + RLS, no
    geometry). ADR-0014 records the transactional/financial scope.
  - Tests: `Money` line-total math (unit); full inventory service, PO
    lifecycle + receipt-into-stock, and tenant isolation (integration, any
    PostgreSQL).
- **Phase 5 — Fisheries + Aquaculture:**
  - Aquatic species master data; culture units (ponds/cages/tanks) with PostGIS
    point location (EPSG:4326, GiST index, GeoJSON import); aquaculture cycles
    with a state-machine lifecycle (stocked→growing→harvested→closed); and
    water-quality, harvest, and mortality records.
  - Quantities are caller-supplied and classified; mortality decrements stocking
    count (never below 0). No fabricated biological/water-quality coefficients.
  - Services + REST endpoints (species, culture-units, cycles + transitions,
    harvest/mortality/water-quality); permission catalog extended and granted to
    TENANT_ADMIN.
  - Migration `0006_fisheries` (additive: 6 tables + RLS + GiST).
  - Tests: cycle lifecycle (unit); species master-data + isolation (any
    PostgreSQL); culture-unit/cycle/records + isolation (PostGIS-gated).
- **Phase 4 — Livestock + Poultry:**
  - Livestock master data (species, breeds) on the master-data framework.
  - Animal groups (herds/flocks) with a Foundation state-machine lifecycle
    (established→active→closed), plus production, mortality, and health-event
    records — quantities are caller-supplied and classified; no biological
    coefficients are fabricated. Mortality decrements head count (never below 0).
  - Services + REST endpoints (species/breeds, animal-groups + transitions +
    production/mortality/health records); permission catalog extended and
    granted to TENANT_ADMIN.
  - Migration `0005_livestock` (additive: 6 tables + RLS).
  - Tests: animal-group lifecycle (unit); species/breed master-data + isolation
    (any PostgreSQL); animal-group records + isolation (PostGIS-gated via the
    farm FK).
- **Phase 3 — Crop Production + Crop Simulation:**
  - Crop production models: cropping cycles (with a Foundation state-machine
    lifecycle planned→planted→growing→harvested→closed), growth observations,
    and harvest records — quantitative values carry a provenance classification.
  - First concrete simulation engine behind the Foundation simulation interface:
    Growing Degree Days (GDD), a standard citable method with caller-supplied
    parameters (base temperature + daily temperature series); no fabricated
    coefficients. Results carry a full CalculationRecord classified SIMULATION.
  - Persisted simulation runs (`simulation_run`) storing the provenance envelope.
  - Services + REST endpoints (cropping-cycles + transitions, harvests,
    crop-simulations/gdd); permission catalog extended and granted to
    TENANT_ADMIN.
  - Migration `0004_crop_production` (additive: 4 tables + RLS, no geometry).
  - Tests: GDD math + provenance (unit); cropping-cycle workflow, harvest,
    simulation persistence, and tenant isolation (integration, PostGIS-gated via
    the parcel FK).
- **Phase 2 — Agriculture Master Data + GIS:**
  - Reference/master data on the master-data framework: crop categories, crops,
    crop varieties, soil types, land-use types (structure/classification only —
    no fabricated agronomic values).
  - PostGIS geospatial entities (EPSG:4326): administrative areas, farms
    (point), and land parcels (polygon) with GiST spatial indexes; geometry
    imported as GeoJSON via `ST_GeomFromGeoJSON`.
  - Derived parcel area computed with `ST_Area` and recorded with an explicit
    provenance classification (never fabricated).
  - Services + REST endpoints (tenant-scoped, permission-guarded, audited);
    new permission catalog entries granted to `TENANT_ADMIN`.
  - Migration `0003_agri_masterdata_gis` (additive: 8 tables + RLS + GiST).
  - Tests: GeoJSON validation (unit); master-data CRUD + isolation (integration,
    any PostgreSQL); farm/parcel GIS + isolation (integration, PostGIS-gated).
- **Phase 1 — Enterprise Core:**
  - Authentication (`POST /auth/login`, `GET /auth/me`) implementing the
    approved JWT design; permission-embedding access tokens.
  - Request authorization pipeline (`api/deps.py`): JWT → execution context,
    `require_permission`, and RLS-bound tenant DB sessions.
  - Reusable domain-service (`platform/service.py`) and repository
    (`platform/repository.py`) layer with tenant filtering (defense in depth).
  - Tenant onboarding/seeding (`platform/onboarding_service.py`): permission
    catalog, `TENANT_ADMIN` system role, first admin user, platform tenant
    bootstrap.
  - IAM administration (users, roles, permission grants) and organizational
    units (`org_unit`, hierarchical, non-geographic) with audited services and
    REST endpoints.
  - Migration `0002_enterprise_core`: additive `org_unit` table + RLS.
  - Tests: auth/RBAC guards (unit) and onboarding/auth/RBAC/CRUD/tenant-isolation
    (integration).
- **Phase 0 — Project Governance:** `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md`, `CODEOWNERS`, pull-request and issue templates,
  `.pre-commit-config.yaml`, and governance docs (`DEFINITION_OF_DONE.md`,
  `BRANCHING.md`, `VERSIONING.md`). SessionStart hook for Claude Code web
  sessions.

## [0.1.0] — 2026-09-05

### Added
- **PAEOS-FX Foundation** (horizontal framework, no domain logic):
  - Backend platform: core (config, DB session with RLS binding, security,
    errors, logging, context, pagination, value classification), db base +
    mixins, and platform engines (tenancy, IAM/RBAC, audit, events + outbox,
    workflow, approval, rules, jobs, notifications, documents, search,
    numbering, UoM, currency, i18n, master-data).
  - Future-phase interfaces (contracts only): AI guarded tool chain, simulation
    provenance envelope, digital-twin, integration.
  - API v1 (health/readiness/meta), error envelopes, context + security
    middleware.
  - Alembic baseline migration: platform schema, extensions, 15 tables, indexes,
    FKs, and Row-Level Security on 13 tenant-owned tables.
  - React + TypeScript frontend shell.
  - Docker development stack and GitHub Actions CI.
  - Governance docs and ADRs.

### Security
- Multi-tenant isolation via PostgreSQL Row-Level Security (fail-closed),
  validated against PostgreSQL 16.
- Argon2id password hashing; JWT authentication framework.
