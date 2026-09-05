import uuid

import pytest

from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import AuthorizationError
from paeos_fx.platform.iam import AccessControl

pytestmark = pytest.mark.unit


def test_require_tenant_missing():
    ctx = ExecutionContext()
    with pytest.raises(PermissionError):
        ctx.require_tenant()


def test_with_tenant_and_user():
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    ctx = ExecutionContext().with_tenant(tid).with_user(uid, frozenset({"p.read"}))
    assert ctx.require_tenant() == tid
    assert ctx.user_id == uid


def test_access_control_permission_check():
    ctx = ExecutionContext(permissions=frozenset({"iam.user.read"}))
    assert AccessControl.has_permission(ctx, "iam.user.read")
    AccessControl.require(ctx, "iam.user.read")  # no raise
    with pytest.raises(AuthorizationError):
        AccessControl.require(ctx, "iam.user.write")
