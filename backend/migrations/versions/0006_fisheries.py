"""Fisheries + Aquaculture.

Adds aquatic species master data and aquaculture operations: culture units
(PostGIS-located ponds/cages/tanks), cycles, and water-quality / harvest /
mortality records. Additive and non-destructive. RLS on every new table;
GiST spatial index on the culture-unit location.

Revision ID: 0006_fisheries
Revises: 0005_livestock
Create Date: 2026-09-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import UUID

revision = "0006_fisheries"
down_revision = "0005_livestock"
branch_labels = None
depends_on = None

SCHEMA = "platform"
SRID = 4326

TENANT_TABLES = (
    "aquatic_species",
    "culture_unit",
    "aquaculture_cycle",
    "water_quality_reading",
    "aqua_harvest_record",
    "aqua_mortality_record",
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


def _md_cols() -> list[sa.Column]:
    return [
        *_base_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("revision", sa.Integer, nullable=False, server_default="1"),
        sa.Column("effective_from", sa.Date, nullable=True),
        sa.Column("effective_to", sa.Date, nullable=True),
    ]


def _ti(table: str) -> None:
    op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"], schema=SCHEMA)


def upgrade() -> None:
    op.create_table(
        "aquatic_species", *_md_cols(),
        sa.UniqueConstraint("tenant_id", "code", name="uq_aquatic_species_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("aquatic_species")

    op.create_table(
        "culture_unit", *_base_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("unit_type", sa.String(32), nullable=False, server_default="pond"),
        sa.Column("farm_id", UUID(as_uuid=True), nullable=True),
        sa.Column("location", Geometry("POINT", srid=SRID, spatial_index=False),
                  nullable=True),
        sa.Column("water_area_sqm", sa.Numeric(16, 2), nullable=True),
        sa.Column("area_classification", sa.String(16), nullable=False,
                  server_default="UNKNOWN"),
        sa.ForeignKeyConstraint(["farm_id"], [f"{SCHEMA}.agri_farm.id"],
                                name="fk_culture_unit_farm_id_agri_farm"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_culture_unit_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("culture_unit")
    op.create_index("ix_culture_unit_location", "culture_unit", ["location"],
                    schema=SCHEMA, postgresql_using="gist")

    op.create_table(
        "aquaculture_cycle", *_base_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("culture_unit_id", UUID(as_uuid=True), nullable=False),
        sa.Column("species_id", UUID(as_uuid=True), nullable=False),
        sa.Column("stocking_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("stocking_date", sa.Date, nullable=True),
        sa.Column("expected_harvest_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="stocked"),
        sa.ForeignKeyConstraint(["culture_unit_id"], [f"{SCHEMA}.culture_unit.id"],
                                name="fk_aquaculture_cycle_culture_unit_id_culture_unit"),
        sa.ForeignKeyConstraint(["species_id"], [f"{SCHEMA}.aquatic_species.id"],
                                name="fk_aquaculture_cycle_species_id_aquatic_species"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_aquaculture_cycle_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("aquaculture_cycle")
    op.create_index("ix_aquaculture_cycle_culture_unit_id", "aquaculture_cycle",
                    ["culture_unit_id"], schema=SCHEMA)

    op.create_table(
        "water_quality_reading", *_base_cols(),
        sa.Column("culture_unit_id", UUID(as_uuid=True), nullable=False),
        sa.Column("read_at", sa.Date, nullable=False),
        sa.Column("metric_type", sa.String(32), nullable=False),
        sa.Column("value", sa.Numeric(16, 4), nullable=False),
        sa.Column("uom", sa.String(16), nullable=False),
        sa.Column("classification", sa.String(16), nullable=False, server_default="MEASURED"),
        sa.ForeignKeyConstraint(["culture_unit_id"], [f"{SCHEMA}.culture_unit.id"],
                                name="fk_water_quality_reading_culture_unit_id_culture_unit"),
        schema=SCHEMA,
    )
    _ti("water_quality_reading")
    op.create_index("ix_water_quality_reading_culture_unit_id", "water_quality_reading",
                    ["culture_unit_id"], schema=SCHEMA)

    op.create_table(
        "aqua_harvest_record", *_base_cols(),
        sa.Column("cycle_id", UUID(as_uuid=True), nullable=False),
        sa.Column("harvest_date", sa.Date, nullable=False),
        sa.Column("quantity", sa.Numeric(16, 4), nullable=False),
        sa.Column("uom", sa.String(16), nullable=False),
        sa.Column("classification", sa.String(16), nullable=False, server_default="MEASURED"),
        sa.ForeignKeyConstraint(["cycle_id"], [f"{SCHEMA}.aquaculture_cycle.id"],
                                name="fk_aqua_harvest_record_cycle_id_aquaculture_cycle"),
        schema=SCHEMA,
    )
    _ti("aqua_harvest_record")
    op.create_index("ix_aqua_harvest_record_cycle_id", "aqua_harvest_record",
                    ["cycle_id"], schema=SCHEMA)

    op.create_table(
        "aqua_mortality_record", *_base_cols(),
        sa.Column("cycle_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_date", sa.Date, nullable=False),
        sa.Column("count", sa.Integer, nullable=False),
        sa.Column("cause_note", sa.String(500), nullable=False, server_default=""),
        sa.Column("classification", sa.String(16), nullable=False, server_default="MEASURED"),
        sa.ForeignKeyConstraint(["cycle_id"], [f"{SCHEMA}.aquaculture_cycle.id"],
                                name="fk_aqua_mortality_record_cycle_id_aquaculture_cycle"),
        schema=SCHEMA,
    )
    _ti("aqua_mortality_record")
    op.create_index("ix_aqua_mortality_record_cycle_id", "aqua_mortality_record",
                    ["cycle_id"], schema=SCHEMA)

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
        "aqua_mortality_record",
        "aqua_harvest_record",
        "water_quality_reading",
        "aquaculture_cycle",
        "culture_unit",
        "aquatic_species",
    ):
        op.drop_table(table, schema=SCHEMA)
