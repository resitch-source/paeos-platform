"""Livestock master/reference data (Phase 4).

Species and breed catalogs on the Foundation ``MasterDataMixin``. Names and
classifications only — no quantitative biological values.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.platform.masterdata import MasterDataMixin


class LivestockSpecies(MasterDataMixin, Base):
    """A livestock/poultry species (e.g. cattle, swine, chicken)."""

    __tablename__ = "livestock_species"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)


class LivestockBreed(MasterDataMixin, Base):
    """A breed under a species (catalog only)."""

    __tablename__ = "livestock_breed"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    species_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.livestock_species.id"), nullable=False, index=True
    )
