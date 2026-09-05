"""Workflow engine (section H).

A reusable finite-state-machine engine: define states and guarded transitions,
then drive instances through them. Domain phases declare their own state graphs;
the engine has no built-in domain states.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy import String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin

Guard = Callable[[dict], bool]


@dataclass(frozen=True)
class Transition:
    source: str
    target: str
    event: str
    guard: Guard | None = None


@dataclass
class StateMachine:
    """A declarative state machine definition."""

    states: frozenset[str]
    initial: str
    transitions: list[Transition] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.initial not in self.states:
            raise ValueError("initial state must be a declared state")
        for t in self.transitions:
            if t.source not in self.states or t.target not in self.states:
                raise ValueError(f"transition references unknown state: {t}")

    def can_fire(self, current: str, event: str, data: dict | None = None) -> bool:
        return self._match(current, event, data or {}) is not None

    def fire(self, current: str, event: str, data: dict | None = None) -> str:
        transition = self._match(current, event, data or {})
        if transition is None:
            raise BusinessRuleError(
                "Illegal state transition.",
                details={"state": current, "event": event},
            )
        return transition.target

    def _match(self, current: str, event: str, data: dict) -> Transition | None:
        for t in self.transitions:
            if t.source == current and t.event == event:
                if t.guard is None or t.guard(data):
                    return t
        return None


class WorkflowInstance(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """Persisted state of a running workflow for a domain entity."""

    __tablename__ = "workflow_instance"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    workflow_key: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
