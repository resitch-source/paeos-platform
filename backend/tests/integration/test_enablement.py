"""Training + Support + Expert-marketplace integration tests (Phase 9).

Fully non-geometry — runs on any PostgreSQL. Validates the course/enrollment
lifecycle, support-ticket lifecycle with comments, the expert-engagement
lifecycle with an agreed fee, and tenant isolation.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.experts.service import EngagementService, ExpertProfileService
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.currency import Money
from paeos_fx.platform.onboarding_service import provision_tenant
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.support.models import SupportTicket
from paeos_fx.support.service import SupportTicketService
from paeos_fx.training.service import CourseService, EnrollmentService

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]


def _ctx(tenant_id, user_id):
    return ExecutionContext(tenant_id=tenant_id, user_id=user_id,
                            permissions=frozenset(perms.TENANT_ADMIN_PERMISSIONS))


def _bind(s, tid):
    s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})


def _bootstrap(session_factory, slug="learnco"):
    with session_factory() as s:
        res = provision_tenant(s, slug=slug, name="Learn Co", admin_email=f"a@{slug}.test",
                               admin_password="supersecret123")
        s.commit()
        return _ctx(res.tenant.id, res.admin_user.id)


def test_course_enrollment_lifecycle(session_factory):
    ctx = _bootstrap(session_factory)
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        course = CourseService(s, ctx).create(code="C1", title="Coconut Agronomy")
        en_svc = EnrollmentService(s, ctx)
        enrollment = en_svc.enroll(course_id=course.id, learner_id=ctx.user_id)
        assert enrollment.status == "enrolled"
        en_svc.transition(enrollment.id, "start")
        completed = en_svc.transition(enrollment.id, "complete")
        assert completed.status == "completed"
        assert completed.completed_at is not None
        s.commit()


def test_support_ticket_flow(session_factory):
    ctx = _bootstrap(session_factory, slug="supportco")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        svc = SupportTicketService(s, ctx)
        ticket = svc.create(code="T1", subject="Login fails", priority="high")
        svc.add_comment(ticket_id=ticket.id, body="Investigating.")
        svc.assign(ticket.id, ctx.user_id)
        resolved = svc.transition(ticket.id, "resolve")
        assert resolved.status == "resolved"
        assert resolved.resolved_at is not None
        closed = svc.transition(ticket.id, "close")
        assert closed.status == "closed"
        assert len(svc.comments(ticket.id)) == 1
        s.commit()


def test_bad_ticket_priority_rejected(session_factory):
    ctx = _bootstrap(session_factory, slug="supportco2")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        with pytest.raises(BusinessRuleError):
            SupportTicketService(s, ctx).create(code="T", subject="x", priority="bogus")


def test_expert_engagement_lifecycle_and_fee(session_factory):
    ctx = _bootstrap(session_factory, slug="expertco")
    with session_factory() as s:
        _bind(s, ctx.tenant_id)
        expert = ExpertProfileService(s, ctx).create(
            code="E1", name="Dr. Reyes", expertise_area="Soil Science",
            rate=Money.from_decimal("1500.00", "PHP"),
        )
        eng_svc = EngagementService(s, ctx)
        engagement = eng_svc.create(code="ENG1", expert_id=expert.id,
                                    subject="Soil assessment",
                                    fee=Money.from_decimal("5000.00", "PHP"))
        assert eng_svc.fee(engagement.id).amount_minor == 500000  # 5000.00 PHP
        eng_svc.transition(engagement.id, "accept")
        eng_svc.transition(engagement.id, "deliver")
        closed = eng_svc.transition(engagement.id, "close")
        assert closed.status == "closed"
        s.commit()


def test_enablement_tenant_isolation(session_factory):
    with session_factory() as s:
        a = provision_tenant(s, slug="ena", name="A", admin_email="a@ena.test",
                             admin_password="supersecret123")
        b = provision_tenant(s, slug="enb", name="B", admin_email="a@enb.test",
                             admin_password="supersecret123")
        s.commit()
        a_id, a_admin, b_id = a.tenant.id, a.admin_user.id, b.tenant.id
    ctx_a = _ctx(a_id, a_admin)
    with session_factory() as s:
        _bind(s, a_id)
        SupportTicketService(s, ctx_a).create(code="SECRET", subject="A-only ticket")
        s.commit()
    with session_factory() as s:
        _bind(s, b_id)
        assert TenantRepository(s, SupportTicket, b_id).list().total == 0
