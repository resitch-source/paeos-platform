"""Land parcel endpoints (Phase 2)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.agri.services import ParcelService
from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_agri import ParcelCreate, ParcelResponse
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.platform import permissions as perms
from paeos_fx.pydantic_page import Paged

router = APIRouter(prefix="/parcels", tags=["parcels"])


@router.post(
    "", response_model=ParcelResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.AGRI_PARCEL_WRITE))],
)
def create_parcel(
    body: ParcelCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ParcelResponse:
    parcel = ParcelService(db, ctx).create(
        code=body.code,
        name=body.name,
        farm_id=body.farm_id,
        soil_type_id=body.soil_type_id,
        land_use_type_id=body.land_use_type_id,
        boundary_geojson=body.boundary_geojson,
    )
    return ParcelResponse.model_validate(parcel)


@router.get(
    "", response_model=Paged[ParcelResponse],
    dependencies=[Depends(require_permission(perms.AGRI_PARCEL_READ))],
)
def list_parcels(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[ParcelResponse]:
    res = ParcelService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[ParcelResponse](
        items=[ParcelResponse.model_validate(p) for p in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )
