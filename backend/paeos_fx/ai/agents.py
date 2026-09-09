"""Advisory agents (Phase 10).

Deterministic, transparent analyzers over authorized read-only tool outputs.
Each returns advisory :class:`AIRecommendation`s — never auto-applied, always
classified and carrying an uncertainty note (NO-FABRICATION). There is no LLM
here: the triggering condition is a documented rule, so ``confidence`` reports
the certainty of that condition, while the recommended action is an ESTIMATE that
``requires_human_approval``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from paeos_fx.core.classification import Classification
from paeos_fx.interfaces.ai import AIRecommendation, ToolResult


def low_stock_advisory(stock: ToolResult, *, threshold: Decimal) -> list[AIRecommendation]:
    """Flag (item, warehouse) stock levels at or below a caller-supplied threshold."""
    recs: list[AIRecommendation] = []
    for row in stock.output:
        qty = Decimal(str(row["quantity"]))
        if qty <= threshold:
            recs.append(AIRecommendation(
                summary=(f"Stock for item {row['item_id']} at warehouse "
                         f"{row['warehouse_id']} is {qty} (≤ threshold {threshold}); "
                         "consider replenishment."),
                classification=Classification.ESTIMATE,
                confidence=1.0,  # the threshold breach itself is deterministic
                assumptions=[
                    f"Reorder threshold = {threshold} (caller-supplied).",
                    "On-hand quantity read directly from the stock ledger (MEASURED).",
                ],
                requires_human_approval=True,
            ))
    return recs


def open_order_advisory(orders: ToolResult, **_params: Any) -> list[AIRecommendation]:
    """Flag confirmed sales orders awaiting fulfilment."""
    recs: list[AIRecommendation] = []
    for row in orders.output:
        recs.append(AIRecommendation(
            summary=(f"Sales order {row['code']} is confirmed but not yet fulfilled; "
                     "review for fulfilment or follow-up."),
            classification=Classification.ESTIMATE,
            confidence=1.0,
            assumptions=["Order status read directly (MEASURED); no delivery SLA modeled."],
            requires_human_approval=True,
        ))
    return recs
