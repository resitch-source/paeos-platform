"""Livestock + Poultry.

Adds livestock species/breed master data and animal-group (herd/flock)
operations with production, mortality, and health records. Additive and
non-destructive; RLS enforces tenant isolation on every new table.

Revision ID: 0005_livestock
Revises: 0004_crop_production
Create Date: 2026-09-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0005_livestock"
down_revision = "0004_crop_production"
branch_labels = None
depends_on = None

SCHEMA = "platform"

TENANT_TABLES = (
    "livestock_species",
    "livestock_breed",
    "animal_group",
    "animal_production_record",
    "animal_mortality_record",
    "animal_health_event",
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


def _tenant_index(table: str) -> None:
    op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"], schema=SCHEMA)


def upgrade() -> None:
    op.create_table(
        "livestock_species", *_md_cols(),
        sa.UniqueConstraint("tenant_id", "code", name="uq_livestock_species_tenant_id_code"),
        schema=SCHEMA,
    )
    _tenant_index("livestock_species")

    op.create_table(
        "livestock_breed", *_md_cols(),
        sa.Column("species_id", UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["species_id"], [f"{SCHEMA}.livestock_species.id"],
                                name="fk_livestock_breed_species_id_livestock_species"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_livestock_breed_tenant_id_code"),
        schema=SCHEMA,
    )
    _tenant_index("livestock_breed")
    op.create_index("ix_livestock_breed_species_id", "livestock_breed",
                    ["species_id"], schema=SCHEMA)

    op.create_table(
        "animal_group", *_base_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("species_id", UUID(as_uuid=True), nullable=False),
        sa.Column("breed_id", UUID(as_uuid=True), nullable=True),
        sa.Column("farm_id", UUID(as_uuid=True), nullable=True),
        sa.Column("org_unit_id", UUID(as_uuid=True), nullable=True),
        sa.Column("purpose", sa.String(32), nullable=True),
        sa.Column("head_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="established"),
        sa.Column("established_date", sa.Date, nullable=True),
        sa.ForeignKeyConstraint(["species_id"], [f"{SCHEMA}.livestock_species.id"],
                                name="fk_animal_group_species_id_livestock_species"),
        sa.ForeignKeyConstraint(["breed_id"], [f"{SCHEMA}.livestock_breed.id"],
                                name="fk_animal_group_breed_id_livestock_breed"),
        sa.ForeignKeyConstraint(["farm_id"], [f"{SCHEMA}.agri_farm.id"],
                                name="fk_animal_group_farm_id_agri_farm"),
        sa.ForeignKeyConstraint(["org_unit_id"], [f"{SCHEMA}.org_unit.id"],
                                name="fk_animal_group_org_unit_id_org_unit"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_animal_group_tenant_id_code"),
        schema=SCHEMA,
    )
    _tenant_index("animal_group")

    op.create_table(
        "animal_production_record", *_base_cols(),
        sa.Column("group_id", UUID(as_uuid=True), nullable=False),
        sa.Column("recorded_at", sa.Date, nullable=False),
        sa.Column("metric_type", sa.String(32), nullable=False),
        sa.Column("quantity", sa.Numeric(16, 4), nullable=False),
        sa.Column("uom", sa.String(16), nullable=False),
        sa.Column("classification", sa.String(16), nullable=False, server_default="MEASURED"),
        sa.ForeignKeyConstraint(["group_id"], [f"{SCHEMA}.animal_group.id"],
                                name="fk_animal_production_record_group_id_animal_group"),
        schema=SCHEMA,
    )
    _tenant_index("animal_production_record")
    op.create_index("ix_animal_production_record_group_id", "animal_production_record",
                    ["group_id"], schema=SCHEMA)

    op.create_table(
        "animal_mortality_record", *_base_cols(),
        sa.Column("group_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_date", sa.Date, nullable=False),
        sa.Column("count", sa.Integer, nullable=False),
        sa.Column("cause_note", sa.String(500), nullable=False, server_default=""),
        sa.Column("classification", sa.String(16), nullable=False, server_default="MEASURED"),
        sa.ForeignKeyConstraint(["group_id"], [f"{SCHEMA}.animal_group.id"],
                                name="fk_animal_mortality_record_group_id_animal_group"),
        schema=SCHEMA,
    )
    _tenant_index("animal_mortality_record")
    op.create_index("ix_animal_mortality_record_group_id", "animal_mortality_record",
                    ["group_id"], schema=SCHEMA)

    op.create_table(
        "animal_health_event", *_base_cols(),
        sa.Column("group_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_date", sa.Date, nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["group_id"], [f"{SCHEMA}.animal_group.id"],
                                name="fk_animal_health_event_group_id_animal_group"),
        schema=SCHEMA,
    )
    _tenant_index("animal_health_event")
    op.create_index("ix_animal_health_event_group_id", "animal_health_event",
                    ["group_id"], schema=SCHEMA)

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
        "animal_health_event",
        "animal_mortality_record",
        "animal_production_record",
        "animal_group",
        "livestock_breed",
        "livestock_species",
    ):
        op.drop_table(table, schema=SCHEMA)
