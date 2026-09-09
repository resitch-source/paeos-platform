"""Integration models (Phase 12).

``InboundMessage`` is an idempotent ledger of messages crossing the integration
boundary. The unique (tenant_id, system, idempotency_key) constraint makes
re-delivery a no-op so external systems can retry safely.
"""

from __future__ import annotations

import uuid

from sqlalchemy import String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin


class InboundMessage(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """An idempotent record of an inbound integration message."""

    __tablename__ = "inbound_message"
    __table_args__ = (
        UniqueConstraint("tenant_id", "system", "idempotency_key",
                         name="uq_inbound_message_tenant_system_idem"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    system: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="received", nullable=False)
    attempt: Mapped[int] = mapped_column(default=1, nullable=False)
    error: Mapped[str] = mapped_column(Text, default="")
