"""Integration framework interface (section AA).

Minimum stable contract for inbound/outbound integrations: adapters with
idempotency keys, retry metadata, and a mapping step. No concrete external
systems (IoT brokers, government registries, payment rails) are implemented at
the foundation — those arrive in Phase 12 and others behind these contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class Direction(StrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


@dataclass(frozen=True)
class IntegrationMessage:
    """A message crossing the integration boundary."""

    system: str
    direction: Direction
    idempotency_key: str
    payload: dict[str, Any] = field(default_factory=dict)
    attempt: int = 1
    max_attempts: int = 5

    @property
    def can_retry(self) -> bool:
        return self.attempt < self.max_attempts


class Adapter(Protocol):
    """Contract for a concrete integration adapter (implemented in later phases)."""

    system: str

    def handle_inbound(self, message: IntegrationMessage) -> None: ...
    def send_outbound(self, message: IntegrationMessage) -> None: ...


class Mapper(Protocol):
    """Translates between an external representation and the domain model."""

    def to_domain(self, external: dict[str, Any]) -> dict[str, Any]: ...
    def to_external(self, domain: dict[str, Any]) -> dict[str, Any]: ...
