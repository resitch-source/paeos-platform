"""Trading + logistics integration tests (Phase 8).

Fully non-geometry — runs on any PostgreSQL. Validates the sales-order lifecycle,
fulfilment posting stock OUT through the central inventory service, order totals,
shipment flow, and tenant isolation.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import text

from paeos_fx.agri.services import MasterDataService
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.inventory.models import InventoryItem, MovementType, Warehouse
from paeos_fx.inventory.service import InventoryService
from paeos_fx.logistics.service import ShipmentService
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.currency import Money
from paeos_fx.platform.onboarding_service import provision_tenant
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.trading.models import SalesOrder
from paeos_fx.trading.service import CustomerService, SalesOrderService

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]


def _ctx(tenant_id, user_id):
    return ExecutionContext(tenant_id=tenant_id, user_id=user_id,
                            permissions=frozenset(perms.TENANT_ADMIN_PERMISSIONS))


def _bind(s, tid):
    s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})


def _bootstrap(session_factory, slug="tradeco"):
    with session_factory() as s:
        res = provision_tenant(s, slug=slug, name="Trade Co", admin_email=f"a@{slug}.test",
                               admin_password="supersecret123")
        s.commit()
        return _ctx(res.tenant.id, res.admin_user.id)


def test_order_lifecycle_and_fulfillment(session_factory):
    ctx = _bootstrap(session_factory)
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        item = MasterDataService(s, ctx, InventoryItem).create(code="OIL", name="Oil")
        wh = Warehouse(tenant_id=ctx.tenant_id, code="WH", name="WH")
        s.add(wh)
        s.flush()
        InventoryService(s, ctx).record_movement(
            item_id=item.id, warehouse_id=wh.id, movement_type=MovementType.IN,
            quantity=Decimal("500"))

        cust = CustomerService(s, ctx).create(code="C1", name="Buyer 1")
        so_svc = SalesOrderService(s, ctx)
        so = so_svc.create(code="SO1", customer_id=cust.id, warehouse_id=wh.id)
        so_svc.add_line(order_id=so.id, item_id=item.id, quantity=Decimal("100"),
                        unit_price=Money.from_decimal("80.00", "PHP"))
        assert so_svc.order_total(so.id).amount_minor == 800000  # 100 * 80.00

        so_svc.transition(so.id, "confirm")
        so_svc.fulfill(so.id)
        # Fulfilment posted stock OUT via the central service.
        assert InventoryService(s, ctx).get_stock(item.id, wh.id) == Decimal("400")
        s.commit()


def test_fulfill_blocks_insufficient_stock(session_factory):
    ctx = _bootstrap(session_factory, slug="tradeco2")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        item = MasterDataService(s, ctx, InventoryItem).create(code="X", name="X")
        wh = Warehouse(tenant_id=ctx.tenant_id, code="W", name="W")
        s.add(wh)
        s.flush()
        cust = CustomerService(s, ctx).create(code="C", name="C")
        so_svc = SalesOrderService(s, ctx)
        so = so_svc.create(code="SO", customer_id=cust.id, warehouse_id=wh.id)
        so_svc.add_line(order_id=so.id, item_id=item.id, quantity=Decimal("10"),
                        unit_price=Money.from_decimal("1.00", "PHP"))
        so_svc.transition(so.id, "confirm")
        with pytest.raises(BusinessRuleError):  # no stock
            so_svc.fulfill(so.id)


def test_shipment_flow(session_factory):
    ctx = _bootstrap(session_factory, slug="shipco")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        wh = Warehouse(tenant_id=ctx.tenant_id, code="W", name="W")
        s.add(wh)
        s.flush()
        cust = CustomerService(s, ctx).create(code="C", name="C")
        so = SalesOrderService(s, ctx).create(code="SO", customer_id=cust.id,
                                              warehouse_id=wh.id)
        sh_svc = ShipmentService(s, ctx)
        sh = sh_svc.create(code="SH1", sales_order_id=so.id, carrier_note="truck A")
        sh_svc.transition(sh.id, "dispatch")
        delivered = sh_svc.transition(sh.id, "deliver")
        assert delivered.status == "delivered"
        assert delivered.dispatched_at is not None
        assert delivered.delivered_at is not None
        s.commit()


def test_trading_tenant_isolation(session_factory):
    with session_factory() as s:
        a = provision_tenant(s, slug="tra", name="A", admin_email="a@tra.test",
                             admin_password="supersecret123")
        b = provision_tenant(s, slug="trb", name="B", admin_email="a@trb.test",
                             admin_password="supersecret123")
        s.commit()
        a_id, a_admin, b_id = a.tenant.id, a.admin_user.id, b.tenant.id
    ctx_a = _ctx(a_id, a_admin)
    with session_factory() as s:
        _bind(s, a_id)
        wh = Warehouse(tenant_id=a_id, code="W", name="W")
        s.add(wh)
        s.flush()
        cust = CustomerService(s, ctx_a).create(code="C", name="C")
        SalesOrderService(s, ctx_a).create(code="SECRET", customer_id=cust.id,
                                           warehouse_id=wh.id)
        s.commit()
    with session_factory() as s:
        _bind(s, b_id)
        assert TenantRepository(s, SalesOrder, b_id).list().total == 0
