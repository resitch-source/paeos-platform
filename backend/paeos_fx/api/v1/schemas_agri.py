"""Pydantic schemas for Agriculture Master Data + GIS (Phase 2)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from paeos_fx.core.classification import Classification


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Master data ---
class MasterDataCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)


class CropCreate(MasterDataCreate):
    category_id: uuid.UUID | None = None
    scientific_name: str | None = Field(default=None, max_length=255)


class CropVarietyCreate(MasterDataCreate):
    crop_id: uuid.UUID


class MasterDataResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    is_active: bool


class CropResponse(MasterDataResponse):
    category_id: uuid.UUID | None = None
    scientific_name: str | None = None


# --- Farms ---
class FarmCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    org_unit_id: uuid.UUID | None = None
    admin_area_id: uuid.UUID | None = None
    location_geojson: dict[str, Any] | None = None
    area_hectares: Decimal | None = None
    area_classification: Classification = Classification.UNKNOWN


class FarmResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    org_unit_id: uuid.UUID | None
    admin_area_id: uuid.UUID | None
    area_hectares: Decimal | None
    area_classification: str


# --- Parcels ---
class ParcelCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    farm_id: uuid.UUID
    soil_type_id: uuid.UUID | None = None
    land_use_type_id: uuid.UUID | None = None
    boundary_geojson: dict[str, Any] | None = None


class ParcelResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    farm_id: uuid.UUID
    soil_type_id: uuid.UUID | None
    land_use_type_id: uuid.UUID | None
    area_sqm: Decimal | None
    area_classification: str
