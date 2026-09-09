"""Reusable repository layer (Phase 1 pattern).

``TenantRepository`` provides tenant-scoped CRUD over a mapped entity. It filters
every query by the current tenant id (defense in depth on top of Row-Level
Security), so cross-tenant access is blocked even if the DB connection role were
ever misconfigured. This is the base every domain phase reuses.
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from paeos_fx.core.errors import NotFoundError
from paeos_fx.core.pagination import Page, PageParams

# Managed entities are SQLAlchemy models carrying ``id`` and ``tenant_id``
# columns. They are accessed dynamically (column expressions live on the mapped
# class), so the type var is unbound and dynamic access is localized below.
T = TypeVar("T")


class TenantRepository(Generic[T]):
    """Tenant-scoped data access for a mapped model with a ``tenant_id`` column."""

    def __init__(self, session: Session, model: type[T], tenant_id: uuid.UUID):
        self.session = session
        self.model = model
        self.tenant_id = tenant_id
        self._m: Any = model  # mapped class for column expressions

    def _base_select(self):
        return select(self._m).where(self._m.tenant_id == self.tenant_id)

    def add(self, entity: T) -> T:
        # Guard: never persist an entity for a different tenant.
        e: Any = entity
        if getattr(entity, "tenant_id", None) not in (None, self.tenant_id):
            raise ValueError("Entity tenant_id does not match repository tenant.")
        e.tenant_id = self.tenant_id
        self.session.add(entity)
        self.session.flush()
        return entity

    def get(self, entity_id: uuid.UUID) -> T | None:
        stmt = self._base_select().where(self._m.id == entity_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_or_404(self, entity_id: uuid.UUID) -> T:
        entity = self.get(entity_id)
        if entity is None:
            raise NotFoundError(
                f"{self.model.__name__} not found.",
                details={"id": str(entity_id)},
            )
        return entity

    def list(self, params: PageParams | None = None) -> Page[T]:
        params = params or PageParams()
        count_stmt = (
            select(func.count())
            .select_from(self._m)
            .where(self._m.tenant_id == self.tenant_id)
        )
        total = self.session.execute(count_stmt).scalar_one()
        stmt = self._base_select().offset(params.offset).limit(params.limit)
        items = list(self.session.execute(stmt).scalars().all())
        return Page(items=items, total=total, page=params.page, size=params.size)

    def delete(self, entity: T) -> None:
        self.session.delete(entity)
        self.session.flush()
