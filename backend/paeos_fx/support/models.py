"""Technical-support models (Phase 9).

A ``SupportTicket`` moves through a lifecycle; ``TicketComment`` records a thread
of caller-supplied messages. No SLA timers or external channels.
"""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin
from paeos_fx.platform.workflow import StateMachine, Transition

SUPPORT_TICKET_WORKFLOW = StateMachine(
    states=frozenset({"open", "in_progress", "resolved", "closed", "cancelled"}),
    initial="open",
    transitions=[
        Transition("open", "in_progress", "assign"),
        Transition("in_progress", "resolved", "resolve"),
        Transition("resolved", "closed", "close"),
        Transition("resolved", "in_progress", "reopen"),
        Transition("open", "cancelled", "cancel"),
        Transition("in_progress", "cancelled", "cancel"),
    ],
)

# Caller-supplied priority labels (authorization/classification constants, not
# fabricated domain values).
TICKET_PRIORITIES = frozenset({"low", "normal", "high", "urgent"})


class SupportTicket(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A technical-support ticket."""

    __tablename__ = "support_ticket"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(16), default="normal", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.app_user.id"), nullable=True, index=True
    )
    resolved_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class TicketComment(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A comment on a support ticket."""

    __tablename__ = "ticket_comment"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.support_ticket.id"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.app_user.id"), nullable=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
