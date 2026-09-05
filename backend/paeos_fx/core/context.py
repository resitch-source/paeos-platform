"""Request/tenant execution context.

Carries tenant, user, and correlation identity across a request or job using
:mod:`contextvars`, so services and repositories can enforce tenant isolation
and structured logging without threading parameters everywhere.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable per-request/per-job context."""

    tenant_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    locale: str = "en"
    permissions: frozenset[str] = frozenset()

    def with_tenant(self, tenant_id: uuid.UUID) -> ExecutionContext:
        return replace(self, tenant_id=tenant_id)

    def with_user(
        self, user_id: uuid.UUID, permissions: frozenset[str] = frozenset()
    ) -> ExecutionContext:
        return replace(self, user_id=user_id, permissions=permissions)

    def require_tenant(self) -> uuid.UUID:
        if self.tenant_id is None:
            raise PermissionError("Tenant context is required but not set.")
        return self.tenant_id


# The default is a *frozen* (immutable) dataclass, so sharing a single default
# instance across contexts is safe — the mutable-default hazard B039 guards
# against does not apply here.
_ctx: ContextVar[ExecutionContext] = ContextVar(
    "paeos_execution_context",
    default=ExecutionContext(),  # noqa: B039
)


def current_context() -> ExecutionContext:
    return _ctx.get()


def set_context(ctx: ExecutionContext):
    """Bind ``ctx`` as current; returns a token for :func:`reset_context`."""
    return _ctx.set(ctx)


def reset_context(token) -> None:
    _ctx.reset(token)
