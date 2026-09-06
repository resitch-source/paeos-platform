"""Inventory + warehouse models (Phase 6).

Item master, warehouses/storage locations, stock levels, and the stock-movement
ledger. Stock is tracked at the (item, warehouse) level; movements are signed
(positive = increase, negative = decrease) so a stock level equals the sum of
its movements. No geometry (warehouses link to org units, not farms).
"""

from __future__ import annotations

import datetime as dt
import enum
import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin
from paeos_fx.platform.masterdata import MasterDataMixin


class MovementType(enum.StrEnum):
    IN = "IN"
    OUT = "OUT"
    ADJUST = "ADJUST"


class InventoryItem(MasterDataMixin, Base):
    """A stock-keeping item (feed, seed, produce, supplies)."""

    __tablename__ = "inventory_item"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    base_uom: Mapped[str] = mapped_column(String(16), nullable=False, default="ea")
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_stocked: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Warehouse(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A storage facility (non-geographic; address is free text)."""

    __tablename__ = "warehouse"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    org_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.org_unit.id"), nullable=True
    )
    address: Mapped[str] = mapped_column(String(500), default="")


class StorageLocation(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A named location within a warehouse (bin/aisle/zone)."""

    __tablename__ = "storage_location"
    __table_args__ = (UniqueConstraint("warehouse_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.warehouse.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class StockLevel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Current on-hand quantity for an (item, warehouse) pair."""

    __tablename__ = "stock_level"
    __table_args__ = (UniqueConstraint("tenant_id", "item_id", "warehouse_id"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.inventory_item.id"), nullable=False, index=True
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.warehouse.id"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0"), nullable=False
    )


class StockMovement(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """An immutable stock-movement ledger entry (signed quantity)."""

    __tablename__ = "stock_movement"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.inventory_item.id"), nullable=False, index=True
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.warehouse.id"), nullable=False, index=True
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.storage_location.id"), nullable=True
    )
    movement_type: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)  # signed
    occurred_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    reference: Mapped[str] = mapped_column(String(128), default="")
