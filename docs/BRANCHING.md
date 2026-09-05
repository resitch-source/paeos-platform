# Branching & Merge Strategy

## Branches

- **`main`** — the integration branch. Always releasable; every phase merges
  here once its gates pass. (ADR-0005 records `main` as the default branch.)
- **Working branches** — one focused deliverable each:
  - `claude/<topic>` — controller-driven work.
  - `phase-<n>/<topic>` — human-driven phase work.

## Flow

1. Branch from the latest `main`.
2. Implement within the current phase only.
3. Keep the branch green (lint, type, tests) before opening a PR.
4. Open a PR into `main`, complete the template + DoD.
5. Merge after CI passes and required approval gates are satisfied.

## Merge policy

- Prefer a **merge commit** or **squash** into `main` (keep history readable);
  do not rewrite history on shared branches.
- Never force-push a shared branch. Force-push is a gated action.
- Regenerate lockfiles/generated files with tooling, never by hand.

## Recommended remote protections (advisory)

> These require repository-admin action and are **not** applied automatically by
> the build controller (changing branch protection is out of scope for
> automated work).

- Protect `main`: require PR, require CI to pass, disallow force-push and
  deletion.
- Require at least one review for gated changes.
- Require linear or merge-commit history per team preference.

## Tagging

- Tag phase completions as `phase-<n>-complete` and releases per
  `docs/VERSIONING.md`.
