"""Animal-group endpoints (Phase 4)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_livestock import (
    AnimalGroupCreate,
    AnimalGroupResponse,
    HealthEventCreate,
    MortalityRecordCreate,
    ProductionRecordCreate,
    RecordResponse,
    TransitionRequest,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.livestock.services import AnimalGroupService
from paeos_fx.platform import permissions as perms
from paeos_fx.pydantic_page import Paged

router = APIRouter(prefix="/livestock/animal-groups", tags=["animal-groups"])

_READ = require_permission(perms.LIVESTOCK_GROUP_READ)
_WRITE = require_permission(perms.LIVESTOCK_GROUP_WRITE)
_RECORD = require_permission(perms.LIVESTOCK_RECORD_WRITE)


@router.post(
    "", response_model=AnimalGroupResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_WRITE)],
)
def create_group(
    body: AnimalGroupCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> AnimalGroupResponse:
    group = AnimalGroupService(db, ctx).create(
        code=body.code, name=body.name, species_id=body.species_id,
        breed_id=body.breed_id, farm_id=body.farm_id, org_unit_id=body.org_unit_id,
        purpose=body.purpose, head_count=body.head_count,
        established_date=body.established_date,
    )
    return AnimalGroupResponse.model_validate(group)


@router.get(
    "", response_model=Paged[AnimalGroupResponse], dependencies=[Depends(_READ)],
)
def list_groups(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[AnimalGroupResponse]:
    res = AnimalGroupService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[AnimalGroupResponse](
        items=[AnimalGroupResponse.model_validate(g) for g in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


@router.post(
    "/{group_id}/transition", response_model=AnimalGroupResponse,
    dependencies=[Depends(_WRITE)],
)
def transition_group(
    group_id: uuid.UUID,
    body: TransitionRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> AnimalGroupResponse:
    group = AnimalGroupService(db, ctx).transition(group_id, body.event)
    return AnimalGroupResponse.model_validate(group)


@router.post(
    "/{group_id}/production", response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_RECORD)],
)
def record_production(
    group_id: uuid.UUID,
    body: ProductionRecordCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> RecordResponse:
    rec = AnimalGroupService(db, ctx).record_production(
        group_id=group_id, recorded_at=body.recorded_at, metric_type=body.metric_type,
        quantity=body.quantity, uom=body.uom, classification=body.classification,
    )
    return RecordResponse(id=rec.id, group_id=rec.group_id)


@router.post(
    "/{group_id}/mortality", response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_RECORD)],
)
def record_mortality(
    group_id: uuid.UUID,
    body: MortalityRecordCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> RecordResponse:
    rec = AnimalGroupService(db, ctx).record_mortality(
        group_id=group_id, event_date=body.event_date, count=body.count,
        cause_note=body.cause_note,
    )
    return RecordResponse(id=rec.id, group_id=rec.group_id)


@router.post(
    "/{group_id}/health", response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_RECORD)],
)
def record_health(
    group_id: uuid.UUID,
    body: HealthEventCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> RecordResponse:
    rec = AnimalGroupService(db, ctx).record_health_event(
        group_id=group_id, event_date=body.event_date, event_type=body.event_type,
        description=body.description,
    )
    return RecordResponse(id=rec.id, group_id=rec.group_id)
