# Definition of Done (DoD)

A change — and a phase — is complete only when **all** applicable items pass.
Critical failures block completion. Derived from the PAEOS Build Controller
quality standard.

## Code
- [ ] Belongs to the current phase only (no future-phase functionality).
- [ ] Lint clean (`ruff check`).
- [ ] Type clean (`mypy paeos_fx`).
- [ ] Formatted (`ruff format`).
- [ ] No secrets, credentials, or `.env` files committed.

## Tests
- [ ] Unit tests added/updated and passing.
- [ ] Integration tests passing (where a DB is involved).
- [ ] API tests passing (for new/changed endpoints).
- [ ] **Tenant-isolation negative tests** added for any new tenant-owned table.
- [ ] Regression: full suite green.

## Database
- [ ] Migration is additive/non-destructive (or the destructive change is
      explicitly approved via a gate).
- [ ] New tenant-owned tables have `tenant_id`, indexes, FKs, and RLS policy.
- [ ] Audit/timestamps present where applicable.

## Security
- [ ] No new unauthenticated or unauthorized data paths.
- [ ] AI access (if any) goes through the authorized-tool → domain-service →
      validation → transaction → audit chain.
- [ ] Safety-critical actions require human approval.

## Data quality
- [ ] All reported values carry a classification (no fabrication).
- [ ] Engineering/simulation calculations record inputs, units, model,
      assumptions, reference, result, model version, validation status.

## Documentation
- [ ] Public behavior documented; `ARCHITECTURE.md` / `docs/` updated if needed.
- [ ] `CHANGELOG.md` updated.
- [ ] `PROJECT_STATUS.md` / `PROGRESS.md` reflect the change.
- [ ] New decisions recorded as ADRs in `DECISIONS.md`.

## Governance
- [ ] Required approval gates obtained and referenced in the PR.
- [ ] PR template completed.
