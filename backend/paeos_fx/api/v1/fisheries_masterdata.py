"""Fisheries master-data + culture-unit endpoints (Phase 5)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.agri.services import MasterDataService
from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_fisheries import (
    CultureUnitCreate,
    CultureUnitResponse,
    MasterDataCreate,
    MasterDataResponse,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.fisheries.masterdata import AquaticSpecies
from paeos_fx.fisheries.services import CultureUnitService
from paeos_fx.platform import permissions as perms
from paeos_fx.pydantic_page import Paged

router = APIRouter(prefix="/fisheries", tags=["fisheries"])


@router.post(
    "/species", response_model=MasterDataResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.FISHERIES_MASTERDATA_MANAGE))],
)
def create_species(
    body: MasterDataCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> MasterDataResponse:
    obj = MasterDataService(db, ctx, AquaticSpecies).create(code=body.code, name=body.name)
    return MasterDataResponse.model_validate(obj)


@router.get(
    "/species", response_model=Paged[MasterDataResponse],
    dependencies=[Depends(require_permission(perms.FISHERIES_MASTERDATA_READ))],
)
def list_species(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[MasterDataResponse]:
    res = MasterDataService(db, ctx, AquaticSpecies).list(PageParams(page=page, size=size))
    return Paged[MasterDataResponse](
        items=[MasterDataResponse.model_validate(o) for o in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


@router.post(
    "/culture-units", response_model=CultureUnitResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.FISHERIES_UNIT_WRITE))],
)
def create_culture_unit(
    body: CultureUnitCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> CultureUnitResponse:
    unit = CultureUnitService(db, ctx).create(
        code=body.code, name=body.name, unit_type=body.unit_type, farm_id=body.farm_id,
        location_geojson=body.location_geojson, water_area_sqm=body.water_area_sqm,
        area_classification=body.area_classification,
    )
    return CultureUnitResponse.model_validate(unit)


@router.get(
    "/culture-units", response_model=Paged[CultureUnitResponse],
    dependencies=[Depends(require_permission(perms.FISHERIES_UNIT_READ))],
)
def list_culture_units(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[CultureUnitResponse]:
    res = CultureUnitService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[CultureUnitResponse](
        items=[CultureUnitResponse.model_validate(u) for u in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )
