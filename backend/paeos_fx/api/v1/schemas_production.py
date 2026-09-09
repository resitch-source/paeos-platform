"""Pydantic schemas for Crop Production + Simulation (Phase 3)."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from paeos_fx.core.classification import Classification


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Cropping cycles ---
class CroppingCycleCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    parcel_id: uuid.UUID
    crop_id: uuid.UUID
    variety_id: uuid.UUID | None = None
    season: str | None = Field(default=None, max_length=64)
    planting_date: dt.date | None = None
    expected_harvest_date: dt.date | None = None
    planted_area_ha: Decimal | None = None
    area_classification: Classification = Classification.UNKNOWN


class CroppingCycleResponse(ORMModel):
    id: uuid.UUID
    code: str
    parcel_id: uuid.UUID
    crop_id: uuid.UUID
    variety_id: uuid.UUID | None
    season: str | None
    status: str
    planting_date: dt.date | None
    expected_harvest_date: dt.date | None
    planted_area_ha: Decimal | None
    area_classification: str


class TransitionRequest(BaseModel):
    event: str = Field(min_length=1, max_length=32)


# --- Harvests ---
class HarvestCreate(BaseModel):
    cycle_id: uuid.UUID
    harvest_date: dt.date
    quantity: Decimal = Field(gt=0)
    uom: str = Field(min_length=1, max_length=16)
    classification: Classification = Classification.MEASURED


class HarvestResponse(ORMModel):
    id: uuid.UUID
    cycle_id: uuid.UUID
    harvest_date: dt.date
    quantity: Decimal
    uom: str
    quantity_classification: str


# --- Simulation ---
class DailyTemperatureIn(BaseModel):
    tmax_c: float
    tmin_c: float


class GddSimulationRequest(BaseModel):
    scenario: str = Field(min_length=1, max_length=128)
    base_temp_c: float
    daily_temperatures: list[DailyTemperatureIn] = Field(min_length=1)
    cycle_id: uuid.UUID | None = None


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
