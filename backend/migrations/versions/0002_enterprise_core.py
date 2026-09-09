"""Enterprise Core: organizational units.

Adds the tenant-scoped, hierarchical ``org_unit`` table with Row-Level Security.
Additive and non-destructive. IAM/tenancy tables from the foundation are reused
unchanged; the enterprise permission catalog and system roles are seeded at
runtime by the onboarding service (not in this migration).

Revision ID: 0002_enterprise_core
Revises: 0001_foundation_baseline
Create Date: 2026-09-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0002_enterprise_core"
down_revision = "0001_foundation_baseline"
branch_labels = None
depends_on = None

SCHEMA = "platform"


def upgrade() -> None:
    op.create_table(
        "org_unit",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("unit_type", sa.String(64), nullable=False, server_default="department"),
        sa.Column("parent_id", UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(
            ["parent_id"], [f"{SCHEMA}.org_unit.id"],
            name="fk_org_unit_parent_id_org_unit",
        ),
        sa.UniqueConstraint("tenant_id", "code", name="uq_org_unit_tenant_id_code"),
        schema=SCHEMA,
    )
    op.create_index("ix_org_unit_tenant_id", "org_unit", ["tenant_id"], schema=SCHEMA)
    op.create_index("ix_org_unit_parent_id", "org_unit", ["parent_id"], schema=SCHEMA)

    fq = f"{SCHEMA}.org_unit"
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
    op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {SCHEMA}.org_unit")
    op.drop_table("org_unit", schema=SCHEMA)
