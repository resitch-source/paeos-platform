"""Integration mappers (Phase 12).

A ``Mapper`` translates an external message payload into the shape a domain
service expects. The telemetry mapper turns an external IoT reading into the
arguments for the Phase 7 asset-telemetry path — records only, MEASURED, no
actuation.
"""

from __future__ import annotations

from typing import Any

from paeos_fx.core.errors import ValidationError

TELEMETRY_SYSTEM = "iot.telemetry"


class TelemetryIngestMapper:
    """Maps an external IoT reading payload to asset-telemetry arguments."""

    def to_domain(self, external: dict[str, Any]) -> dict[str, Any]:
        required = ("asset_code", "metric", "value", "uom")
        missing = [k for k in required if external.get(k) in (None, "")]
        if missing:
            raise ValidationError(
                "Telemetry payload missing required fields.",
                details={"missing": missing},
            )
        return {
            "asset_code": str(external["asset_code"]),
            "metric": str(external["metric"]),
            "value": str(external["value"]),  # exact decimal string; never a float
            "uom": str(external["uom"]),
            "read_at": external.get("read_at"),
        }

    def to_external(self, domain: dict[str, Any]) -> dict[str, Any]:
        return dict(domain)
