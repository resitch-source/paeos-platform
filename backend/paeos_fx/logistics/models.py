"""Logistics models (Phase 8). Shipment records only — no carrier integration."""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin
from paeos_fx.platform.workflow import StateMachine, Transition

SHIPMENT_WORKFLOW = StateMachine(
    states=frozenset({"planned", "dispatched", "delivered", "cancelled"}),
    initial="planned",
    transitions=[
        Transition("planned", "dispatched", "dispatch"),
        Transition("dispatched", "delivered", "deliver"),
        Transition("planned", "cancelled", "cancel"),
    ],
)


class Shipment(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A shipment fulfilling a sales order (tracking record only)."""

    __tablename__ = "shipment"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    sales_order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.sales_order.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(16), default="planned", nullable=False)
    carrier_note: Mapped[str] = mapped_column(String(255), default="")
    dispatched_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
