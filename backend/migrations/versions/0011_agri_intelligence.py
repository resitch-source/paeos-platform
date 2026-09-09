"""AgriIntelligence / AI Agents.

Adds agent runs and persisted AI recommendations (advisory only; never
auto-applied). Additive and non-destructive; no geometry. RLS on every new table.

Revision ID: 0011_agri_intelligence
Revises: 0010_training_support_experts
Create Date: 2026-09-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0011_agri_intelligence"
down_revision = "0010_training_support_experts"
branch_labels = None
depends_on = None

SCHEMA = "platform"

TENANT_TABLES = (
    "agent_run",
    "ai_recommendation",
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


def upgrade() -> None:
    op.create_table(
        "agent_run", *_base_cols(), *_audit_cols(),
        sa.Column("agent_name", sa.String(128), nullable=False),
        sa.Column("params", JSONB, nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="completed"),
        schema=SCHEMA,
    )
    _ti("agent_run")

    op.create_table(
        "ai_recommendation", *_base_cols(), *_audit_cols(),
        sa.Column("agent_run_id", UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("classification", sa.String(16), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("assumptions", JSONB, nullable=True),
        sa.Column("uncertainty_note", sa.Text, nullable=False, server_default=""),
        sa.Column("requires_human_approval", sa.Boolean, nullable=False,
                  server_default=sa.text("true")),
        sa.Column("status", sa.String(16), nullable=False, server_default="proposed"),
        sa.Column("decided_by", UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_run_id"], [f"{SCHEMA}.agent_run.id"],
                                name="fk_ai_recommendation_agent_run_id_agent_run"),
        schema=SCHEMA,
    )
    _ti("ai_recommendation")
    op.create_index("ix_ai_recommendation_agent_run_id", "ai_recommendation",
                    ["agent_run_id"], schema=SCHEMA)

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
    for table in ("ai_recommendation", "agent_run"):
        op.drop_table(table, schema=SCHEMA)
