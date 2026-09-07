"""Training + Technical Support + Expert Marketplace.

Adds courses + enrollments, support tickets + comments, and expert profiles +
engagements (with an agreed fee in integer minor units). Additive and
non-destructive; no geometry. RLS on every new table.

Revision ID: 0010_training_support_experts
Revises: 0009_marketplace_trading
Create Date: 2026-09-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0010_training_support_experts"
down_revision = "0009_marketplace_trading"
branch_labels = None
depends_on = None

SCHEMA = "platform"

TENANT_TABLES = (
    "course",
    "enrollment",
    "support_ticket",
    "ticket_comment",
    "expert_profile",
    "engagement",
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
    # --- Training ---
    op.create_table(
        "course", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("category", sa.String(128), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_course_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("course")

    op.create_table(
        "enrollment", *_base_cols(), *_audit_cols(),
        sa.Column("course_id", UUID(as_uuid=True), nullable=False),
        sa.Column("learner_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="enrolled"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], [f"{SCHEMA}.course.id"],
                                name="fk_enrollment_course_id_course"),
        sa.ForeignKeyConstraint(["learner_id"], [f"{SCHEMA}.app_user.id"],
                                name="fk_enrollment_learner_id_app_user"),
        sa.UniqueConstraint("tenant_id", "course_id", "learner_id",
                            name="uq_enrollment_tenant_course_learner"),
        schema=SCHEMA,
    )
    _ti("enrollment")
    op.create_index("ix_enrollment_course_id", "enrollment", ["course_id"], schema=SCHEMA)
    op.create_index("ix_enrollment_learner_id", "enrollment", ["learner_id"], schema=SCHEMA)

    # --- Technical support ---
    op.create_table(
        "support_ticket", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False, server_default=""),
        sa.Column("priority", sa.String(16), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("assignee_id", UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assignee_id"], [f"{SCHEMA}.app_user.id"],
                                name="fk_support_ticket_assignee_id_app_user"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_support_ticket_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("support_ticket")
    op.create_index("ix_support_ticket_assignee_id", "support_ticket",
                    ["assignee_id"], schema=SCHEMA)

    op.create_table(
        "ticket_comment", *_base_cols(), *_audit_cols(),
        sa.Column("ticket_id", UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", UUID(as_uuid=True), nullable=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], [f"{SCHEMA}.support_ticket.id"],
                                name="fk_ticket_comment_ticket_id_support_ticket"),
        sa.ForeignKeyConstraint(["author_id"], [f"{SCHEMA}.app_user.id"],
                                name="fk_ticket_comment_author_id_app_user"),
        schema=SCHEMA,
    )
    _ti("ticket_comment")
    op.create_index("ix_ticket_comment_ticket_id", "ticket_comment",
                    ["ticket_id"], schema=SCHEMA)

    # --- Expert marketplace (financial: gate #12) ---
    op.create_table(
        "expert_profile", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("expertise_area", sa.String(128), nullable=False, server_default=""),
        sa.Column("bio", sa.Text, nullable=False, server_default=""),
        sa.Column("rate_minor", sa.BigInteger, nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="PHP"),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.ForeignKeyConstraint(["user_id"], [f"{SCHEMA}.app_user.id"],
                                name="fk_expert_profile_user_id_app_user"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_expert_profile_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("expert_profile")

    op.create_table(
        "engagement", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("expert_id", UUID(as_uuid=True), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("fee_minor", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="PHP"),
        sa.Column("status", sa.String(16), nullable=False, server_default="requested"),
        sa.ForeignKeyConstraint(["expert_id"], [f"{SCHEMA}.expert_profile.id"],
                                name="fk_engagement_expert_id_expert_profile"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_engagement_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("engagement")
    op.create_index("ix_engagement_expert_id", "engagement", ["expert_id"], schema=SCHEMA)

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
    for table in ("engagement", "expert_profile", "ticket_comment", "support_ticket",
                  "enrollment", "course"):
        op.drop_table(table, schema=SCHEMA)
