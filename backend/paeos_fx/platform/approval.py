"""Approval engine (section I).

Configurable multi-step approval chains. Mirrors the build controller's own
human-gate concept: a request advances only when each required step is approved;
any rejection terminates the chain. All decisions are auditable.
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ApprovalStatus(enum.StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRequest(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A request routed through an ordered chain of approval steps."""

    __tablename__ = "approval_request"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(128), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default=ApprovalStatus.PENDING.value, nullable=False
    )
    context: Mapped[dict] = mapped_column(JSONB, default=dict)


class ApprovalStep(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single ordered step within an approval request."""

    __tablename__ = "approval_step"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.approval_request.id"), nullable=False
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    approver_role: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default=ApprovalStatus.PENDING.value, nullable=False
    )
    decided_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    comment: Mapped[str] = mapped_column(String(500), default="")


class ApprovalService:
    """Advances approval requests through their steps."""

    def __init__(self, session):
        self.session = session

    def decide(
        self, step: ApprovalStep, *, approve: bool, actor: uuid.UUID, comment: str = ""
    ) -> ApprovalStep:
        if step.status != ApprovalStatus.PENDING.value:
            raise BusinessRuleError("Approval step already decided.")
        step.status = (
            ApprovalStatus.APPROVED.value if approve else ApprovalStatus.REJECTED.value
        )
        step.decided_by = actor
        step.comment = comment
        self.session.flush()
        return step
