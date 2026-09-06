"""Crop Production + Simulation.

Adds cropping cycles, growth observations, harvest records, and persisted
simulation runs. Additive and non-destructive; no geometry. RLS enforces tenant
isolation on every new table.

Revision ID: 0004_crop_production
Revises: 0003_agri_masterdata_gis
Create Date: 2026-09-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0004_crop_production"
down_revision = "0003_agri_masterdata_gis"
branch_labels = None
depends_on = None

SCHEMA = "platform"

TENANT_TABLES = (
    "cropping_cycle",
    "growth_observation",
    "harvest_record",
    "simulation_run",
)


def _base_cols() -> list[sa.Column]:
    return [
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "cropping_cycle", *_base_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("parcel_id", UUID(as_uuid=True), nullable=False),
        sa.Column("crop_id", UUID(as_uuid=True), nullable=False),
        sa.Column("variety_id", UUID(as_uuid=True), nullable=True),
        sa.Column("season", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="planned"),
        sa.Column("planting_date", sa.Date, nullable=True),
        sa.Column("expected_harvest_date", sa.Date, nullable=True),
        sa.Column("planted_area_ha", sa.Numeric(12, 4), nullable=True),
        sa.Column("area_classification", sa.String(16), nullable=False,
                  server_default="UNKNOWN"),
        sa.ForeignKeyConstraint(["parcel_id"], [f"{SCHEMA}.agri_land_parcel.id"],
                                name="fk_cropping_cycle_parcel_id_agri_land_parcel"),
        sa.ForeignKeyConstraint(["crop_id"], [f"{SCHEMA}.agri_crop.id"],
                                name="fk_cropping_cycle_crop_id_agri_crop"),
        sa.ForeignKeyConstraint(["variety_id"], [f"{SCHEMA}.agri_crop_variety.id"],
                                name="fk_cropping_cycle_variety_id_agri_crop_variety"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_cropping_cycle_tenant_id_code"),
        schema=SCHEMA,
    )
    op.create_index("ix_cropping_cycle_tenant_id", "cropping_cycle", ["tenant_id"], schema=SCHEMA)
    op.create_index("ix_cropping_cycle_parcel_id", "cropping_cycle", ["parcel_id"], schema=SCHEMA)

    op.create_table(
        "growth_observation", *_base_cols(),
        sa.Column("cycle_id", UUID(as_uuid=True), nullable=False),
        sa.Column("observed_at", sa.Date, nullable=False),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        sa.Column("metric_value", sa.Numeric(16, 4), nullable=True),
        sa.Column("metric_unit", sa.String(16), nullable=True),
        sa.Column("metric_classification", sa.String(16), nullable=False,
                  server_default="UNKNOWN"),
        sa.ForeignKeyConstraint(["cycle_id"], [f"{SCHEMA}.cropping_cycle.id"],
                                name="fk_growth_observation_cycle_id_cropping_cycle"),
        schema=SCHEMA,
    )
    op.create_index("ix_growth_observation_tenant_id", "growth_observation",
                    ["tenant_id"], schema=SCHEMA)
    op.create_index("ix_growth_observation_cycle_id", "growth_observation",
                    ["cycle_id"], schema=SCHEMA)

    op.create_table(
        "harvest_record", *_base_cols(),
        sa.Column("cycle_id", UUID(as_uuid=True), nullable=False),
        sa.Column("harvest_date", sa.Date, nullable=False),
        sa.Column("quantity", sa.Numeric(16, 4), nullable=False),
        sa.Column("uom", sa.String(16), nullable=False),
        sa.Column("quantity_classification", sa.String(16), nullable=False,
                  server_default="MEASURED"),
        sa.ForeignKeyConstraint(["cycle_id"], [f"{SCHEMA}.cropping_cycle.id"],
                                name="fk_harvest_record_cycle_id_cropping_cycle"),
        schema=SCHEMA,
    )
    op.create_index("ix_harvest_record_tenant_id", "harvest_record", ["tenant_id"], schema=SCHEMA)
    op.create_index("ix_harvest_record_cycle_id", "harvest_record", ["cycle_id"], schema=SCHEMA)

    op.create_table(
        "simulation_run", *_base_cols(),
        sa.Column("cycle_id", UUID(as_uuid=True), nullable=True),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
        sa.Column("scenario", sa.String(128), nullable=False),
        sa.Column("ran_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["cycle_id"], [f"{SCHEMA}.cropping_cycle.id"],
                                name="fk_simulation_run_cycle_id_cropping_cycle"),
        schema=SCHEMA,
    )
    op.create_index("ix_simulation_run_tenant_id", "simulation_run", ["tenant_id"], schema=SCHEMA)
    op.create_index("ix_simulation_run_cycle_id", "simulation_run", ["cycle_id"], schema=SCHEMA)

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
    for table in ("simulation_run", "harvest_record", "growth_observation", "cropping_cycle"):
        op.drop_table(table, schema=SCHEMA)
