"""Training models (Phase 9).

A ``Course`` is tenant reference/catalog data; an ``Enrollment`` links a learner
(an ``app_user``) to a course and moves through a lifecycle. No scoring,
certification, or fabricated competency values.
"""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin
from paeos_fx.platform.workflow import StateMachine, Transition

ENROLLMENT_WORKFLOW = StateMachine(
    states=frozenset({"enrolled", "in_progress", "completed", "withdrawn"}),
    initial="enrolled",
    transitions=[
        Transition("enrolled", "in_progress", "start"),
        Transition("in_progress", "completed", "complete"),
        Transition("enrolled", "withdrawn", "withdraw"),
        Transition("in_progress", "withdrawn", "withdraw"),
    ],
)


class Course(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A training course (catalog entry)."""

    __tablename__ = "course"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)


class Enrollment(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A learner's enrollment in a course."""

    __tablename__ = "enrollment"
    __table_args__ = (UniqueConstraint("tenant_id", "course_id", "learner_id"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.course.id"), nullable=False, index=True
    )
    learner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.app_user.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(16), default="enrolled", nullable=False)
    completed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
