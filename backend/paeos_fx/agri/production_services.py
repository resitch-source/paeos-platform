"""Crop production services (Phase 3).

Cropping-cycle lifecycle (Foundation workflow engine), harvest recording, and
crop-simulation execution with persisted, provenance-carrying runs.
"""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import asdict
from decimal import Decimal
from typing import Any

from paeos_fx.agri.production import (
    CROPPING_CYCLE_WORKFLOW,
    CroppingCycle,
    HarvestRecord,
    SimulationRun,
)
from paeos_fx.agri.simulation import GrowingDegreeDaysModel
from paeos_fx.core.classification import Classification
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import Page, PageParams
from paeos_fx.interfaces.simulation import SimulationRequest, SimulationResult
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService


class CroppingCycleService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[CroppingCycle] = TenantRepository(
            session, CroppingCycle, self.tenant_id
        )

    def create(
        self,
        *,
        code: str,
        parcel_id: uuid.UUID,
        crop_id: uuid.UUID,
        variety_id: uuid.UUID | None = None,
        season: str | None = None,
        planting_date: dt.date | None = None,
        expected_harvest_date: dt.date | None = None,
        planted_area_ha: Decimal | None = None,
        area_classification: Classification = Classification.UNKNOWN,
    ) -> CroppingCycle:
        cycle = CroppingCycle(
            code=code,
            parcel_id=parcel_id,
            crop_id=crop_id,
            variety_id=variety_id,
            season=season,
            planting_date=planting_date,
            expected_harvest_date=expected_harvest_date,
            planted_area_ha=planted_area_ha,
            area_classification=area_classification.value,
            status=CROPPING_CYCLE_WORKFLOW.initial,
        )
        self.repo.add(cycle)
        self._record(action="cropping_cycle.create", entity_type="CroppingCycle",
                     entity_id=str(cycle.id), after={"code": code})
        self._emit("cropping_cycle.created", {"id": str(cycle.id)})
        return cycle

    def transition(self, cycle_id: uuid.UUID, event: str) -> CroppingCycle:
        cycle = self.repo.get_or_404(cycle_id)
        new_state = CROPPING_CYCLE_WORKFLOW.fire(cycle.status, event)
        before = cycle.status
        cycle.status = new_state
        self.session.flush()
        self._record(action=f"cropping_cycle.{event}", entity_type="CroppingCycle",
                     entity_id=str(cycle_id),
                     before={"status": before}, after={"status": new_state})
        return cycle

    def list(self, params: PageParams | None = None) -> Page[CroppingCycle]:
        return self.repo.list(params)


class HarvestService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[HarvestRecord] = TenantRepository(
            session, HarvestRecord, self.tenant_id
        )
        self.cycles: TenantRepository[CroppingCycle] = TenantRepository(
            session, CroppingCycle, self.tenant_id
        )

    def record_harvest(
        self,
        *,
        cycle_id: uuid.UUID,
        harvest_date: dt.date,
        quantity: Decimal,
        uom: str,
        classification: Classification = Classification.MEASURED,
    ) -> HarvestRecord:
        self.cycles.get_or_404(cycle_id)  # ensure the cycle exists in this tenant
        rec = HarvestRecord(
            cycle_id=cycle_id,
            harvest_date=harvest_date,
            quantity=quantity,
            uom=uom,
            quantity_classification=classification.value,
        )
        self.repo.add(rec)
        self._record(action="harvest.record", entity_type="HarvestRecord",
                     entity_id=str(rec.id), after={"cycle_id": str(cycle_id)})
        return rec

    def list(self, params: PageParams | None = None) -> Page[HarvestRecord]:
        return self.repo.list(params)


class CropSimulationService(DomainService):
    """Runs a simulation model and persists the run with full provenance."""

    _MODELS = {GrowingDegreeDaysModel.name: GrowingDegreeDaysModel}

    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[SimulationRun] = TenantRepository(
            session, SimulationRun, self.tenant_id
        )

    def run_gdd(
        self,
        *,
        scenario: str,
        parameters: dict[str, Any],
        cycle_id: uuid.UUID | None = None,
    ) -> tuple[SimulationRun, SimulationResult]:
        model = GrowingDegreeDaysModel()
        result = model.run(SimulationRequest(scenario=scenario, parameters=parameters))
        run = SimulationRun(
            cycle_id=cycle_id,
            model_name=model.name,
            model_version=model.version,
            scenario=scenario,
            ran_at=dt.datetime.now(dt.UTC),
            record=self._serialize_record(result),
        )
        self.repo.add(run)
        self._record(action="simulation.run", entity_type="SimulationRun",
                     entity_id=str(run.id), after={"model": model.name})
        return run, result

    @staticmethod
    def _serialize_record(result: SimulationResult) -> dict:
        record = asdict(result.record)
        # Enum -> its string value for JSON storage.
        record["validation_status"] = result.record.validation_status.value
        return record
