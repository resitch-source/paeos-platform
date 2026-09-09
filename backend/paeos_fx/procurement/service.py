"""Procurement service (Phase 6) — financial (approval gate #12).

Builds and advances purchase orders and, on receipt, posts stock IN through the
central :class:`InventoryService` (never bypassing it). Line totals are computed
exactly from caller-supplied unit prices and quantities using integer minor
units; no prices are fabricated and there is no tax/GL/payment logic.
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_UP, Decimal

from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.inventory.models import MovementType
from paeos_fx.inventory.service import InventoryService
from paeos_fx.platform.currency import Money
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService
from paeos_fx.procurement.models import (
    PURCHASE_ORDER_WORKFLOW,
    PurchaseOrder,
    PurchaseOrderLine,
)


def _line_total_minor(unit_price_minor: int, quantity: Decimal) -> int:
    """Exact line total in minor units: round(unit_price * quantity)."""
    total = (Decimal(unit_price_minor) * Decimal(quantity)).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(total)


class PurchaseOrderService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[PurchaseOrder] = TenantRepository(
            session, PurchaseOrder, self.tenant_id
        )

    def create(
        self, *, code: str, supplier_id: uuid.UUID, warehouse_id: uuid.UUID,
        currency: str = "PHP",
    ) -> PurchaseOrder:
        po = PurchaseOrder(
            code=code, supplier_id=supplier_id, warehouse_id=warehouse_id,
            currency=currency.upper(), status=PURCHASE_ORDER_WORKFLOW.initial,
        )
        self.repo.add(po)
        self._record(action="purchase_order.create", entity_type="PurchaseOrder",
                     entity_id=str(po.id), after={"code": code})
        return po

    def add_line(
        self, *, po_id: uuid.UUID, item_id: uuid.UUID, quantity: Decimal,
        unit_price: Money,
    ) -> PurchaseOrderLine:
        po = self.repo.get_or_404(po_id)
        if po.status != "draft":
            raise BusinessRuleError("Lines can only be added to a draft PO.")
        if unit_price.currency != po.currency:
            raise BusinessRuleError(
                f"Line currency {unit_price.currency} != PO currency {po.currency}."
            )
        if Decimal(quantity) <= 0:
            raise BusinessRuleError("Line quantity must be positive.")
        total_minor = _line_total_minor(unit_price.amount_minor, Decimal(quantity))
        line = PurchaseOrderLine(
            tenant_id=self.tenant_id, purchase_order_id=po.id, item_id=item_id,
            quantity=Decimal(quantity), unit_price_minor=unit_price.amount_minor,
            line_total_minor=total_minor,
        )
        self.session.add(line)
        self.session.flush()
        self._record(action="purchase_order.add_line", entity_type="PurchaseOrderLine",
                     entity_id=str(line.id), after={"po_id": str(po_id)})
        return line

    def order_total(self, po_id: uuid.UUID) -> Money:
        po = self.repo.get_or_404(po_id)
        from sqlalchemy import select

        total = self.session.execute(
            select(PurchaseOrderLine).where(
                PurchaseOrderLine.purchase_order_id == po_id,
                PurchaseOrderLine.tenant_id == self.tenant_id,
            )
        ).scalars().all()
        return Money(sum(line.line_total_minor for line in total), po.currency)

    def transition(self, po_id: uuid.UUID, event: str) -> PurchaseOrder:
        po = self.repo.get_or_404(po_id)
        before = po.status
        po.status = PURCHASE_ORDER_WORKFLOW.fire(po.status, event)
        self.session.flush()
        self._record(action=f"purchase_order.{event}", entity_type="PurchaseOrder",
                     entity_id=str(po_id),
                     before={"status": before}, after={"status": po.status})
        return po

    def receive(self, po_id: uuid.UUID) -> PurchaseOrder:
        """Receive an approved PO: post stock IN via the central service."""
        po = self.repo.get_or_404(po_id)
        if po.status != "approved":
            raise BusinessRuleError("Only an approved PO can be received.")
        from sqlalchemy import select

        lines = self.session.execute(
            select(PurchaseOrderLine).where(
                PurchaseOrderLine.purchase_order_id == po_id,
                PurchaseOrderLine.tenant_id == self.tenant_id,
            )
        ).scalars().all()
        inventory = InventoryService(self.session, self.ctx)
        for line in lines:
            inventory.record_movement(
                item_id=line.item_id, warehouse_id=po.warehouse_id,
                movement_type=MovementType.IN, quantity=line.quantity,
                reference=f"PO:{po.code}",
            )
        po.status = PURCHASE_ORDER_WORKFLOW.fire(po.status, "receive")
        self.session.flush()
        self._record(action="purchase_order.receive", entity_type="PurchaseOrder",
                     entity_id=str(po_id), after={"status": po.status})
        return po
