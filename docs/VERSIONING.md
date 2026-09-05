# Versioning Policy

PAEOS follows [Semantic Versioning 2.0.0](https://semver.org/): `MAJOR.MINOR.PATCH`.

- **MAJOR** — incompatible API/schema changes or a completed major phase group.
- **MINOR** — backwards-compatible functionality (typical phase increments).
- **PATCH** — backwards-compatible fixes.

Pre-1.0.0, the API is considered unstable; minor versions may introduce
breaking changes while the foundation and early phases evolve.

## Phase tagging

- Each completed phase is tagged `phase-<n>-complete` (e.g. `phase-0-complete`).
- The Foundation baseline corresponds to `0.1.0`.

## Changelog

All notable changes are recorded in `CHANGELOG.md` using the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. Each release
section lists Added / Changed / Deprecated / Removed / Fixed / Security.

## Component versions

- Backend package version lives in `backend/pyproject.toml`.
- Frontend version lives in `frontend/package.json`.
- Keep them in step for coordinated releases.
