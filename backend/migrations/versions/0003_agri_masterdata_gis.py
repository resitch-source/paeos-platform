"""Agriculture Master Data + GIS.

Adds agriculture reference-data tables and PostGIS geospatial tables (farms,
parcels, administrative areas) with GiST spatial indexes and Row-Level Security.
Additive and non-destructive. PostGIS was enabled by the foundation baseline.

Revision ID: 0003_agri_masterdata_gis
Revises: 0002_enterprise_core
Create Date: 2026-09-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import UUID

revision = "0003_agri_masterdata_gis"
down_revision = "0002_enterprise_core"
branch_labels = None
depends_on = None

SCHEMA = "platform"
SRID = 4326

MASTER_DATA_TABLES = (
    "agri_crop_category",
    "agri_crop",
    "agri_crop_variety",
    "agri_soil_type",
    "agri_land_use_type",
)
GIS_TABLES = ("agri_admin_area", "agri_farm", "agri_land_parcel")


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
    # --- Master data ---
    op.create_table(
        "agri_crop_category", *_md_cols(),
        sa.UniqueConstraint("tenant_id", "code", name="uq_agri_crop_category_tenant_id_code"),
        schema=SCHEMA,
    )
    _tenant_index("agri_crop_category")

    op.create_table(
        "agri_crop", *_md_cols(),
        sa.Column("category_id", UUID(as_uuid=True), nullable=True),
        sa.Column("scientific_name", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_id"], [f"{SCHEMA}.agri_crop_category.id"],
            name="fk_agri_crop_category_id_agri_crop_category",
        ),
        sa.UniqueConstraint("tenant_id", "code", name="uq_agri_crop_tenant_id_code"),
        schema=SCHEMA,
    )
    _tenant_index("agri_crop")

    op.create_table(
        "agri_crop_variety", *_md_cols(),
        sa.Column("crop_id", UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["crop_id"], [f"{SCHEMA}.agri_crop.id"],
            name="fk_agri_crop_variety_crop_id_agri_crop",
        ),
        sa.UniqueConstraint("tenant_id", "code", name="uq_agri_crop_variety_tenant_id_code"),
        schema=SCHEMA,
    )
    _tenant_index("agri_crop_variety")
    op.create_index("ix_agri_crop_variety_crop_id", "agri_crop_variety", ["crop_id"], schema=SCHEMA)

    for tbl in ("agri_soil_type", "agri_land_use_type"):
        op.create_table(
            tbl, *_md_cols(),
            sa.UniqueConstraint("tenant_id", "code", name=f"uq_{tbl}_tenant_id_code"),
            schema=SCHEMA,
        )
        _tenant_index(tbl)

    # --- GIS ---
    op.create_table(
        "agri_admin_area", *_base_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("level", sa.String(32), nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), nullable=True),
        sa.Column("boundary", Geometry("MULTIPOLYGON", srid=SRID, spatial_index=False),
                  nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_id"], [f"{SCHEMA}.agri_admin_area.id"],
            name="fk_agri_admin_area_parent_id_agri_admin_area",
        ),
        sa.UniqueConstraint("tenant_id", "code", name="uq_agri_admin_area_tenant_id_code"),
        schema=SCHEMA,
    )
    _tenant_index("agri_admin_area")
    op.create_index("ix_agri_admin_area_parent_id", "agri_admin_area", ["parent_id"], schema=SCHEMA)
    op.create_index(
        "ix_agri_admin_area_boundary", "agri_admin_area", ["boundary"],
        schema=SCHEMA, postgresql_using="gist",
    )

    op.create_table(
        "agri_farm", *_base_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("org_unit_id", UUID(as_uuid=True), nullable=True),
        sa.Column("admin_area_id", UUID(as_uuid=True), nullable=True),
        sa.Column("location", Geometry("POINT", srid=SRID, spatial_index=False),
                  nullable=True),
        sa.Column("area_hectares", sa.Numeric(12, 4), nullable=True),
        sa.Column("area_classification", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.ForeignKeyConstraint(
            ["org_unit_id"], [f"{SCHEMA}.org_unit.id"],
            name="fk_agri_farm_org_unit_id_org_unit",
        ),
        sa.ForeignKeyConstraint(
            ["admin_area_id"], [f"{SCHEMA}.agri_admin_area.id"],
            name="fk_agri_farm_admin_area_id_agri_admin_area",
        ),
        sa.UniqueConstraint("tenant_id", "code", name="uq_agri_farm_tenant_id_code"),
        schema=SCHEMA,
    )
    _tenant_index("agri_farm")
    op.create_index(
        "ix_agri_farm_location", "agri_farm", ["location"],
        schema=SCHEMA, postgresql_using="gist",
    )

    op.create_table(
        "agri_land_parcel", *_base_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("farm_id", UUID(as_uuid=True), nullable=False),
        sa.Column("soil_type_id", UUID(as_uuid=True), nullable=True),
        sa.Column("land_use_type_id", UUID(as_uuid=True), nullable=True),
        sa.Column("boundary", Geometry("MULTIPOLYGON", srid=SRID, spatial_index=False),
                  nullable=True),
        sa.Column("area_sqm", sa.Numeric(16, 2), nullable=True),
        sa.Column("area_classification", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.ForeignKeyConstraint(
            ["farm_id"], [f"{SCHEMA}.agri_farm.id"],
            name="fk_agri_land_parcel_farm_id_agri_farm",
        ),
        sa.ForeignKeyConstraint(
            ["soil_type_id"], [f"{SCHEMA}.agri_soil_type.id"],
            name="fk_agri_land_parcel_soil_type_id_agri_soil_type",
        ),
        sa.ForeignKeyConstraint(
            ["land_use_type_id"], [f"{SCHEMA}.agri_land_use_type.id"],
            name="fk_agri_land_parcel_land_use_type_id_agri_land_use_type",
        ),
        sa.UniqueConstraint("tenant_id", "code", name="uq_agri_land_parcel_tenant_id_code"),
        schema=SCHEMA,
    )
    _tenant_index("agri_land_parcel")
    op.create_index("ix_agri_land_parcel_farm_id", "agri_land_parcel", ["farm_id"], schema=SCHEMA)
    op.create_index(
        "ix_agri_land_parcel_boundary", "agri_land_parcel", ["boundary"],
        schema=SCHEMA, postgresql_using="gist",
    )

    # --- Row-Level Security on all new tenant-owned tables ---
    for table in (*MASTER_DATA_TABLES, *GIS_TABLES):
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
    for table in (*GIS_TABLES, *MASTER_DATA_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {SCHEMA}.{table}")
    for table in (
        "agri_land_parcel",
        "agri_farm",
        "agri_admin_area",
        "agri_land_use_type",
        "agri_soil_type",
        "agri_crop_variety",
        "agri_crop",
        "agri_crop_category",
    ):
        op.drop_table(table, schema=SCHEMA)
