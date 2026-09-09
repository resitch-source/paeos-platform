"""AgriIntelligence agent service (Phase 10).

Orchestrates advisory agents strictly through the Foundation AI-safety chain:
data is fetched only via permission-checked read tools in the ToolRegistry, the
agent produces advisory recommendations, and both the run and its recommendations
are persisted and audited. Accepting a recommendation records a HUMAN DECISION —
it executes nothing and mutates no domain data.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from paeos_fx.ai.agents import low_stock_advisory, open_order_advisory
from paeos_fx.ai.models import RECOMMENDATION_WORKFLOW, AgentRun, AiRecommendation
from paeos_fx.ai.tools import build_registry
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.interfaces.ai import AIRecommendation
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService


class _AgentSpec:
    """Binds an agent name to the read tool it needs and its analyzer."""

    def __init__(self, tool_name: str, runner: Callable[..., list[AIRecommendation]]):
        self.tool_name = tool_name
        self.runner = runner


def _run_low_stock(tool_result, params: dict[str, Any]) -> list[AIRecommendation]:
    threshold = Decimal(str(params.get("threshold", "0")))
    return low_stock_advisory(tool_result, threshold=threshold)


def _run_open_orders(tool_result, params: dict[str, Any]) -> list[AIRecommendation]:
    return open_order_advisory(tool_result)


AGENTS: dict[str, _AgentSpec] = {
    "low_stock": _AgentSpec("inventory.stock_levels", _run_low_stock),
    "open_orders": _AgentSpec("trading.open_orders", _run_open_orders),
}


class AgentService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[AiRecommendation] = TenantRepository(
            session, AiRecommendation, self.tenant_id
        )
        self.runs: TenantRepository[AgentRun] = TenantRepository(
            session, AgentRun, self.tenant_id
        )

    def run(self, agent_name: str, params: dict[str, Any] | None = None
            ) -> list[AiRecommendation]:
        params = params or {}
        spec = AGENTS.get(agent_name)
        if spec is None:
            raise BusinessRuleError("Unknown agent.", details={"agent": agent_name})

        run = AgentRun(agent_name=agent_name, params=params, status="completed")
        self.runs.add(run)
        self._record(action="agent.run", entity_type="AgentRun",
                     entity_id=str(run.id), after={"agent": agent_name})

        # Data is fetched ONLY through the guarded, permission-checked registry.
        registry = build_registry(self.session, self.ctx)
        tool_result = registry.invoke(spec.tool_name, self.ctx)
        recommendations = spec.runner(tool_result, params)

        persisted: list[AiRecommendation] = []
        for rec in recommendations:
            row = AiRecommendation(
                tenant_id=self.tenant_id, agent_run_id=run.id, summary=rec.summary,
                classification=rec.classification.value, confidence=float(rec.confidence),
                assumptions=list(rec.assumptions), uncertainty_note="",
                requires_human_approval=rec.requires_human_approval,
                status=RECOMMENDATION_WORKFLOW.initial,
            )
            self.session.add(row)
            persisted.append(row)
        self.session.flush()
        for row in persisted:
            self._record(action="ai_recommendation.propose",
                         entity_type="AiRecommendation", entity_id=str(row.id),
                         after={"agent_run_id": str(run.id)})
        return persisted

    def decide(self, recommendation_id: uuid.UUID, event: str) -> AiRecommendation:
        """Record a human accept/reject decision. Executes nothing downstream."""
        rec = self.repo.get_or_404(recommendation_id)
        before = rec.status
        rec.status = RECOMMENDATION_WORKFLOW.fire(rec.status, event)
        rec.decided_by = self.ctx.user_id
        self.session.flush()
        self._record(action=f"ai_recommendation.{event}",
                     entity_type="AiRecommendation", entity_id=str(recommendation_id),
                     before={"status": before}, after={"status": rec.status})
        return rec

    def list_recommendations(self, params=None):
        return self.repo.list(params)

    def run_recommendations(self, run_id: uuid.UUID) -> list[AiRecommendation]:
        return list(self.session.execute(
            select(AiRecommendation).where(
                AiRecommendation.tenant_id == self.tenant_id,
                AiRecommendation.agent_run_id == run_id,
            ).order_by(AiRecommendation.created_at)
        ).scalars().all())
