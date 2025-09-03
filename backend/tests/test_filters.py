from filters import whitelist_filter, merge_with_scope

def test_whitelist_filter_blocks_operators():
    payload = {"$where": "this.a == 1", "email": "x@y.com", "$ne": 1, "role": "USER"}
    out = whitelist_filter(payload, ["email", "role"])
    assert "$where" not in out
    assert "$ne" not in out
    assert out["email"] == "x@y.com"
    assert out["role"] == "USER"

def test_whitelist_filter_blocks_non_allowed_fields():
    payload = {"email": "x@y.com", "tenant_id": "t1", "foo": "bar"}
    out = whitelist_filter(payload, ["email", "tenant_id"])
    assert "email" in out
    assert "tenant_id" in out
    assert "foo" not in out

def test_merge_with_scope_overrides_client_filter():
    scope = {"tenant_id": "t1", "seller_admin_id": "a1"}
    client = {"tenant_id": "t2", "seller_admin_id": "hack", "email": "x@y.com"}
    out = merge_with_scope(scope, client)
    assert out["tenant_id"] == "t1"
    assert out["seller_admin_id"] == "a1"
    assert out["email"] == "x@y.com"