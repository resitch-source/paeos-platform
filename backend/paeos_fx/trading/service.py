"""Trading + marketplace services (Phase 8) — financial (gate #12).

Fulfilling a sales order posts stock OUT through the central InventoryService.
Line totals are computed exactly from caller-supplied unit prices and quantities
(integer minor units). No payment/AR/GL logic.
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select

from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.inventory.models import MovementType
from paeos_fx.inventory.service import InventoryService
from paeos_fx.platform.currency import Money
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService
from paeos_fx.trading.models import (
    SALES_ORDER_WORKFLOW,
    Customer,
    Listing,
    SalesOrder,
    SalesOrderLine,
)


def _line_total_minor(unit_price_minor: int, quantity: Decimal) -> int:
    total = (Decimal(unit_price_minor) * Decimal(quantity)).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(total)


class CustomerService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[Customer] = TenantRepository(
            session, Customer, self.tenant_id
        )

    def create(self, *, code: str, name: str, contact: str = "") -> Customer:
        c = Customer(code=code, name=name, contact=contact)
        self.repo.add(c)
        self._record(action="customer.create", entity_type="Customer",
                     entity_id=str(c.id), after={"code": code})
        return c


class ListingService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[Listing] = TenantRepository(
            session, Listing, self.tenant_id
        )

    def create(self, *, code: str, item_id: uuid.UUID, quantity_available: Decimal,
               unit_price: Money) -> Listing:
        listing = Listing(
            code=code, item_id=item_id, quantity_available=Decimal(quantity_available),
            unit_price_minor=unit_price.amount_minor, currency=unit_price.currency,
        )
        self.repo.add(listing)
        self._record(action="listing.create", entity_type="Listing",
                     entity_id=str(listing.id), after={"code": code})
        return listing

    def set_status(self, listing_id: uuid.UUID, status: str) -> Listing:
        if status not in {"active", "paused", "closed"}:
            raise BusinessRuleError("Invalid listing status.")
        listing = self.repo.get_or_404(listing_id)
        listing.status = status
        self.session.flush()
        return listing

    def list(self, params=None):
        return self.repo.list(params)


class SalesOrderService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[SalesOrder] = TenantRepository(
            session, SalesOrder, self.tenant_id
        )

    def create(self, *, code: str, customer_id: uuid.UUID, warehouse_id: uuid.UUID,
               currency: str = "PHP") -> SalesOrder:
        so = SalesOrder(code=code, customer_id=customer_id, warehouse_id=warehouse_id,
                        currency=currency.upper(), status=SALES_ORDER_WORKFLOW.initial)
        self.repo.add(so)
        self._record(action="sales_order.create", entity_type="SalesOrder",
                     entity_id=str(so.id), after={"code": code})
        return so

    def add_line(self, *, order_id: uuid.UUID, item_id: uuid.UUID, quantity: Decimal,
                 unit_price: Money) -> SalesOrderLine:
        so = self.repo.get_or_404(order_id)
        if so.status != "draft":
            raise BusinessRuleError("Lines can only be added to a draft order.")
        if unit_price.currency != so.currency:
            raise BusinessRuleError(
                f"Line currency {unit_price.currency} != order currency {so.currency}."
            )
        if Decimal(quantity) <= 0:
            raise BusinessRuleError("Line quantity must be positive.")
        line = SalesOrderLine(
            tenant_id=self.tenant_id, sales_order_id=so.id, item_id=item_id,
            quantity=Decimal(quantity), unit_price_minor=unit_price.amount_minor,
            line_total_minor=_line_total_minor(unit_price.amount_minor, Decimal(quantity)),
        )
        self.session.add(line)
        self.session.flush()
        self._record(action="sales_order.add_line", entity_type="SalesOrderLine",
                     entity_id=str(line.id), after={"order_id": str(order_id)})
        return line

    def order_total(self, order_id: uuid.UUID) -> Money:
        so = self.repo.get_or_404(order_id)
        lines = self.session.execute(
            select(SalesOrderLine).where(
                SalesOrderLine.tenant_id == self.tenant_id,
                SalesOrderLine.sales_order_id == order_id,
            )
        ).scalars().all()
        return Money(sum(line.line_total_minor for line in lines), so.currency)

    def transition(self, order_id: uuid.UUID, event: str) -> SalesOrder:
        so = self.repo.get_or_404(order_id)
        before = so.status
        so.status = SALES_ORDER_WORKFLOW.fire(so.status, event)
        self.session.flush()
        self._record(action=f"sales_order.{event}", entity_type="SalesOrder",
                     entity_id=str(order_id),
                     before={"status": before}, after={"status": so.status})
        return so

    def fulfill(self, order_id: uuid.UUID) -> SalesOrder:
        """Fulfill a confirmed order: post stock OUT via the central service."""
        so = self.repo.get_or_404(order_id)
        if so.status != "confirmed":
            raise BusinessRuleError("Only a confirmed order can be fulfilled.")
        lines = self.session.execute(
            select(SalesOrderLine).where(
                SalesOrderLine.tenant_id == self.tenant_id,
                SalesOrderLine.sales_order_id == order_id,
            )
        ).scalars().all()
        inventory = InventoryService(self.session, self.ctx)
        for line in lines:
            inventory.record_movement(
                item_id=line.item_id, warehouse_id=so.warehouse_id,
                movement_type=MovementType.OUT, quantity=line.quantity,
                reference=f"SO:{so.code}",
            )
        so.status = SALES_ORDER_WORKFLOW.fire(so.status, "fulfill")
        self.session.flush()
        self._record(action="sales_order.fulfill", entity_type="SalesOrder",
                     entity_id=str(order_id), after={"status": so.status})
        self._emit("sales_order.fulfilled", {"id": str(order_id)})
        return so

    def list(self, params=None):
        return self.repo.list(params)
