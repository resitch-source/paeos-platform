"""Crop production integration tests (Phase 3).

Uses ``gis_session_factory`` (PostGIS-gated) because cropping cycles reference
parcels/farms, which are geometry tables. Covers cycle workflow, harvest
recording, simulation-run persistence, and cross-tenant isolation. Parcel rows
are seeded directly with geometry columns left null.
"""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import text

from paeos_fx.agri.masterdata import Crop
from paeos_fx.agri.production import CroppingCycle
from paeos_fx.agri.production_services import (
    CroppingCycleService,
    CropSimulationService,
    HarvestService,
)
from paeos_fx.agri.services import MasterDataService
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.onboarding_service import provision_tenant
from paeos_fx.platform.repository import TenantRepository

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]


def _ctx(tenant_id, user_id):
    return ExecutionContext(
        tenant_id=tenant_id, user_id=user_id,
        permissions=frozenset(perms.TENANT_ADMIN_PERMISSIONS),
    )


def _bind(session, tenant_id):
    session.execute(text("SELECT set_config('app.tenant_id', :t, true)"),
                    {"t": str(tenant_id)})


def _seed_parcel(session, tenant_id) -> uuid.UUID:
    """Create a parcel row directly (no geometry) for FK targets."""
    parcel_id = uuid.uuid4()
    farm_id = uuid.uuid4()
    session.execute(
        text(
            "INSERT INTO platform.agri_farm (id, tenant_id, code, name, "
            "area_classification) VALUES (:id, :t, 'F', 'Farm', 'UNKNOWN')"
        ),
        {"id": farm_id, "t": str(tenant_id)},
    )
    session.execute(
        text(
            "INSERT INTO platform.agri_land_parcel (id, tenant_id, code, name, "
            "farm_id, area_classification) VALUES (:id, :t, 'P', 'Parcel', :f, 'UNKNOWN')"
        ),
        {"id": parcel_id, "t": str(tenant_id), "f": farm_id},
    )
    return parcel_id


def _bootstrap(gis_session_factory):
    with gis_session_factory() as s:
        res = provision_tenant(
            s, slug="cropco", name="Crop Co", admin_email="a@crop.test",
            admin_password="supersecret123",
        )
        s.commit()
        ctx = _ctx(res.tenant.id, res.admin_user.id)
    return ctx


def test_cycle_workflow_and_harvest(gis_session_factory):
    ctx = _bootstrap(gis_session_factory)
    with gis_session_factory() as s:
        _bind(s, ctx.tenant_id)
        parcel_id = _seed_parcel(s, ctx.tenant_id)
        crop = MasterDataService(s, ctx, Crop).create(code="RICE", name="Rice")
        cycles = CroppingCycleService(s, ctx)
        cycle = cycles.create(code="C1", parcel_id=parcel_id, crop_id=crop.id)
        assert cycle.status == "planned"
        cycles.transition(cycle.id, "plant")
        cycles.transition(cycle.id, "start_growth")
        grown = cycles.transition(cycle.id, "harvest")
        assert grown.status == "harvested"

        h = HarvestService(s, ctx).record_harvest(
            cycle_id=cycle.id, harvest_date=dt.date(2026, 6, 1),
            quantity=Decimal("1234.5"), uom="kg",
        )
        assert h.quantity == Decimal("1234.5")
        s.commit()


def test_illegal_transition_rejected(gis_session_factory):
    ctx = _bootstrap(gis_session_factory)
    with gis_session_factory() as s:
        _bind(s, ctx.tenant_id)
        parcel_id = _seed_parcel(s, ctx.tenant_id)
        crop = MasterDataService(s, ctx, Crop).create(code="CORN", name="Corn")
        cycle = CroppingCycleService(s, ctx).create(
            code="C2", parcel_id=parcel_id, crop_id=crop.id
        )
        with pytest.raises(BusinessRuleError):
            CroppingCycleService(s, ctx).transition(cycle.id, "harvest")  # from planned


def test_simulation_run_persisted(gis_session_factory):
    ctx = _bootstrap(gis_session_factory)
    with gis_session_factory() as s:
        _bind(s, ctx.tenant_id)
        run, result = CropSimulationService(s, ctx).run_gdd(
            scenario="season-2026",
            parameters={
                "base_temp_c": 10,
                "daily_temperatures": [
                    {"tmax_c": 30, "tmin_c": 20},
                    {"tmax_c": 25, "tmin_c": 15},
                ],
            },
        )
        assert result.outputs["accumulated_gdd_degc_day"] == 25.0
        assert run.record["validation_status"] == "SIMULATION"
        s.commit()


def test_production_tenant_isolation(gis_session_factory):
    with gis_session_factory() as s:
        a = provision_tenant(s, slug="pa", name="A", admin_email="a@pa.test",
                             admin_password="supersecret123")
        b = provision_tenant(s, slug="pb", name="B", admin_email="a@pb.test",
                             admin_password="supersecret123")
        s.commit()
        a_id, a_admin = a.tenant.id, a.admin_user.id
        b_id = b.tenant.id

    ctx_a = _ctx(a_id, a_admin)
    with gis_session_factory() as s:
        _bind(s, a_id)
        parcel_id = _seed_parcel(s, a_id)
        crop = MasterDataService(s, ctx_a, Crop).create(code="RICE", name="Rice")
        CroppingCycleService(s, ctx_a).create(
            code="SECRET", parcel_id=parcel_id, crop_id=crop.id
        )
        s.commit()

    with gis_session_factory() as s:
        _bind(s, b_id)
        repo: TenantRepository[CroppingCycle] = TenantRepository(s, CroppingCycle, b_id)
        assert repo.list().total == 0
