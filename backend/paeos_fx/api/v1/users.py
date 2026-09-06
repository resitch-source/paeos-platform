"""User administration endpoints (Phase 1)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import (
    AssignRoleRequest,
    CreateUserRequest,
    PageMeta,
    UserResponse,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.iam_service import UserService
from paeos_fx.pydantic_page import Paged

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.IAM_USER_WRITE))],
)
def create_user(
    body: CreateUserRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> UserResponse:
    user = UserService(db, ctx).create_user(
        email=body.email, password=body.password, full_name=body.full_name
    )
    return UserResponse.model_validate(user)


@router.get(
    "",
    response_model=Paged[UserResponse],
    dependencies=[Depends(require_permission(perms.IAM_USER_READ))],
)
def list_users(
    page: int = 1,
    size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[UserResponse]:
    result = UserService(db, ctx).list_users(PageParams(page=page, size=size))
    return Paged[UserResponse](
        items=[UserResponse.model_validate(u) for u in result.items],
        meta=PageMeta(
            total=result.total, page=result.page, size=result.size, pages=result.pages
        ),
    )


@router.post(
    "/{user_id}/roles",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(perms.IAM_USER_WRITE))],
)
def assign_role(
    user_id: uuid.UUID,
    body: AssignRoleRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> None:
    UserService(db, ctx).assign_role(user_id, body.role_id)


@router.delete(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(perms.IAM_USER_WRITE))],
)
def revoke_role(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> None:
    UserService(db, ctx).revoke_role(user_id, role_id)


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    dependencies=[Depends(require_permission(perms.IAM_USER_WRITE))],
)
def deactivate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> UserResponse:
    user = UserService(db, ctx).deactivate_user(user_id)
    return UserResponse.model_validate(user)
