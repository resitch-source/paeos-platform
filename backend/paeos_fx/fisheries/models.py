"""Aquaculture domain models (Phase 5).

Culture units (ponds/cages/tanks) with PostGIS location, culture cycles with a
lifecycle, and water-quality / harvest / mortality records. Quantities carry a
provenance classification; nothing is fabricated.
"""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.core.classification import Classification
from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin
from paeos_fx.platform.workflow import StateMachine, Transition

SRID = 4326

AQUACULTURE_CYCLE_WORKFLOW = StateMachine(
    states=frozenset({"stocked", "growing", "harvested", "closed"}),
    initial="stocked",
    transitions=[
        Transition("stocked", "growing", "start_growth"),
        Transition("growing", "harvested", "harvest"),
        Transition("harvested", "closed", "close"),
    ],
)


class CultureUnit(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A pond, cage, or tank used for aquaculture."""

    __tablename__ = "culture_unit"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(32), default="pond", nullable=False)
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.agri_farm.id"), nullable=True
    )
    location: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=SRID, spatial_index=True), nullable=True
    )
    water_area_sqm: Mapped[Decimal | None] = mapped_column(Numeric(16, 2), nullable=True)
    area_classification: Mapped[str] = mapped_column(
        String(16), default=Classification.UNKNOWN.value, nullable=False
    )


class AquacultureCycle(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A stocking-to-harvest production cycle within a culture unit."""

    __tablename__ = "aquaculture_cycle"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    culture_unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.culture_unit.id"), nullable=False, index=True
    )
    species_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.aquatic_species.id"), nullable=False
    )
    stocking_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stocking_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    expected_harvest_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="stocked", nullable=False)


class WaterQualityReading(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A water-quality reading for a culture unit (MEASURED)."""

    __tablename__ = "water_quality_reading"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    culture_unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.culture_unit.id"), nullable=False, index=True
    )
    read_at: Mapped[dt.date] = mapped_column(Date, nullable=False)
    metric_type: Mapped[str] = mapped_column(String(32), nullable=False)  # temp/DO/pH/...
    value: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    uom: Mapped[str] = mapped_column(String(16), nullable=False)
    classification: Mapped[str] = mapped_column(
        String(16), default=Classification.MEASURED.value, nullable=False
    )


class AquaHarvestRecord(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A harvest quantity for an aquaculture cycle (MEASURED)."""

    __tablename__ = "aqua_harvest_record"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    cycle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.aquaculture_cycle.id"), nullable=False, index=True
    )
    harvest_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    uom: Mapped[str] = mapped_column(String(16), nullable=False)
    classification: Mapped[str] = mapped_column(
        String(16), default=Classification.MEASURED.value, nullable=False
    )


class AquaMortalityRecord(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A mortality event for an aquaculture cycle (count MEASURED)."""

    __tablename__ = "aqua_mortality_record"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    cycle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.aquaculture_cycle.id"), nullable=False, index=True
    )
    event_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    cause_note: Mapped[str] = mapped_column(String(500), default="")
    classification: Mapped[str] = mapped_column(
        String(16), default=Classification.MEASURED.value, nullable=False
    )
