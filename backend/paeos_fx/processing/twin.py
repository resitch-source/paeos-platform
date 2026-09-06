"""Coconut-oil digital twin (Phase 7) — ADVISORY / NON-ACTUATING.

Implements the Foundation ``DigitalTwin`` protocol over persisted telemetry.
This twin has NO autonomous control path: any control command must pass through
``guard_control``, which refuses without explicit human approval. No actuation
endpoint is exposed anywhere in the platform.
"""

from __future__ import annotations

import datetime as dt

from paeos_fx.interfaces.digital_twin import (
    ControlCommand,
    TelemetrySample,
    TwinState,
    guard_control,
)


class CoconutOilTwin:
    """A virtual model of a coconut-oil processing asset.

    State is derived from the most recent telemetry per metric. The twin is
    read/advisory only; ``request_control`` always routes through the safety
    guard and never actuates on its own.
    """

    def __init__(self, asset_id: str):
        self.asset_id = asset_id
        self._metrics: dict[str, float] = {}
        self._updated_at = dt.datetime.now(dt.UTC)

    def ingest(self, sample: TelemetrySample) -> None:
        self._metrics[sample.metric] = sample.value
        self._updated_at = sample.at

    def state(self) -> TwinState:
        return TwinState(
            asset_id=self.asset_id,
            updated_at=self._updated_at,
            metrics=dict(self._metrics),
        )

    def request_control(self, command: ControlCommand, *, human_approved: bool) -> None:
        """Route a control request through the safety guard.

        Deliberately never actuates autonomously: without explicit human
        approval this raises ``UnsafeControlError``. Even with approval, this
        method performs no machinery action — a validated control architecture
        is out of scope until a later, separately gated phase.
        """
        guard_control(command, human_approved=human_approved)
        # No actuation is performed here by design.
