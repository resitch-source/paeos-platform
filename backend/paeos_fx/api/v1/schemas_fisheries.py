"""Pydantic schemas for Fisheries + Aquaculture (Phase 5)."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from paeos_fx.core.classification import Classification


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MasterDataCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)


class MasterDataResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    is_active: bool


# --- Culture units ---
class CultureUnitCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    unit_type: str = Field(default="pond", max_length=32)
    farm_id: uuid.UUID | None = None
    location_geojson: dict[str, Any] | None = None
    water_area_sqm: Decimal | None = None
    area_classification: Classification = Classification.UNKNOWN


class CultureUnitResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    unit_type: str
    farm_id: uuid.UUID | None
    water_area_sqm: Decimal | None
    area_classification: str


# --- Cycles ---
class AquaCycleCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    culture_unit_id: uuid.UUID
    species_id: uuid.UUID
    stocking_count: int = Field(default=0, ge=0)
    stocking_date: dt.date | None = None
    expected_harvest_date: dt.date | None = None


class AquaCycleResponse(ORMModel):
    id: uuid.UUID
    code: str
    culture_unit_id: uuid.UUID
    species_id: uuid.UUID
    stocking_count: int
    status: str


class TransitionRequest(BaseModel):
    event: str = Field(min_length=1, max_length=32)


# --- Records ---
class WaterQualityCreate(BaseModel):
    culture_unit_id: uuid.UUID
    read_at: dt.date
    metric_type: str = Field(min_length=1, max_length=32)
    value: Decimal
    uom: str = Field(min_length=1, max_length=16)
    classification: Classification = Classification.MEASURED


class HarvestCreate(BaseModel):
    harvest_date: dt.date
    quantity: Decimal = Field(gt=0)
    uom: str = Field(min_length=1, max_length=16)
    classification: Classification = Classification.MEASURED


class MortalityCreate(BaseModel):
    event_date: dt.date
    count: int = Field(gt=0)
    cause_note: str = Field(default="", max_length=500)


class RecordResponse(BaseModel):
    id: uuid.UUID
