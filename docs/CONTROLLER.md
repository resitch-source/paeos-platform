# PAEOS Automated Development Controller

Every phase is executed through the same governed pipeline. This document is the
operational reference; the binding rules live in `CLAUDE.md`.

## Per-phase pipeline

```
DISCOVER → PLAN → REQUEST APPROVAL → IMPLEMENT → TEST → AUTO-FIX → RETEST →
QUALITY CHECK → SECURITY CHECK → PERFORMANCE CHECK → DATA QUALITY CHECK →
INTEGRATION CHECK → DOCUMENT → REPORT → REQUEST RELEASE APPROVAL →
PREPARE COMMIT → REQUEST COMMIT APPROVAL → COMMIT → VERIFY BACKUP →
REQUEST NEXT-PHASE APPROVAL
```

## Approval gates (STOP and request)

Destructive DB ops; deleting user data; deleting source code; resetting Git;
force-push; production deployment; production DB migration; changing security
boundaries; changing tenant isolation; changing authentication architecture;
changing major architecture; financial transaction logic; safety-critical
engineering logic; autonomous machinery control; releasing a phase; committing a
phase; starting the next phase.

### Confirmation format

```
GATE / ACTION / WHY / AFFECTED COMPONENTS / FILES / DATABASE IMPACT /
SECURITY IMPACT / BUSINESS IMPACT / RISK / TESTS COMPLETED / FAILED TESTS /
RECOMMENDED ACTION
```
Followed by: `[APPROVE] [REVIEW] [MODIFY] [STOP]`. Approval is never assumed.

## Quality standard (every phase must pass)

Architecture, Code Quality, Database, Functional, Unit, Integration, API,
Security, Tenant Isolation, Performance, Data Quality, Regression, End-to-End,
Documentation. Critical failures block phase completion.

## Migration policy

Migrations are additive and non-destructive by default. Any destructive schema
change, data migration, or production migration is a gated action.
