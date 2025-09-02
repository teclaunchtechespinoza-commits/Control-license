import pytest
from types import SimpleNamespace
from authz import build_scope_filter, enforce_object_scope, Role

def mk_user(role, tid="t1", uid="u1"):
    return SimpleNamespace(role=role, tenant_id=tid, id=uid)

def test_scope_superadmin_no_limits():
    u = mk_user(Role.SUPER_ADMIN, tid=None)
    q = build_scope_filter(u, {})
    assert "tenant_id" not in q

def test_scope_admin_limits_to_tenant_and_seller():
    u = mk_user(Role.ADMIN, tid="t1", uid="a1")
    q = build_scope_filter(u, {})
    assert q["tenant_id"] == "t1"
    assert q["seller_admin_id"] == "a1"

def test_scope_user_limits_to_tenant_and_assigned():
    u = mk_user(Role.USER, tid="t1", uid="x1")
    q = build_scope_filter(u, {})
    assert q["tenant_id"] == "t1"
    assert q["assigned_user_id"] == "x1"

def test_enforce_object_scope_admin_true():
    u = mk_user(Role.ADMIN, tid="t1", uid="a1")
    obj = {"tenant_id": "t1", "seller_admin_id": "a1"}
    assert enforce_object_scope(obj, u) is True

def test_enforce_object_scope_admin_false_other_seller():
    u = mk_user(Role.ADMIN, tid="t1", uid="a1")
    obj = {"tenant_id": "t1", "seller_admin_id": "a2"}
    assert enforce_object_scope(obj, u) is False

def test_enforce_object_scope_user_true():
    u = mk_user(Role.USER, tid="t1", uid="u1")
    obj = {"tenant_id": "t1", "assigned_user_id": "u1"}
    assert enforce_object_scope(obj, u) is True

def test_enforce_object_scope_user_false_other_owner():
    u = mk_user(Role.USER, tid="t1", uid="u1")
    obj = {"tenant_id": "t1", "assigned_user_id": "u2"}
    assert enforce_object_scope(obj, u) is False

def test_enforce_object_scope_different_tenant():
    u = mk_user(Role.ADMIN, tid="t1", uid="a1")
    obj = {"tenant_id": "t2", "seller_admin_id": "a1"}
    assert enforce_object_scope(obj, u) is False