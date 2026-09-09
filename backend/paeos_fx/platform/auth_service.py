"""Authentication service (Phase 1, Enterprise Core).

Implements the approved JWT design (ADR-0004): verify a user's password within a
tenant, resolve the union of permissions granted by the user's roles, and issue
a signed access token. No architecture change — this realizes the Foundation's
security primitives.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from paeos_fx.core.config import Settings
from paeos_fx.core.errors import AuthenticationError
from paeos_fx.core.security import PasswordHasher, create_access_token
from paeos_fx.platform.iam import (
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from paeos_fx.platform.tenancy import Tenant

_hasher = PasswordHasher()


def resolve_tenant(session: Session, slug: str) -> Tenant | None:
    """Look up a tenant by slug (the tenant catalog is not tenant-scoped)."""
    return session.execute(
        select(Tenant).where(Tenant.slug == slug)
    ).scalar_one_or_none()


def resolve_permissions(session: Session, user_id: uuid.UUID) -> set[str]:
    """Return the set of permission codes granted to a user via their roles."""
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    return set(session.execute(stmt).scalars().all())


def authenticate(
    session: Session, *, tenant_id: uuid.UUID, email: str, password: str
) -> User:
    """Verify credentials within a tenant-bound session. Raises on failure."""
    user = session.execute(
        select(User).where(User.tenant_id == tenant_id, User.email == email)
    ).scalar_one_or_none()
    # Constant-ish behavior: always run a verify to avoid user enumeration.
    stored = user.password_hash if user else _hasher.hash("invalid-placeholder")
    ok = _hasher.verify(password, stored)
    if user is None or not ok or not user.is_active:
        raise AuthenticationError("Invalid credentials.")
    return user


def issue_access_token(
    *,
    user: User,
    tenant_id: uuid.UUID,
    permissions: set[str],
    settings: Settings,
) -> str:
    return create_access_token(
        subject=user.id,
        tenant_id=tenant_id,
        permissions=sorted(permissions),
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        ttl_seconds=settings.jwt_access_ttl_seconds,
    )
