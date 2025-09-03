import pytest
from types import SimpleNamespace
from authz import enforce_object_scope, Role

def mk_user(role, tid="t1", uid="u1"):
    return SimpleNamespace(role=role, tenant_id=tid, id=uid)

def test_object_scope_superadmin_ok():
    su = mk_user(Role.SUPER_ADMIN, tid=None, uid="root")
    obj = {"tenant_id": "tX", "seller_admin_id": "a1", "assigned_user_id": "u123"}
    assert enforce_object_scope(obj, su) is True

def test_object_scope_admin_ok_same_seller():
    admin = mk_user(Role.ADMIN, tid="t1", uid="a1")
    obj = {"tenant_id": "t1", "seller_admin_id": "a1"}
    assert enforce_object_scope(obj, admin) is True

def test_object_scope_admin_block_other_seller():
    admin = mk_user(Role.ADMIN, tid="t1", uid="a1")
    obj = {"tenant_id": "t1", "seller_admin_id": "a2"}
    assert enforce_object_scope(obj, admin) is False

def test_object_scope_user_ok_self():
    user = mk_user(Role.USER, tid="t1", uid="u1")
    obj = {"tenant_id": "t1", "assigned_user_id": "u1"}
    assert enforce_object_scope(obj, user) is True

def test_object_scope_user_block_other():
    user = mk_user(Role.USER, tid="t1", uid="u1")
    obj = {"tenant_id": "t1", "assigned_user_id": "u2"}
    assert enforce_object_scope(obj, user) is False

def test_object_scope_wrong_tenant():
    admin = mk_user(Role.ADMIN, tid="t1", uid="a1")
    obj = {"tenant_id": "t2", "seller_admin_id": "a1"}
    assert enforce_object_scope(obj, admin) is False