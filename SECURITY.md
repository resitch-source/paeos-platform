# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in PAEOS, **do not open a public
issue.** Report it privately to the maintainers via GitHub's private
vulnerability reporting (Security → Report a vulnerability) or the project's
designated security contact.

> **ASSUMPTION:** the security contact address is pending confirmation. Update
> this section with the real contact once established.

Please include: affected component/version, reproduction steps, impact, and any
suggested remediation. We aim to acknowledge reports promptly and coordinate
disclosure responsibly.

## Supported versions

While pre-1.0.0, only the latest `main` and the most recent tagged release
receive security fixes.

## Secret handling

- Never commit secrets, tokens, credentials, or `.env` files. Use `.env`
  (git-ignored) and document variables in `.env.example`.
- The pre-commit configuration includes a private-key/secret guard; CI runs a
  dependency audit.
- Rotate any credential that is exposed, even briefly.

## Security architecture (foundation)

- Passwords are hashed with Argon2id; authentication uses JWT (auth
  architecture is a gated concern — see `CLAUDE.md`).
- Multi-tenant data is isolated by PostgreSQL Row-Level Security; the
  application connects as a non-superuser role so RLS is always enforced.
- AI has no direct database access; it operates only through authorized tools →
  domain services → business validation → transaction → audit log.
- Safety-critical actions (e.g. machinery control) require human approval unless
  an explicitly validated control architecture is in place.

## Changes to security boundaries

Any change to authentication, authorization, tenant isolation, or security
boundaries is a **mandatory human-approval gate** and must be reviewed
explicitly before merge.
