"""AgriIntelligence integration tests (Phase 10).

Fully non-geometry — runs on any PostgreSQL. Validates that an advisory agent
runs end-to-end through the guarded read-only tool registry, persists an
AgentRun + AiRecommendation, that a human decision records status without
touching domain data, and that recommendations are tenant-isolated.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import text

from paeos_fx.agri.services import MasterDataService
from paeos_fx.ai.models import AiRecommendation
from paeos_fx.ai.service import AgentService
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import AuthorizationError
from paeos_fx.inventory.models import InventoryItem, MovementType, Warehouse
from paeos_fx.inventory.service import InventoryService
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.onboarding_service import provision_tenant
from paeos_fx.platform.repository import TenantRepository

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]


def _ctx(tenant_id, user_id, permissions=None):
    return ExecutionContext(
        tenant_id=tenant_id, user_id=user_id,
        permissions=frozenset(permissions or perms.TENANT_ADMIN_PERMISSIONS),
    )


def _bind(s, tid):
    s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})


def _bootstrap(session_factory, slug="aico"):
    with session_factory() as s:
        res = provision_tenant(s, slug=slug, name="AI Co", admin_email=f"a@{slug}.test",
                               admin_password="supersecret123")
        s.commit()
        return _ctx(res.tenant.id, res.admin_user.id)


def _seed_stock(s, ctx, qty):
    item = MasterDataService(s, ctx, InventoryItem).create(code="OIL", name="Oil")
    wh = Warehouse(tenant_id=ctx.tenant_id, code="WH", name="WH")
    s.add(wh)
    s.flush()
    if qty > 0:
        InventoryService(s, ctx).record_movement(
            item_id=item.id, warehouse_id=wh.id, movement_type=MovementType.IN,
            quantity=Decimal(qty))
    return item, wh


def test_low_stock_agent_end_to_end(session_factory):
    ctx = _bootstrap(session_factory)
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        _seed_stock(s, ctx, 5)  # below threshold 10
        recs = AgentService(s, ctx).run("low_stock", {"threshold": "10"})
        assert len(recs) == 1
        assert recs[0].status == "proposed"
        assert recs[0].requires_human_approval is True
        assert recs[0].classification == "ESTIMATE"
        # Human decision records status; nothing downstream executes.
        decided = AgentService(s, ctx).decide(recs[0].id, "accept")
        assert decided.status == "accepted"
        assert decided.decided_by == ctx.user_id
        s.commit()


def test_agent_run_blocked_without_tool_permission(session_factory):
    ctx = _bootstrap(session_factory, slug="aico2")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        _seed_stock(s, ctx, 5)
        # Caller can run agents but lacks the inventory.stock.read tool permission.
        limited = _ctx(ctx.tenant_id, ctx.user_id, permissions={perms.AI_AGENT_RUN})
        with pytest.raises(AuthorizationError):
            AgentService(s, limited).run("low_stock", {"threshold": "10"})


def test_agent_tenant_isolation(session_factory):
    with session_factory() as s:
        a = provision_tenant(s, slug="aia", name="A", admin_email="a@aia.test",
                             admin_password="supersecret123")
        b = provision_tenant(s, slug="aib", name="B", admin_email="a@aib.test",
                             admin_password="supersecret123")
        s.commit()
        a_id, a_admin, b_id = a.tenant.id, a.admin_user.id, b.tenant.id
    ctx_a = _ctx(a_id, a_admin)
    with session_factory() as s:
        _bind(s, a_id)
        _seed_stock(s, ctx_a, 1)
        AgentService(s, ctx_a).run("low_stock", {"threshold": "10"})
        s.commit()
    with session_factory() as s:
        _bind(s, b_id)
        assert TenantRepository(s, AiRecommendation, b_id).list().total == 0
