"""Expert-marketplace models (Phase 9) — financial (gate #12).

``ExpertProfile`` is a directory entry with a caller-supplied rate; ``Engagement``
records a client's engagement of an expert at an agreed fee (integer minor
units). No payment/AR/GL/tax logic; no fabricated ratings.
"""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin
from paeos_fx.platform.workflow import StateMachine, Transition

ENGAGEMENT_WORKFLOW = StateMachine(
    states=frozenset({"requested", "accepted", "delivered", "closed", "cancelled"}),
    initial="requested",
    transitions=[
        Transition("requested", "accepted", "accept"),
        Transition("accepted", "delivered", "deliver"),
        Transition("delivered", "closed", "close"),
        Transition("requested", "cancelled", "cancel"),
        Transition("accepted", "cancelled", "cancel"),
    ],
)


class ExpertProfile(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A directory entry for a domain expert."""

    __tablename__ = "expert_profile"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    expertise_area: Mapped[str] = mapped_column(String(128), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    # Caller-supplied rate card (integer minor units); optional.
    rate_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PHP")
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.app_user.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)


class Engagement(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A client engagement of an expert at an agreed fee (integer minor units)."""

    __tablename__ = "engagement"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    expert_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.expert_profile.id"), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    fee_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PHP")
    status: Mapped[str] = mapped_column(String(16), default="requested", nullable=False)
