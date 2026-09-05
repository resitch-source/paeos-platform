import datetime as dt
import uuid

import pytest

from paeos_fx.core.errors import AuthenticationError
from paeos_fx.core.security import (
    PasswordHasher,
    create_access_token,
    decode_access_token,
)

pytestmark = pytest.mark.unit

SECRET = "test-secret-not-for-production-000000000000000000"


def test_password_hash_roundtrip():
    hasher = PasswordHasher()
    hashed = hasher.hash("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert hasher.verify("correct horse battery staple", hashed)
    assert not hasher.verify("wrong password", hashed)


def test_access_token_roundtrip():
    tid = uuid.uuid4()
    sub = uuid.uuid4()
    token = create_access_token(
        subject=sub, tenant_id=tid, permissions=["iam.user.read"], secret=SECRET
    )
    claims = decode_access_token(token, secret=SECRET)
    assert claims["sub"] == str(sub)
    assert claims["tid"] == str(tid)
    assert claims["perms"] == ["iam.user.read"]


def test_expired_token_raises():
    past = dt.datetime.now(dt.UTC) - dt.timedelta(hours=2)
    token = create_access_token(
        subject="u", tenant_id=None, secret=SECRET, ttl_seconds=1, now=past
    )
    with pytest.raises(AuthenticationError):
        decode_access_token(token, secret=SECRET)


def test_tampered_token_raises():
    token = create_access_token(subject="u", tenant_id=None, secret=SECRET)
    with pytest.raises(AuthenticationError):
        decode_access_token(
            token + "x", secret="different-secret-0000000000000000000000"
        )
