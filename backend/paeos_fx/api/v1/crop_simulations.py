"""Crop simulation endpoints (Phase 3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.agri.production_services import CropSimulationService
from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas_production import (
    CalculationRecordOut,
    GddSimulationRequest,
    SimulationRunResponse,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.platform import permissions as perms

router = APIRouter(prefix="/agri/crop-simulations", tags=["crop-simulations"])


@router.post(
    "/gdd", response_model=SimulationRunResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.AGRI_SIMULATION_RUN))],
)
def run_gdd(
    body: GddSimulationRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> SimulationRunResponse:
    parameters = {
        "base_temp_c": body.base_temp_c,
        "daily_temperatures": [d.model_dump() for d in body.daily_temperatures],
    }
    run, result = CropSimulationService(db, ctx).run_gdd(
        scenario=body.scenario, parameters=parameters, cycle_id=body.cycle_id
    )
    return SimulationRunResponse(
        id=run.id,
        model_name=run.model_name,
        model_version=run.model_version,
        scenario=run.scenario,
        outputs=result.outputs,
        record=CalculationRecordOut(**run.record),
    )
