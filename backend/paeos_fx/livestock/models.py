"""Livestock domain models (Phase 4).

Animal groups (herds/flocks) with a lifecycle, plus production, mortality, and
health-event records. Quantities carry a provenance classification; nothing is
fabricated. Feed/treatment stock movements are out of scope (Phase 6).
"""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.core.classification import Classification
from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin
from paeos_fx.platform.workflow import StateMachine, Transition

# Animal-group lifecycle.
ANIMAL_GROUP_WORKFLOW = StateMachine(
    states=frozenset({"established", "active", "closed"}),
    initial="established",
    transitions=[
        Transition("established", "active", "activate"),
        Transition("active", "closed", "close"),
    ],
)


class AnimalGroup(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A herd or flock managed as a unit."""

    __tablename__ = "animal_group"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    species_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.livestock_species.id"), nullable=False
    )
    breed_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.livestock_breed.id"), nullable=True
    )
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.agri_farm.id"), nullable=True
    )
    org_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.org_unit.id"), nullable=True
    )
    purpose: Mapped[str | None] = mapped_column(String(32), nullable=True)
    head_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="established", nullable=False)
    established_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)


class AnimalProductionRecord(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A production observation (e.g. milk, eggs, weight) for a group."""

    __tablename__ = "animal_production_record"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.animal_group.id"), nullable=False, index=True
    )
    recorded_at: Mapped[dt.date] = mapped_column(Date, nullable=False)
    metric_type: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    uom: Mapped[str] = mapped_column(String(16), nullable=False)
    classification: Mapped[str] = mapped_column(
        String(16), default=Classification.MEASURED.value, nullable=False
    )


class AnimalMortalityRecord(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A mortality event for a group (count MEASURED)."""

    __tablename__ = "animal_mortality_record"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.animal_group.id"), nullable=False, index=True
    )
    event_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    cause_note: Mapped[str] = mapped_column(String(500), default="")
    classification: Mapped[str] = mapped_column(
        String(16), default=Classification.MEASURED.value, nullable=False
    )


class AnimalHealthEvent(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A health/veterinary event for a group (vaccination, treatment, etc.)."""

    __tablename__ = "animal_health_event"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.animal_group.id"), nullable=False, index=True
    )
    event_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
