"""Multi-tenancy foundation (section D).

Defines the tenant entity and per-tenant settings. Row isolation itself is
enforced at the database by RLS policies (see migrations) driven by the
``app.tenant_id`` session variable set in :mod:`paeos_fx.db.session`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import (
    AuditMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A tenant (organization) — the root of an isolation boundary.

    The tenant registry itself is NOT tenant-scoped (it is the catalog of
    tenants) and is therefore administered by platform-level services only.
    """

    __tablename__ = "tenant"

    slug: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    locale: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    timezone: Mapped[str] = mapped_column(
        String(64), default="Asia/Manila", nullable=False
    )


class TenantSetting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Per-tenant configuration values (layer 2 of the configuration engine)."""

    __tablename__ = "tenant_setting"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.tenant.id"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class TenantService:
    """Platform-level tenant administration (not tenant-scoped)."""

    def __init__(self, session):
        self.session = session

    def create(self, *, slug: str, name: str) -> Tenant:
        tenant = Tenant(slug=slug, name=name)
        self.session.add(tenant)
        self.session.flush()
        return tenant

    def get(self, tenant_id: uuid.UUID) -> Tenant | None:
        return self.session.get(Tenant, tenant_id)
