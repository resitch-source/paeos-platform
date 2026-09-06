"""Organizational unit endpoints (Phase 1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import (
    CreateOrgUnitRequest,
    OrgUnitResponse,
    PageMeta,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.org import OrgUnit, OrgUnitService
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.pydantic_page import Paged

router = APIRouter(prefix="/org-units", tags=["org-units"])


@router.post(
    "",
    response_model=OrgUnitResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.ORG_UNIT_WRITE))],
)
def create_org_unit(
    body: CreateOrgUnitRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> OrgUnitResponse:
    unit = OrgUnitService(db, ctx).create(
        code=body.code,
        name=body.name,
        unit_type=body.unit_type,
        parent_id=body.parent_id,
    )
    return OrgUnitResponse.model_validate(unit)


@router.get(
    "",
    response_model=Paged[OrgUnitResponse],
    dependencies=[Depends(require_permission(perms.ORG_UNIT_READ))],
)
def list_org_units(
    page: int = 1,
    size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[OrgUnitResponse]:
    repo: TenantRepository[OrgUnit] = TenantRepository(db, OrgUnit, ctx.require_tenant())
    result = repo.list(PageParams(page=page, size=size))
    return Paged[OrgUnitResponse](
        items=[OrgUnitResponse.model_validate(u) for u in result.items],
        meta=PageMeta(
            total=result.total, page=result.page, size=result.size, pages=result.pages
        ),
    )
