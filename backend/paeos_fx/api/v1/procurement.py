"""Procurement endpoints (Phase 6) — financial (approval gate #12)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas_inventory import (
    MoneyResponse,
    POCreate,
    POLineCreate,
    POLineResponse,
    POResponse,
    POTransitionRequest,
    SupplierCreate,
    SupplierResponse,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.currency import Money
from paeos_fx.procurement.models import Supplier
from paeos_fx.procurement.service import PurchaseOrderService

router = APIRouter(prefix="/procurement", tags=["procurement"])


@router.post(
    "/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.PROCUREMENT_SUPPLIER_MANAGE))],
)
def create_supplier(
    body: SupplierCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> SupplierResponse:
    sup = Supplier(tenant_id=ctx.require_tenant(), code=body.code, name=body.name,
                   contact=body.contact)
    db.add(sup)
    db.flush()
    return SupplierResponse.model_validate(sup)


@router.post(
    "/purchase-orders", response_model=POResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.PROCUREMENT_PO_WRITE))],
)
def create_po(
    body: POCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> POResponse:
    po = PurchaseOrderService(db, ctx).create(
        code=body.code, supplier_id=body.supplier_id, warehouse_id=body.warehouse_id,
        currency=body.currency,
    )
    return POResponse.model_validate(po)


@router.post(
    "/purchase-orders/{po_id}/lines", response_model=POLineResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.PROCUREMENT_PO_WRITE))],
)
def add_line(
    po_id: uuid.UUID,
    body: POLineCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> POLineResponse:
    svc = PurchaseOrderService(db, ctx)
    po = svc.repo.get_or_404(po_id)
    price = Money.from_decimal(body.unit_price, po.currency)
    line = svc.add_line(po_id=po_id, item_id=body.item_id, quantity=body.quantity,
                        unit_price=price)
    return POLineResponse(
        id=line.id, item_id=line.item_id, quantity=line.quantity,
        unit_price_minor=line.unit_price_minor, line_total_minor=line.line_total_minor,
    )


@router.get(
    "/purchase-orders/{po_id}/total", response_model=MoneyResponse,
    dependencies=[Depends(require_permission(perms.PROCUREMENT_PO_READ))],
)
def po_total(
    po_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> MoneyResponse:
    total = PurchaseOrderService(db, ctx).order_total(po_id)
    return MoneyResponse(amount_minor=total.amount_minor, currency=total.currency,
                         amount=total.to_decimal())


@router.post(
    "/purchase-orders/{po_id}/transition", response_model=POResponse,
    dependencies=[Depends(require_permission(perms.PROCUREMENT_PO_APPROVE))],
)
def transition_po(
    po_id: uuid.UUID,
    body: POTransitionRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> POResponse:
    po = PurchaseOrderService(db, ctx).transition(po_id, body.event)
    return POResponse.model_validate(po)


@router.post(
    "/purchase-orders/{po_id}/receive", response_model=POResponse,
    dependencies=[Depends(require_permission(perms.PROCUREMENT_PO_RECEIVE))],
)
def receive_po(
    po_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> POResponse:
    po = PurchaseOrderService(db, ctx).receive(po_id)
    return POResponse.model_validate(po)
