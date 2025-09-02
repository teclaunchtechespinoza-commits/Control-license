import base64, json, time, os, pytest

JWT_SECRET = os.getenv("JWT_SECRET", "test-secret-please-change")
JWT_ALG = os.getenv("JWT_ALG", "HS256")

def _jwt(payload: dict, secret=JWT_SECRET):
    header = {"alg": "HS256", "typ": "JWT"}
    def b64(x): 
        import json, base64
        return base64.urlsafe_b64encode(json.dumps(x, separators=(",",":")).encode()).rstrip(b"=")
    import hmac, hashlib
    seg1 = b64(header); seg2 = b64(payload)
    signing = seg1 + b"." + seg2
    sig = __import__("base64").urlsafe_b64encode(
        __import__("hmac").new(secret.encode(), signing, __import__("hashlib").sha256).digest()
    ).rstrip(b"=")
    return (signing + b"." + sig).decode()

def _token(tenant_id, role, sub="u1", email="u1@test"):
    now = int(time.time())
    payload = {
        "sub": sub, "email": email, "tenant_id": tenant_id, "role": role,
        "iat": now, "exp": now + 3600, "iss": "licenser-api", "aud": "licenser-clients"
    }
    return _jwt(payload)

ROTA_ADMIN_DELETE = "/licenses/LIC-001"  # ajuste para uma rota admin

@pytest.mark.asyncio
async def test_rbac_admin_ok(client, tenant_id):
    token = _token(tenant_id, "admin")
    r = await client.delete(ROTA_ADMIN_DELETE, headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    assert r.status_code not in (401, 403), r.text

@pytest.mark.asyncio
async def test_rbac_user_bloqueado_para_admin(client, tenant_id):
    token = _token(tenant_id, "user")
    r = await client.delete(ROTA_ADMIN_DELETE, headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    assert r.status_code in (401, 403), r.text

@pytest.mark.asyncio
async def test_rbac_tenant_mismatch(client, tenant_id):
    token_outro = _token("outro-tenant", "admin")
    r = await client.delete(ROTA_ADMIN_DELETE, headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token_outro}"})
    assert r.status_code in (401, 403)
