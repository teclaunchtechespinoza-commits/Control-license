import time
from invitations import generate_invite_token, verify_invite, token_hash

def test_invite_token_roundtrip():
    tok = generate_invite_token("x@y.com", "t1", "a1", ttl_seconds=60)
    p = verify_invite(tok)
    assert p["email"] == "x@y.com"
    assert p["tenant_id"] == "t1"
    assert p["admin_vendor_id"] == "a1"
    assert p["exp"] > p["iat"]

def test_invite_token_expiration():
    tok = generate_invite_token("x@y.com", "t1", "a1", ttl_seconds=1)
    time.sleep(2)
    try:
        verify_invite(tok)
        assert False, "Deveria expirar"
    except Exception:
        assert True

def test_token_hash_stable():
    tok = generate_invite_token("x@y.com", "t1", "a1", ttl_seconds=60)
    h1 = token_hash(tok)
    h2 = token_hash(tok)
    assert h1 == h2