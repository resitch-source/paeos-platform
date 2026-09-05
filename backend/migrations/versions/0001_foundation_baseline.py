"""PAEOS-FX foundation baseline.

Creates the platform schema, required extensions, foundation tables, and
Row-Level Security policies enforcing tenant isolation. Additive and
non-destructive: this migration only CREATEs objects.

Revision ID: 0001_foundation_baseline
Revises:
Create Date: 2026-09-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0001_foundation_baseline"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = "platform"

# Tenant-owned tables that receive RLS policies bound to app.tenant_id.
TENANT_OWNED_TABLES = (
    "tenant_setting",
    "app_user",
    "role",
    "role_permission",
    "user_role",
    "audit_log",
    "outbox_event",
    "number_sequence",
    "workflow_instance",
    "approval_request",
    "approval_step",
    "document",
    "notification",
)


def _ts_cols() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def _audit_cols() -> list[sa.Column]:
    return [
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
    ]


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    # Extensions (idempotent). PostGIS is mandated by the controller rules.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # --- tenant (catalog; not tenant-scoped) ---
    op.create_table(
        "tenant",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        *_audit_cols(),
        sa.Column("slug", sa.String(63), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("locale", sa.String(8), nullable=False, server_default="en"),
        sa.Column(
            "timezone", sa.String(64), nullable=False, server_default="Asia/Manila"
        ),
        sa.UniqueConstraint("slug", name="uq_tenant_slug"),
        schema=SCHEMA,
    )

    # --- tenant_setting ---
    op.create_table(
        "tenant_setting",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(
            ["tenant_id"], [f"{SCHEMA}.tenant.id"],
            name="fk_tenant_setting_tenant_id_tenant",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_tenant_setting_tenant_id", "tenant_setting", ["tenant_id"], schema=SCHEMA
    )

    # --- permission (global catalog) ---
    op.create_table(
        "permission",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        sa.Column("code", sa.String(128), nullable=False),
        sa.Column("description", sa.String(255), nullable=False, server_default=""),
        sa.UniqueConstraint("code", name="uq_permission_code"),
        schema=SCHEMA,
    )

    # --- role ---
    op.create_table(
        "role",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        *_audit_cols(),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_role_tenant_id_code"),
        schema=SCHEMA,
    )
    op.create_index("ix_role_tenant_id", "role", ["tenant_id"], schema=SCHEMA)

    # --- role_permission ---
    op.create_table(
        "role_permission",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"], [f"{SCHEMA}.role.id"],
            name="fk_role_permission_role_id_role",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"], [f"{SCHEMA}.permission.id"],
            name="fk_role_permission_permission_id_permission",
        ),
        sa.UniqueConstraint(
            "role_id", "permission_id", name="uq_role_permission_role_id_permission_id"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_role_permission_tenant_id", "role_permission", ["tenant_id"], schema=SCHEMA
    )

    # --- app_user ---
    op.create_table(
        "app_user",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        *_audit_cols(),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "email", name="uq_app_user_tenant_id_email"),
        schema=SCHEMA,
    )
    op.create_index("ix_app_user_tenant_id", "app_user", ["tenant_id"], schema=SCHEMA)

    # --- user_role ---
    op.create_table(
        "user_role",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], [f"{SCHEMA}.app_user.id"],
            name="fk_user_role_user_id_app_user",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], [f"{SCHEMA}.role.id"], name="fk_user_role_role_id_role"
        ),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role_user_id_role_id"),
        schema=SCHEMA,
    )
    op.create_index("ix_user_role_tenant_id", "user_role", ["tenant_id"], schema=SCHEMA)

    # --- audit_log ---
    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(128), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("before", JSONB, nullable=True),
        sa.Column("after", JSONB, nullable=True),
        sa.Column("context", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        schema=SCHEMA,
    )
    op.create_index("ix_audit_log_tenant_id", "audit_log", ["tenant_id"], schema=SCHEMA)
    op.create_index("ix_audit_log_action", "audit_log", ["action"], schema=SCHEMA)

    # --- outbox_event ---
    op.create_table(
        "outbox_event",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("dispatched", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_outbox_event_tenant_id", "outbox_event", ["tenant_id"], schema=SCHEMA
    )
    op.create_index("ix_outbox_event_name", "outbox_event", ["name"], schema=SCHEMA)
    op.create_index(
        "ix_outbox_event_dispatched", "outbox_event", ["dispatched"], schema=SCHEMA
    )

    # --- number_sequence ---
    op.create_table(
        "number_sequence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("doc_type", sa.String(64), nullable=False),
        sa.Column("prefix", sa.String(16), nullable=False, server_default=""),
        sa.Column("padding", sa.Integer, nullable=False, server_default="6"),
        sa.Column("current_value", sa.BigInteger, nullable=False, server_default="0"),
        sa.UniqueConstraint(
            "tenant_id", "doc_type", name="uq_number_sequence_tenant_id_doc_type"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_number_sequence_tenant_id", "number_sequence", ["tenant_id"], schema=SCHEMA
    )

    # --- workflow_instance ---
    op.create_table(
        "workflow_instance",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        *_audit_cols(),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_key", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(128), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("data", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_workflow_instance_tenant_id", "workflow_instance", ["tenant_id"],
        schema=SCHEMA,
    )

    # --- approval_request ---
    op.create_table(
        "approval_request",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        *_audit_cols(),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("subject_type", sa.String(128), nullable=False),
        sa.Column("subject_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("context", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_approval_request_tenant_id", "approval_request", ["tenant_id"],
        schema=SCHEMA,
    )

    # --- approval_step ---
    op.create_table(
        "approval_step",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", UUID(as_uuid=True), nullable=False),
        sa.Column("step_order", sa.Integer, nullable=False),
        sa.Column("approver_role", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("decided_by", UUID(as_uuid=True), nullable=True),
        sa.Column("comment", sa.String(500), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(
            ["request_id"], [f"{SCHEMA}.approval_request.id"],
            name="fk_approval_step_request_id_approval_request",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_approval_step_tenant_id", "approval_step", ["tenant_id"], schema=SCHEMA
    )

    # --- document ---
    op.create_table(
        "document",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        *_audit_cols(),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(127), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        schema=SCHEMA,
    )
    op.create_index("ix_document_tenant_id", "document", ["tenant_id"], schema=SCHEMA)

    # --- notification ---
    op.create_table(
        "notification",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        *_ts_cols(),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("template_key", sa.String(128), nullable=False),
        sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.false()),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_notification_tenant_id", "notification", ["tenant_id"], schema=SCHEMA
    )
    op.create_index(
        "ix_notification_recipient_id", "notification", ["recipient_id"], schema=SCHEMA
    )

    # --- Row-Level Security policies (tenant isolation) ---
    # Comparison is text-vs-text against the app.tenant_id session variable so an
    # unset/empty value simply matches no rows (fail-closed) rather than erroring.
    for table in TENANT_OWNED_TABLES:
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
    for table in TENANT_OWNED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {SCHEMA}.{table}")
    for table in (
        "notification",
        "document",
        "approval_step",
        "approval_request",
        "workflow_instance",
        "number_sequence",
        "outbox_event",
        "audit_log",
        "user_role",
        "app_user",
        "role_permission",
        "role",
        "permission",
        "tenant_setting",
        "tenant",
    ):
        op.drop_table(table, schema=SCHEMA)
