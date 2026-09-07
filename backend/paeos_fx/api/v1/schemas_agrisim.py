"""Pydantic schemas for AgriSim + Optimization + Digital Twins (Phase 11)."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ScenarioRunRequest(BaseModel):
    model_name: str = Field(min_length=1, max_length=64)
    scenario: str = Field(min_length=1, max_length=128)
    parameters: dict[str, Any] = Field(default_factory=dict)
    subject_ref: str = Field(default="", max_length=128)


class TwinProjectionRequest(BaseModel):
    model_name: str = Field(min_length=1, max_length=64)
    subject_ref: str = Field(min_length=1, max_length=128)
    parameters: dict[str, Any] = Field(default_factory=dict)


class ScenarioRunResponse(ORMModel):
    id: uuid.UUID
    model_name: str
    model_version: str
    scenario: str
    subject_ref: str
    ran_at: dt.datetime
    record: dict[str, Any]


class EngineInfo(BaseModel):
    name: str
    version: str
