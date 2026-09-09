"""Procurement models (Phase 6) — financial (approval gate #12).

Purchase orders carry monetary line pricing as integer minor units plus a
currency (the Foundation ``Money`` type). Prices are caller-supplied and stored
exactly; nothing is fabricated. No tax, discount, GL, or payment logic.
"""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin
from paeos_fx.platform.workflow import StateMachine, Transition

PURCHASE_ORDER_WORKFLOW = StateMachine(
    states=frozenset({"draft", "submitted", "approved", "received", "cancelled"}),
    initial="draft",
    transitions=[
        Transition("draft", "submitted", "submit"),
        Transition("submitted", "approved", "approve"),
        Transition("approved", "received", "receive"),
        Transition("draft", "cancelled", "cancel"),
        Transition("submitted", "cancelled", "cancel"),
        Transition("approved", "cancelled", "cancel"),
    ],
)


class Supplier(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A procurement supplier (catalog)."""

    __tablename__ = "supplier"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact: Mapped[str] = mapped_column(String(255), default="")


class PurchaseOrder(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A purchase order header."""

    __tablename__ = "purchase_order"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.supplier.id"), nullable=False, index=True
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.warehouse.id"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PHP")
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)
    order_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)


class PurchaseOrderLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A purchase-order line with exact monetary pricing (integer minor units)."""

    __tablename__ = "purchase_order_line"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.purchase_order.id"), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.inventory_item.id"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    line_total_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
