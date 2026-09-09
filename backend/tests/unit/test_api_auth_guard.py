"""Auth/authorization guard tests that do not require a database.

401 (no/invalid token) and 403 (missing permission) are enforced by the request
pipeline before any tenant DB session is opened, so these run in the unit suite.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from paeos_fx.core.config import Settings
from paeos_fx.core.security import create_access_token
from paeos_fx.main import create_app
from paeos_fx.platform import permissions as perms

pytestmark = pytest.mark.unit

SECRET = "unit-test-secret-000000000000000000000000"


@pytest.fixture()
def settings() -> Settings:
    return Settings(environment="test", jwt_secret=SECRET)


@pytest.fixture()
def client(settings) -> TestClient:
    return TestClient(create_app(settings))


def _token(perms_list, settings, tenant_id=None, sub=None) -> str:
    return create_access_token(
        subject=sub or uuid.uuid4(),
        tenant_id=tenant_id or uuid.uuid4(),
        permissions=perms_list,
        secret=settings.jwt_secret,
        ttl_seconds=3600,
    )


def test_protected_endpoint_requires_token(client):
    resp = client.get("/api/v1/users")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "authentication_error"


def test_invalid_token_rejected(client):
    resp = client.get(
        "/api/v1/users", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert resp.status_code == 401


def test_missing_permission_forbidden(client, settings):
    # Valid token but without iam.user.read -> 403 before any DB access.
    token = _token([], settings)
    resp = client.get(
        "/api/v1/users", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "authorization_error"
    assert resp.json()["error"]["details"]["required_permission"] == perms.IAM_USER_READ


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_returns_identity(client, settings):
    tid, uid = uuid.uuid4(), uuid.uuid4()
    token = _token([perms.IAM_USER_READ], settings, tenant_id=tid, sub=uid)
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == str(uid)
    assert body["tenant_id"] == str(tid)
    assert perms.IAM_USER_READ in body["permissions"]
