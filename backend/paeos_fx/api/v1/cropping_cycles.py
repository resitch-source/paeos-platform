"""Cropping-cycle endpoints (Phase 3)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.agri.production_services import CroppingCycleService
from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_production import (
    CroppingCycleCreate,
    CroppingCycleResponse,
    TransitionRequest,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.platform import permissions as perms
from paeos_fx.pydantic_page import Paged

router = APIRouter(prefix="/agri/cropping-cycles", tags=["cropping-cycles"])


@router.post(
    "", response_model=CroppingCycleResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.AGRI_PRODUCTION_WRITE))],
)
def create_cycle(
    body: CroppingCycleCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> CroppingCycleResponse:
    cycle = CroppingCycleService(db, ctx).create(
        code=body.code,
        parcel_id=body.parcel_id,
        crop_id=body.crop_id,
        variety_id=body.variety_id,
        season=body.season,
        planting_date=body.planting_date,
        expected_harvest_date=body.expected_harvest_date,
        planted_area_ha=body.planted_area_ha,
        area_classification=body.area_classification,
    )
    return CroppingCycleResponse.model_validate(cycle)


@router.get(
    "", response_model=Paged[CroppingCycleResponse],
    dependencies=[Depends(require_permission(perms.AGRI_PRODUCTION_READ))],
)
def list_cycles(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[CroppingCycleResponse]:
    res = CroppingCycleService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[CroppingCycleResponse](
        items=[CroppingCycleResponse.model_validate(c) for c in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


@router.post(
    "/{cycle_id}/transition", response_model=CroppingCycleResponse,
    dependencies=[Depends(require_permission(perms.AGRI_PRODUCTION_WRITE))],
)
def transition_cycle(
    cycle_id: uuid.UUID,
    body: TransitionRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> CroppingCycleResponse:
    cycle = CroppingCycleService(db, ctx).transition(cycle_id, body.event)
    return CroppingCycleResponse.model_validate(cycle)
