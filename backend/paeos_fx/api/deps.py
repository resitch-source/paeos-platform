"""API dependencies: authentication, authorization, and tenant DB sessions.

Wires the Foundation's context, security, and RLS session together into the
first live request-authorization pipeline (Phase 1).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from paeos_fx.core.config import Settings, get_settings
from paeos_fx.core.context import ExecutionContext, current_context, set_context
from paeos_fx.core.errors import AuthenticationError, AuthorizationError
from paeos_fx.core.security import decode_access_token
from paeos_fx.db.session import tenant_session

_bearer = HTTPBearer(auto_error=False)


def settings_dep(request: Request) -> Settings:
    """Return the settings the app was created with (falls back to global)."""
    return getattr(request.app.state, "settings", None) or get_settings()


def get_current_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(settings_dep),
) -> ExecutionContext:
    """Decode the bearer token into an authenticated execution context."""
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Missing bearer token.")
    claims = decode_access_token(
        credentials.credentials,
        secret=settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
    tid = claims.get("tid")
    sub = claims.get("sub")
    if not tid or not sub:
        raise AuthenticationError("Token missing tenant or subject.")

    base = current_context()  # carries the request correlation id
    ctx = ExecutionContext(
        tenant_id=uuid.UUID(tid),
        user_id=uuid.UUID(sub),
        correlation_id=base.correlation_id,
        permissions=frozenset(claims.get("perms", [])),
    )
    set_context(ctx)  # middleware restores the prior context at request end
    return ctx


def require_permission(permission: str):
    """Build a dependency that requires the given permission."""

    def _dep(ctx: ExecutionContext = Depends(get_current_context)) -> ExecutionContext:
        if permission not in ctx.permissions:
            raise AuthorizationError(
                "Missing required permission.",
                details={"required_permission": permission},
            )
        return ctx

    return _dep


def get_tenant_db(
    ctx: ExecutionContext = Depends(get_current_context),
) -> Iterator[Session]:
    """Yield a tenant-scoped (RLS-bound) session for the authenticated tenant."""
    with tenant_session(ctx.tenant_id) as session:
        yield session
