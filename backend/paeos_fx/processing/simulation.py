"""Processing simulation (Phase 7) — mass balance.

A transparent, advisory mass-balance model implementing the Foundation
``SimulationEngine``. Estimated output mass = input mass × yield fraction, where
BOTH the input mass and the yield fraction are caller-supplied (a tenant's own
measured/validated figures). No extraction rates or equipment coefficients are
invented. Results carry a full ``CalculationRecord`` classified SIMULATION.
"""

from __future__ import annotations

from paeos_fx.core.classification import Classification
from paeos_fx.core.errors import ValidationError
from paeos_fx.interfaces.simulation import (
    CalculationRecord,
    SimulationRequest,
    SimulationResult,
)

MODEL_NAME = "mass_balance"
MODEL_VERSION = "1.0.0"


def mass_balance_output(input_mass: float, yield_fraction: float) -> float:
    """Output mass = input mass × yield fraction (conservation of mass)."""
    if input_mass < 0:
        raise ValidationError("input_mass must be non-negative.")
    if not (0.0 <= yield_fraction <= 1.0):
        raise ValidationError("yield_fraction must be within [0, 1].")
    return input_mass * yield_fraction


class MassBalanceModel:
    """A ``SimulationEngine`` computing an advisory output-mass estimate."""

    name = MODEL_NAME
    version = MODEL_VERSION

    def run(self, request: SimulationRequest) -> SimulationResult:
        params = request.parameters
        input_mass = params.get("input_mass")
        yield_fraction = params.get("yield_fraction")
        unit = params.get("mass_unit", "kg")
        if input_mass is None or yield_fraction is None:
            raise ValidationError(
                "mass_balance requires 'input_mass' and 'yield_fraction'."
            )
        output = mass_balance_output(float(input_mass), float(yield_fraction))
        record = CalculationRecord(
            inputs={
                "input_mass": float(input_mass),
                "yield_fraction": float(yield_fraction),
            },
            units={"input_mass": unit, "output_mass": unit},
            formula_or_model="output_mass = input_mass * yield_fraction",
            assumptions=[
                "Conservation of mass; single-stage yield.",
                "Input mass and yield fraction are caller-supplied.",
            ],
            reference="Mass balance (conservation of mass).",
            result={"output_mass": output},
            model_version=MODEL_VERSION,
            validation_status=Classification.SIMULATION,
        )
        return SimulationResult(
            scenario=request.scenario,
            outputs={"output_mass": output, "unit": unit},
            record=record,
        )
