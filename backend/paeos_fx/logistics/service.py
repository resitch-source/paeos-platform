"""Logistics service (Phase 8). Shipment lifecycle records only."""

from __future__ import annotations

import datetime as dt
import uuid

from paeos_fx.core.context import ExecutionContext
from paeos_fx.logistics.models import SHIPMENT_WORKFLOW, Shipment
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService
from paeos_fx.trading.models import SalesOrder


class ShipmentService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[Shipment] = TenantRepository(
            session, Shipment, self.tenant_id
        )
        self.orders: TenantRepository[SalesOrder] = TenantRepository(
            session, SalesOrder, self.tenant_id
        )

    def create(self, *, code: str, sales_order_id: uuid.UUID,
               carrier_note: str = "") -> Shipment:
        self.orders.get_or_404(sales_order_id)
        sh = Shipment(code=code, sales_order_id=sales_order_id, carrier_note=carrier_note,
                      status=SHIPMENT_WORKFLOW.initial)
        self.repo.add(sh)
        self._record(action="shipment.create", entity_type="Shipment",
                     entity_id=str(sh.id), after={"code": code})
        return sh

    def transition(self, shipment_id: uuid.UUID, event: str) -> Shipment:
        sh = self.repo.get_or_404(shipment_id)
        before = sh.status
        sh.status = SHIPMENT_WORKFLOW.fire(sh.status, event)
        if sh.status == "dispatched":
            sh.dispatched_at = dt.datetime.now(dt.UTC)
        elif sh.status == "delivered":
            sh.delivered_at = dt.datetime.now(dt.UTC)
        self.session.flush()
        self._record(action=f"shipment.{event}", entity_type="Shipment",
                     entity_id=str(shipment_id),
                     before={"status": before}, after={"status": sh.status})
        return sh

    def list(self, params=None):
        return self.repo.list(params)
