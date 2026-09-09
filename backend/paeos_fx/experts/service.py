"""Expert-marketplace services (Phase 9) — financial (gate #12).

Expert directory CRUD and engagement lifecycle with an agreed fee. Fees are exact
``Money`` amounts (integer minor units), caller-supplied. No payment/AR/GL/tax
logic; no fabricated ratings.
"""

from __future__ import annotations

import uuid

from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.experts.models import ENGAGEMENT_WORKFLOW, Engagement, ExpertProfile
from paeos_fx.platform.currency import Money
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService


class ExpertProfileService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[ExpertProfile] = TenantRepository(
            session, ExpertProfile, self.tenant_id
        )

    def create(self, *, code: str, name: str, expertise_area: str = "",
               bio: str = "", rate: Money | None = None,
               user_id: uuid.UUID | None = None) -> ExpertProfile:
        profile = ExpertProfile(
            code=code, name=name, expertise_area=expertise_area, bio=bio,
            rate_minor=rate.amount_minor if rate else None,
            currency=rate.currency if rate else "PHP",
            user_id=user_id, status="active",
        )
        self.repo.add(profile)
        self._record(action="expert_profile.create", entity_type="ExpertProfile",
                     entity_id=str(profile.id), after={"code": code})
        return profile

    def get(self, profile_id: uuid.UUID) -> ExpertProfile:
        return self.repo.get_or_404(profile_id)

    def list(self, params=None):
        return self.repo.list(params)


class EngagementService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[Engagement] = TenantRepository(
            session, Engagement, self.tenant_id
        )
        self.experts: TenantRepository[ExpertProfile] = TenantRepository(
            session, ExpertProfile, self.tenant_id
        )

    def create(self, *, code: str, expert_id: uuid.UUID, subject: str,
               fee: Money) -> Engagement:
        self.experts.get_or_404(expert_id)
        if fee.amount_minor < 0:
            raise BusinessRuleError("Engagement fee cannot be negative.")
        engagement = Engagement(
            code=code, expert_id=expert_id, subject=subject,
            fee_minor=fee.amount_minor, currency=fee.currency,
            status=ENGAGEMENT_WORKFLOW.initial,
        )
        self.repo.add(engagement)
        self._record(action="engagement.create", entity_type="Engagement",
                     entity_id=str(engagement.id), after={"code": code})
        return engagement

    def fee(self, engagement_id: uuid.UUID) -> Money:
        engagement = self.repo.get_or_404(engagement_id)
        return Money(engagement.fee_minor, engagement.currency)

    def transition(self, engagement_id: uuid.UUID, event: str) -> Engagement:
        engagement = self.repo.get_or_404(engagement_id)
        before = engagement.status
        engagement.status = ENGAGEMENT_WORKFLOW.fire(engagement.status, event)
        self.session.flush()
        self._record(action=f"engagement.{event}", entity_type="Engagement",
                     entity_id=str(engagement_id),
                     before={"status": before}, after={"status": engagement.status})
        return engagement

    def list(self, params=None):
        return self.repo.list(params)
