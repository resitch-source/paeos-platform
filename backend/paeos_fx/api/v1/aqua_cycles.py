"""Aquaculture cycle + water-quality endpoints (Phase 5)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_fisheries import (
    AquaCycleCreate,
    AquaCycleResponse,
    HarvestCreate,
    MortalityCreate,
    RecordResponse,
    TransitionRequest,
    WaterQualityCreate,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.fisheries.services import AquacultureCycleService, WaterQualityService
from paeos_fx.platform import permissions as perms
from paeos_fx.pydantic_page import Paged

router = APIRouter(prefix="/fisheries", tags=["aquaculture-cycles"])

_READ = require_permission(perms.FISHERIES_CYCLE_READ)
_WRITE = require_permission(perms.FISHERIES_CYCLE_WRITE)
_RECORD = require_permission(perms.FISHERIES_RECORD_WRITE)


@router.post(
    "/cycles", response_model=AquaCycleResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_WRITE)],
)
def create_cycle(
    body: AquaCycleCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> AquaCycleResponse:
    cycle = AquacultureCycleService(db, ctx).create(
        code=body.code, culture_unit_id=body.culture_unit_id, species_id=body.species_id,
        stocking_count=body.stocking_count, stocking_date=body.stocking_date,
        expected_harvest_date=body.expected_harvest_date,
    )
    return AquaCycleResponse.model_validate(cycle)


@router.get(
    "/cycles", response_model=Paged[AquaCycleResponse], dependencies=[Depends(_READ)],
)
def list_cycles(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[AquaCycleResponse]:
    res = AquacultureCycleService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[AquaCycleResponse](
        items=[AquaCycleResponse.model_validate(c) for c in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


@router.post(
    "/cycles/{cycle_id}/transition", response_model=AquaCycleResponse,
    dependencies=[Depends(_WRITE)],
)
def transition_cycle(
    cycle_id: uuid.UUID,
    body: TransitionRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> AquaCycleResponse:
    cycle = AquacultureCycleService(db, ctx).transition(cycle_id, body.event)
    return AquaCycleResponse.model_validate(cycle)


@router.post(
    "/cycles/{cycle_id}/harvest", response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_RECORD)],
)
def record_harvest(
    cycle_id: uuid.UUID,
    body: HarvestCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> RecordResponse:
    rec = AquacultureCycleService(db, ctx).record_harvest(
        cycle_id=cycle_id, harvest_date=body.harvest_date, quantity=body.quantity,
        uom=body.uom, classification=body.classification,
    )
    return RecordResponse(id=rec.id)


@router.post(
    "/cycles/{cycle_id}/mortality", response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_RECORD)],
)
def record_mortality(
    cycle_id: uuid.UUID,
    body: MortalityCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> RecordResponse:
    rec = AquacultureCycleService(db, ctx).record_mortality(
        cycle_id=cycle_id, event_date=body.event_date, count=body.count,
        cause_note=body.cause_note,
    )
    return RecordResponse(id=rec.id)


@router.post(
    "/water-quality", response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_RECORD)],
)
def record_water_quality(
    body: WaterQualityCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> RecordResponse:
    rec = WaterQualityService(db, ctx).record(
        culture_unit_id=body.culture_unit_id, read_at=body.read_at,
        metric_type=body.metric_type, value=body.value, uom=body.uom,
        classification=body.classification,
    )
    return RecordResponse(id=rec.id)
