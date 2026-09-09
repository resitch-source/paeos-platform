"""Agriculture GIS integration tests (Phase 2).

Requires PostGIS (uses ``gis_session_factory``); skipped otherwise. Covers farm
and parcel creation from GeoJSON, derived-area provenance, and tenant isolation.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from paeos_fx.agri.gis import Farm, LandParcel
from paeos_fx.agri.services import FarmService, ParcelService
from paeos_fx.core.classification import Classification
from paeos_fx.core.context import ExecutionContext
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.onboarding_service import provision_tenant
from paeos_fx.platform.repository import TenantRepository

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]

POINT = {"type": "Point", "coordinates": [120.98, 14.6]}
POLYGON = {
    "type": "Polygon",
    "coordinates": [[[120.9, 14.5], [120.9, 14.6], [121.0, 14.6],
                     [121.0, 14.5], [120.9, 14.5]]],
}


def _ctx(tenant_id, user_id):
    return ExecutionContext(
        tenant_id=tenant_id, user_id=user_id,
        permissions=frozenset(perms.TENANT_ADMIN_PERMISSIONS),
    )


def _bind(session, tenant_id):
    session.execute(text("SELECT set_config('app.tenant_id', :t, true)"),
                    {"t": str(tenant_id)})


def test_farm_and_parcel_from_geojson(gis_session_factory):
    with gis_session_factory() as s:
        res = provision_tenant(
            s, slug="gisco", name="GIS Co", admin_email="a@gis.test",
            admin_password="supersecret123",
        )
        s.commit()
        ctx = _ctx(res.tenant.id, res.admin_user.id)

    with gis_session_factory() as s:
        _bind(s, ctx.tenant_id)
        farm = FarmService(s, ctx).create(
            code="F1", name="Farm 1", location_geojson=POINT
        )
        parcel = ParcelService(s, ctx).create(
            code="P1", name="Parcel 1", farm_id=farm.id, boundary_geojson=POLYGON
        )
        s.flush()
        # Area is derived from the imported geometry and classified as ESTIMATE.
        s.refresh(parcel)
        assert parcel.area_sqm is not None
        assert float(parcel.area_sqm) > 0
        assert parcel.area_classification == Classification.ESTIMATE.value
        s.commit()


def test_gis_tenant_isolation(gis_session_factory):
    with gis_session_factory() as s:
        a = provision_tenant(
            s, slug="gisa", name="A", admin_email="a@ga.test",
            admin_password="supersecret123",
        )
        b = provision_tenant(
            s, slug="gisb", name="B", admin_email="a@gb.test",
            admin_password="supersecret123",
        )
        s.commit()
        a_id, a_admin = a.tenant.id, a.admin_user.id
        b_id = b.tenant.id

    with gis_session_factory() as s:
        _bind(s, a_id)
        FarmService(s, _ctx(a_id, a_admin)).create(
            code="AF", name="A Farm", location_geojson=POINT
        )
        s.commit()

    with gis_session_factory() as s:
        _bind(s, b_id)
        repo: TenantRepository[Farm] = TenantRepository(s, Farm, b_id)
        assert repo.list().total == 0
        assert TenantRepository(s, LandParcel, b_id).list().total == 0
