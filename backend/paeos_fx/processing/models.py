"""Processing / MES + digital-twin models (Phase 7).

Recipes (process definitions with input/output lines), production runs, quality
checks, processing assets, and asset telemetry. Recipe quantities are
tenant-defined; actual/observed values carry a provenance classification. No
fabricated coefficients.
"""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
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

PRODUCTION_RUN_WORKFLOW = StateMachine(
    states=frozenset({"planned", "running", "completed", "closed", "cancelled"}),
    initial="planned",
    transitions=[
        Transition("planned", "running", "start"),
        Transition("running", "completed", "complete"),
        Transition("completed", "closed", "close"),
        Transition("planned", "cancelled", "cancel"),
        Transition("running", "cancelled", "cancel"),
    ],
)


class ProcessDefinition(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A recipe: named process producing outputs from inputs per batch."""

    __tablename__ = "process_definition"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")


class ProcessInput(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An input item consumed per batch (quantity is tenant-defined)."""

    __tablename__ = "process_input"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    definition_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.process_definition.id"), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.inventory_item.id"), nullable=False
    )
    quantity_per_batch: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)


class ProcessOutput(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An output item produced per batch (quantity is tenant-defined)."""

    __tablename__ = "process_output"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    definition_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.process_definition.id"), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.inventory_item.id"), nullable=False
    )
    quantity_per_batch: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)


class ProductionRun(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """An MES production run executing a process definition."""

    __tablename__ = "production_run"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    definition_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.process_definition.id"), nullable=False
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.warehouse.id"), nullable=False
    )
    batch_size: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("1"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), default="planned", nullable=False)
    started_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class QualityCheck(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A quality measurement recorded against a production run."""

    __tablename__ = "quality_check"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.production_run.id"), nullable=False, index=True
    )
    metric_type: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    uom: Mapped[str] = mapped_column(String(16), nullable=False)
    classification: Mapped[str] = mapped_column(
        String(16), default=Classification.MEASURED.value, nullable=False
    )


class ProcessingAsset(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """A processing asset that a digital twin can model (e.g. an oil expeller)."""

    __tablename__ = "processing_asset"
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(64), default="processor")


class AssetTelemetry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A telemetry reading for a processing asset (MEASURED)."""

    __tablename__ = "asset_telemetry"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("platform.processing_asset.id"), nullable=False, index=True
    )
    metric: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    uom: Mapped[str] = mapped_column(String(16), nullable=False)
    read_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    classification: Mapped[str] = mapped_column(
        String(16), default=Classification.MEASURED.value, nullable=False
    )
