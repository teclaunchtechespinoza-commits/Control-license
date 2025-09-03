import os
import pytest

def test_cors_no_wildcard_with_credentials(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    # allow_credentials=True por padrão no server
    from importlib import reload
    import backend.server as srv
    reload(srv)
    assert "*" not in srv.CORS_ORIGINS

def test_tenant_header_constant():
    from backend.server import TENANT_HEADER
    assert TENANT_HEADER == "X-Tenant-ID"

def test_tenant_ctx_middleware_exports_header():
    # Teste superficial: apenas confere que o middleware existe e usa o mesmo header
    from backend.middlewares import TenantContextMiddleware
    mw = TenantContextMiddleware(lambda x: x)
    assert mw.TENANT_HEADER == "X-Tenant-ID"