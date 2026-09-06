"""Organizational structure (Phase 1, Enterprise Core).

A hierarchical, **non-geographic** organizational unit (department / division /
business unit). Geography, farms, and spatial data belong to Phase 2 and are
deliberately excluded here.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService


class OrgUnit(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A node in a tenant's organizational hierarchy."""

    __tablename__ = "org_unit"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(64), default="department")
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.org_unit.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class OrgUnitService(DomainService):
    """Create and organize a tenant's org units."""

    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[OrgUnit] = TenantRepository(
            session, OrgUnit, self.tenant_id
        )

    def create(
        self,
        *,
        code: str,
        name: str,
        unit_type: str = "department",
        parent_id: uuid.UUID | None = None,
    ) -> OrgUnit:
        if parent_id is not None:
            # Parent must exist within the same tenant.
            self.repo.get_or_404(parent_id)
        unit = OrgUnit(
            code=code, name=name, unit_type=unit_type, parent_id=parent_id
        )
        self.repo.add(unit)
        self._record(action="org_unit.create", entity_type="OrgUnit",
                     entity_id=str(unit.id), after={"code": code, "name": name})
        self._emit("org_unit.created", {"id": str(unit.id), "code": code})
        return unit

    def set_parent(self, unit_id: uuid.UUID, parent_id: uuid.UUID | None) -> OrgUnit:
        unit = self.repo.get_or_404(unit_id)
        if parent_id == unit_id:
            raise BusinessRuleError("An org unit cannot be its own parent.")
        if parent_id is not None and self._would_cycle(unit_id, parent_id):
            raise BusinessRuleError("Reparenting would create a cycle.")
        unit.parent_id = parent_id
        self.session.flush()
        self._record(action="org_unit.reparent", entity_type="OrgUnit",
                     entity_id=str(unit_id), after={"parent_id": str(parent_id)})
        return unit

    def _would_cycle(self, unit_id: uuid.UUID, new_parent_id: uuid.UUID) -> bool:
        """Walk up from the proposed parent; a cycle exists if we reach unit_id."""
        seen: set[uuid.UUID] = set()
        current: uuid.UUID | None = new_parent_id
        while current is not None:
            if current == unit_id:
                return True
            if current in seen:
                break
            seen.add(current)
            parent = self.repo.get(current)
            current = parent.parent_id if parent else None
        return False
