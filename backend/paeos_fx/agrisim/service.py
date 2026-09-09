"""AgriSim service (Phase 11).

Runs a registered simulation/optimization engine under a named scenario and
persists the full provenance envelope. ``project`` records an ADVISORY digital-
twin what-if forward run tagged by ``subject_ref`` — it performs no actuation and
opens no control path (gates #13/#14).
"""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import asdict
from typing import Any

from paeos_fx.agrisim.engines import get_engine
from paeos_fx.agrisim.models import ScenarioRun
from paeos_fx.core.context import ExecutionContext
from paeos_fx.interfaces.simulation import SimulationRequest, SimulationResult
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService


class ScenarioService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[ScenarioRun] = TenantRepository(
            session, ScenarioRun, self.tenant_id
        )

    def run(self, *, model_name: str, scenario: str,
            parameters: dict[str, Any] | None = None,
            subject_ref: str = "") -> tuple[ScenarioRun, SimulationResult]:
        engine = get_engine(model_name)
        result = engine.run(SimulationRequest(scenario=scenario,
                                              parameters=parameters or {}))
        run = ScenarioRun(
            model_name=engine.name, model_version=engine.version, scenario=scenario,
            subject_ref=subject_ref, ran_at=dt.datetime.now(dt.UTC),
            record=self._serialize_record(result),
        )
        self.repo.add(run)
        self._record(action="scenario.run", entity_type="ScenarioRun",
                     entity_id=str(run.id),
                     after={"model": engine.name, "scenario": scenario})
        return run, result

    def project(self, *, model_name: str, subject_ref: str,
                parameters: dict[str, Any] | None = None) -> tuple[ScenarioRun,
                                                                   SimulationResult]:
        """Advisory digital-twin what-if projection. Records only; no actuation."""
        return self.run(model_name=model_name, scenario=f"twin:{subject_ref}",
                        parameters=parameters, subject_ref=subject_ref)

    def get(self, run_id: uuid.UUID) -> ScenarioRun:
        return self.repo.get_or_404(run_id)

    def list(self, params=None):
        return self.repo.list(params)

    @staticmethod
    def _serialize_record(result: SimulationResult) -> dict:
        record = asdict(result.record)
        record["validation_status"] = result.record.validation_status.value
        return record
