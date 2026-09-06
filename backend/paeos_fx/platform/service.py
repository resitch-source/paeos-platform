"""Reusable domain-service base (Phase 1 pattern).

A ``DomainService`` binds a tenant-scoped session and execution context and
provides audit + event helpers. Domain services are the ONLY layer that mutates
data: they enforce business rules, write audit records, and enqueue events —
never bypassed by API or AI callers.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from paeos_fx.core.context import ExecutionContext
from paeos_fx.platform.audit import AuditService
from paeos_fx.platform.events import DomainEvent, OutboxService


class DomainService:
    """Base class for tenant-scoped domain services."""

    def __init__(self, session: Session, ctx: ExecutionContext):
        self.session = session
        self.ctx = ctx
        self.tenant_id = ctx.require_tenant()
        self.audit = AuditService(session)
        self.outbox = OutboxService(session)

    def _record(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
    ) -> None:
        self.audit.record(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            ctx=self.ctx,
        )

    def _emit(self, name: str, payload: dict | None = None) -> None:
        self.outbox.enqueue(self.tenant_id, DomainEvent(name=name, payload=payload or {}))
