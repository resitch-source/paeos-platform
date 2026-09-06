"""IAM administration services (Phase 1, Enterprise Core).

Tenant-scoped user and role management built on the domain-service/repository
pattern. All mutations are audited; cross-tenant access is prevented by the
repository's tenant filter plus Row-Level Security.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import ConflictError, NotFoundError, ValidationError
from paeos_fx.core.pagination import Page, PageParams
from paeos_fx.core.security import PasswordHasher
from paeos_fx.platform.iam import (
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService

_hasher = PasswordHasher()


class UserService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.users: TenantRepository[User] = TenantRepository(
            session, User, self.tenant_id
        )
        self.roles: TenantRepository[Role] = TenantRepository(
            session, Role, self.tenant_id
        )

    def create_user(
        self, *, email: str, password: str, full_name: str = ""
    ) -> User:
        if len(password) < 12:
            raise ValidationError("Password must be at least 12 characters.")
        exists = self.session.execute(
            select(User).where(
                User.tenant_id == self.tenant_id, User.email == email
            )
        ).scalar_one_or_none()
        if exists:
            raise ConflictError("A user with this email already exists.")
        user = User(
            email=email,
            full_name=full_name,
            password_hash=_hasher.hash(password),
        )
        self.users.add(user)
        self._record(action="user.create", entity_type="User",
                     entity_id=str(user.id), after={"email": email})
        self._emit("user.created", {"id": str(user.id)})
        return user

    def list_users(self, params: PageParams | None = None) -> Page[User]:
        return self.users.list(params)

    def deactivate_user(self, user_id: uuid.UUID) -> User:
        user = self.users.get_or_404(user_id)
        user.is_active = False
        self.session.flush()
        self._record(action="user.deactivate", entity_type="User",
                     entity_id=str(user_id))
        return user

    def assign_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        self.users.get_or_404(user_id)
        self.roles.get_or_404(role_id)
        exists = self.session.execute(
            select(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        ).scalar_one_or_none()
        if exists:
            return
        self.session.add(
            UserRole(tenant_id=self.tenant_id, user_id=user_id, role_id=role_id)
        )
        self.session.flush()
        self._record(action="user.assign_role", entity_type="User",
                     entity_id=str(user_id), after={"role_id": str(role_id)})

    def revoke_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        link = self.session.execute(
            select(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        ).scalar_one_or_none()
        if link is None:
            raise NotFoundError("User does not hold this role.")
        self.session.delete(link)
        self.session.flush()
        self._record(action="user.revoke_role", entity_type="User",
                     entity_id=str(user_id), after={"role_id": str(role_id)})


class RoleService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.roles: TenantRepository[Role] = TenantRepository(
            session, Role, self.tenant_id
        )

    def list_permissions(self) -> list[Permission]:
        return list(
            self.session.execute(
                select(Permission).order_by(Permission.code)
            ).scalars().all()
        )

    def create_role(self, *, code: str, name: str) -> Role:
        exists = self.session.execute(
            select(Role).where(Role.tenant_id == self.tenant_id, Role.code == code)
        ).scalar_one_or_none()
        if exists:
            raise ConflictError("A role with this code already exists.")
        role = Role(code=code, name=name)
        self.roles.add(role)
        self._record(action="role.create", entity_type="Role",
                     entity_id=str(role.id), after={"code": code})
        return role

    def grant_permission(self, role_id: uuid.UUID, permission_code: str) -> None:
        role = self.roles.get_or_404(role_id)
        perm = self.session.execute(
            select(Permission).where(Permission.code == permission_code)
        ).scalar_one_or_none()
        if perm is None:
            raise NotFoundError(f"Unknown permission: {permission_code}")
        exists = self.session.execute(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == perm.id,
            )
        ).scalar_one_or_none()
        if exists:
            return
        self.session.add(
            RolePermission(
                tenant_id=self.tenant_id, role_id=role.id, permission_id=perm.id
            )
        )
        self.session.flush()
        self._record(action="role.grant_permission", entity_type="Role",
                     entity_id=str(role_id), after={"permission": permission_code})
