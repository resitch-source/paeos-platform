"""Geospatial (PostGIS) entities (Phase 2).

Farms, land parcels, and administrative areas with PostGIS geometry (EPSG:4326).
Geometries are imported by tenants — none are fabricated. Derived quantities
(e.g. parcel area) carry a provenance classification.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.core.classification import Classification
from paeos_fx.db.base import Base
from paeos_fx.db.mixins import (
    AuditMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

SRID = 4326


class AdministrativeArea(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A tenant-scoped administrative area (region → … → barangay).

    Boundary geometry is optional and imported by the tenant.
    """

    __tablename__ = "agri_admin_area"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False)  # region/province/...
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.agri_admin_area.id"), nullable=True, index=True
    )
    boundary: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=SRID, spatial_index=True),
        nullable=True,
    )


class Farm(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A tenant-scoped farm with an optional point location."""

    __tablename__ = "agri_farm"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    org_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.org_unit.id"), nullable=True
    )
    admin_area_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.agri_admin_area.id"), nullable=True
    )
    location: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=SRID, spatial_index=True), nullable=True
    )
    # Reported area, if supplied by the tenant. Provenance is explicit.
    area_hectares: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True
    )
    area_classification: Mapped[str] = mapped_column(
        String(16), default=Classification.UNKNOWN.value, nullable=False
    )


class LandParcel(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A tenant-scoped land parcel with a polygon boundary."""

    __tablename__ = "agri_land_parcel"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.agri_farm.id"), nullable=False, index=True
    )
    soil_type_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.agri_soil_type.id"), nullable=True
    )
    land_use_type_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.agri_land_use_type.id"), nullable=True
    )
    boundary: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=SRID, spatial_index=True),
        nullable=True,
    )
    # Area is DERIVED from the imported boundary via PostGIS ST_Area; it is an
    # estimate of the geometry, not a fabricated measurement.
    area_sqm: Mapped[Decimal | None] = mapped_column(Numeric(16, 2), nullable=True)
    area_classification: Mapped[str] = mapped_column(
        String(16), default=Classification.UNKNOWN.value, nullable=False
    )
