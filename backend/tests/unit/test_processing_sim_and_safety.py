import pytest

from paeos_fx.core.classification import Classification
from paeos_fx.core.errors import ValidationError
from paeos_fx.interfaces.digital_twin import ControlCommand, UnsafeControlError
from paeos_fx.interfaces.simulation import SimulationRequest
from paeos_fx.processing.simulation import MassBalanceModel, mass_balance_output
from paeos_fx.processing.twin import CoconutOilTwin

pytestmark = pytest.mark.unit


def test_mass_balance_math():
    # 1000 kg copra * 0.62 yield = 620 kg oil (yield is caller-supplied).
    assert mass_balance_output(1000.0, 0.62) == 620.0


def test_mass_balance_rejects_out_of_range_yield():
    with pytest.raises(ValidationError):
        mass_balance_output(100.0, 1.5)


def test_mass_balance_model_provenance():
    result = MassBalanceModel().run(
        SimulationRequest(scenario="s", parameters={"input_mass": 100, "yield_fraction": 0.5})
    )
    assert result.outputs["output_mass"] == 50.0
    assert result.record.validation_status == Classification.SIMULATION
    assert result.record.formula_or_model
    assert result.record.model_version == "1.0.0"


def test_mass_balance_requires_params():
    with pytest.raises(ValidationError):
        MassBalanceModel().run(SimulationRequest(scenario="s", parameters={}))


def test_twin_control_is_gated_and_non_actuating():
    """SAFETY: the twin never actuates without explicit human approval."""
    twin = CoconutOilTwin("asset-1")
    cmd = ControlCommand(asset_id="asset-1", command="start_press")
    with pytest.raises(UnsafeControlError):
        twin.request_control(cmd, human_approved=False)
    # Even with approval the method performs no actuation (returns None).
    assert twin.request_control(cmd, human_approved=True) is None
