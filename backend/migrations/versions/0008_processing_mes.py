"""Processing + MES + Digital Twin.

Adds process definitions (recipes) with input/output lines, production runs,
quality checks, processing assets, and asset telemetry. Additive and
non-destructive; no geometry. RLS on every new table. No machinery-control
objects are created — the digital twin is advisory only.

Revision ID: 0008_processing_mes
Revises: 0007_inventory_procurement
Create Date: 2026-09-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0008_processing_mes"
down_revision = "0007_inventory_procurement"
branch_labels = None
depends_on = None

SCHEMA = "platform"

TENANT_TABLES = (
    "process_definition",
    "process_input",
    "process_output",
    "production_run",
    "quality_check",
    "processing_asset",
    "asset_telemetry",
)


def _base_cols() -> list[sa.Column]:
    return [
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
    ]


def _audit_cols() -> list[sa.Column]:
    return [
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
    ]


def _ti(table: str) -> None:
    op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"], schema=SCHEMA)


def _line_table(name: str) -> None:
    op.create_table(
        name, *_base_cols(),
        sa.Column("definition_id", UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("quantity_per_batch", sa.Numeric(18, 4), nullable=False),
        sa.ForeignKeyConstraint(["definition_id"], [f"{SCHEMA}.process_definition.id"],
                                name=f"fk_{name}_definition_id_process_definition"),
        sa.ForeignKeyConstraint(["item_id"], [f"{SCHEMA}.inventory_item.id"],
                                name=f"fk_{name}_item_id_inventory_item"),
        schema=SCHEMA,
    )
    _ti(name)
    op.create_index(f"ix_{name}_definition_id", name, ["definition_id"], schema=SCHEMA)


def upgrade() -> None:
    op.create_table(
        "process_definition", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.UniqueConstraint("tenant_id", "code", name="uq_process_definition_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("process_definition")

    _line_table("process_input")
    _line_table("process_output")

    op.create_table(
        "production_run", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("definition_id", UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", UUID(as_uuid=True), nullable=False),
        sa.Column("batch_size", sa.Numeric(18, 4), nullable=False, server_default="1"),
        sa.Column("status", sa.String(16), nullable=False, server_default="planned"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["definition_id"], [f"{SCHEMA}.process_definition.id"],
                                name="fk_production_run_definition_id_process_definition"),
        sa.ForeignKeyConstraint(["warehouse_id"], [f"{SCHEMA}.warehouse.id"],
                                name="fk_production_run_warehouse_id_warehouse"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_production_run_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("production_run")

    op.create_table(
        "quality_check", *_base_cols(), *_audit_cols(),
        sa.Column("run_id", UUID(as_uuid=True), nullable=False),
        sa.Column("metric_type", sa.String(32), nullable=False),
        sa.Column("value", sa.Numeric(18, 4), nullable=False),
        sa.Column("uom", sa.String(16), nullable=False),
        sa.Column("classification", sa.String(16), nullable=False, server_default="MEASURED"),
        sa.ForeignKeyConstraint(["run_id"], [f"{SCHEMA}.production_run.id"],
                                name="fk_quality_check_run_id_production_run"),
        schema=SCHEMA,
    )
    _ti("quality_check")
    op.create_index("ix_quality_check_run_id", "quality_check", ["run_id"], schema=SCHEMA)

    op.create_table(
        "processing_asset", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("asset_type", sa.String(64), nullable=False, server_default="processor"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_processing_asset_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("processing_asset")

    op.create_table(
        "asset_telemetry", *_base_cols(),
        sa.Column("asset_id", UUID(as_uuid=True), nullable=False),
        sa.Column("metric", sa.String(32), nullable=False),
        sa.Column("value", sa.Numeric(18, 4), nullable=False),
        sa.Column("uom", sa.String(16), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("classification", sa.String(16), nullable=False, server_default="MEASURED"),
        sa.ForeignKeyConstraint(["asset_id"], [f"{SCHEMA}.processing_asset.id"],
                                name="fk_asset_telemetry_asset_id_processing_asset"),
        schema=SCHEMA,
    )
    _ti("asset_telemetry")
    op.create_index("ix_asset_telemetry_asset_id", "asset_telemetry", ["asset_id"], schema=SCHEMA)

    for table in TENANT_TABLES:
        fq = f"{SCHEMA}.{table}"
        op.execute(f"ALTER TABLE {fq} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {fq} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {fq}
            USING (tenant_id::text = current_setting('app.tenant_id', true))
            WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
            """
        )


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {SCHEMA}.{table}")
    for table in (
        "asset_telemetry",
        "processing_asset",
        "quality_check",
        "production_run",
        "process_output",
        "process_input",
        "process_definition",
    ):
        op.drop_table(table, schema=SCHEMA)
