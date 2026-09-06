"""Pydantic schemas for Marketplace + Trading + Logistics (Phase 8)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Customers / listings ---
class CustomerCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    contact: str = Field(default="", max_length=255)


class CustomerResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    contact: str


class ListingCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    item_id: uuid.UUID
    quantity_available: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    currency: str = Field(default="PHP", min_length=3, max_length=3)


class ListingResponse(ORMModel):
    id: uuid.UUID
    code: str
    item_id: uuid.UUID
    quantity_available: Decimal
    unit_price_minor: int
    currency: str
    status: str


# --- Sales orders ---
class SalesOrderCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    customer_id: uuid.UUID
    warehouse_id: uuid.UUID
    currency: str = Field(default="PHP", min_length=3, max_length=3)


class SalesOrderLineCreate(BaseModel):
    item_id: uuid.UUID
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class SalesOrderLineResponse(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    quantity: Decimal
    unit_price_minor: int
    line_total_minor: int


class SalesOrderResponse(ORMModel):
    id: uuid.UUID
    code: str
    customer_id: uuid.UUID
    warehouse_id: uuid.UUID
    currency: str
    status: str


class OrderTransitionRequest(BaseModel):
    event: str = Field(min_length=1, max_length=32)


class MoneyResponse(BaseModel):
    amount_minor: int
    currency: str
    amount: Decimal


# --- Shipments ---
class ShipmentCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    sales_order_id: uuid.UUID
    carrier_note: str = Field(default="", max_length=255)


class ShipmentResponse(ORMModel):
    id: uuid.UUID
    code: str
    sales_order_id: uuid.UUID
    status: str
    carrier_note: str
