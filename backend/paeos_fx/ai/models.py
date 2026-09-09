"""AgriIntelligence models (Phase 10).

``AgentRun`` records an agent invocation; ``AiRecommendation`` persists the
advisory envelope surfaced by an agent. Recommendations are never auto-applied —
they move through a human-decision lifecycle and mutate no domain data.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin
from paeos_fx.platform.workflow import StateMachine, Transition

RECOMMENDATION_WORKFLOW = StateMachine(
    states=frozenset({"proposed", "accepted", "rejected", "superseded"}),
    initial="proposed",
    transitions=[
        Transition("proposed", "accepted", "accept"),
        Transition("proposed", "rejected", "reject"),
        Transition("proposed", "superseded", "supersede"),
        Transition("accepted", "superseded", "supersede"),
    ],
)


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A single invocation of an advisory agent."""

    __tablename__ = "agent_run"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="completed", nullable=False)


class AiRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A persisted advisory recommendation (never auto-applied)."""

    __tablename__ = "ai_recommendation"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.agent_run.id"), nullable=False, index=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    # Provenance/uncertainty envelope (mirrors interfaces.ai.AIRecommendation).
    classification: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), default=0, nullable=False)
    assumptions: Mapped[list] = mapped_column(JSONB, default=list)
    uncertainty_note: Mapped[str] = mapped_column(Text, default="")
    requires_human_approval: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), default="proposed", nullable=False)
    decided_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
