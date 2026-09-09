"""Crop production domain models (Phase 3).

Cropping cycles on parcels/farms, growth observations, harvest records, and
persisted simulation runs. Quantitative values carry a provenance
classification; no agronomic values are fabricated. Input applications that
would deduct inventory are out of scope (Phase 6).
"""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.core.classification import Classification
from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin
from paeos_fx.platform.workflow import StateMachine, Transition

# Cropping-cycle lifecycle (Foundation workflow engine).
CROPPING_CYCLE_WORKFLOW = StateMachine(
    states=frozenset({"planned", "planted", "growing", "harvested", "closed"}),
    initial="planned",
    transitions=[
        Transition("planned", "planted", "plant"),
        Transition("planted", "growing", "start_growth"),
        Transition("growing", "harvested", "harvest"),
        Transition("harvested", "closed", "close"),
    ],
)


class CroppingCycle(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A single crop production cycle on a parcel (optionally under a farm)."""

    __tablename__ = "cropping_cycle"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    parcel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.agri_land_parcel.id"), nullable=False, index=True
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.agri_crop.id"), nullable=False
    )
    variety_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.agri_crop_variety.id"), nullable=True
    )
    season: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="planned", nullable=False)
    planting_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    expected_harvest_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    planted_area_ha: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    area_classification: Mapped[str] = mapped_column(
        String(16), default=Classification.UNKNOWN.value, nullable=False
    )


class GrowthObservation(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A dated growth-stage observation for a cycle."""

    __tablename__ = "growth_observation"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    cycle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.cropping_cycle.id"), nullable=False, index=True
    )
    observed_at: Mapped[dt.date] = mapped_column(Date, nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    note: Mapped[str] = mapped_column(String(500), default="")
    metric_value: Mapped[Decimal | None] = mapped_column(Numeric(16, 4), nullable=True)
    metric_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    metric_classification: Mapped[str] = mapped_column(
        String(16), default=Classification.UNKNOWN.value, nullable=False
    )


class HarvestRecord(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """An actual harvest quantity for a cycle (MEASURED when observed)."""

    __tablename__ = "harvest_record"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    cycle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.cropping_cycle.id"), nullable=False, index=True
    )
    harvest_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    uom: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity_classification: Mapped[str] = mapped_column(
        String(16), default=Classification.MEASURED.value, nullable=False
    )


class SimulationRun(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """An auditable record of a simulation run and its provenance envelope."""

    __tablename__ = "simulation_run"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.cropping_cycle.id"), nullable=True, index=True
    )
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    scenario: Mapped[str] = mapped_column(String(128), nullable=False)
    ran_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    record: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
