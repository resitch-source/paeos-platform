"""Engine registry (Phase 11).

Maps a model name to a concrete ``SimulationEngine`` so scenarios can run any
registered model uniformly. Reuses the existing GDD (Phase 3) and mass-balance
(Phase 7) engines alongside the Phase 11 optimizers.
"""

from __future__ import annotations

from paeos_fx.agri.simulation import GrowingDegreeDaysModel
from paeos_fx.agrisim.optimization import AllocationModel, EOQModel
from paeos_fx.core.errors import ValidationError
from paeos_fx.interfaces.simulation import SimulationEngine
from paeos_fx.processing.simulation import MassBalanceModel

_ENGINES: dict[str, SimulationEngine] = {
    GrowingDegreeDaysModel.name: GrowingDegreeDaysModel(),
    MassBalanceModel.name: MassBalanceModel(),
    EOQModel.name: EOQModel(),
    AllocationModel.name: AllocationModel(),
}


def available_models() -> list[dict[str, str]]:
    """List registered engines with their versions."""
    return [{"name": e.name, "version": e.version} for e in _ENGINES.values()]


def get_engine(model_name: str) -> SimulationEngine:
    engine = _ENGINES.get(model_name)
    if engine is None:
        raise ValidationError(
            "Unknown simulation model.",
            details={"model": model_name,
                     "available": sorted(_ENGINES.keys())},
        )
    return engine
