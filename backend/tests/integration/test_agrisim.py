"""AgriSim integration tests (Phase 11).

Fully non-geometry — runs on any PostgreSQL. Validates that scenario/optimization
runs persist their provenance envelope, that a digital-twin projection is
recorded (advisory only), and that scenario runs are tenant-isolated.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from paeos_fx.agrisim.models import ScenarioRun
from paeos_fx.agrisim.service import ScenarioService
from paeos_fx.core.context import ExecutionContext
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.onboarding_service import provision_tenant
from paeos_fx.platform.repository import TenantRepository

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]


def _ctx(tenant_id, user_id):
    return ExecutionContext(tenant_id=tenant_id, user_id=user_id,
                            permissions=frozenset(perms.TENANT_ADMIN_PERMISSIONS))


def _bind(s, tid):
    s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})


def _bootstrap(session_factory, slug="simco"):
    with session_factory() as s:
        res = provision_tenant(s, slug=slug, name="Sim Co", admin_email=f"a@{slug}.test",
                               admin_password="supersecret123")
        s.commit()
        return _ctx(res.tenant.id, res.admin_user.id)


def test_eoq_scenario_persisted_with_provenance(session_factory):
    ctx = _bootstrap(session_factory)
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        run, result = ScenarioService(s, ctx).run(
            model_name="eoq", scenario="reorder",
            parameters={"annual_demand": 1000, "order_cost": 10, "holding_cost": 2},
        )
        assert result.outputs["eoq"] == pytest.approx(100.0)
        assert run.model_name == "eoq"
        assert run.record["validation_status"] == "SIMULATION"
        assert run.record["reference"]  # provenance recorded
        s.commit()


def test_twin_projection_recorded_advisory(session_factory):
    ctx = _bootstrap(session_factory, slug="twinco")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        run, result = ScenarioService(s, ctx).project(
            model_name="mass_balance", subject_ref="MILL-1",
            parameters={"input_mass": 100.0, "yield_fraction": 0.63},
        )
        assert result.outputs["output_mass"] == pytest.approx(63.0)
        assert run.subject_ref == "MILL-1"
        assert run.scenario == "twin:MILL-1"
        s.commit()


def test_scenario_tenant_isolation(session_factory):
    with session_factory() as s:
        a = provision_tenant(s, slug="sima", name="A", admin_email="a@sima.test",
                             admin_password="supersecret123")
        b = provision_tenant(s, slug="simb", name="B", admin_email="a@simb.test",
                             admin_password="supersecret123")
        s.commit()
        a_id, a_admin, b_id = a.tenant.id, a.admin_user.id, b.tenant.id
    ctx_a = _ctx(a_id, a_admin)
    with session_factory() as s:
        _bind(s, a_id)
        ScenarioService(s, ctx_a).run(
            model_name="eoq", scenario="secret",
            parameters={"annual_demand": 1, "order_cost": 1, "holding_cost": 1},
        )
        s.commit()
    with session_factory() as s:
        _bind(s, b_id)
        assert TenantRepository(s, ScenarioRun, b_id).list().total == 0
