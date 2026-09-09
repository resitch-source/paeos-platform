"""Agriculture master/reference data (Phase 2).

Built on the Foundation ``MasterDataMixin`` (versioned, effective-dated,
tenant-scoped). These are structural catalogs (codes/names/classifications).
No quantitative agronomic values are defined here.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.platform.masterdata import MasterDataMixin


class CropCategory(MasterDataMixin, Base):
    """A structural crop taxonomy node (e.g. cereal, oilseed, fruit)."""

    __tablename__ = "agri_crop_category"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)


class Crop(MasterDataMixin, Base):
    """A crop reference entry. Quantitative agronomy is NOT stored here."""

    __tablename__ = "agri_crop"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("platform.agri_crop_category.id"), nullable=True
    )
    scientific_name: Mapped[str | None] = mapped_column(String(255), nullable=True)


class CropVariety(MasterDataMixin, Base):
    """A named variety/cultivar under a crop (catalog only)."""

    __tablename__ = "agri_crop_variety"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    crop_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.agri_crop.id"), nullable=False, index=True
    )


class SoilType(MasterDataMixin, Base):
    """Soil type reference catalog (classification only)."""

    __tablename__ = "agri_soil_type"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)


class LandUseType(MasterDataMixin, Base):
    """Land-use type reference catalog (classification only)."""

    __tablename__ = "agri_land_use_type"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)
