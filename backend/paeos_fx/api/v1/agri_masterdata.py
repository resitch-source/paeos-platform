"""Agriculture master-data endpoints (Phase 2)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.agri.masterdata import (
    Crop,
    CropCategory,
    CropVariety,
    LandUseType,
    SoilType,
)
from paeos_fx.agri.services import MasterDataService
from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_agri import (
    CropCreate,
    CropResponse,
    CropVarietyCreate,
    MasterDataCreate,
    MasterDataResponse,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.platform import permissions as perms
from paeos_fx.pydantic_page import Paged

router = APIRouter(prefix="/agri", tags=["agri-masterdata"])

_READ = require_permission(perms.AGRI_MASTERDATA_READ)
_MANAGE = require_permission(perms.AGRI_MASTERDATA_MANAGE)


# --- Crop categories ---
@router.post(
    "/crop-categories", response_model=MasterDataResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_MANAGE)],
)
def create_crop_category(
    body: MasterDataCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> MasterDataResponse:
    obj = MasterDataService(db, ctx, CropCategory).create(code=body.code, name=body.name)
    return MasterDataResponse.model_validate(obj)


@router.get(
    "/crop-categories", response_model=Paged[MasterDataResponse],
    dependencies=[Depends(_READ)],
)
def list_crop_categories(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[MasterDataResponse]:
    res = MasterDataService(db, ctx, CropCategory).list(PageParams(page=page, size=size))
    return Paged[MasterDataResponse](
        items=[MasterDataResponse.model_validate(o) for o in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


# --- Crops ---
@router.post(
    "/crops", response_model=CropResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_MANAGE)],
)
def create_crop(
    body: CropCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> CropResponse:
    obj = MasterDataService(db, ctx, Crop).create(
        code=body.code, name=body.name,
        category_id=body.category_id, scientific_name=body.scientific_name,
    )
    return CropResponse.model_validate(obj)


@router.get(
    "/crops", response_model=Paged[CropResponse], dependencies=[Depends(_READ)],
)
def list_crops(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[CropResponse]:
    res = MasterDataService(db, ctx, Crop).list(PageParams(page=page, size=size))
    return Paged[CropResponse](
        items=[CropResponse.model_validate(o) for o in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


# --- Crop varieties ---
@router.post(
    "/crop-varieties", response_model=MasterDataResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_MANAGE)],
)
def create_crop_variety(
    body: CropVarietyCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> MasterDataResponse:
    obj = MasterDataService(db, ctx, CropVariety).create(
        code=body.code, name=body.name, crop_id=body.crop_id
    )
    return MasterDataResponse.model_validate(obj)


# --- Soil types ---
@router.post(
    "/soil-types", response_model=MasterDataResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_MANAGE)],
)
def create_soil_type(
    body: MasterDataCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> MasterDataResponse:
    obj = MasterDataService(db, ctx, SoilType).create(code=body.code, name=body.name)
    return MasterDataResponse.model_validate(obj)


# --- Land-use types ---
@router.post(
    "/land-use-types", response_model=MasterDataResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_MANAGE)],
)
def create_land_use_type(
    body: MasterDataCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> MasterDataResponse:
    obj = MasterDataService(db, ctx, LandUseType).create(code=body.code, name=body.name)
    return MasterDataResponse.model_validate(obj)
