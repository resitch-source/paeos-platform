"""Trading + marketplace models (Phase 8).

Customers, marketplace listings, and sales orders with exact monetary line
pricing (integer minor units). Prices/quantities are caller-supplied; nothing is
fabricated. No payment/AR/GL logic.
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

SALES_ORDER_WORKFLOW = StateMachine(
    states=frozenset({"draft", "confirmed", "fulfilled", "closed", "cancelled"}),
    initial="draft",
    transitions=[
        Transition("draft", "confirmed", "confirm"),
        Transition("confirmed", "fulfilled", "fulfill"),
        Transition("fulfilled", "closed", "close"),
        Transition("draft", "cancelled", "cancel"),
        Transition("confirmed", "cancelled", "cancel"),
    ],
)


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A buyer/customer (catalog)."""

    __tablename__ = "customer"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact: Mapped[str] = mapped_column(String(255), default="")


class Listing(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A marketplace offer to sell an item at a caller-supplied price."""

    __tablename__ = "listing"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.inventory_item.id"), nullable=False, index=True
    )
    quantity_available: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0"), nullable=False
    )
    unit_price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PHP")
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)


class SalesOrder(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A sales order fulfilled from a warehouse."""

    __tablename__ = "sales_order"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.customer.id"), nullable=False, index=True
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.warehouse.id"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PHP")
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)
    order_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)


class SalesOrderLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A sales-order line with exact monetary pricing (integer minor units)."""

    __tablename__ = "sales_order_line"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    sales_order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.sales_order.id"), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.inventory_item.id"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    line_total_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
