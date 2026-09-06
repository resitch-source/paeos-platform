"""Processing / MES integration tests (Phase 7).

Fully non-geometry — runs on any PostgreSQL. Validates that a production run
consumes inputs and produces outputs through the central inventory service,
telemetry-driven twin state, mass-balance simulation persistence, and tenant
isolation.
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
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.onboarding_service import provision_tenant
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.processing.models import ProductionRun
from paeos_fx.processing.service import (
    ProcessDefinitionService,
    ProcessingAssetService,
    ProcessSimulationService,
    ProductionRunService,
)

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]


def _ctx(tenant_id, user_id):
    return ExecutionContext(tenant_id=tenant_id, user_id=user_id,
                            permissions=frozenset(perms.TENANT_ADMIN_PERMISSIONS))


def _bind(s, tid):
    s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})


def _bootstrap(session_factory, slug="mesco"):
    with session_factory() as s:
        res = provision_tenant(s, slug=slug, name="MES Co", admin_email=f"a@{slug}.test",
                               admin_password="supersecret123")
        s.commit()
        return _ctx(res.tenant.id, res.admin_user.id)


def test_production_run_consumes_and_produces_stock(session_factory):
    ctx = _bootstrap(session_factory)
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        md = MasterDataService(s, ctx, InventoryItem)
        copra = md.create(code="COPRA", name="Copra")
        oil = md.create(code="OIL", name="Coconut Oil")
        wh = Warehouse(tenant_id=ctx.tenant_id, code="WH", name="WH")
        s.add(wh)
        s.flush()

        # Seed copra stock via the central service.
        inv = InventoryService(s, ctx)
        inv.record_movement(item_id=copra.id, warehouse_id=wh.id,
                            movement_type=MovementType.IN, quantity=Decimal("1000"))

        # Recipe: 1000 copra -> 620 oil per batch (tenant-defined quantities).
        pd = ProcessDefinitionService(s, ctx)
        d = pd.create(code="CO_OIL", name="Coconut oil extraction")
        pd.add_input(definition_id=d.id, item_id=copra.id, quantity_per_batch=Decimal("1000"))
        pd.add_output(definition_id=d.id, item_id=oil.id, quantity_per_batch=Decimal("620"))

        runs = ProductionRunService(s, ctx)
        run = runs.create(code="RUN1", definition_id=d.id, warehouse_id=wh.id,
                          batch_size=Decimal("1"))
        runs.start(run.id)
        runs.complete(run.id)

        # Inputs consumed, outputs produced — via the central inventory service.
        assert inv.get_stock(copra.id, wh.id) == Decimal("0")
        assert inv.get_stock(oil.id, wh.id) == Decimal("620")
        s.commit()


def test_run_complete_blocks_without_stock(session_factory):
    ctx = _bootstrap(session_factory, slug="mesco2")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        md = MasterDataService(s, ctx, InventoryItem)
        inp = md.create(code="IN", name="Input")
        outp = md.create(code="OUT", name="Output")
        wh = Warehouse(tenant_id=ctx.tenant_id, code="W", name="W")
        s.add(wh)
        s.flush()
        pd = ProcessDefinitionService(s, ctx)
        d = pd.create(code="P", name="P")
        pd.add_input(definition_id=d.id, item_id=inp.id, quantity_per_batch=Decimal("5"))
        pd.add_output(definition_id=d.id, item_id=outp.id, quantity_per_batch=Decimal("1"))
        runs = ProductionRunService(s, ctx)
        run = runs.create(code="R", definition_id=d.id, warehouse_id=wh.id)
        runs.start(run.id)
        with pytest.raises(BusinessRuleError):  # no input stock
            runs.complete(run.id)


def test_twin_state_from_telemetry(session_factory):
    ctx = _bootstrap(session_factory, slug="twinco")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        svc = ProcessingAssetService(s, ctx)
        asset = svc.create(code="EXP1", name="Expeller 1")
        svc.ingest_telemetry(asset_id=asset.id, metric="temperature", value=Decimal("70.5"),
                             uom="degC")
        svc.ingest_telemetry(asset_id=asset.id, metric="throughput", value=Decimal("120"),
                             uom="kg/h")
        state = svc.twin_state(asset.id)
        assert state.metrics["temperature"] == 70.5
        assert state.metrics["throughput"] == 120.0
        s.commit()


def test_mass_balance_run_persisted(gis_session_factory):
    # Persists into the shared simulation_run table, which is PostGIS-gated via
    # its cropping_cycle -> parcel FK closure; the math/provenance is unit-tested.
    ctx = _bootstrap(gis_session_factory, slug="simco")
    with gis_session_factory() as s:
        _bind(s, ctx.tenant_id)
        run, result = ProcessSimulationService(s, ctx).run_mass_balance(
            scenario="batch-1", parameters={"input_mass": 1000, "yield_fraction": 0.62},
        )
        assert result.outputs["output_mass"] == 620.0
        assert run.record["validation_status"] == "SIMULATION"
        s.commit()


def test_processing_tenant_isolation(session_factory):
    with session_factory() as s:
        a = provision_tenant(s, slug="pra", name="A", admin_email="a@pra.test",
                             admin_password="supersecret123")
        b = provision_tenant(s, slug="prb", name="B", admin_email="a@prb.test",
                             admin_password="supersecret123")
        s.commit()
        a_id, a_admin, b_id = a.tenant.id, a.admin_user.id, b.tenant.id
    ctx_a = _ctx(a_id, a_admin)
    with session_factory() as s:
        _bind(s, a_id)
        wh = Warehouse(tenant_id=a_id, code="W", name="W")
        s.add(wh)
        s.flush()
        pd = ProcessDefinitionService(s, ctx_a).create(code="SECRET", name="Secret")
        ProductionRunService(s, ctx_a).create(code="R", definition_id=pd.id,
                                              warehouse_id=wh.id)
        s.commit()
    with session_factory() as s:
        _bind(s, b_id)
        assert TenantRepository(s, ProductionRun, b_id).list().total == 0
