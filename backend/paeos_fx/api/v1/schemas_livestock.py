"""Pydantic schemas for Livestock + Poultry (Phase 4)."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from paeos_fx.core.classification import Classification


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Master data ---
class MasterDataCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)


class BreedCreate(MasterDataCreate):
    species_id: uuid.UUID


class MasterDataResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    is_active: bool


# --- Animal groups ---
class AnimalGroupCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    species_id: uuid.UUID
    breed_id: uuid.UUID | None = None
    farm_id: uuid.UUID | None = None
    org_unit_id: uuid.UUID | None = None
    purpose: str | None = Field(default=None, max_length=32)
    head_count: int = Field(default=0, ge=0)
    established_date: dt.date | None = None


class AnimalGroupResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    species_id: uuid.UUID
    breed_id: uuid.UUID | None
    farm_id: uuid.UUID | None
    org_unit_id: uuid.UUID | None
    purpose: str | None
    head_count: int
    status: str


class TransitionRequest(BaseModel):
    event: str = Field(min_length=1, max_length=32)


# --- Records ---
class ProductionRecordCreate(BaseModel):
    recorded_at: dt.date
    metric_type: str = Field(min_length=1, max_length=32)
    quantity: Decimal
    uom: str = Field(min_length=1, max_length=16)
    classification: Classification = Classification.MEASURED


class MortalityRecordCreate(BaseModel):
    event_date: dt.date
    count: int = Field(gt=0)
    cause_note: str = Field(default="", max_length=500)


class HealthEventCreate(BaseModel):
    event_date: dt.date
    event_type: str = Field(min_length=1, max_length=64)
    description: str = Field(default="", max_length=500)


class RecordResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
