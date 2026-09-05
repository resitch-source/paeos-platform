"""Search abstraction (section O).

A backend-agnostic search interface. The foundation default targets PostgreSQL
full-text search; an external engine (e.g. OpenSearch) can be introduced later
behind the same :class:`SearchBackend` protocol without changing callers. All
queries are tenant-scoped by contract.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class SearchQuery:
    tenant_id: uuid.UUID
    text: str
    entity_types: tuple[str, ...] = ()
    limit: int = 25
    filters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchHit:
    entity_type: str
    entity_id: str
    score: float
    highlight: str = ""


class SearchBackend(Protocol):
    def index(
        self, tenant_id: uuid.UUID, entity_type: str, entity_id: str, document: dict
    ) -> None: ...

    def search(self, query: SearchQuery) -> list[SearchHit]: ...


class InMemorySearchBackend:
    """Reference backend for tests and local dev (not for production)."""

    def __init__(self) -> None:
        self._docs: dict[tuple, dict] = {}

    def index(
        self, tenant_id: uuid.UUID, entity_type: str, entity_id: str, document: dict
    ) -> None:
        self._docs[(tenant_id, entity_type, entity_id)] = document

    def search(self, query: SearchQuery) -> list[SearchHit]:
        needle = query.text.lower().strip()
        hits: list[SearchHit] = []
        for (tid, etype, eid), doc in self._docs.items():
            if tid != query.tenant_id:
                continue  # tenant isolation
            if query.entity_types and etype not in query.entity_types:
                continue
            haystack = " ".join(str(v) for v in doc.values()).lower()
            if needle and needle in haystack:
                hits.append(SearchHit(etype, eid, score=1.0, highlight=needle))
        return hits[: query.limit]
