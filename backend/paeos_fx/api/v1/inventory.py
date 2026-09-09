"""Inventory + warehouse endpoints (Phase 6)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.agri.services import MasterDataService
from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_inventory import (
    ItemCreate,
    ItemResponse,
    MovementCreate,
    MovementResponse,
    StockResponse,
    TransferCreate,
    WarehouseCreate,
    WarehouseResponse,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.inventory.models import InventoryItem, MovementType, Warehouse
from paeos_fx.inventory.service import InventoryService
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.pydantic_page import Paged

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post(
    "/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.INVENTORY_ITEM_MANAGE))],
)
def create_item(
    body: ItemCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ItemResponse:
    obj = MasterDataService(db, ctx, InventoryItem).create(
        code=body.code, name=body.name, base_uom=body.base_uom, category=body.category,
    )
    return ItemResponse.model_validate(obj)


@router.get(
    "/items", response_model=Paged[ItemResponse],
    dependencies=[Depends(require_permission(perms.INVENTORY_ITEM_READ))],
)
def list_items(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[ItemResponse]:
    res = MasterDataService(db, ctx, InventoryItem).list(PageParams(page=page, size=size))
    return Paged[ItemResponse](
        items=[ItemResponse.model_validate(o) for o in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


@router.post(
    "/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.INVENTORY_WAREHOUSE_MANAGE))],
)
def create_warehouse(
    body: WarehouseCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> WarehouseResponse:
    ctx.require_tenant()
    wh = Warehouse(
        tenant_id=ctx.tenant_id, code=body.code, name=body.name,
        org_unit_id=body.org_unit_id, address=body.address,
    )
    db.add(wh)
    db.flush()
    return WarehouseResponse.model_validate(wh)


@router.get(
    "/warehouses", response_model=Paged[WarehouseResponse],
    dependencies=[Depends(require_permission(perms.INVENTORY_WAREHOUSE_READ))],
)
def list_warehouses(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[WarehouseResponse]:
    repo: TenantRepository[Warehouse] = TenantRepository(db, Warehouse, ctx.require_tenant())
    res = repo.list(PageParams(page=page, size=size))
    return Paged[WarehouseResponse](
        items=[WarehouseResponse.model_validate(w) for w in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


@router.post(
    "/movements", response_model=MovementResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.INVENTORY_MOVEMENT_WRITE))],
)
def record_movement(
    body: MovementCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> MovementResponse:
    mv = InventoryService(db, ctx).record_movement(
        item_id=body.item_id, warehouse_id=body.warehouse_id,
        movement_type=MovementType(body.movement_type), quantity=body.quantity,
        reference=body.reference,
    )
    return MovementResponse(
        id=mv.id, item_id=mv.item_id, warehouse_id=mv.warehouse_id,
        movement_type=mv.movement_type, quantity=mv.quantity,
    )


@router.post(
    "/transfers", response_model=list[MovementResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.INVENTORY_MOVEMENT_WRITE))],
)
def transfer_stock(
    body: TransferCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> list[MovementResponse]:
    out_mv, in_mv = InventoryService(db, ctx).transfer(
        item_id=body.item_id, from_warehouse_id=body.from_warehouse_id,
        to_warehouse_id=body.to_warehouse_id, quantity=body.quantity,
        reference=body.reference,
    )
    return [
        MovementResponse(id=m.id, item_id=m.item_id, warehouse_id=m.warehouse_id,
                         movement_type=m.movement_type, quantity=m.quantity)
        for m in (out_mv, in_mv)
    ]


@router.get(
    "/stock", response_model=StockResponse,
    dependencies=[Depends(require_permission(perms.INVENTORY_STOCK_READ))],
)
def get_stock(
    item_id: str, warehouse_id: str,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> StockResponse:
    import uuid

    iid, wid = uuid.UUID(item_id), uuid.UUID(warehouse_id)
    qty = InventoryService(db, ctx).get_stock(iid, wid)
    return StockResponse(item_id=iid, warehouse_id=wid, quantity=qty)
