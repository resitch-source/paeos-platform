"""Crop simulation engines (Phase 3).

Implements the Foundation ``SimulationEngine`` interface with a standard,
citable agronomic method — **Growing Degree Days (GDD)**. The method is explicit
and all parameters (base temperature, daily temperature series) are supplied by
the caller; no crop-specific coefficients, growth rates, or yields are invented.
Every result is a ``SimulationResult`` carrying a full ``CalculationRecord`` with
``validation_status = SIMULATION`` (NO-FABRICATION policy).

Reference: McMaster, G.S. & Wilhelm, W.W. (1997), "Growing degree-days: one
equation, two interpretations", Agricultural and Forest Meteorology 87(4).
Method 1 (bounded at the base temperature) is used here.
"""

from __future__ import annotations

from dataclasses import dataclass

from paeos_fx.core.classification import Classification
from paeos_fx.core.errors import ValidationError
from paeos_fx.interfaces.simulation import (
    CalculationRecord,
    SimulationRequest,
    SimulationResult,
)

MODEL_NAME = "growing_degree_days"
MODEL_VERSION = "1.0.0"
GDD_REFERENCE = (
    "McMaster & Wilhelm (1997), Agricultural and Forest Meteorology 87(4), "
    "method 1 (daily mean bounded at base temperature)."
)


@dataclass(frozen=True)
class DailyTemperature:
    """One day's max/min air temperature in degrees Celsius (caller-supplied)."""

    tmax_c: float
    tmin_c: float


def growing_degree_days(
    series: list[DailyTemperature], base_temp_c: float
) -> float:
    """Accumulate GDD over a daily temperature series.

    GDD_day = max(0, (Tmax + Tmin) / 2 - Tbase); total = sum over days.
    All inputs are caller-supplied; the base temperature is a parameter, never a
    fabricated crop constant.
    """
    if not series:
        raise ValidationError("Temperature series must not be empty.")
    total = 0.0
    for day in series:
        if day.tmax_c < day.tmin_c:
            raise ValidationError("tmax_c must be >= tmin_c for each day.")
        mean = (day.tmax_c + day.tmin_c) / 2.0
        total += max(0.0, mean - base_temp_c)
    return total


class GrowingDegreeDaysModel:
    """A ``SimulationEngine`` computing accumulated GDD with full provenance."""

    name = MODEL_NAME
    version = MODEL_VERSION

    def run(self, request: SimulationRequest) -> SimulationResult:
        params = request.parameters
        base_temp = params.get("base_temp_c")
        raw_series = params.get("daily_temperatures")
        if base_temp is None or raw_series is None:
            raise ValidationError(
                "GDD requires 'base_temp_c' and 'daily_temperatures' parameters."
            )
        series = [
            DailyTemperature(tmax_c=float(d["tmax_c"]), tmin_c=float(d["tmin_c"]))
            for d in raw_series
        ]
        total_gdd = growing_degree_days(series, float(base_temp))

        record = CalculationRecord(
            inputs={
                "base_temp_c": float(base_temp),
                "n_days": len(series),
            },
            units={"base_temp_c": "degC", "gdd": "degC-day"},
            formula_or_model="GDD = sum(max(0, (Tmax+Tmin)/2 - Tbase))",
            assumptions=[
                "Daily mean bounded at the base temperature (no upper cap).",
                "Caller-supplied temperatures and base temperature.",
            ],
            reference=GDD_REFERENCE,
            result={"accumulated_gdd_degc_day": total_gdd},
            model_version=MODEL_VERSION,
            validation_status=Classification.SIMULATION,
        )
        return SimulationResult(
            scenario=request.scenario,
            outputs={"accumulated_gdd_degc_day": total_gdd},
            record=record,
        )
