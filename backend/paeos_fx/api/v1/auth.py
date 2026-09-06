"""Authentication endpoints (Phase 1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from paeos_fx.api.deps import get_current_context, settings_dep
from paeos_fx.api.v1.schemas import LoginRequest, MeResponse, TokenResponse
from paeos_fx.core.config import Settings
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import AuthenticationError
from paeos_fx.db.session import tenant_session
from paeos_fx.platform.auth_service import (
    authenticate,
    issue_access_token,
    resolve_permissions,
    resolve_tenant,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, settings: Settings = Depends(settings_dep)) -> TokenResponse:
    # Resolve tenant from the (non-tenant-scoped) catalog.
    with tenant_session(None) as session:
        tenant = resolve_tenant(session, body.tenant_slug)
        if tenant is None or not tenant.is_active:
            raise AuthenticationError("Invalid credentials.")
        tenant_id = tenant.id

    # Authenticate and resolve permissions within the tenant's RLS context.
    with tenant_session(tenant_id) as session:
        user = authenticate(
            session, tenant_id=tenant_id, email=body.email, password=body.password
        )
        perms = resolve_permissions(session, user.id)
        token = issue_access_token(
            user=user, tenant_id=tenant_id, permissions=perms, settings=settings
        )

    return TokenResponse(
        access_token=token, expires_in=settings.jwt_access_ttl_seconds
    )


@router.get("/me", response_model=MeResponse)
def me(ctx: ExecutionContext = Depends(get_current_context)) -> MeResponse:
    # get_current_context guarantees both are present on an authenticated request.
    assert ctx.user_id is not None
    return MeResponse(
        user_id=ctx.user_id,
        tenant_id=ctx.require_tenant(),
        permissions=sorted(ctx.permissions),
    )
