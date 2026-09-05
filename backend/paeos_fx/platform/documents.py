"""Documents / files foundation (section N).

Document metadata model + a pluggable storage backend interface. The foundation
ships a local-filesystem backend for development; S3-compatible object storage
plugs in behind :class:`StorageBackend` in later phases. A virus-scan hook point
is defined but not wired to any engine.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Protocol

from sqlalchemy import BigInteger, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import AuditMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Document(UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, Base):
    """Tenant-scoped document metadata; bytes live in the storage backend."""

    __tablename__ = "document"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(127), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)


class StorageBackend(Protocol):
    def put(self, key: str, data: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


class LocalStorageBackend:
    """Filesystem storage for development. Keys are tenant-namespaced by caller."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Prevent path traversal outside the storage root.
        p = (self.root / key).resolve()
        if not str(p).startswith(str(self.root.resolve())):
            raise ValueError("Invalid storage key (path traversal).")
        return p

    def put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


class VirusScanner(Protocol):
    """Hook point for content scanning; no engine wired at the foundation."""

    def is_clean(self, data: bytes) -> bool: ...
