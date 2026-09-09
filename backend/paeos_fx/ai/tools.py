"""Authorized read-only tool catalog (Phase 10).

Builds a :class:`ToolRegistry` of READ-ONLY tools the AI may call. Every tool
delegates to an existing tenant-scoped read path (never raw DB access from the
AI), declares the RBAC permission it requires, and returns a classified
``ToolResult``. NO mutating or safety-critical tool is registered here — by
design, so the AI cannot change state or actuate machinery (gates #13/#14).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from paeos_fx.core.classification import Classification
from paeos_fx.core.context import ExecutionContext
from paeos_fx.interfaces.ai import AuthorizedTool, ToolRegistry, ToolResult
from paeos_fx.inventory.models import StockLevel
from paeos_fx.platform import permissions as perms
from paeos_fx.trading.models import SalesOrder


def build_registry(session: Session, ctx: ExecutionContext) -> ToolRegistry:
    """Register the read-only AI tools bound to this session/tenant."""
    registry = ToolRegistry()
    tenant_id = ctx.require_tenant()

    def _stock_levels(_ctx: ExecutionContext, **_params: Any) -> ToolResult:
        rows = session.execute(
            select(StockLevel).where(StockLevel.tenant_id == tenant_id)
        ).scalars().all()
        data = [
            {"item_id": str(r.item_id), "warehouse_id": str(r.warehouse_id),
             "quantity": str(r.quantity)}
            for r in rows
        ]
        # A direct read of persisted stock — MEASURED (observed), not inferred.
        return ToolResult(output=data, classification=Classification.MEASURED,
                          confidence=1.0)

    def _open_orders(_ctx: ExecutionContext, **_params: Any) -> ToolResult:
        rows = session.execute(
            select(SalesOrder).where(
                SalesOrder.tenant_id == tenant_id,
                SalesOrder.status == "confirmed",
            )
        ).scalars().all()
        data = [{"id": str(r.id), "code": r.code, "status": r.status} for r in rows]
        return ToolResult(output=data, classification=Classification.MEASURED,
                          confidence=1.0)

    registry.register(AuthorizedTool(
        name="inventory.stock_levels",
        required_permission=perms.INVENTORY_STOCK_READ,
        handler=_stock_levels, mutates=False, safety_critical=False,
    ))
    registry.register(AuthorizedTool(
        name="trading.open_orders",
        required_permission=perms.TRADING_ORDER_READ,
        handler=_open_orders, mutates=False, safety_critical=False,
    ))
    return registry
