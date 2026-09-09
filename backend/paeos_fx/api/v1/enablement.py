"""Training + Technical Support + Expert Marketplace endpoints (Phase 9)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from paeos_fx.api.deps import get_current_context, get_tenant_db, require_permission
from paeos_fx.api.v1.schemas import PageMeta
from paeos_fx.api.v1.schemas_enablement import (
    CourseCreate,
    CourseResponse,
    EngagementCreate,
    EngagementResponse,
    EnrollmentCreate,
    EnrollmentResponse,
    ExpertProfileCreate,
    ExpertProfileResponse,
    MoneyResponse,
    TicketAssignRequest,
    TicketCommentCreate,
    TicketCommentResponse,
    TicketCreate,
    TicketResponse,
    TransitionRequest,
)
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.pagination import PageParams
from paeos_fx.experts.service import EngagementService, ExpertProfileService
from paeos_fx.platform import permissions as perms
from paeos_fx.platform.currency import Money
from paeos_fx.pydantic_page import Paged
from paeos_fx.support.service import SupportTicketService
from paeos_fx.training.service import CourseService, EnrollmentService

router = APIRouter(tags=["training-support-experts"])


# --- Training: courses ---
@router.post(
    "/training/courses", response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.TRAINING_COURSE_MANAGE))],
)
def create_course(
    body: CourseCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> CourseResponse:
    course = CourseService(db, ctx).create(
        code=body.code, title=body.title, description=body.description,
        category=body.category,
    )
    return CourseResponse.model_validate(course)


@router.get(
    "/training/courses", response_model=Paged[CourseResponse],
    dependencies=[Depends(require_permission(perms.TRAINING_COURSE_READ))],
)
def list_courses(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[CourseResponse]:
    res = CourseService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[CourseResponse](
        items=[CourseResponse.model_validate(x) for x in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


# --- Training: enrollments ---
@router.post(
    "/training/enrollments", response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.TRAINING_ENROLLMENT_WRITE))],
)
def create_enrollment(
    body: EnrollmentCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> EnrollmentResponse:
    enrollment = EnrollmentService(db, ctx).enroll(
        course_id=body.course_id, learner_id=body.learner_id,
    )
    return EnrollmentResponse.model_validate(enrollment)


@router.post(
    "/training/enrollments/{enrollment_id}/transition",
    response_model=EnrollmentResponse,
    dependencies=[Depends(require_permission(perms.TRAINING_ENROLLMENT_WRITE))],
)
def transition_enrollment(
    enrollment_id: uuid.UUID, body: TransitionRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> EnrollmentResponse:
    enrollment = EnrollmentService(db, ctx).transition(enrollment_id, body.event)
    return EnrollmentResponse.model_validate(enrollment)


# --- Technical support: tickets ---
@router.post(
    "/support/tickets", response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.SUPPORT_TICKET_WRITE))],
)
def create_ticket(
    body: TicketCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> TicketResponse:
    ticket = SupportTicketService(db, ctx).create(
        code=body.code, subject=body.subject, body=body.body, priority=body.priority,
    )
    return TicketResponse.model_validate(ticket)


@router.get(
    "/support/tickets", response_model=Paged[TicketResponse],
    dependencies=[Depends(require_permission(perms.SUPPORT_TICKET_READ))],
)
def list_tickets(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[TicketResponse]:
    res = SupportTicketService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[TicketResponse](
        items=[TicketResponse.model_validate(x) for x in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


@router.post(
    "/support/tickets/{ticket_id}/assign", response_model=TicketResponse,
    dependencies=[Depends(require_permission(perms.SUPPORT_TICKET_WRITE))],
)
def assign_ticket(
    ticket_id: uuid.UUID, body: TicketAssignRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> TicketResponse:
    ticket = SupportTicketService(db, ctx).assign(ticket_id, body.assignee_id)
    return TicketResponse.model_validate(ticket)


@router.post(
    "/support/tickets/{ticket_id}/transition", response_model=TicketResponse,
    dependencies=[Depends(require_permission(perms.SUPPORT_TICKET_RESOLVE))],
)
def transition_ticket(
    ticket_id: uuid.UUID, body: TransitionRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> TicketResponse:
    ticket = SupportTicketService(db, ctx).transition(ticket_id, body.event)
    return TicketResponse.model_validate(ticket)


@router.post(
    "/support/tickets/{ticket_id}/comments", response_model=TicketCommentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.SUPPORT_TICKET_WRITE))],
)
def add_ticket_comment(
    ticket_id: uuid.UUID, body: TicketCommentCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> TicketCommentResponse:
    comment = SupportTicketService(db, ctx).add_comment(ticket_id=ticket_id, body=body.body)
    return TicketCommentResponse.model_validate(comment)


# --- Expert marketplace (financial: gate #12) ---
@router.post(
    "/experts/profiles", response_model=ExpertProfileResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.EXPERTS_PROFILE_MANAGE))],
)
def create_expert_profile(
    body: ExpertProfileCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> ExpertProfileResponse:
    rate = Money.from_decimal(body.rate, body.currency) if body.rate is not None else None
    profile = ExpertProfileService(db, ctx).create(
        code=body.code, name=body.name, expertise_area=body.expertise_area,
        bio=body.bio, rate=rate, user_id=body.user_id,
    )
    return ExpertProfileResponse.model_validate(profile)


@router.get(
    "/experts/profiles", response_model=Paged[ExpertProfileResponse],
    dependencies=[Depends(require_permission(perms.EXPERTS_PROFILE_READ))],
)
def list_expert_profiles(
    page: int = 1, size: int = 25,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> Paged[ExpertProfileResponse]:
    res = ExpertProfileService(db, ctx).list(PageParams(page=page, size=size))
    return Paged[ExpertProfileResponse](
        items=[ExpertProfileResponse.model_validate(x) for x in res.items],
        meta=PageMeta(total=res.total, page=res.page, size=res.size, pages=res.pages),
    )


@router.post(
    "/experts/engagements", response_model=EngagementResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(perms.EXPERTS_ENGAGEMENT_WRITE))],
)
def create_engagement(
    body: EngagementCreate,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> EngagementResponse:
    fee = Money.from_decimal(body.fee, body.currency)
    engagement = EngagementService(db, ctx).create(
        code=body.code, expert_id=body.expert_id, subject=body.subject, fee=fee,
    )
    return EngagementResponse.model_validate(engagement)


@router.get(
    "/experts/engagements/{engagement_id}/fee", response_model=MoneyResponse,
    dependencies=[Depends(require_permission(perms.EXPERTS_ENGAGEMENT_READ))],
)
def engagement_fee(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> MoneyResponse:
    fee = EngagementService(db, ctx).fee(engagement_id)
    return MoneyResponse(amount_minor=fee.amount_minor, currency=fee.currency,
                         amount=fee.to_decimal())


@router.post(
    "/experts/engagements/{engagement_id}/transition", response_model=EngagementResponse,
    dependencies=[Depends(require_permission(perms.EXPERTS_ENGAGEMENT_WRITE))],
)
def transition_engagement(
    engagement_id: uuid.UUID, body: TransitionRequest,
    db: Session = Depends(get_tenant_db),
    ctx: ExecutionContext = Depends(get_current_context),
) -> EngagementResponse:
    engagement = EngagementService(db, ctx).transition(engagement_id, body.event)
    return EngagementResponse.model_validate(engagement)
