"""Generic paged API response wrapper (Phase 1)."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

from paeos_fx.api.v1.schemas import PageMeta

T = TypeVar("T")


class Paged(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMeta
