"""Agriculture master-data integration tests (Phase 2).

Non-geometry; runs on any PostgreSQL via ``session_factory``. Covers CRUD and
cross-tenant isolation for reference catalogs.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from paeos_fx.agri.masterdata import Crop, CropCategory
from paeos_fx.agri.services import MasterDataService
from paeos_fx.core.context import ExecutionContext
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


def test_master_data_crud(session_factory):
    with session_factory() as s:
        res = provision_tenant(
            s, slug="mdco", name="MD Co", admin_email="a@md.test",
            admin_password="supersecret123",
        )
        s.commit()
        ctx = _ctx(res.tenant.id, res.admin_user.id)

    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        cat = MasterDataService(s, ctx, CropCategory).create(code="CEREAL", name="Cereal")
        crop = MasterDataService(s, ctx, Crop).create(
            code="RICE", name="Rice", category_id=cat.id, scientific_name="Oryza sativa"
        )
        assert crop.category_id == cat.id
        page = MasterDataService(s, ctx, Crop).list()
        assert {c.code for c in page.items} == {"RICE"}
        s.commit()


def test_master_data_tenant_isolation(session_factory):
    with session_factory() as s:
        a = provision_tenant(
            s, slug="mda", name="A", admin_email="a@a.test",
            admin_password="supersecret123",
        )
        b = provision_tenant(
            s, slug="mdb", name="B", admin_email="a@b.test",
            admin_password="supersecret123",
        )
        s.commit()
        a_id, a_admin = a.tenant.id, a.admin_user.id
        b_id = b.tenant.id

    with session_factory() as s:
        _bind(s, a_id)
        MasterDataService(s, _ctx(a_id, a_admin), Crop).create(code="SECRET", name="Secret Crop")
        s.commit()

    # Tenant B cannot see tenant A's crops (service-layer tenant filter).
    with session_factory() as s:
        _bind(s, b_id)
        repo: TenantRepository[Crop] = TenantRepository(s, Crop, b_id)
        assert repo.list().total == 0
