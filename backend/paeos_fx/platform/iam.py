"""IAM / RBAC foundation (section E).

Entities: User (tenant-scoped), Role (tenant-scoped), Permission (global
catalog), and the role↔permission / user↔role associations. Authorization is a
simple, auditable permission check; richer policies plug in later behind
:class:`AccessControl`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import AuthorizationError
from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Global permission catalog entry, e.g. ``iam.user.read``."""

    __tablename__ = "permission"

    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")


class Role(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A tenant-scoped role that groups permissions."""

    __tablename__ = "role"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class RolePermission(UUIDPrimaryKeyMixin, Base):
    """Association: which permissions a role grants."""

    __tablename__ = "role_permission"
    __table_args__ = (UniqueConstraint("role_id", "permission_id"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.role.id"), nullable=False
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.permission.id"), nullable=False
    )


class User(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A tenant-scoped user identity (authentication credential holder)."""

    __tablename__ = "app_user"
    __table_args__ = (UniqueConstraint("tenant_id", "email"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UserRole(UUIDPrimaryKeyMixin, Base):
    """Association: which roles a user holds within a tenant."""

    __tablename__ = "user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.app_user.id"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.role.id"), nullable=False
    )


class AccessControl:
    """Permission-check helper used by API/domain layers.

    Kept intentionally small: it answers "does this context hold permission X?"
    Concrete permission resolution (role expansion) is performed by domain
    services against the DB; here we evaluate against the context's permission
    set, which is populated at authentication time.
    """

    @staticmethod
    def has_permission(ctx: ExecutionContext, permission: str) -> bool:
        return permission in ctx.permissions

    @staticmethod
    def require(ctx: ExecutionContext, permission: str) -> None:
        if not AccessControl.has_permission(ctx, permission):
            raise AuthorizationError(
                "Missing required permission.",
                details={"required_permission": permission},
            )
