"""Role & permission administration endpoints (Phase 1)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import (
    CreateRoleRequest,
    GrantPermissionRequest,
    PermissionResponse,
    RoleResponse,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.iam_service import RoleService

router = APIRouter(tags=["roles"])


@router.get(
    "/permissions",
    response_model=list[PermissionResponse],
    dependencies=[Depends(require_permission(perms.IAM_ROLE_READ))],
)
def list_permissions(
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> list[PermissionResponse]:
    items = RoleService(db, ctx).list_permissions()
    return [PermissionResponse.model_validate(p) for p in items]


@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.IAM_ROLE_MANAGE))],
)
def create_role(
    body: CreateRoleRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> RoleResponse:
    role = RoleService(db, ctx).create_role(code=body.code, name=body.name)
    return RoleResponse.model_validate(role)


@router.post(
    "/roles/{role_id}/permissions",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(perms.IAM_ROLE_MANAGE))],
)
def grant_permission(
    role_id: uuid.UUID,
    body: GrantPermissionRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> None:
    RoleService(db, ctx).grant_permission(role_id, body.permission_code)
