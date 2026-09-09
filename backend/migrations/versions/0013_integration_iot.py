"""IoT + Integrations.

Adds an idempotent inbound-message ledger for integration messages (e.g. IoT
telemetry). Additive and non-destructive; no geometry. RLS on the new table.

Revision ID: 0013_integration_iot
Revises: 0012_agrisim_optimization
Create Date: 2026-09-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0013_integration_iot"
down_revision = "0012_agrisim_optimization"
branch_labels = None
depends_on = None

SCHEMA = "platform"

TENANT_TABLES = ("inbound_message",)


def upgrade() -> None:
    op.create_table(
        "inbound_message",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("system", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("payload", JSONB, nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="received"),
        sa.Column("attempt", sa.Integer, nullable=False, server_default="1"),
        sa.Column("error", sa.Text, nullable=False, server_default=""),
        sa.UniqueConstraint("tenant_id", "system", "idempotency_key",
                            name="uq_inbound_message_tenant_system_idem"),
        schema=SCHEMA,
    )
    op.create_index("ix_inbound_message_tenant_id", "inbound_message", ["tenant_id"],
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
    op.drop_table("inbound_message", schema=SCHEMA)
