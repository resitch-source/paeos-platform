"""AgriIntelligence / AI Agents endpoints (Phase 10).

Advisory only: running an agent returns persisted recommendations; deciding on
one records a human accept/reject. Nothing is auto-applied and the AI touches no
domain data except through the guarded read-only tool registry.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.ai.service import AgentService
from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_agents import (
    AgentRunRequest,
    DecisionRequest,
    RecommendationResponse,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.platform import permissions as perms
from paeos_fx.pydantic_page import Paged

router = APIRouter(tags=["agri-intelligence"])


@router.post(
    "/ai/agents/{agent_name}/run", response_model=list[RecommendationResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.AI_AGENT_RUN))],
)
def run_agent(
    agent_name: str, body: AgentRunRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> list[RecommendationResponse]:
    recs = AgentService(db, ctx).run(agent_name, body.params)
    return [RecommendationResponse.model_validate(r) for r in recs]


@router.get(
    "/ai/recommendations", response_model=Paged[RecommendationResponse],
    dependencies=[Depends(require_permission(perms.AI_RECOMMENDATION_READ))],
)
def list_recommendations(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[RecommendationResponse]:
    res = AgentService(db, ctx).list_recommendations(PageParams(page=page, size=size))
    return Paged[RecommendationResponse](
        items=[RecommendationResponse.model_validate(x) for x in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


@router.post(
    "/ai/recommendations/{recommendation_id}/decide",
    response_model=RecommendationResponse,
    dependencies=[Depends(require_permission(perms.AI_RECOMMENDATION_DECIDE))],
)
def decide_recommendation(
    recommendation_id: uuid.UUID, body: DecisionRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> RecommendationResponse:
    rec = AgentService(db, ctx).decide(recommendation_id, body.event)
    return RecommendationResponse.model_validate(rec)
