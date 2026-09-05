import pytest

from paeos_fx.core.classification import Classification
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import AuthorizationError
from paeos_fx.interfaces.ai import (
    AISafetyError,
    AuthorizedTool,
    ToolRegistry,
    ToolResult,
)

pytestmark = pytest.mark.unit


def _ok_tool(ctx, **params):
    return ToolResult(output="ok", classification=Classification.SIMULATION)


def test_unknown_tool_rejected():
    reg = ToolRegistry()
    with pytest.raises(AISafetyError):
        reg.invoke("nope", ExecutionContext())


def test_permission_enforced():
    reg = ToolRegistry()
    reg.register(
        AuthorizedTool("read_yield", "sim.read", _ok_tool)
    )
    ctx = ExecutionContext(permissions=frozenset())
    with pytest.raises(AuthorizationError):
        reg.invoke("read_yield", ctx)


def test_safety_critical_requires_control_approval():
    reg = ToolRegistry()
    reg.register(
        AuthorizedTool(
            "actuate", "twin.control", _ok_tool, mutates=True, safety_critical=True
        )
    )
    ctx = ExecutionContext(permissions=frozenset({"twin.control"}))
    with pytest.raises(AISafetyError):
        reg.invoke("actuate", ctx, control_approved=False)
    # With explicit control approval it proceeds.
    result = reg.invoke("actuate", ctx, control_approved=True)
    assert result.output == "ok"
