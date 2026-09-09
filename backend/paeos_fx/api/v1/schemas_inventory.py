"""Pydantic schemas for Inventory + Procurement (Phase 6)."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Items / warehouses ---
class ItemCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    base_uom: str = Field(default="ea", max_length=16)
    category: str | None = Field(default=None, max_length=64)


class ItemResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    base_uom: str
    category: str | None
    is_stocked: bool


class WarehouseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    org_unit_id: uuid.UUID | None = None
    address: str = Field(default="", max_length=500)


class WarehouseResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    org_unit_id: uuid.UUID | None
    address: str


# --- Stock ---
class MovementCreate(BaseModel):
    item_id: uuid.UUID
    warehouse_id: uuid.UUID
    movement_type: str = Field(pattern="^(IN|OUT|ADJUST)$")
    quantity: Decimal
    reference: str = Field(default="", max_length=128)


class TransferCreate(BaseModel):
    item_id: uuid.UUID
    from_warehouse_id: uuid.UUID
    to_warehouse_id: uuid.UUID
    quantity: Decimal = Field(gt=0)
    reference: str = Field(default="", max_length=128)


class StockResponse(BaseModel):
    item_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: Decimal


class MovementResponse(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    warehouse_id: uuid.UUID
    movement_type: str
    quantity: Decimal


# --- Procurement ---
class SupplierCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    contact: str = Field(default="", max_length=255)


class SupplierResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    contact: str


class POCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID
    currency: str = Field(default="PHP", min_length=3, max_length=3)


class POLineCreate(BaseModel):
    item_id: uuid.UUID
    quantity: Decimal = Field(gt=0)
    # Unit price as a decimal amount in the PO currency (e.g. "12.50").
    unit_price: Decimal = Field(ge=0)


class POLineResponse(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    quantity: Decimal
    unit_price_minor: int
    line_total_minor: int


class POResponse(ORMModel):
    id: uuid.UUID
    code: str
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID
    currency: str
    status: str
    order_date: dt.date | None


class POTransitionRequest(BaseModel):
    event: str = Field(min_length=1, max_length=32)


class MoneyResponse(BaseModel):
    amount_minor: int
    currency: str
    amount: Decimal
