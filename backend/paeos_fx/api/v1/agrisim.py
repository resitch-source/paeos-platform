"""AgriSim + Optimization + Digital Twins endpoints (Phase 11).

Run a registered simulation/optimization model under a named scenario (results
persisted with full provenance), list past runs and available engines, and record
an advisory digital-twin what-if projection. No actuation or control path.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.agrisim.engines import available_models
from paeos_fx.agrisim.service import ScenarioService
from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_agrisim import (
    EngineInfo,
    ScenarioRunRequest,
    ScenarioRunResponse,
    TwinProjectionRequest,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.platform import permissions as perms
from paeos_fx.pydantic_page import Paged

router = APIRouter(tags=["agrisim"])


@router.get(
    "/agrisim/engines", response_model=list[EngineInfo],
    dependencies=[Depends(require_permission(perms.AGRISIM_SCENARIO_READ))],
)
def list_engines() -> list[EngineInfo]:
    return [EngineInfo(**e) for e in available_models()]


@router.post(
    "/agrisim/scenarios/run", response_model=ScenarioRunResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.AGRISIM_SCENARIO_RUN))],
)
def run_scenario(
    body: ScenarioRunRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ScenarioRunResponse:
    run, _ = ScenarioService(db, ctx).run(
        model_name=body.model_name, scenario=body.scenario,
        parameters=body.parameters, subject_ref=body.subject_ref,
    )
    return ScenarioRunResponse.model_validate(run)


@router.post(
    "/agrisim/twins/project", response_model=ScenarioRunResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.AGRISIM_SCENARIO_RUN))],
)
def project_twin(
    body: TwinProjectionRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ScenarioRunResponse:
    run, _ = ScenarioService(db, ctx).project(
        model_name=body.model_name, subject_ref=body.subject_ref,
        parameters=body.parameters,
    )
    return ScenarioRunResponse.model_validate(run)


@router.get(
    "/agrisim/scenarios", response_model=Paged[ScenarioRunResponse],
    dependencies=[Depends(require_permission(perms.AGRISIM_SCENARIO_READ))],
)
def list_scenarios(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[ScenarioRunResponse]:
    res = ScenarioService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[ScenarioRunResponse](
        items=[ScenarioRunResponse.model_validate(x) for x in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )
