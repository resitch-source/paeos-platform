"""Inventory + procurement integration tests (Phase 6).

Fully non-geometry — runs on any PostgreSQL via ``session_factory``. Validates
the central inventory service (movements, transfers, negative-stock block),
procurement PO lifecycle + receipt-into-stock, monetary totals, and tenant
isolation.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import text

from paeos_fx.agri.services import MasterDataService
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.inventory.models import InventoryItem, MovementType, Warehouse
from paeos_fx.inventory.service import InventoryService
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.currency import Money
from paeos_fx.platform.onboarding_service import provision_tenant
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.procurement.models import PurchaseOrder, Supplier
from paeos_fx.procurement.service import PurchaseOrderService

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]


def _ctx(tenant_id, user_id):
    return ExecutionContext(
        tenant_id=tenant_id, user_id=user_id,
        permissions=frozenset(perms.TENANT_ADMIN_PERMISSIONS),
    )


def _bind(session, tenant_id):
    session.execute(text("SELECT set_config('app.tenant_id', :t, true)"),
                    {"t": str(tenant_id)})


def _bootstrap(session_factory, slug="invco"):
    with session_factory() as s:
        res = provision_tenant(
            s, slug=slug, name="Inv Co", admin_email=f"a@{slug}.test",
            admin_password="supersecret123",
        )
        s.commit()
        return _ctx(res.tenant.id, res.admin_user.id)


def _warehouse(session, tenant_id, code="WH1") -> uuid.UUID:
    wh = Warehouse(tenant_id=tenant_id, code=code, name=code)
    session.add(wh)
    session.flush()
    return wh.id


def test_inventory_movements_and_negative_block(session_factory):
    ctx = _bootstrap(session_factory)
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        item = MasterDataService(s, ctx, InventoryItem).create(code="FEED", name="Feed")
        wh = _warehouse(s, ctx.tenant_id)
        inv = InventoryService(s, ctx)
        inv.record_movement(item_id=item.id, warehouse_id=wh,
                            movement_type=MovementType.IN, quantity=Decimal("100"))
        inv.record_movement(item_id=item.id, warehouse_id=wh,
                            movement_type=MovementType.OUT, quantity=Decimal("30"))
        assert inv.get_stock(item.id, wh) == Decimal("70")
        with pytest.raises(BusinessRuleError):
            inv.record_movement(item_id=item.id, warehouse_id=wh,
                                movement_type=MovementType.OUT, quantity=Decimal("1000"))
        s.commit()


def test_inventory_transfer(session_factory):
    ctx = _bootstrap(session_factory, slug="invco2")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        item = MasterDataService(s, ctx, InventoryItem).create(code="SEED", name="Seed")
        wh1 = _warehouse(s, ctx.tenant_id, "A")
        wh2 = _warehouse(s, ctx.tenant_id, "B")
        inv = InventoryService(s, ctx)
        inv.record_movement(item_id=item.id, warehouse_id=wh1,
                            movement_type=MovementType.IN, quantity=Decimal("50"))
        inv.transfer(item_id=item.id, from_warehouse_id=wh1, to_warehouse_id=wh2,
                     quantity=Decimal("20"))
        assert inv.get_stock(item.id, wh1) == Decimal("30")
        assert inv.get_stock(item.id, wh2) == Decimal("20")
        s.commit()


def test_po_lifecycle_receive_creates_stock(session_factory):
    ctx = _bootstrap(session_factory, slug="poco")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        item = MasterDataService(s, ctx, InventoryItem).create(code="UREA", name="Urea")
        wh = _warehouse(s, ctx.tenant_id)
        sup = Supplier(tenant_id=ctx.tenant_id, code="SUP1", name="Supplier 1")
        s.add(sup)
        s.flush()

        po_svc = PurchaseOrderService(s, ctx)
        po = po_svc.create(code="PO1", supplier_id=sup.id, warehouse_id=wh, currency="PHP")
        po_svc.add_line(po_id=po.id, item_id=item.id, quantity=Decimal("10"),
                        unit_price=Money.from_decimal("25.00", "PHP"))
        total = po_svc.order_total(po.id)
        assert total.amount_minor == 25000  # 10 * 25.00 = 250.00

        po_svc.transition(po.id, "submit")
        po_svc.transition(po.id, "approve")
        received = po_svc.receive(po.id)
        assert received.status == "received"

        # Receipt posted stock IN via the central service.
        assert InventoryService(s, ctx).get_stock(item.id, wh) == Decimal("10")
        s.commit()


def test_receive_requires_approved(session_factory):
    ctx = _bootstrap(session_factory, slug="poco2")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        item = MasterDataService(s, ctx, InventoryItem).create(code="X", name="X")
        wh = _warehouse(s, ctx.tenant_id)
        sup = Supplier(tenant_id=ctx.tenant_id, code="S", name="S")
        s.add(sup)
        s.flush()
        po_svc = PurchaseOrderService(s, ctx)
        po = po_svc.create(code="PO9", supplier_id=sup.id, warehouse_id=wh)
        po_svc.add_line(po_id=po.id, item_id=item.id, quantity=Decimal("1"),
                        unit_price=Money.from_decimal("1.00", "PHP"))
        with pytest.raises(BusinessRuleError):
            po_svc.receive(po.id)  # still draft


def test_inventory_tenant_isolation(session_factory):
    with session_factory() as s:
        a = provision_tenant(s, slug="ia", name="A", admin_email="a@ia.test",
                             admin_password="supersecret123")
        b = provision_tenant(s, slug="ib", name="B", admin_email="a@ib.test",
                             admin_password="supersecret123")
        s.commit()
        a_id, a_admin, b_id = a.tenant.id, a.admin_user.id, b.tenant.id
    ctx_a = _ctx(a_id, a_admin)
    with session_factory() as s:
        _bind(s, a_id)
        item = MasterDataService(s, ctx_a, InventoryItem).create(code="SEC", name="Secret")
        wh = _warehouse(s, a_id)
        sup = Supplier(tenant_id=a_id, code="S", name="S")
        s.add(sup)
        s.flush()
        PurchaseOrderService(s, ctx_a).create(code="SECRETPO", supplier_id=sup.id,
                                              warehouse_id=wh)
        InventoryService(s, ctx_a).record_movement(
            item_id=item.id, warehouse_id=wh, movement_type=MovementType.IN,
            quantity=Decimal("5"))
        s.commit()
    with session_factory() as s:
        _bind(s, b_id)
        assert TenantRepository(s, Warehouse, b_id).list().total == 0
        assert TenantRepository(s, PurchaseOrder, b_id).list().total == 0
