"""Marketplace + Trading + Logistics.

Adds customers, marketplace listings, sales orders + lines (with monetary
pricing in integer minor units), and shipments. Additive and non-destructive;
no geometry. RLS on every new table.

Revision ID: 0009_marketplace_trading_logistics
Revises: 0008_processing_mes
Create Date: 2026-09-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0009_marketplace_trading_logistics"
down_revision = "0008_processing_mes"
branch_labels = None
depends_on = None

SCHEMA = "platform"

TENANT_TABLES = (
    "customer",
    "listing",
    "sales_order",
    "sales_order_line",
    "shipment",
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
        "customer", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contact", sa.String(255), nullable=False, server_default=""),
        sa.UniqueConstraint("tenant_id", "code", name="uq_customer_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("customer")

    op.create_table(
        "listing", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("quantity_available", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("unit_price_minor", sa.BigInteger, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="PHP"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.ForeignKeyConstraint(["item_id"], [f"{SCHEMA}.inventory_item.id"],
                                name="fk_listing_item_id_inventory_item"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_listing_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("listing")
    op.create_index("ix_listing_item_id", "listing", ["item_id"], schema=SCHEMA)

    op.create_table(
        "sales_order", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("customer_id", UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="PHP"),
        sa.Column("status", sa.String(16), nullable=False, server_default="draft"),
        sa.Column("order_date", sa.Date, nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], [f"{SCHEMA}.customer.id"],
                                name="fk_sales_order_customer_id_customer"),
        sa.ForeignKeyConstraint(["warehouse_id"], [f"{SCHEMA}.warehouse.id"],
                                name="fk_sales_order_warehouse_id_warehouse"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sales_order_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("sales_order")
    op.create_index("ix_sales_order_customer_id", "sales_order", ["customer_id"], schema=SCHEMA)

    op.create_table(
        "sales_order_line", *_base_cols(),
        sa.Column("sales_order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_price_minor", sa.BigInteger, nullable=False),
        sa.Column("line_total_minor", sa.BigInteger, nullable=False),
        sa.ForeignKeyConstraint(["sales_order_id"], [f"{SCHEMA}.sales_order.id"],
                                name="fk_sales_order_line_sales_order_id_sales_order"),
        sa.ForeignKeyConstraint(["item_id"], [f"{SCHEMA}.inventory_item.id"],
                                name="fk_sales_order_line_item_id_inventory_item"),
        schema=SCHEMA,
    )
    _ti("sales_order_line")
    op.create_index("ix_sales_order_line_sales_order_id", "sales_order_line",
                    ["sales_order_id"], schema=SCHEMA)

    op.create_table(
        "shipment", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("sales_order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="planned"),
        sa.Column("carrier_note", sa.String(255), nullable=False, server_default=""),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["sales_order_id"], [f"{SCHEMA}.sales_order.id"],
                                name="fk_shipment_sales_order_id_sales_order"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_shipment_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("shipment")
    op.create_index("ix_shipment_sales_order_id", "shipment", ["sales_order_id"], schema=SCHEMA)

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
    for table in ("shipment", "sales_order_line", "sales_order", "listing", "customer"):
        op.drop_table(table, schema=SCHEMA)
