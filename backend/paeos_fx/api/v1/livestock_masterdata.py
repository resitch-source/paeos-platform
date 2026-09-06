"""Livestock master-data endpoints (Phase 4)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.agri.services import MasterDataService
from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_livestock import (
    BreedCreate,
    MasterDataCreate,
    MasterDataResponse,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.livestock.masterdata import LivestockBreed, LivestockSpecies
from paeos_fx.platform import permissions as perms
from paeos_fx.pydantic_page import Paged

router = APIRouter(prefix="/livestock", tags=["livestock-masterdata"])

_READ = require_permission(perms.LIVESTOCK_MASTERDATA_READ)
_MANAGE = require_permission(perms.LIVESTOCK_MASTERDATA_MANAGE)


@router.post(
    "/species", response_model=MasterDataResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_MANAGE)],
)
def create_species(
    body: MasterDataCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> MasterDataResponse:
    obj = MasterDataService(db, ctx, LivestockSpecies).create(
        code=body.code, name=body.name
    )
    return MasterDataResponse.model_validate(obj)


@router.get(
    "/species", response_model=Paged[MasterDataResponse],
    dependencies=[Depends(_READ)],
)
def list_species(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[MasterDataResponse]:
    res = MasterDataService(db, ctx, LivestockSpecies).list(PageParams(page=page, size=size))
    return Paged[MasterDataResponse](
        items=[MasterDataResponse.model_validate(o) for o in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


@router.post(
    "/breeds", response_model=MasterDataResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(_MANAGE)],
)
def create_breed(
    body: BreedCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> MasterDataResponse:
    obj = MasterDataService(db, ctx, LivestockBreed).create(
        code=body.code, name=body.name, species_id=body.species_id
    )
    return MasterDataResponse.model_validate(obj)
