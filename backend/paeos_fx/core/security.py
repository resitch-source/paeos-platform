"""Security primitives (sections E/AB): password hashing and JWT.

- Passwords: Argon2id via argon2-cffi.
- Tokens: JWT (HS256 by default) with issued/expiry claims.

This is the *framework*. Authentication architecture is gated (ADR-0004);
concrete identity providers plug in behind :class:`PasswordHasher` and the
token helpers here.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

import jwt
from argon2 import PasswordHasher as _Argon2
from argon2.exceptions import VerifyMismatchError

from paeos_fx.core.errors import AuthenticationError

_hasher = _Argon2()


class PasswordHasher:
    """Argon2id password hashing wrapper."""

    def hash(self, password: str) -> str:
        return _hasher.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        try:
            return _hasher.verify(hashed, password)
        except VerifyMismatchError:
            return False

    def needs_rehash(self, hashed: str) -> bool:
        return _hasher.check_needs_rehash(hashed)


def create_access_token(
    *,
    subject: uuid.UUID | str,
    tenant_id: uuid.UUID | str | None,
    permissions: list[str] | None = None,
    secret: str,
    algorithm: str = "HS256",
    ttl_seconds: int = 3600,
    now: dt.datetime | None = None,
) -> str:
    """Create a signed access token. Never embeds secrets in the payload."""
    issued = now or dt.datetime.now(dt.UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "tid": str(tenant_id) if tenant_id is not None else None,
        "perms": permissions or [],
        "iat": int(issued.timestamp()),
        "exp": int((issued + dt.timedelta(seconds=ttl_seconds)).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_access_token(
    token: str, *, secret: str, algorithms: list[str] | None = None
) -> dict[str, Any]:
    """Decode and verify a token, raising :class:`AuthenticationError` on failure."""
    try:
        return jwt.decode(token, secret, algorithms=algorithms or ["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid authentication token.") from exc
