import pytest
from fastapi.testclient import TestClient

from paeos_fx.core.config import Settings
from paeos_fx.main import create_app

pytestmark = pytest.mark.unit


@pytest.fixture()
def client():
    settings = Settings(
        environment="test", jwt_secret="test-secret-0000000000000000000000000000"
    )
    return TestClient(create_app(settings))


def test_health_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_meta_reports_foundation(client):
    resp = client.get("/api/v1/meta")
    assert resp.status_code == 200
    body = resp.json()
    assert body["component"] == "PAEOS-FX Foundation"
    assert body["active_phase"] == "PHASE_8_MARKETPLACE_TRADING_LOGISTICS"
    assert body["domain_phases_started"] == [1, 2, 3, 4, 5, 6, 7, 8]


def test_correlation_header_present(client):
    resp = client.get("/api/v1/health")
    assert "X-Correlation-ID" in resp.headers
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
