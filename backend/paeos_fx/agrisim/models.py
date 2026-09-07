"""AgriSim models (Phase 11).

``ScenarioRun`` is a standalone (non-geometric) auditable record of a simulation
or optimization run and its full provenance envelope. Unlike the Phase 3
``simulation_run`` table it has no cropping-cycle FK, so AgriSim/optimization
runs are testable on any PostgreSQL. An optional free-text ``subject_ref`` tags a
run to a subject (e.g. a digital-twin asset code) without a geometry dependency.
"""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ScenarioRun(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """An auditable AgriSim/optimization run with its provenance envelope."""

    __tablename__ = "scenario_run"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    scenario: Mapped[str] = mapped_column(String(128), nullable=False)
    subject_ref: Mapped[str] = mapped_column(String(128), default="")
    ran_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    record: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
