"""IoT + Integrations endpoints (Phase 12).

Ingest inbound integration messages idempotently (e.g. IoT telemetry, routed to
the asset-telemetry path — records only, no actuation) and list them. Duplicate
idempotency keys are a no-op (HTTP 200 on the existing record).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_integration import (
    InboundMessageCreate,
    InboundMessageResponse,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.integration.service import IntegrationService
from paeos_fx.platform import permissions as perms
from paeos_fx.pydantic_page import Paged

router = APIRouter(tags=["iot-integrations"])


@router.post(
    "/integration/messages", response_model=InboundMessageResponse,
    dependencies=[Depends(require_permission(perms.INTEGRATION_MESSAGE_INGEST))],
)
def ingest_message(
    body: InboundMessageCreate, response: Response,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> InboundMessageResponse:
    message, created = IntegrationService(db, ctx).ingest(
        system=body.system, idempotency_key=body.idempotency_key, payload=body.payload,
    )
    # 201 for a newly ingested message; 200 when the idempotency key was a no-op.
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return InboundMessageResponse.model_validate(message)


@router.get(
    "/integration/messages", response_model=Paged[InboundMessageResponse],
    dependencies=[Depends(require_permission(perms.INTEGRATION_MESSAGE_READ))],
)
def list_messages(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[InboundMessageResponse]:
    res = IntegrationService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[InboundMessageResponse](
        items=[InboundMessageResponse.model_validate(x) for x in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )
