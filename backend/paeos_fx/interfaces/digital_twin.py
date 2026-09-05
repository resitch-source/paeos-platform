"""Digital-twin interface (section Z).

A minimum stable contract for binding a physical asset to a virtual model:
telemetry ingestion, state synchronization, and a command channel. The command
channel is deliberately inert at the foundation — autonomous control of
machinery is safety-critical and gated (approval #14). No coconut-oil or other
twin models are implemented here (Phase 7/11).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from paeos_fx.core.classification import Classification
from paeos_fx.core.errors import PaeosError


class UnsafeControlError(PaeosError):
    code = "unsafe_control_error"
    http_status = 403


@dataclass(frozen=True)
class TelemetrySample:
    """A single telemetry reading with provenance (sensor values are MEASURED)."""

    metric: str
    value: float
    unit: str
    at: datetime = field(default_factory=lambda: datetime.now(UTC))
    classification: Classification = Classification.MEASURED


@dataclass(frozen=True)
class TwinState:
    asset_id: str
    updated_at: datetime
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ControlCommand:
    asset_id: str
    command: str
    parameters: dict[str, Any] = field(default_factory=dict)


class DigitalTwin(Protocol):
    """Contract implemented by concrete twins in later phases."""

    asset_id: str

    def ingest(self, sample: TelemetrySample) -> None: ...
    def state(self) -> TwinState: ...


def guard_control(command: ControlCommand, *, human_approved: bool) -> None:
    """Refuse machinery control commands without explicit human approval.

    Until an explicitly validated control architecture exists (later phase),
    every command is treated as safety-critical.
    """
    if not human_approved:
        raise UnsafeControlError(
            "Machinery control requires human approval (no validated autonomous "
            "control architecture at the foundation).",
            details={"asset_id": command.asset_id, "command": command.command},
        )
