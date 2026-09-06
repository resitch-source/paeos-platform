"""Central inventory service (Phase 6).

The single authorized path for stock changes. Every movement atomically updates
the stock level, appends an immutable ledger entry, and writes an audit record.
Negative stock is blocked unless explicitly allowed. Domain code (including
procurement receipts) MUST route stock changes through this service.
"""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import select

from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.inventory.models import (
    MovementType,
    StockLevel,
    StockMovement,
)
from paeos_fx.platform.service import DomainService


class InventoryService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)

    def get_stock(self, item_id: uuid.UUID, warehouse_id: uuid.UUID) -> Decimal:
        level = self._get_level(item_id, warehouse_id)
        return level.quantity if level else Decimal("0")

    def _get_level(self, item_id: uuid.UUID, warehouse_id: uuid.UUID) -> StockLevel | None:
        return self.session.execute(
            select(StockLevel).where(
                StockLevel.tenant_id == self.tenant_id,
                StockLevel.item_id == item_id,
                StockLevel.warehouse_id == warehouse_id,
            )
        ).scalar_one_or_none()

    def _get_or_create_level(
        self, item_id: uuid.UUID, warehouse_id: uuid.UUID
    ) -> StockLevel:
        level = self._get_level(item_id, warehouse_id)
        if level is None:
            level = StockLevel(
                tenant_id=self.tenant_id, item_id=item_id,
                warehouse_id=warehouse_id, quantity=Decimal("0"),
            )
            self.session.add(level)
            self.session.flush()
        return level

    def record_movement(
        self,
        *,
        item_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        movement_type: MovementType,
        quantity: Decimal,
        reference: str = "",
        location_id: uuid.UUID | None = None,
        allow_negative: bool = False,
    ) -> StockMovement:
        """Apply a stock movement. Returns the ledger entry.

        For IN/OUT, ``quantity`` must be positive; the sign is derived from the
        type. For ADJUST, ``quantity`` is a signed delta.
        """
        quantity = Decimal(quantity)
        if movement_type in (MovementType.IN, MovementType.OUT) and quantity <= 0:
            raise BusinessRuleError("IN/OUT movement quantity must be positive.")
        signed = {
            MovementType.IN: quantity,
            MovementType.OUT: -quantity,
            MovementType.ADJUST: quantity,
        }[movement_type]

        level = self._get_or_create_level(item_id, warehouse_id)
        new_qty = level.quantity + signed
        if new_qty < 0 and not allow_negative:
            raise BusinessRuleError(
                "Movement would drive stock negative.",
                details={"current": str(level.quantity), "delta": str(signed)},
            )
        level.quantity = new_qty

        movement = StockMovement(
            tenant_id=self.tenant_id, item_id=item_id, warehouse_id=warehouse_id,
            location_id=location_id, movement_type=movement_type.value,
            quantity=signed, occurred_at=dt.datetime.now(dt.UTC), reference=reference,
        )
        self.session.add(movement)
        self.session.flush()
        self._record(action=f"stock.{movement_type.value.lower()}",
                     entity_type="StockMovement", entity_id=str(movement.id),
                     after={"item_id": str(item_id), "warehouse_id": str(warehouse_id),
                            "quantity": str(signed)})
        self._emit("stock.moved", {"item_id": str(item_id), "quantity": str(signed)})
        return movement

    def transfer(
        self,
        *,
        item_id: uuid.UUID,
        from_warehouse_id: uuid.UUID,
        to_warehouse_id: uuid.UUID,
        quantity: Decimal,
        reference: str = "",
    ) -> tuple[StockMovement, StockMovement]:
        """Move stock between warehouses as a paired OUT/IN in one transaction."""
        if from_warehouse_id == to_warehouse_id:
            raise BusinessRuleError("Transfer source and destination must differ.")
        out_mv = self.record_movement(
            item_id=item_id, warehouse_id=from_warehouse_id,
            movement_type=MovementType.OUT, quantity=quantity,
            reference=reference or "transfer",
        )
        in_mv = self.record_movement(
            item_id=item_id, warehouse_id=to_warehouse_id,
            movement_type=MovementType.IN, quantity=quantity,
            reference=reference or "transfer",
        )
        return out_mv, in_mv
