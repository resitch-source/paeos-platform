# Changelog

All notable changes to PAEOS are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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
