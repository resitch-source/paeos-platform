"""Livestock integration tests (Phase 4).

Species/breed master-data + isolation run on any PostgreSQL (``session_factory``).
Animal-group + records + isolation use ``gis_session_factory`` (PostGIS-gated,
because animal_group FKs the PostGIS farm table). The animal-group tests do not
set farm_id (nullable), but the table's presence still requires PostGIS.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest
from sqlalchemy import text

from paeos_fx.agri.services import MasterDataService
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.livestock.masterdata import LivestockSpecies
from paeos_fx.livestock.models import AnimalGroup
from paeos_fx.livestock.services import AnimalGroupService
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


def _bootstrap(factory):
    with factory() as s:
        res = provision_tenant(
            s, slug="lvco", name="Livestock Co", admin_email="a@lv.test",
            admin_password="supersecret123",
        )
        s.commit()
        return _ctx(res.tenant.id, res.admin_user.id)


def test_species_master_data(session_factory):
    ctx = _bootstrap(session_factory)
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        sp = MasterDataService(s, ctx, LivestockSpecies).create(
            code="CATTLE", name="Cattle"
        )
        assert sp.id is not None
        page = MasterDataService(s, ctx, LivestockSpecies).list()
        assert {x.code for x in page.items} == {"CATTLE"}
        s.commit()


def test_species_tenant_isolation(session_factory):
    with session_factory() as s:
        a = provision_tenant(s, slug="la", name="A", admin_email="a@la.test",
                             admin_password="supersecret123")
        b = provision_tenant(s, slug="lb", name="B", admin_email="a@lb.test",
                             admin_password="supersecret123")
        s.commit()
        a_id, a_admin = a.tenant.id, a.admin_user.id
        b_id = b.tenant.id
    with session_factory() as s:
        _bind(s, a_id)
        MasterDataService(s, _ctx(a_id, a_admin), LivestockSpecies).create(
            code="SWINE", name="Swine"
        )
        s.commit()
    with session_factory() as s:
        _bind(s, b_id)
        repo: TenantRepository[LivestockSpecies] = TenantRepository(
            s, LivestockSpecies, b_id
        )
        assert repo.list().total == 0


def test_group_lifecycle_and_mortality(gis_session_factory):
    ctx = _bootstrap(gis_session_factory)
    with gis_session_factory() as s:
        _bind(s, ctx.tenant_id)
        sp = MasterDataService(s, ctx, LivestockSpecies).create(code="POULTRY", name="Poultry")
        svc = AnimalGroupService(s, ctx)
        group = svc.create(code="FLOCK1", name="Flock 1", species_id=sp.id, head_count=100)
        assert group.status == "established"
        svc.transition(group.id, "activate")

        svc.record_production(
            group_id=group.id, recorded_at=dt.date(2026, 6, 1),
            metric_type="eggs_count", quantity=Decimal("80"), uom="ea",
        )
        svc.record_mortality(
            group_id=group.id, event_date=dt.date(2026, 6, 2), count=5,
        )
        s.refresh(group)
        assert group.head_count == 95
        s.commit()


def test_mortality_cannot_exceed_headcount(gis_session_factory):
    ctx = _bootstrap(gis_session_factory)
    with gis_session_factory() as s:
        _bind(s, ctx.tenant_id)
        sp = MasterDataService(s, ctx, LivestockSpecies).create(code="GOAT", name="Goat")
        svc = AnimalGroupService(s, ctx)
        group = svc.create(code="HERD1", name="Herd 1", species_id=sp.id, head_count=3)
        with pytest.raises(BusinessRuleError):
            svc.record_mortality(
                group_id=group.id, event_date=dt.date(2026, 6, 2), count=10
            )


def test_group_tenant_isolation(gis_session_factory):
    with gis_session_factory() as s:
        a = provision_tenant(s, slug="ga2", name="A", admin_email="a@ga2.test",
                             admin_password="supersecret123")
        b = provision_tenant(s, slug="gb2", name="B", admin_email="a@gb2.test",
                             admin_password="supersecret123")
        s.commit()
        a_id, a_admin = a.tenant.id, a.admin_user.id
        b_id = b.tenant.id
    ctx_a = _ctx(a_id, a_admin)
    with gis_session_factory() as s:
        _bind(s, a_id)
        sp = MasterDataService(s, ctx_a, LivestockSpecies).create(code="CATTLE", name="Cattle")
        AnimalGroupService(s, ctx_a).create(code="SECRET", name="Secret", species_id=sp.id)
        s.commit()
    with gis_session_factory() as s:
        _bind(s, b_id)
        repo: TenantRepository[AnimalGroup] = TenantRepository(s, AnimalGroup, b_id)
        assert repo.list().total == 0
