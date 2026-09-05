"""Reusable ORM mixins (section C).

- :class:`UUIDPrimaryKeyMixin` — UUID v4 primary key.
- :class:`TimestampMixin` — created/updated timestamps.
- :class:`AuditMixin` — created_by/updated_by audit fields.
- :class:`VersionMixin` — optimistic concurrency version column.
- :class:`SoftDeleteMixin` — soft-delete flag + timestamp.
- :class:`TenantMixin` — mandatory tenant_id for tenant-owned entities.

Compose these to build consistent, isolation-aware tables.
"""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import Boolean, DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AuditMixin:
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)


class VersionMixin:
    """Optimistic concurrency control via a monotonically increasing version.

    The ``version`` column is maintained by application/domain services on
    update. Models that want SQLAlchemy to enforce it automatically can set
    ``__mapper_args__ = {"version_id_col": <Model>.version}`` on the concrete
    class.
    """

    version: Mapped[int] = mapped_column(default=1, nullable=False)


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    deleted_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class TenantMixin:
    """Mandatory tenant scoping for tenant-owned entities.

    ``tenant_id`` is non-null and indexed. Row-Level Security policies (see
    migrations) enforce that only rows matching the current ``app.tenant_id``
    session variable are visible.
    """

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
