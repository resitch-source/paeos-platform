"""Event engine (section K).

An in-process synchronous event bus for intra-request reactions, plus a
transactional **outbox** table so events destined for async/external consumers
are persisted atomically with the business transaction and dispatched later by a
background job.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


@dataclass(frozen=True)
class DomainEvent:
    """A domain event with a stable name and JSON-serializable payload."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


Handler = Callable[[DomainEvent], None]


class EventBus:
    """Minimal synchronous in-process publish/subscribe bus."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Handler) -> None:
        self._handlers[event_name].append(handler)

    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(event.name, []):
            handler(event)


class OutboxEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Durable event awaiting asynchronous dispatch (transactional outbox)."""

    __tablename__ = "outbox_event"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    dispatched: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class OutboxService:
    """Enqueue events into the outbox within the current transaction."""

    def __init__(self, session):
        self.session = session

    def enqueue(self, tenant_id: uuid.UUID, event: DomainEvent) -> OutboxEvent:
        row = OutboxEvent(
            tenant_id=tenant_id, name=event.name, payload=event.payload
        )
        self.session.add(row)
        self.session.flush()
        return row
