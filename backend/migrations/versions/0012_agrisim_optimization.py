"""AgriSim + Optimization + Digital Twins.

Adds a standalone scenario_run table capturing simulation/optimization runs with
their full provenance envelope (no cropping-cycle FK, so it is non-geometric and
testable on any PostgreSQL). Additive and non-destructive. RLS on the new table.

Revision ID: 0012_agrisim_optimization
Revises: 0011_agri_intelligence
Create Date: 2026-09-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0012_agrisim_optimization"
down_revision = "0011_agri_intelligence"
branch_labels = None
depends_on = None

SCHEMA = "platform"

TENANT_TABLES = ("scenario_run",)


def upgrade() -> None:
    op.create_table(
        "scenario_run",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
        sa.Column("scenario", sa.String(128), nullable=False),
        sa.Column("subject_ref", sa.String(128), nullable=False, server_default=""),
        sa.Column("ran_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record", JSONB, nullable=False),
        schema=SCHEMA,
    )
    op.create_index("ix_scenario_run_tenant_id", "scenario_run", ["tenant_id"],
                    schema=SCHEMA)

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
    op.drop_table("scenario_run", schema=SCHEMA)
