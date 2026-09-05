"""Master-data framework (section G).

The *pattern* for versioned, effective-dated, tenant-scoped reference data — not
any agricultural master data (that is Phase 2). Domain phases subclass
:class:`MasterDataMixin` to get consistent reference-entity behavior.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.mixins import (
    AuditMixin,
    TenantMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class MasterDataMixin(
    UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, AuditMixin
):
    """Common columns for reference/master-data entities.

    Provides a stable business ``code``, human ``name``, activation flag,
    version, and effective dating so reference values can evolve without losing
    history.
    """

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    effective_from: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[dt.date | None] = mapped_column(Date, nullable=True)

    def is_effective_on(self, day: dt.date) -> bool:
        if self.effective_from and day < self.effective_from:
            return False
        if self.effective_to and day > self.effective_to:
            return False
        return self.is_active
