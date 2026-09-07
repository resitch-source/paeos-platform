import pytest

from paeos_fx.core.config import Settings
from paeos_fx.core.errors import ValidationError
from paeos_fx.core.ratelimit import FixedWindowRateLimiter
from paeos_fx.integration.adapters import (
    IntegrationNotConfiguredError,
    UnconfiguredOutboundAdapter,
)
from paeos_fx.integration.mappers import TelemetryIngestMapper
from paeos_fx.interfaces.integration import Direction, IntegrationMessage

pytestmark = pytest.mark.unit


def test_rate_limiter_allows_then_blocks_within_window():
    rl = FixedWindowRateLimiter(limit=2, window_seconds=60)
    assert rl.allow("c", 100.0) is True
    assert rl.allow("c", 101.0) is True
    assert rl.allow("c", 102.0) is False  # third hit in the same window


def test_rate_limiter_resets_next_window():
    rl = FixedWindowRateLimiter(limit=1, window_seconds=60)
    assert rl.allow("c", 0.0) is True
    assert rl.allow("c", 30.0) is False
    assert rl.allow("c", 61.0) is True  # new window


def test_rate_limiter_isolates_keys():
    rl = FixedWindowRateLimiter(limit=1, window_seconds=60)
    assert rl.allow("a", 0.0) is True
    assert rl.allow("b", 0.0) is True


def test_unconfigured_outbound_adapter_refuses():
    adapter = UnconfiguredOutboundAdapter()
    msg = IntegrationMessage(system="x", direction=Direction.OUTBOUND,
                             idempotency_key="k")
    with pytest.raises(IntegrationNotConfiguredError):
        adapter.send_outbound(msg)


def test_telemetry_mapper_requires_fields():
    m = TelemetryIngestMapper()
    with pytest.raises(ValidationError):
        m.to_domain({"asset_code": "A", "metric": "temp"})  # missing value/uom
    out = m.to_domain({"asset_code": "A", "metric": "temp", "value": 42, "uom": "C"})
    assert out["value"] == "42"  # exact string, not a float


def test_production_safety_rejects_default_db_creds():
    s = Settings(environment="production", jwt_secret="real-secret", debug=False,
                 database_url="postgresql+psycopg://paeos:paeos@localhost:5432/paeos")
    with pytest.raises(RuntimeError):
        s.assert_production_safe()
