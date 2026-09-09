"""IoT + Integrations integration tests (Phase 12).

Fully non-geometry — runs on any PostgreSQL. Validates idempotent telemetry
ingestion into the Phase 7 asset-telemetry path, that a duplicate idempotency
key is a no-op, and that inbound messages are tenant-isolated.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select, text

from paeos_fx.core.context import ExecutionContext
from paeos_fx.integration.mappers import TELEMETRY_SYSTEM
from paeos_fx.integration.models import InboundMessage
from paeos_fx.integration.service import IntegrationService
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.onboarding_service import provision_tenant
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.processing.models import AssetTelemetry
from paeos_fx.processing.service import ProcessingAssetService

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]


def _ctx(tenant_id, user_id):
    return ExecutionContext(tenant_id=tenant_id, user_id=user_id,
                            permissions=frozenset(perms.TENANT_ADMIN_PERMISSIONS))


def _bind(s, tid):
    s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})


def _bootstrap(session_factory, slug="iotco"):
    with session_factory() as s:
        res = provision_tenant(s, slug=slug, name="IoT Co", admin_email=f"a@{slug}.test",
                               admin_password="supersecret123")
        s.commit()
        return _ctx(res.tenant.id, res.admin_user.id)


def _reading(key):
    return {"system": TELEMETRY_SYSTEM, "idempotency_key": key,
            "payload": {"asset_code": "MILL-1", "metric": "temp_c",
                        "value": "82.5", "uom": "C"}}


def test_telemetry_ingest_records_reading(session_factory):
    ctx = _bootstrap(session_factory)
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        ProcessingAssetService(s, ctx).create(code="MILL-1", name="Expeller 1")
        r = _reading("evt-1")
        msg, created = IntegrationService(s, ctx).ingest(
            system=r["system"], idempotency_key=r["idempotency_key"], payload=r["payload"])
        assert created is True
        assert msg.status == "processed"
        n = s.execute(select(func.count()).select_from(AssetTelemetry).where(
            AssetTelemetry.tenant_id == ctx.tenant_id)).scalar_one()
        assert n == 1
        s.commit()


def test_duplicate_idempotency_key_is_noop(session_factory):
    ctx = _bootstrap(session_factory, slug="iotco2")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        ProcessingAssetService(s, ctx).create(code="MILL-1", name="Expeller 1")
        svc = IntegrationService(s, ctx)
        r = _reading("evt-dup")
        _, created1 = svc.ingest(system=r["system"], idempotency_key=r["idempotency_key"],
                                 payload=r["payload"])
        _, created2 = svc.ingest(system=r["system"], idempotency_key=r["idempotency_key"],
                                 payload=r["payload"])
        assert created1 is True
        assert created2 is False  # dedupe
        # Only one telemetry row and one inbound message despite two ingests.
        assert s.execute(select(func.count()).select_from(AssetTelemetry).where(
            AssetTelemetry.tenant_id == ctx.tenant_id)).scalar_one() == 1
        assert s.execute(select(func.count()).select_from(InboundMessage).where(
            InboundMessage.tenant_id == ctx.tenant_id)).scalar_one() == 1
        s.commit()


def test_integration_tenant_isolation(session_factory):
    with session_factory() as s:
        a = provision_tenant(s, slug="iota", name="A", admin_email="a@iota.test",
                             admin_password="supersecret123")
        b = provision_tenant(s, slug="iotb", name="B", admin_email="a@iotb.test",
                             admin_password="supersecret123")
        s.commit()
        a_id, a_admin, b_id = a.tenant.id, a.admin_user.id, b.tenant.id
    ctx_a = _ctx(a_id, a_admin)
    with session_factory() as s:
        _bind(s, a_id)
        ProcessingAssetService(s, ctx_a).create(code="MILL-1", name="M")
        r = _reading("evt-secret")
        IntegrationService(s, ctx_a).ingest(system=r["system"],
                                            idempotency_key=r["idempotency_key"],
                                            payload=r["payload"])
        s.commit()
    with session_factory() as s:
        _bind(s, b_id)
        assert TenantRepository(s, InboundMessage, b_id).list().total == 0
