"""Inventory + Procurement + Warehouse.

Adds item master, warehouses/storage locations, stock levels, the stock-movement
ledger, and procurement (suppliers, purchase orders + lines with monetary
pricing in integer minor units). Additive and non-destructive; no geometry.
RLS enforces tenant isolation on every new table.

Revision ID: 0007_inventory_procurement
Revises: 0006_fisheries
Create Date: 2026-09-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0007_inventory_procurement"
down_revision = "0006_fisheries"
branch_labels = None
depends_on = None

SCHEMA = "platform"

TENANT_TABLES = (
    "inventory_item",
    "warehouse",
    "storage_location",
    "stock_level",
    "stock_movement",
    "supplier",
    "purchase_order",
    "purchase_order_line",
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
    # inventory_item (master data)
    op.create_table(
        "inventory_item",
        *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("revision", sa.Integer, nullable=False, server_default="1"),
        sa.Column("effective_from", sa.Date, nullable=True),
        sa.Column("effective_to", sa.Date, nullable=True),
        sa.Column("base_uom", sa.String(16), nullable=False, server_default="ea"),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("is_stocked", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_inventory_item_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("inventory_item")

    op.create_table(
        "warehouse", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("org_unit_id", UUID(as_uuid=True), nullable=True),
        sa.Column("address", sa.String(500), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["org_unit_id"], [f"{SCHEMA}.org_unit.id"],
                                name="fk_warehouse_org_unit_id_org_unit"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_warehouse_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("warehouse")

    op.create_table(
        "storage_location", *_base_cols(), *_audit_cols(),
        sa.Column("warehouse_id", UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(["warehouse_id"], [f"{SCHEMA}.warehouse.id"],
                                name="fk_storage_location_warehouse_id_warehouse"),
        sa.UniqueConstraint("warehouse_id", "code", name="uq_storage_location_warehouse_id_code"),
        schema=SCHEMA,
    )
    _ti("storage_location")
    op.create_index("ix_storage_location_warehouse_id", "storage_location",
                    ["warehouse_id"], schema=SCHEMA)

    op.create_table(
        "stock_level", *_base_cols(),
        sa.Column("item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["item_id"], [f"{SCHEMA}.inventory_item.id"],
                                name="fk_stock_level_item_id_inventory_item"),
        sa.ForeignKeyConstraint(["warehouse_id"], [f"{SCHEMA}.warehouse.id"],
                                name="fk_stock_level_warehouse_id_warehouse"),
        sa.UniqueConstraint("tenant_id", "item_id", "warehouse_id",
                            name="uq_stock_level_tenant_id_item_id_warehouse_id"),
        schema=SCHEMA,
    )
    _ti("stock_level")
    op.create_index("ix_stock_level_item_id", "stock_level", ["item_id"], schema=SCHEMA)
    op.create_index("ix_stock_level_warehouse_id", "stock_level", ["warehouse_id"], schema=SCHEMA)

    op.create_table(
        "stock_movement", *_base_cols(), *_audit_cols(),
        sa.Column("item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", UUID(as_uuid=True), nullable=True),
        sa.Column("movement_type", sa.String(16), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reference", sa.String(128), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["item_id"], [f"{SCHEMA}.inventory_item.id"],
                                name="fk_stock_movement_item_id_inventory_item"),
        sa.ForeignKeyConstraint(["warehouse_id"], [f"{SCHEMA}.warehouse.id"],
                                name="fk_stock_movement_warehouse_id_warehouse"),
        sa.ForeignKeyConstraint(["location_id"], [f"{SCHEMA}.storage_location.id"],
                                name="fk_stock_movement_location_id_storage_location"),
        schema=SCHEMA,
    )
    _ti("stock_movement")
    op.create_index("ix_stock_movement_item_id", "stock_movement", ["item_id"], schema=SCHEMA)
    op.create_index("ix_stock_movement_warehouse_id", "stock_movement",
                    ["warehouse_id"], schema=SCHEMA)

    op.create_table(
        "supplier", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contact", sa.String(255), nullable=False, server_default=""),
        sa.UniqueConstraint("tenant_id", "code", name="uq_supplier_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("supplier")

    op.create_table(
        "purchase_order", *_base_cols(), *_audit_cols(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("supplier_id", UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="PHP"),
        sa.Column("status", sa.String(16), nullable=False, server_default="draft"),
        sa.Column("order_date", sa.Date, nullable=True),
        sa.ForeignKeyConstraint(["supplier_id"], [f"{SCHEMA}.supplier.id"],
                                name="fk_purchase_order_supplier_id_supplier"),
        sa.ForeignKeyConstraint(["warehouse_id"], [f"{SCHEMA}.warehouse.id"],
                                name="fk_purchase_order_warehouse_id_warehouse"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_purchase_order_tenant_id_code"),
        schema=SCHEMA,
    )
    _ti("purchase_order")
    op.create_index("ix_purchase_order_supplier_id", "purchase_order",
                    ["supplier_id"], schema=SCHEMA)

    op.create_table(
        "purchase_order_line", *_base_cols(),
        sa.Column("purchase_order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_price_minor", sa.BigInteger, nullable=False),
        sa.Column("line_total_minor", sa.BigInteger, nullable=False),
        sa.ForeignKeyConstraint(["purchase_order_id"], [f"{SCHEMA}.purchase_order.id"],
                                name="fk_purchase_order_line_purchase_order_id_purchase_order"),
        sa.ForeignKeyConstraint(["item_id"], [f"{SCHEMA}.inventory_item.id"],
                                name="fk_purchase_order_line_item_id_inventory_item"),
        schema=SCHEMA,
    )
    _ti("purchase_order_line")
    op.create_index("ix_purchase_order_line_purchase_order_id", "purchase_order_line",
                    ["purchase_order_id"], schema=SCHEMA)

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
        "purchase_order_line",
        "purchase_order",
        "supplier",
        "stock_movement",
        "stock_level",
        "storage_location",
        "warehouse",
        "inventory_item",
    ):
        op.drop_table(table, schema=SCHEMA)
