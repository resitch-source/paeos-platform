"""Platform-admin tenant provisioning (Phase 1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.api.deps import get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import ProvisionTenantRequest, TenantResponse
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.onboarding_service import provision_tenant

router = APIRouter(prefix="/admin/tenants", tags=["admin"])


@router.post(
    "",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.PLATFORM_TENANT_PROVISION))],
)
def create_tenant(
    body: ProvisionTenantRequest,
    db: Session = Depends(get_tenant_db),
) -> TenantResponse:
    result = provision_tenant(
        db,
        slug=body.slug,
        name=body.name,
        admin_email=body.admin_email,
        admin_password=body.admin_password,
    )
    return TenantResponse.model_validate(result.tenant)
