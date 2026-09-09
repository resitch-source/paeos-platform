"""Tenant onboarding & seeding (Phase 1, Enterprise Core).

Platform-level operations that provision a tenant and seed its baseline IAM:
the global permission catalog, a ``TENANT_ADMIN`` role, and the first admin user.
Also bootstraps the reserved platform tenant used by platform administrators.

All operations are idempotent where practical so re-running provisioning does
not duplicate catalog rows.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from paeos_fx.core.errors import ConflictError
from paeos_fx.core.security import PasswordHasher
from paeos_fx.db.session import bind_tenant
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.iam import (
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from paeos_fx.platform.tenancy import Tenant

PLATFORM_TENANT_SLUG = "__platform__"

_hasher = PasswordHasher()


@dataclass(frozen=True)
class ProvisionResult:
    tenant: Tenant
    admin_user: User
    admin_role: Role


def seed_permission_catalog(session: Session) -> None:
    """Insert any missing enterprise-core permissions (global, idempotent)."""
    existing = set(session.execute(select(Permission.code)).scalars().all())
    for code, description in perms.ENTERPRISE_CORE_PERMISSIONS.items():
        if code not in existing:
            session.add(Permission(code=code, description=description))
    session.flush()


def _grant_role(
    session: Session, tenant_id: uuid.UUID, role: Role, codes: tuple[str, ...]
) -> None:
    perm_rows = session.execute(
        select(Permission).where(Permission.code.in_(codes))
    ).scalars().all()
    for perm in perm_rows:
        session.add(
            RolePermission(
                tenant_id=tenant_id, role_id=role.id, permission_id=perm.id
            )
        )
    session.flush()


def provision_tenant(
    session: Session,
    *,
    slug: str,
    name: str,
    admin_email: str,
    admin_password: str,
    admin_permissions: tuple[str, ...] = perms.TENANT_ADMIN_PERMISSIONS,
    admin_role_code: str = perms.TENANT_ADMIN_ROLE_CODE,
) -> ProvisionResult:
    """Create a tenant with a seeded admin role and first admin user.

    The caller's ``session`` must be able to write the (non-RLS) tenant/permission
    catalogs. Tenant-scoped rows are written after binding the RLS context to the
    new tenant.
    """
    if session.execute(
        select(Tenant).where(Tenant.slug == slug)
    ).scalar_one_or_none():
        raise ConflictError(f"Tenant slug already exists: {slug!r}")

    seed_permission_catalog(session)

    tenant = Tenant(slug=slug, name=name)
    session.add(tenant)
    session.flush()  # allocate tenant.id

    # Bind RLS context to the new tenant for all tenant-scoped inserts.
    bind_tenant(session, tenant.id)

    role = Role(
        tenant_id=tenant.id, code=admin_role_code, name=admin_role_code,
        is_system=True,
    )
    session.add(role)
    session.flush()
    _grant_role(session, tenant.id, role, admin_permissions)

    admin = User(
        tenant_id=tenant.id,
        email=admin_email,
        full_name="Administrator",
        password_hash=_hasher.hash(admin_password),
    )
    session.add(admin)
    session.flush()
    session.add(UserRole(tenant_id=tenant.id, user_id=admin.id, role_id=role.id))
    session.flush()

    return ProvisionResult(tenant=tenant, admin_user=admin, admin_role=role)


def bootstrap_platform_tenant(
    session: Session, *, admin_email: str, admin_password: str
) -> ProvisionResult:
    """Create the reserved platform tenant + a platform administrator.

    The platform admin holds the platform provisioning permission plus tenant
    admin permissions. Idempotent: returns the existing setup if already present.
    """
    existing = session.execute(
        select(Tenant).where(Tenant.slug == PLATFORM_TENANT_SLUG)
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("Platform tenant already bootstrapped.")

    return provision_tenant(
        session,
        slug=PLATFORM_TENANT_SLUG,
        name="PAEOS Platform",
        admin_email=admin_email,
        admin_password=admin_password,
        admin_permissions=(perms.PLATFORM_TENANT_PROVISION, *perms.TENANT_ADMIN_PERMISSIONS),
        admin_role_code=perms.PLATFORM_ADMIN_ROLE_CODE,
    )
