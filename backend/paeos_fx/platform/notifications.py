"""Notifications foundation (section M).

Channel-abstract notifications with a persisted record and pluggable channel
providers (email/SMS/in-app). The foundation ships an in-app channel and null
providers for the rest; concrete providers plug in behind :class:`Channel`.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import Boolean, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ChannelKind(enum.StrEnum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A tenant-scoped notification addressed to a user."""

    __tablename__ = "notification"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    recipient_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    template_key: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


@dataclass(frozen=True)
class Message:
    to: str
    subject: str
    body: str


class Channel(Protocol):
    kind: ChannelKind

    def send(self, message: Message) -> None: ...


class NullChannel:
    """No-op channel (default until a provider is configured)."""

    def __init__(self, kind: ChannelKind) -> None:
        self.kind = kind

    def send(self, message: Message) -> None:
        return None


class NotificationService:
    """Persists in-app notifications and dispatches to configured channels."""

    def __init__(self, session, channels: dict[ChannelKind, Channel] | None = None):
        self.session = session
        self.channels = channels or {}

    def notify_in_app(
        self,
        *,
        tenant_id: uuid.UUID,
        recipient_id: uuid.UUID,
        template_key: str,
        payload: dict | None = None,
    ) -> Notification:
        note = Notification(
            tenant_id=tenant_id,
            recipient_id=recipient_id,
            channel=ChannelKind.IN_APP.value,
            template_key=template_key,
            payload=payload or {},
        )
        self.session.add(note)
        self.session.flush()
        return note
