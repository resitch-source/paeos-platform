"""Processing / MES + twin endpoints (Phase 7).

Note: there is deliberately NO machinery-control endpoint. The digital twin is
advisory (telemetry + state + simulation) only.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas_processing import (
    AssetCreate,
    AssetResponse,
    CalculationRecordOut,
    MassBalanceRequest,
    ProcessDefinitionCreate,
    ProcessDefinitionResponse,
    ProcessLineCreate,
    ProcessLineResponse,
    ProductionRunCreate,
    ProductionRunResponse,
    QualityCheckCreate,
    RecordResponse,
    SimulationRunResponse,
    TelemetryCreate,
    TwinStateResponse,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.platform import permissions as perms
from paeos_fx.processing.service import (
    ProcessDefinitionService,
    ProcessingAssetService,
    ProcessSimulationService,
    ProductionRunService,
)

router = APIRouter(prefix="/processing", tags=["processing"])


# --- Recipes ---
@router.post(
    "/definitions", response_model=ProcessDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.PROCESSING_DEFINITION_MANAGE))],
)
def create_definition(
    body: ProcessDefinitionCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ProcessDefinitionResponse:
    d = ProcessDefinitionService(db, ctx).create(
        code=body.code, name=body.name, description=body.description
    )
    return ProcessDefinitionResponse.model_validate(d)


@router.post(
    "/definitions/{definition_id}/inputs", response_model=ProcessLineResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.PROCESSING_DEFINITION_MANAGE))],
)
def add_input(
    definition_id: uuid.UUID, body: ProcessLineCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ProcessLineResponse:
    row = ProcessDefinitionService(db, ctx).add_input(
        definition_id=definition_id, item_id=body.item_id,
        quantity_per_batch=body.quantity_per_batch,
    )
    return ProcessLineResponse(id=row.id, item_id=row.item_id,
                               quantity_per_batch=row.quantity_per_batch)


@router.post(
    "/definitions/{definition_id}/outputs", response_model=ProcessLineResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.PROCESSING_DEFINITION_MANAGE))],
)
def add_output(
    definition_id: uuid.UUID, body: ProcessLineCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ProcessLineResponse:
    row = ProcessDefinitionService(db, ctx).add_output(
        definition_id=definition_id, item_id=body.item_id,
        quantity_per_batch=body.quantity_per_batch,
    )
    return ProcessLineResponse(id=row.id, item_id=row.item_id,
                               quantity_per_batch=row.quantity_per_batch)


# --- Production runs ---
@router.post(
    "/runs", response_model=ProductionRunResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.PROCESSING_RUN_WRITE))],
)
def create_run(
    body: ProductionRunCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ProductionRunResponse:
    run = ProductionRunService(db, ctx).create(
        code=body.code, definition_id=body.definition_id,
        warehouse_id=body.warehouse_id, batch_size=body.batch_size,
    )
    return ProductionRunResponse.model_validate(run)


@router.post(
    "/runs/{run_id}/start", response_model=ProductionRunResponse,
    dependencies=[Depends(require_permission(perms.PROCESSING_RUN_WRITE))],
)
def start_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ProductionRunResponse:
    return ProductionRunResponse.model_validate(ProductionRunService(db, ctx).start(run_id))


@router.post(
    "/runs/{run_id}/complete", response_model=ProductionRunResponse,
    dependencies=[Depends(require_permission(perms.PROCESSING_RUN_WRITE))],
)
def complete_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ProductionRunResponse:
    return ProductionRunResponse.model_validate(ProductionRunService(db, ctx).complete(run_id))


@router.post(
    "/runs/{run_id}/quality", response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.PROCESSING_QUALITY_WRITE))],
)
def record_quality(
    run_id: uuid.UUID, body: QualityCheckCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> RecordResponse:
    qc = ProductionRunService(db, ctx).record_quality(
        run_id=run_id, metric_type=body.metric_type, value=body.value,
        uom=body.uom, classification=body.classification,
    )
    return RecordResponse(id=qc.id)


# --- Assets / twin (advisory) ---
@router.post(
    "/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.PROCESSING_ASSET_MANAGE))],
)
def create_asset(
    body: AssetCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> AssetResponse:
    asset = ProcessingAssetService(db, ctx).create(
        code=body.code, name=body.name, asset_type=body.asset_type
    )
    return AssetResponse.model_validate(asset)


@router.post(
    "/assets/{asset_id}/telemetry", response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.PROCESSING_TELEMETRY_WRITE))],
)
def ingest_telemetry(
    asset_id: uuid.UUID, body: TelemetryCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> RecordResponse:
    row = ProcessingAssetService(db, ctx).ingest_telemetry(
        asset_id=asset_id, metric=body.metric, value=body.value, uom=body.uom,
        read_at=body.read_at,
    )
    return RecordResponse(id=row.id)


@router.get(
    "/assets/{asset_id}/twin", response_model=TwinStateResponse,
    dependencies=[Depends(require_permission(perms.PROCESSING_ASSET_READ))],
)
def twin_state(
    asset_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> TwinStateResponse:
    state = ProcessingAssetService(db, ctx).twin_state(asset_id)
    return TwinStateResponse(asset_id=state.asset_id, updated_at=state.updated_at,
                             metrics=state.metrics)


# --- Advisory simulation ---
@router.post(
    "/simulations/mass-balance", response_model=SimulationRunResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.PROCESSING_SIMULATION_RUN))],
)
def run_mass_balance(
    body: MassBalanceRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> SimulationRunResponse:
    run, result = ProcessSimulationService(db, ctx).run_mass_balance(
        scenario=body.scenario,
        parameters={
            "input_mass": body.input_mass,
            "yield_fraction": body.yield_fraction,
            "mass_unit": body.mass_unit,
        },
    )
    return SimulationRunResponse(
        id=run.id, model_name=run.model_name, model_version=run.model_version,
        scenario=run.scenario, outputs=result.outputs,
        record=CalculationRecordOut(**run.record),
    )
