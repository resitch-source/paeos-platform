"""Pydantic schemas for IoT + Integrations (Phase 12)."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class InboundMessageCreate(BaseModel):
    system: str = Field(min_length=1, max_length=64)
    idempotency_key: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)


class InboundMessageResponse(ORMModel):
    id: uuid.UUID
    system: str
    idempotency_key: str
    payload: dict[str, Any]
    status: str
    attempt: int
    error: str
