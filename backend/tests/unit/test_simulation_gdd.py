import pytest

from paeos_fx.agri.simulation import (
    DailyTemperature,
    GrowingDegreeDaysModel,
    growing_degree_days,
)
from paeos_fx.core.classification import Classification
from paeos_fx.core.errors import ValidationError
from paeos_fx.interfaces.simulation import SimulationRequest

pytestmark = pytest.mark.unit


def test_gdd_hand_computed():
    # Day1 mean=25, Day2 mean=20; base=10 -> (15)+(10) = 25 degC-day.
    series = [DailyTemperature(30, 20), DailyTemperature(25, 15)]
    assert growing_degree_days(series, base_temp_c=10) == 25.0


def test_gdd_bounded_at_base():
    # Mean below base contributes 0, never negative.
    series = [DailyTemperature(8, 4)]  # mean 6 < base 10
    assert growing_degree_days(series, base_temp_c=10) == 0.0


def test_gdd_empty_series_rejected():
    with pytest.raises(ValidationError):
        growing_degree_days([], base_temp_c=10)


def test_gdd_tmax_lt_tmin_rejected():
    with pytest.raises(ValidationError):
        growing_degree_days([DailyTemperature(5, 10)], base_temp_c=0)


def test_model_produces_full_provenance():
    model = GrowingDegreeDaysModel()
    req = SimulationRequest(
        scenario="demo",
        parameters={
            "base_temp_c": 10,
            "daily_temperatures": [
                {"tmax_c": 30, "tmin_c": 20},
                {"tmax_c": 25, "tmin_c": 15},
            ],
        },
    )
    result = model.run(req)
    assert result.outputs["accumulated_gdd_degc_day"] == 25.0
    rec = result.record
    # NO-FABRICATION: provenance envelope is complete and classified SIMULATION.
    assert rec.validation_status == Classification.SIMULATION
    assert rec.formula_or_model
    assert rec.model_version == "1.0.0"
    assert rec.reference
    assert rec.units["gdd"] == "degC-day"


def test_model_missing_params_rejected():
    with pytest.raises(ValidationError):
        GrowingDegreeDaysModel().run(SimulationRequest(scenario="x", parameters={}))
