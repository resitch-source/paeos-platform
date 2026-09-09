"""Pydantic schemas for AgriIntelligence / AI Agents (Phase 10)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AgentRunRequest(BaseModel):
    # Free-form agent parameters (e.g. {"threshold": "10"}); caller-supplied.
    params: dict[str, Any] = Field(default_factory=dict)


class RecommendationResponse(ORMModel):
    id: uuid.UUID
    agent_run_id: uuid.UUID
    summary: str
    classification: str
    confidence: Decimal
    assumptions: list[Any]
    uncertainty_note: str
    requires_human_approval: bool
    status: str


class DecisionRequest(BaseModel):
    event: str = Field(min_length=1, max_length=32)  # accept | reject | supersede
