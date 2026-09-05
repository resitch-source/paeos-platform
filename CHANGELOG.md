# Changelog

All notable changes to PAEOS are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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
