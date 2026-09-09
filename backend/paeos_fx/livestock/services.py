"""Livestock services (Phase 4)."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from paeos_fx.core.classification import Classification
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.core.pagination import Page, PageParams
from paeos_fx.livestock.models import (
    ANIMAL_GROUP_WORKFLOW,
    AnimalGroup,
    AnimalHealthEvent,
    AnimalMortalityRecord,
    AnimalProductionRecord,
)
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService


class AnimalGroupService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[AnimalGroup] = TenantRepository(
            session, AnimalGroup, self.tenant_id
        )

    def create(
        self,
        *,
        code: str,
        name: str,
        species_id: uuid.UUID,
        breed_id: uuid.UUID | None = None,
        farm_id: uuid.UUID | None = None,
        org_unit_id: uuid.UUID | None = None,
        purpose: str | None = None,
        head_count: int = 0,
        established_date: dt.date | None = None,
    ) -> AnimalGroup:
        if head_count < 0:
            raise BusinessRuleError("head_count cannot be negative.")
        group = AnimalGroup(
            code=code, name=name, species_id=species_id, breed_id=breed_id,
            farm_id=farm_id, org_unit_id=org_unit_id, purpose=purpose,
            head_count=head_count, established_date=established_date,
            status=ANIMAL_GROUP_WORKFLOW.initial,
        )
        self.repo.add(group)
        self._record(action="animal_group.create", entity_type="AnimalGroup",
                     entity_id=str(group.id), after={"code": code})
        self._emit("animal_group.created", {"id": str(group.id)})
        return group

    def transition(self, group_id: uuid.UUID, event: str) -> AnimalGroup:
        group = self.repo.get_or_404(group_id)
        before = group.status
        group.status = ANIMAL_GROUP_WORKFLOW.fire(group.status, event)
        self.session.flush()
        self._record(action=f"animal_group.{event}", entity_type="AnimalGroup",
                     entity_id=str(group_id),
                     before={"status": before}, after={"status": group.status})
        return group

    def record_production(
        self, *, group_id: uuid.UUID, recorded_at: dt.date, metric_type: str,
        quantity: Decimal, uom: str,
        classification: Classification = Classification.MEASURED,
    ) -> AnimalProductionRecord:
        self.repo.get_or_404(group_id)
        rec = AnimalProductionRecord(
            tenant_id=self.tenant_id, group_id=group_id, recorded_at=recorded_at,
            metric_type=metric_type, quantity=quantity, uom=uom,
            classification=classification.value,
        )
        self.session.add(rec)
        self.session.flush()
        self._record(action="animal_production.record", entity_type="AnimalProductionRecord",
                     entity_id=str(rec.id), after={"group_id": str(group_id)})
        return rec

    def record_mortality(
        self, *, group_id: uuid.UUID, event_date: dt.date, count: int,
        cause_note: str = "",
    ) -> AnimalMortalityRecord:
        group = self.repo.get_or_404(group_id)
        if count <= 0:
            raise BusinessRuleError("Mortality count must be positive.")
        if count > group.head_count:
            raise BusinessRuleError("Mortality count exceeds current head count.")
        group.head_count -= count
        rec = AnimalMortalityRecord(
            tenant_id=self.tenant_id, group_id=group_id, event_date=event_date,
            count=count, cause_note=cause_note,
        )
        self.session.add(rec)
        self.session.flush()
        self._record(action="animal_mortality.record", entity_type="AnimalMortalityRecord",
                     entity_id=str(rec.id),
                     after={"group_id": str(group_id), "count": count})
        return rec

    def record_health_event(
        self, *, group_id: uuid.UUID, event_date: dt.date, event_type: str,
        description: str = "",
    ) -> AnimalHealthEvent:
        self.repo.get_or_404(group_id)
        rec = AnimalHealthEvent(
            tenant_id=self.tenant_id, group_id=group_id, event_date=event_date,
            event_type=event_type, description=description,
        )
        self.session.add(rec)
        self.session.flush()
        self._record(action="animal_health.record", entity_type="AnimalHealthEvent",
                     entity_id=str(rec.id), after={"group_id": str(group_id)})
        return rec

    def list(self, params: PageParams | None = None) -> Page[AnimalGroup]:
        return self.repo.list(params)
