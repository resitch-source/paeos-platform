"""Pydantic schemas for Processing + MES + Twin (Phase 7)."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from paeos_fx.core.classification import Classification


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProcessDefinitionCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=500)


class ProcessDefinitionResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    description: str


class ProcessLineCreate(BaseModel):
    item_id: uuid.UUID
    quantity_per_batch: Decimal = Field(gt=0)


class ProcessLineResponse(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    quantity_per_batch: Decimal


class ProductionRunCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    definition_id: uuid.UUID
    warehouse_id: uuid.UUID
    batch_size: Decimal = Field(default=Decimal("1"), gt=0)


class ProductionRunResponse(ORMModel):
    id: uuid.UUID
    code: str
    definition_id: uuid.UUID
    warehouse_id: uuid.UUID
    batch_size: Decimal
    status: str


class QualityCheckCreate(BaseModel):
    metric_type: str = Field(min_length=1, max_length=32)
    value: Decimal
    uom: str = Field(min_length=1, max_length=16)
    classification: Classification = Classification.MEASURED


class RecordResponse(BaseModel):
    id: uuid.UUID


# --- Assets / twin ---
class AssetCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    asset_type: str = Field(default="processor", max_length=64)


class AssetResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    asset_type: str


class TelemetryCreate(BaseModel):
    metric: str = Field(min_length=1, max_length=32)
    value: Decimal
    uom: str = Field(min_length=1, max_length=16)
    read_at: dt.datetime | None = None


class TwinStateResponse(BaseModel):
    asset_id: str
    updated_at: dt.datetime
    metrics: dict[str, float]


# --- Simulation ---
class MassBalanceRequest(BaseModel):
    scenario: str = Field(min_length=1, max_length=128)
    input_mass: float = Field(ge=0)
    yield_fraction: float = Field(ge=0, le=1)
    mass_unit: str = Field(default="kg", max_length=16)


class CalculationRecordOut(BaseModel):
    inputs: dict[str, Any]
    units: dict[str, str]
    formula_or_model: str
    assumptions: list[str]
    reference: str
    result: Any
    model_version: str
    validation_status: str


class SimulationRunResponse(BaseModel):
    id: uuid.UUID
    model_name: str
    model_version: str
    scenario: str
    outputs: dict[str, Any]
    record: CalculationRecordOut
