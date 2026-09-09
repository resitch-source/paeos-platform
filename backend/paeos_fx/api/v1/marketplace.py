"""Marketplace + trading + logistics endpoints (Phase 8)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_trading import (
    CustomerCreate,
    CustomerResponse,
    ListingCreate,
    ListingResponse,
    MoneyResponse,
    OrderTransitionRequest,
    SalesOrderCreate,
    SalesOrderLineCreate,
    SalesOrderLineResponse,
    SalesOrderResponse,
    ShipmentCreate,
    ShipmentResponse,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.logistics.service import ShipmentService
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.currency import Money
from paeos_fx.pydantic_page import Paged
from paeos_fx.trading.service import (
    CustomerService,
    ListingService,
    SalesOrderService,
)

router = APIRouter(tags=["marketplace-trading-logistics"])


# --- Customers ---
@router.post(
    "/trading/customers", response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.TRADING_CUSTOMER_MANAGE))],
)
def create_customer(
    body: CustomerCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> CustomerResponse:
    c = CustomerService(db, ctx).create(code=body.code, name=body.name, contact=body.contact)
    return CustomerResponse.model_validate(c)


# --- Listings ---
@router.post(
    "/marketplace/listings", response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.MARKETPLACE_LISTING_MANAGE))],
)
def create_listing(
    body: ListingCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ListingResponse:
    price = Money.from_decimal(body.unit_price, body.currency)
    listing = ListingService(db, ctx).create(
        code=body.code, item_id=body.item_id,
        quantity_available=body.quantity_available, unit_price=price,
    )
    return ListingResponse.model_validate(listing)


@router.get(
    "/marketplace/listings", response_model=Paged[ListingResponse],
    dependencies=[Depends(require_permission(perms.MARKETPLACE_LISTING_READ))],
)
def list_listings(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[ListingResponse]:
    res = ListingService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[ListingResponse](
        items=[ListingResponse.model_validate(x) for x in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


# --- Sales orders ---
@router.post(
    "/trading/orders", response_model=SalesOrderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.TRADING_ORDER_WRITE))],
)
def create_order(
    body: SalesOrderCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> SalesOrderResponse:
    so = SalesOrderService(db, ctx).create(
        code=body.code, customer_id=body.customer_id, warehouse_id=body.warehouse_id,
        currency=body.currency,
    )
    return SalesOrderResponse.model_validate(so)


@router.post(
    "/trading/orders/{order_id}/lines", response_model=SalesOrderLineResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.TRADING_ORDER_WRITE))],
)
def add_order_line(
    order_id: uuid.UUID, body: SalesOrderLineCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> SalesOrderLineResponse:
    svc = SalesOrderService(db, ctx)
    so = svc.repo.get_or_404(order_id)
    price = Money.from_decimal(body.unit_price, so.currency)
    line = svc.add_line(order_id=order_id, item_id=body.item_id, quantity=body.quantity,
                        unit_price=price)
    return SalesOrderLineResponse(
        id=line.id, item_id=line.item_id, quantity=line.quantity,
        unit_price_minor=line.unit_price_minor, line_total_minor=line.line_total_minor,
    )


@router.get(
    "/trading/orders/{order_id}/total", response_model=MoneyResponse,
    dependencies=[Depends(require_permission(perms.TRADING_ORDER_READ))],
)
def order_total(
    order_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> MoneyResponse:
    total = SalesOrderService(db, ctx).order_total(order_id)
    return MoneyResponse(amount_minor=total.amount_minor, currency=total.currency,
                         amount=total.to_decimal())


@router.post(
    "/trading/orders/{order_id}/transition", response_model=SalesOrderResponse,
    dependencies=[Depends(require_permission(perms.TRADING_ORDER_CONFIRM))],
)
def transition_order(
    order_id: uuid.UUID, body: OrderTransitionRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> SalesOrderResponse:
    so = SalesOrderService(db, ctx).transition(order_id, body.event)
    return SalesOrderResponse.model_validate(so)


@router.post(
    "/trading/orders/{order_id}/fulfill", response_model=SalesOrderResponse,
    dependencies=[Depends(require_permission(perms.TRADING_ORDER_FULFILL))],
)
def fulfill_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> SalesOrderResponse:
    so = SalesOrderService(db, ctx).fulfill(order_id)
    return SalesOrderResponse.model_validate(so)


# --- Shipments ---
@router.post(
    "/logistics/shipments", response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.LOGISTICS_SHIPMENT_WRITE))],
)
def create_shipment(
    body: ShipmentCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ShipmentResponse:
    sh = ShipmentService(db, ctx).create(
        code=body.code, sales_order_id=body.sales_order_id, carrier_note=body.carrier_note,
    )
    return ShipmentResponse.model_validate(sh)


@router.post(
    "/logistics/shipments/{shipment_id}/transition", response_model=ShipmentResponse,
    dependencies=[Depends(require_permission(perms.LOGISTICS_SHIPMENT_WRITE))],
)
def transition_shipment(
    shipment_id: uuid.UUID, body: OrderTransitionRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ShipmentResponse:
    sh = ShipmentService(db, ctx).transition(shipment_id, body.event)
    return ShipmentResponse.model_validate(sh)
