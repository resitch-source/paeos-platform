"""Optimization engines (Phase 11).

Deterministic, closed-form optimizers implemented behind the Foundation
``SimulationEngine`` contract. Inputs are caller-supplied; results carry a full
``CalculationRecord`` classified SIMULATION. No solver dependency and no
fabricated coefficients.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

from paeos_fx.core.classification import Classification
from paeos_fx.core.errors import ValidationError
from paeos_fx.interfaces.simulation import (
    CalculationRecord,
    SimulationRequest,
    SimulationResult,
)

EOQ_MODEL = "eoq"
EOQ_VERSION = "1.0.0"
EOQ_REFERENCE = (
    "Harris, F.W. (1913), 'How many parts to make at once', Factory, The "
    "Magazine of Management 10(2). Classic Economic Order Quantity."
)

ALLOCATION_MODEL = "allocation"
ALLOCATION_VERSION = "1.0.0"


def economic_order_quantity(
    annual_demand: float, order_cost: float, holding_cost: float
) -> float:
    """EOQ = sqrt(2 * D * S / H). All parameters are caller-supplied."""
    if annual_demand < 0:
        raise ValidationError("annual_demand must be non-negative.")
    if order_cost < 0:
        raise ValidationError("order_cost must be non-negative.")
    if holding_cost <= 0:
        raise ValidationError("holding_cost must be positive.")
    return math.sqrt(2.0 * annual_demand * order_cost / holding_cost)


def proportional_allocation(
    total: Decimal, weights: dict[str, Decimal]
) -> dict[str, Decimal]:
    """Split ``total`` across keys in proportion to caller-supplied weights.

    Amounts are quantized to 4 decimal places; any rounding remainder is added to
    the largest-weight key so the parts sum exactly to ``total``.
    """
    if total < 0:
        raise ValidationError("total must be non-negative.")
    if not weights:
        raise ValidationError("weights must not be empty.")
    weight_sum = sum(weights.values(), Decimal("0"))
    if weight_sum <= 0:
        raise ValidationError("weights must sum to a positive value.")

    q = Decimal("0.0001")
    parts: dict[str, Decimal] = {}
    for key, w in weights.items():
        if w < 0:
            raise ValidationError("weights must be non-negative.")
        parts[key] = (total * w / weight_sum).quantize(q, rounding=ROUND_HALF_UP)
    remainder = total - sum(parts.values(), Decimal("0"))
    if remainder != 0:
        largest = max(weights, key=lambda k: weights[k])
        parts[largest] = parts[largest] + remainder
    return parts


class EOQModel:
    """A ``SimulationEngine`` computing the Economic Order Quantity."""

    name = EOQ_MODEL
    version = EOQ_VERSION

    def run(self, request: SimulationRequest) -> SimulationResult:
        p = request.parameters
        demand = p.get("annual_demand")
        order_cost = p.get("order_cost")
        holding_cost = p.get("holding_cost")
        if demand is None or order_cost is None or holding_cost is None:
            raise ValidationError(
                "eoq requires 'annual_demand', 'order_cost', and 'holding_cost'."
            )
        eoq = economic_order_quantity(float(demand), float(order_cost),
                                      float(holding_cost))
        record = CalculationRecord(
            inputs={"annual_demand": float(demand), "order_cost": float(order_cost),
                    "holding_cost": float(holding_cost)},
            units={"annual_demand": "units/yr", "order_cost": "currency/order",
                   "holding_cost": "currency/unit/yr", "eoq": "units"},
            formula_or_model="EOQ = sqrt(2 * D * S / H)",
            assumptions=[
                "Constant demand, instantaneous replenishment, no stockouts.",
                "Demand, order cost, and holding cost are caller-supplied.",
            ],
            reference=EOQ_REFERENCE,
            result={"eoq": eoq},
            model_version=EOQ_VERSION,
            validation_status=Classification.SIMULATION,
        )
        return SimulationResult(scenario=request.scenario, outputs={"eoq": eoq},
                                record=record)


class AllocationModel:
    """A ``SimulationEngine`` doing proportional resource allocation."""

    name = ALLOCATION_MODEL
    version = ALLOCATION_VERSION

    def run(self, request: SimulationRequest) -> SimulationResult:
        p = request.parameters
        total = p.get("total")
        weights = p.get("weights")
        if total is None or weights is None:
            raise ValidationError("allocation requires 'total' and 'weights'.")
        if not isinstance(weights, dict):
            raise ValidationError("'weights' must be a mapping of key -> weight.")
        dec_weights = {k: Decimal(str(v)) for k, v in weights.items()}
        parts = proportional_allocation(Decimal(str(total)), dec_weights)
        out = {k: str(v) for k, v in parts.items()}
        record = CalculationRecord(
            inputs={"total": str(total), "weights": {k: str(v) for k, v in
                                                     dec_weights.items()}},
            units={"total": "units", "allocation": "units"},
            formula_or_model="part_i = total * w_i / sum(w)",
            assumptions=[
                "Linear proportional split; remainder assigned to the largest weight.",
                "Total and weights are caller-supplied.",
            ],
            reference="Proportional (pro-rata) allocation.",
            result={"allocation": out},
            model_version=ALLOCATION_VERSION,
            validation_status=Classification.SIMULATION,
        )
        return SimulationResult(scenario=request.scenario,
                                outputs={"allocation": out}, record=record)
