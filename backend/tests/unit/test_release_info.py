import pytest
from fastapi.testclient import TestClient

from paeos_fx import __version__
from paeos_fx.core.config import Settings
from paeos_fx.main import create_app
from paeos_fx.platform.release import (
    CAPABILITY_BUNDLES,
    PHASE_MANIFEST,
    RELEASE_VERSION,
    build_sha,
)

pytestmark = pytest.mark.unit


@pytest.fixture()
def client():
    settings = Settings(
        environment="test", jwt_secret="test-secret-0000000000000000000000000000"
    )
    return TestClient(create_app(settings))


def test_release_version_is_1_0_0():
    assert __version__ == "1.0.0"
    assert RELEASE_VERSION == "1.0.0"


def test_phase_manifest_is_complete_and_unique():
    phases = [p["phase"] for p in PHASE_MANIFEST]
    assert phases[0] == "FX"
    assert [p for p in phases if p != "FX"] == [str(n) for n in range(0, 14)]
    assert len(phases) == len(set(phases))  # no duplicates
    for entry in PHASE_MANIFEST:
        assert entry["name"] and entry["summary"]


def test_build_sha_defaults_to_unknown(monkeypatch):
    monkeypatch.delenv("PAEOS_BUILD_SHA", raising=False)
    assert build_sha() == "unknown"


def test_build_sha_reads_env(monkeypatch):
    monkeypatch.setenv("PAEOS_BUILD_SHA", "abc123")
    assert build_sha() == "abc123"


def test_capability_bundles_present():
    assert set(CAPABILITY_BUNDLES) == {"core", "agriculture", "enterprise"}


def test_info_endpoint(client):
    resp = client.get("/api/v1/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["product"] == "PAEOS"
    assert body["version"] == "1.0.0"
    assert body["build_sha"] == "unknown"
    assert len(body["phases"]) == len(PHASE_MANIFEST)
    assert "enterprise" in body["capability_bundles"]
