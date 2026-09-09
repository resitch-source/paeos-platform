"""Enterprise Core integration tests (Phase 1).

Exercises onboarding, authentication, RBAC, user/org administration, and
cross-tenant isolation against a live PostgreSQL. Requires
``PAEOS_TEST_DATABASE_URL``; skipped otherwise.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from paeos_fx.core.context import ExecutionContext
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.auth_service import authenticate, resolve_permissions
from paeos_fx.platform.iam_service import UserService
from paeos_fx.platform.onboarding_service import provision_tenant
from paeos_fx.platform.org import OrgUnit, OrgUnitService
from paeos_fx.platform.repository import TenantRepository

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]


def _ctx(tenant_id, user_id, perms_list):
    return ExecutionContext(
        tenant_id=tenant_id,
        user_id=user_id,
        permissions=frozenset(perms_list),
    )


def test_provision_and_authenticate(session_factory):
    with session_factory() as s:
        result = provision_tenant(
            s, slug="acme", name="Acme", admin_email="admin@acme.test",
            admin_password="supersecret123",
        )
        s.commit()
        tenant_id = result.tenant.id
        admin_id = result.admin_user.id

    with session_factory() as s:
        s.execute(text("SELECT set_config('app.tenant_id', :t, true)"),
                  {"t": str(tenant_id)})
        user = authenticate(
            s, tenant_id=tenant_id, email="admin@acme.test",
            password="supersecret123",
        )
        assert user.id == admin_id
        granted = resolve_permissions(s, admin_id)
        assert perms.IAM_USER_WRITE in granted
        assert perms.ORG_UNIT_WRITE in granted


def test_wrong_password_rejected(session_factory):
    from paeos_fx.core.errors import AuthenticationError

    with session_factory() as s:
        provision_tenant(
            s, slug="beta", name="Beta", admin_email="a@beta.test",
            admin_password="supersecret123",
        )
        s.commit()
        tid = s.execute(
            text("SELECT id FROM platform.tenant WHERE slug='beta'")
        ).scalar_one()

    with session_factory() as s:
        s.execute(text("SELECT set_config('app.tenant_id', :t, true)"),
                  {"t": str(tid)})
        with pytest.raises(AuthenticationError):
            authenticate(s, tenant_id=tid, email="a@beta.test", password="wrong")


def test_user_and_org_crud(session_factory):
    with session_factory() as s:
        res = provision_tenant(
            s, slug="gamma", name="Gamma", admin_email="admin@gamma.test",
            admin_password="supersecret123",
        )
        s.commit()
        ctx = _ctx(res.tenant.id, res.admin_user.id, perms.TENANT_ADMIN_PERMISSIONS)

    with session_factory() as s:
        s.execute(text("SELECT set_config('app.tenant_id', :t, true)"),
                  {"t": str(ctx.tenant_id)})
        users = UserService(s, ctx)
        u = users.create_user(email="worker@gamma.test", password="workerpass123")
        assert u.id is not None
        page = users.list_users()
        emails = {x.email for x in page.items}
        assert "worker@gamma.test" in emails

        org = OrgUnitService(s, ctx)
        root = org.create(code="HQ", name="Headquarters")
        child = org.create(code="OPS", name="Operations", parent_id=root.id)
        assert child.parent_id == root.id
        s.commit()


def test_org_reparent_cycle_rejected(session_factory):
    from paeos_fx.core.errors import BusinessRuleError

    with session_factory() as s:
        res = provision_tenant(
            s, slug="delta", name="Delta", admin_email="admin@delta.test",
            admin_password="supersecret123",
        )
        s.commit()
        ctx = _ctx(res.tenant.id, res.admin_user.id, perms.TENANT_ADMIN_PERMISSIONS)

    with session_factory() as s:
        s.execute(text("SELECT set_config('app.tenant_id', :t, true)"),
                  {"t": str(ctx.tenant_id)})
        org = OrgUnitService(s, ctx)
        a = org.create(code="A", name="A")
        b = org.create(code="B", name="B", parent_id=a.id)
        # Making A a child of B would create a cycle.
        with pytest.raises(BusinessRuleError):
            org.set_parent(a.id, b.id)


def test_tenant_isolation_users_and_org(session_factory):
    """Service-layer isolation: tenant B cannot see tenant A's rows."""
    with session_factory() as s:
        a = provision_tenant(
            s, slug="ta", name="Tenant A", admin_email="admin@ta.test",
            admin_password="supersecret123",
        )
        b = provision_tenant(
            s, slug="tb", name="Tenant B", admin_email="admin@tb.test",
            admin_password="supersecret123",
        )
        s.commit()
        a_id, a_admin = a.tenant.id, a.admin_user.id
        b_id, b_admin = b.tenant.id, b.admin_user.id

    # Seed an org unit + user in tenant A.
    ctx_a = _ctx(a_id, a_admin, perms.TENANT_ADMIN_PERMISSIONS)
    with session_factory() as s:
        s.execute(text("SELECT set_config('app.tenant_id', :t, true)"),
                  {"t": str(a_id)})
        OrgUnitService(s, ctx_a).create(code="SECRET", name="A Secret Unit")
        UserService(s, ctx_a).create_user(
            email="a-only@ta.test", password="workerpass123"
        )
        s.commit()

    # As tenant B, neither the org unit nor the user is visible.
    ctx_b = _ctx(b_id, b_admin, perms.TENANT_ADMIN_PERMISSIONS)
    with session_factory() as s:
        s.execute(text("SELECT set_config('app.tenant_id', :t, true)"),
                  {"t": str(b_id)})
        org_repo: TenantRepository[OrgUnit] = TenantRepository(s, OrgUnit, b_id)
        assert org_repo.list().total == 0

        b_users = UserService(s, ctx_b).list_users()
        emails = {u.email for u in b_users.items}
        assert "a-only@ta.test" not in emails
        assert emails == {"admin@tb.test"}
