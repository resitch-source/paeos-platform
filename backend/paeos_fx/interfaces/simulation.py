"""Simulation interface (section Y).

A minimum stable contract for simulation engines with a mandatory provenance
envelope enforcing the NO-FABRICATION calculation-recording rule: every result
records inputs, units, formula/model, assumptions, reference, result, model
version, and validation status.

No crop/coconut/digital-twin models are defined here — those belong to Phases 3,
7, and 11. This module only defines the shape a simulation result must take.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from paeos_fx.core.classification import Classification


@dataclass(frozen=True)
class CalculationRecord:
    """Mandatory provenance record for any engineering/simulation calculation."""

    inputs: dict[str, Any]
    units: dict[str, str]
    formula_or_model: str
    assumptions: list[str]
    reference: str
    result: Any
    model_version: str
    validation_status: Classification

    def __post_init__(self) -> None:
        if not self.formula_or_model:
            raise ValueError("formula_or_model is required (no fabrication).")
        if not self.model_version:
            raise ValueError("model_version is required (no fabrication).")


@dataclass(frozen=True)
class SimulationRequest:
    scenario: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SimulationResult:
    scenario: str
    outputs: dict[str, Any]
    record: CalculationRecord


class SimulationEngine(Protocol):
    """Contract implemented by concrete simulation engines in later phases."""

    name: str
    version: str

    def run(self, request: SimulationRequest) -> SimulationResult: ...
