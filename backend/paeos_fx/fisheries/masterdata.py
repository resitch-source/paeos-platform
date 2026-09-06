"""Fisheries master/reference data (Phase 5)."""

from __future__ import annotations

from sqlalchemy import UniqueConstraint

from paeos_fx.db.base import Base
from paeos_fx.platform.masterdata import MasterDataMixin


class AquaticSpecies(MasterDataMixin, Base):
    """An aquatic species reference entry (catalog only)."""

    __tablename__ = "aquatic_species"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)
