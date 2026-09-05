"""AI interface (section X) — guarded tool contract.

Enforces the mandated AI safety chain:

    AI → Authorized Tool → Domain Service → Business Validation →
    Transaction → Audit Log

The AI never touches the database directly. It may only invoke registered
:class:`AuthorizedTool` instances, each of which declares the permission it
requires and whether it mutates state. Mutating/safety-critical tools require an
approved control context. Every invocation is auditable and every result carries
an uncertainty/confidence signal.

This is an interface + guardrail only. No AI provider is wired at the foundation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from paeos_fx.core.classification import Classification
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import AuthorizationError, PaeosError


class AISafetyError(PaeosError):
    code = "ai_safety_error"
    http_status = 403


@dataclass(frozen=True)
class ToolResult:
    """Result of a tool invocation, always carrying an uncertainty signal."""

    output: Any
    classification: Classification
    confidence: float = 0.0
    uncertainty_note: str = ""


@dataclass(frozen=True)
class AuthorizedTool:
    """A whitelisted capability the AI may call via a domain service.

    Attributes:
        name: stable tool identifier.
        required_permission: RBAC permission the caller must hold.
        handler: callable ``(ctx, **params) -> ToolResult`` implemented by a
            domain service (never raw DB access).
        mutates: whether the tool changes state.
        safety_critical: whether the tool affects safety-critical outcomes;
            such tools require an approved control context to execute.
    """

    name: str
    required_permission: str
    handler: Callable[..., ToolResult]
    mutates: bool = False
    safety_critical: bool = False


class ToolRegistry:
    """Registry + guarded dispatcher for AI-authorized tools."""

    def __init__(self) -> None:
        self._tools: dict[str, AuthorizedTool] = {}

    def register(self, tool: AuthorizedTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def invoke(
        self,
        name: str,
        ctx: ExecutionContext,
        *,
        control_approved: bool = False,
        **params: Any,
    ) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            raise AISafetyError(f"Unknown or unauthorized tool: {name!r}")
        if tool.required_permission not in ctx.permissions:
            raise AuthorizationError(
                "AI tool requires a permission the caller does not hold.",
                details={"tool": name, "required": tool.required_permission},
            )
        if tool.safety_critical and not control_approved:
            raise AISafetyError(
                "Safety-critical tool requires an approved control context.",
                details={"tool": name},
            )
        return tool.handler(ctx, **params)


@dataclass(frozen=True)
class AIRecommendation:
    """A recommendation surfaced by an AI agent (never auto-applied)."""

    summary: str
    classification: Classification = Classification.ESTIMATE
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    requires_human_approval: bool = True
