"""Integration adapters (Phase 12).

The default outbound adapter refuses to fabricate a delivery: no external system
is wired in this build, so rather than silently pretending success it raises. A
real adapter (broker, registry, webhook) is configured per deployment behind the
Foundation ``Adapter`` contract.
"""

from __future__ import annotations

from paeos_fx.core.errors import PaeosError
from paeos_fx.interfaces.integration import IntegrationMessage


class IntegrationNotConfiguredError(PaeosError):
    code = "integration_not_configured"
    http_status = 501


class UnconfiguredOutboundAdapter:
    """Default outbound adapter — refuses to invent a delivery (NO-FABRICATION)."""

    system = "unconfigured"

    def handle_inbound(self, message: IntegrationMessage) -> None:
        raise IntegrationNotConfiguredError(
            "No inbound adapter configured for this system.",
            details={"system": message.system},
        )

    def send_outbound(self, message: IntegrationMessage) -> None:
        raise IntegrationNotConfiguredError(
            "No outbound adapter configured; refusing to fabricate a delivery.",
            details={"system": message.system},
        )
