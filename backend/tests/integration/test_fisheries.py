"""Fisheries integration tests (Phase 5).

Aquatic-species master data + isolation run on any PostgreSQL. Culture units,
cycles, and records use ``gis_session_factory`` (PostGIS-gated — culture units
carry geometry).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest
from sqlalchemy import text

from paeos_fx.agri.services import MasterDataService
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.fisheries.masterdata import AquaticSpecies
from paeos_fx.fisheries.models import AquacultureCycle
from paeos_fx.fisheries.services import (
    AquacultureCycleService,
    CultureUnitService,
    WaterQualityService,
)
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.onboarding_service import provision_tenant
from paeos_fx.platform.repository import TenantRepository

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]

POINT = {"type": "Point", "coordinates": [121.0, 14.5]}


def _ctx(tenant_id, user_id):
    return ExecutionContext(
        tenant_id=tenant_id, user_id=user_id,
        permissions=frozenset(perms.TENANT_ADMIN_PERMISSIONS),
    )


def _bind(session, tenant_id):
    session.execute(text("SELECT set_config('app.tenant_id', :t, true)"),
                    {"t": str(tenant_id)})


def _bootstrap(factory, slug="fishco"):
    with factory() as s:
        res = provision_tenant(
            s, slug=slug, name="Fish Co", admin_email=f"a@{slug}.test",
            admin_password="supersecret123",
        )
        s.commit()
        return _ctx(res.tenant.id, res.admin_user.id)


def test_species_master_data(session_factory):
    ctx = _bootstrap(session_factory)
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        svc = MasterDataService(s, ctx, AquaticSpecies)
        sp = svc.create(code="TILAPIA", name="Tilapia")
        assert sp.id is not None
        assert {x.code for x in svc.list().items} == {"TILAPIA"}
        s.commit()


def test_species_tenant_isolation(session_factory):
    with session_factory() as s:
        a = provision_tenant(s, slug="fa", name="A", admin_email="a@fa.test",
                             admin_password="supersecret123")
        b = provision_tenant(s, slug="fb", name="B", admin_email="a@fb.test",
                             admin_password="supersecret123")
        s.commit()
        a_id, a_admin, b_id = a.tenant.id, a.admin_user.id, b.tenant.id
    with session_factory() as s:
        _bind(s, a_id)
        MasterDataService(s, _ctx(a_id, a_admin), AquaticSpecies).create(
            code="MILKFISH", name="Milkfish"
        )
        s.commit()
    with session_factory() as s:
        _bind(s, b_id)
        assert TenantRepository(s, AquaticSpecies, b_id).list().total == 0


def test_cycle_lifecycle_water_quality_and_mortality(gis_session_factory):
    ctx = _bootstrap(gis_session_factory)
    with gis_session_factory() as s:
        _bind(s, ctx.tenant_id)
        sp = MasterDataService(s, ctx, AquaticSpecies).create(code="SHRIMP", name="Shrimp")
        unit = CultureUnitService(s, ctx).create(
            code="POND1", name="Pond 1", location_geojson=POINT
        )
        cyc_svc = AquacultureCycleService(s, ctx)
        cycle = cyc_svc.create(
            code="AC1", culture_unit_id=unit.id, species_id=sp.id, stocking_count=1000
        )
        assert cycle.status == "stocked"
        cyc_svc.transition(cycle.id, "start_growth")

        WaterQualityService(s, ctx).record(
            culture_unit_id=unit.id, read_at=dt.date(2026, 6, 1),
            metric_type="pH", value=Decimal("7.8"), uom="pH",
        )
        cyc_svc.record_mortality(cycle_id=cycle.id, event_date=dt.date(2026, 6, 2), count=50)
        s.refresh(cycle)
        assert cycle.stocking_count == 950

        cyc_svc.transition(cycle.id, "harvest")
        cyc_svc.record_harvest(
            cycle_id=cycle.id, harvest_date=dt.date(2026, 8, 1),
            quantity=Decimal("450.0"), uom="kg",
        )
        s.commit()


def test_mortality_cannot_exceed_stock(gis_session_factory):
    ctx = _bootstrap(gis_session_factory, slug="fishco2")
    with gis_session_factory() as s:
        _bind(s, ctx.tenant_id)
        sp = MasterDataService(s, ctx, AquaticSpecies).create(code="CARP", name="Carp")
        unit = CultureUnitService(s, ctx).create(code="C2", name="Cage 2")
        cycle = AquacultureCycleService(s, ctx).create(
            code="AC2", culture_unit_id=unit.id, species_id=sp.id, stocking_count=10
        )
        with pytest.raises(BusinessRuleError):
            AquacultureCycleService(s, ctx).record_mortality(
                cycle_id=cycle.id, event_date=dt.date(2026, 6, 2), count=100
            )


def test_cycle_tenant_isolation(gis_session_factory):
    a = _bootstrap(gis_session_factory, slug="fca")
    b = _bootstrap(gis_session_factory, slug="fcb")
    with gis_session_factory() as s:
        _bind(s, a.tenant_id)
        sp = MasterDataService(s, a, AquaticSpecies).create(code="EEL", name="Eel")
        unit = CultureUnitService(s, a).create(code="U", name="Unit")
        AquacultureCycleService(s, a).create(
            code="SECRET", culture_unit_id=unit.id, species_id=sp.id
        )
        s.commit()
    with gis_session_factory() as s:
        _bind(s, b.tenant_id)
        assert TenantRepository(s, AquacultureCycle, b.tenant_id).list().total == 0
