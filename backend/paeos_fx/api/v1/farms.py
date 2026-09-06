"""Farm endpoints (Phase 2)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.agri.services import FarmService
from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_agri import FarmCreate, FarmResponse
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.platform import permissions as perms
from paeos_fx.pydantic_page import Paged

router = APIRouter(prefix="/farms", tags=["farms"])


@router.post(
    "", response_model=FarmResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.AGRI_FARM_WRITE))],
)
def create_farm(
    body: FarmCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> FarmResponse:
    farm = FarmService(db, ctx).create(
        code=body.code,
        name=body.name,
        org_unit_id=body.org_unit_id,
        admin_area_id=body.admin_area_id,
        location_geojson=body.location_geojson,
        area_hectares=body.area_hectares,
        area_classification=body.area_classification,
    )
    return FarmResponse.model_validate(farm)


@router.get(
    "", response_model=Paged[FarmResponse],
    dependencies=[Depends(require_permission(perms.AGRI_FARM_READ))],
)
def list_farms(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[FarmResponse]:
    res = FarmService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[FarmResponse](
        items=[FarmResponse.model_validate(f) for f in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )
