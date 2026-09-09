"""Pydantic schemas for Training + Support + Expert Marketplace (Phase 9)."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Training ---
class CourseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=4000)
    category: str = Field(default="", max_length=128)


class CourseResponse(ORMModel):
    id: uuid.UUID
    code: str
    title: str
    description: str
    category: str
    status: str


class EnrollmentCreate(BaseModel):
    course_id: uuid.UUID
    learner_id: uuid.UUID


class EnrollmentResponse(ORMModel):
    id: uuid.UUID
    course_id: uuid.UUID
    learner_id: uuid.UUID
    status: str
    completed_at: dt.datetime | None


# --- Technical support ---
class TicketCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(default="", max_length=8000)
    priority: str = Field(default="normal", max_length=16)


class TicketResponse(ORMModel):
    id: uuid.UUID
    code: str
    subject: str
    body: str
    priority: str
    status: str
    assignee_id: uuid.UUID | None
    resolved_at: dt.datetime | None


class TicketAssignRequest(BaseModel):
    assignee_id: uuid.UUID


class TicketCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=8000)


class TicketCommentResponse(ORMModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    author_id: uuid.UUID | None
    body: str


# --- Expert marketplace (financial: gate #12) ---
class ExpertProfileCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    expertise_area: str = Field(default="", max_length=128)
    bio: str = Field(default="", max_length=4000)
    rate: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="PHP", min_length=3, max_length=3)
    user_id: uuid.UUID | None = None


class ExpertProfileResponse(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    expertise_area: str
    bio: str
    rate_minor: int | None
    currency: str
    status: str


class EngagementCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    expert_id: uuid.UUID
    subject: str = Field(min_length=1, max_length=255)
    fee: Decimal = Field(ge=0)
    currency: str = Field(default="PHP", min_length=3, max_length=3)


class EngagementResponse(ORMModel):
    id: uuid.UUID
    code: str
    expert_id: uuid.UUID
    subject: str
    fee_minor: int
    currency: str
    status: str


class TransitionRequest(BaseModel):
    event: str = Field(min_length=1, max_length=32)


class MoneyResponse(BaseModel):
    amount_minor: int
    currency: str
    amount: Decimal
