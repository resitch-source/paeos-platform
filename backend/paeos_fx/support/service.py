"""Technical-support services (Phase 9).

Ticket lifecycle + threaded comments. Pure workflow + audit; no SLA automation
or external channels.
"""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import select

from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService
from paeos_fx.support.models import (
    SUPPORT_TICKET_WORKFLOW,
    TICKET_PRIORITIES,
    SupportTicket,
    TicketComment,
)


class SupportTicketService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[SupportTicket] = TenantRepository(
            session, SupportTicket, self.tenant_id
        )

    def create(self, *, code: str, subject: str, body: str = "",
               priority: str = "normal") -> SupportTicket:
        if priority not in TICKET_PRIORITIES:
            raise BusinessRuleError("Invalid ticket priority.")
        ticket = SupportTicket(code=code, subject=subject, body=body,
                               priority=priority, status=SUPPORT_TICKET_WORKFLOW.initial)
        self.repo.add(ticket)
        self._record(action="support_ticket.create", entity_type="SupportTicket",
                     entity_id=str(ticket.id), after={"code": code})
        return ticket

    def assign(self, ticket_id: uuid.UUID, assignee_id: uuid.UUID) -> SupportTicket:
        ticket = self.repo.get_or_404(ticket_id)
        ticket.assignee_id = assignee_id
        if ticket.status == "open":
            ticket.status = SUPPORT_TICKET_WORKFLOW.fire(ticket.status, "assign")
        self.session.flush()
        self._record(action="support_ticket.assign", entity_type="SupportTicket",
                     entity_id=str(ticket_id), after={"assignee_id": str(assignee_id)})
        return ticket

    def transition(self, ticket_id: uuid.UUID, event: str) -> SupportTicket:
        ticket = self.repo.get_or_404(ticket_id)
        before = ticket.status
        ticket.status = SUPPORT_TICKET_WORKFLOW.fire(ticket.status, event)
        if ticket.status == "resolved":
            ticket.resolved_at = dt.datetime.now(dt.UTC)
        self.session.flush()
        self._record(action=f"support_ticket.{event}", entity_type="SupportTicket",
                     entity_id=str(ticket_id),
                     before={"status": before}, after={"status": ticket.status})
        return ticket

    def add_comment(self, *, ticket_id: uuid.UUID, body: str) -> TicketComment:
        self.repo.get_or_404(ticket_id)
        comment = TicketComment(tenant_id=self.tenant_id, ticket_id=ticket_id,
                                author_id=self.ctx.user_id, body=body)
        self.session.add(comment)
        self.session.flush()
        self._record(action="support_ticket.comment", entity_type="TicketComment",
                     entity_id=str(comment.id), after={"ticket_id": str(ticket_id)})
        return comment

    def comments(self, ticket_id: uuid.UUID) -> list[TicketComment]:
        return list(self.session.execute(
            select(TicketComment).where(
                TicketComment.tenant_id == self.tenant_id,
                TicketComment.ticket_id == ticket_id,
            ).order_by(TicketComment.created_at)
        ).scalars().all())

    def list(self, params=None):
        return self.repo.list(params)
