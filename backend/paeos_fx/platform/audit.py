"""Audit foundation (section T).

Immutable audit log capturing who did what, when, and the before/after state.
Wired into the AI tool chain, approval engine, and domain mutations. Records are
append-only; there is deliberately no update/delete API.
"""

from __future__ import annotations

import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.core.context import ExecutionContext, current_context
from paeos_fx.db.base import Base
from paeos_fx.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single immutable audit record."""

    __tablename__ = "audit_log"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    context: Mapped[dict] = mapped_column(JSONB, default=dict)


class AuditService:
    """Append-only audit recorder."""

    def __init__(self, session):
        self.session = session

    def record(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
        ctx: ExecutionContext | None = None,
    ) -> AuditLog:
        ctx = ctx or current_context()
        entry = AuditLog(
            tenant_id=ctx.require_tenant(),
            actor_id=ctx.user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            correlation_id=ctx.correlation_id,
            before=before,
            after=after,
            context={"locale": ctx.locale},
        )
        self.session.add(entry)
        self.session.flush()
        return entry
