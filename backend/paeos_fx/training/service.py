"""Training services (Phase 9).

Course catalog CRUD and enrollment lifecycle. Records only — completion is a
recorded state transition, not a fabricated assessment/score.
"""

from __future__ import annotations

import datetime as dt
import uuid

from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.platform.repository import TenantRepository
from paeos_fx.platform.service import DomainService
from paeos_fx.training.models import ENROLLMENT_WORKFLOW, Course, Enrollment


class CourseService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[Course] = TenantRepository(
            session, Course, self.tenant_id
        )

    def create(self, *, code: str, title: str, description: str = "",
               category: str = "") -> Course:
        course = Course(code=code, title=title, description=description,
                        category=category, status="active")
        self.repo.add(course)
        self._record(action="course.create", entity_type="Course",
                     entity_id=str(course.id), after={"code": code})
        return course

    def set_status(self, course_id: uuid.UUID, status: str) -> Course:
        if status not in {"active", "archived"}:
            raise BusinessRuleError("Invalid course status.")
        course = self.repo.get_or_404(course_id)
        course.status = status
        self.session.flush()
        return course

    def get(self, course_id: uuid.UUID) -> Course:
        return self.repo.get_or_404(course_id)

    def list(self, params=None):
        return self.repo.list(params)


class EnrollmentService(DomainService):
    def __init__(self, session, ctx: ExecutionContext):
        super().__init__(session, ctx)
        self.repo: TenantRepository[Enrollment] = TenantRepository(
            session, Enrollment, self.tenant_id
        )
        self.courses: TenantRepository[Course] = TenantRepository(
            session, Course, self.tenant_id
        )

    def enroll(self, *, course_id: uuid.UUID, learner_id: uuid.UUID) -> Enrollment:
        self.courses.get_or_404(course_id)
        enrollment = Enrollment(course_id=course_id, learner_id=learner_id,
                                status=ENROLLMENT_WORKFLOW.initial)
        self.repo.add(enrollment)
        self._record(action="enrollment.create", entity_type="Enrollment",
                     entity_id=str(enrollment.id),
                     after={"course_id": str(course_id), "learner_id": str(learner_id)})
        return enrollment

    def transition(self, enrollment_id: uuid.UUID, event: str) -> Enrollment:
        enrollment = self.repo.get_or_404(enrollment_id)
        before = enrollment.status
        enrollment.status = ENROLLMENT_WORKFLOW.fire(enrollment.status, event)
        if enrollment.status == "completed":
            enrollment.completed_at = dt.datetime.now(dt.UTC)
        self.session.flush()
        self._record(action=f"enrollment.{event}", entity_type="Enrollment",
                     entity_id=str(enrollment_id),
                     before={"status": before}, after={"status": enrollment.status})
        return enrollment

    def list(self, params=None):
        return self.repo.list(params)
