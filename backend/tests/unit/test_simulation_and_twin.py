import pytest

from paeos_fx.core.classification import Classification
from paeos_fx.interfaces.digital_twin import (
    ControlCommand,
    UnsafeControlError,
    guard_control,
)
from paeos_fx.interfaces.simulation import CalculationRecord

pytestmark = pytest.mark.unit


def test_calculation_record_requires_provenance():
    with pytest.raises(ValueError):
        CalculationRecord(
            inputs={"a": 1},
            units={"a": "kg"},
            formula_or_model="",  # missing -> no fabrication
            assumptions=[],
            reference="ref",
            result=1,
            model_version="1.0.0",
            validation_status=Classification.SIMULATION,
        )


def test_valid_calculation_record():
    rec = CalculationRecord(
        inputs={"mass": 10},
        units={"mass": "kg"},
        formula_or_model="linear-demo",
        assumptions=["demo only"],
        reference="internal",
        result=20,
        model_version="0.1.0",
        validation_status=Classification.SIMULATION,
    )
    assert rec.model_version == "0.1.0"


def test_machinery_control_requires_human_approval():
    cmd = ControlCommand(asset_id="press-1", command="start")
    with pytest.raises(UnsafeControlError):
        guard_control(cmd, human_approved=False)
    guard_control(cmd, human_approved=True)  # no raise
