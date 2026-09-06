"""Harvest endpoints (Phase 3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.agri.production_services import HarvestService
from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_production import HarvestCreate, HarvestResponse
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.platform import permissions as perms
from paeos_fx.pydantic_page import Paged

router = APIRouter(prefix="/agri/harvests", tags=["harvests"])


@router.post(
    "", response_model=HarvestResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.AGRI_PRODUCTION_WRITE))],
)
def record_harvest(
    body: HarvestCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> HarvestResponse:
    rec = HarvestService(db, ctx).record_harvest(
        cycle_id=body.cycle_id,
        harvest_date=body.harvest_date,
        quantity=body.quantity,
        uom=body.uom,
        classification=body.classification,
    )
    return HarvestResponse.model_validate(rec)


@router.get(
    "", response_model=Paged[HarvestResponse],
    dependencies=[Depends(require_permission(perms.AGRI_PRODUCTION_READ))],
)
def list_harvests(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[HarvestResponse]:
    res = HarvestService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[HarvestResponse](
        items=[HarvestResponse.model_validate(h) for h in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )
