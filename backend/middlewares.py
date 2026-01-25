from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, status
import time
import os
import contextvars

class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        try:
            response: Response = await call_next(request)
        finally:
            dur = (time.time() - start) * 1000.0
            # substitua por logger estruturado
            path = request.url.path
            method = request.method
            status_code = getattr(response, "status_code", 0)
            print(f"[obs] {method} {path} -> {status_code} ({dur:.1f}ms)")
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    # Implementação simples de rate limit por IP (coloque Redis em produção)
    _buckets = {}
    WINDOW_MS = 60_000
    LIMIT = 300
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"
        now = int(time.time() * 1000)
        bucket = self._buckets.get(ip, [])
        # limpa janelas antigas
        bucket = [t for t in bucket if now - t < self.WINDOW_MS]
        if len(bucket) >= self.LIMIT:
            from starlette.responses import JSONResponse
            return JSONResponse({"detail": "Too Many Requests"}, status_code=429)
        bucket.append(now)
        self._buckets[ip] = bucket
        return await call_next(request)

class ResponseTenantHeaderMiddleware(BaseHTTPMiddleware):
    """
    Espelha o header de tenant do request para a resposta usando o nome padronizado 'X-Tenant-ID'.
    Não faz fallback automático para 'default'; se ausente, deixa a dependency (require_tenant)
    decidir o que fazer (ex.: retornar 400).
    """
    TENANT_HEADER = "X-Tenant-ID"

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        tenant_id = request.headers.get(self.TENANT_HEADER)
        if tenant_id:
            response.headers[self.TENANT_HEADER] = tenant_id
        return response

# ----------------- Tenant Context (fallback seguro para add_tenant_filter) -----------------
TENANT_CTX: contextvars.ContextVar[str | None] = contextvars.ContextVar("TENANT_CTX", default=None)

class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Extrai X-Tenant-ID do request e guarda em ContextVar para ser usado como fallback
    por helpers que, historicamente, não recebiam tenant explicitamente.
    Produção: se X-Tenant-ID estiver ausente, retorna 400, exceto para endpoints públicos.
    """
    TENANT_HEADER = "X-Tenant-ID"
    
    # Endpoints que não requerem X-Tenant-ID header
    PUBLIC_ENDPOINTS = {
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/me",       # 🔐 Allow auth/me with cookies (tenant extracted from JWT)
        "/api/auth/refresh",  # 🔄 Allow refresh endpoint
        "/api/auth/logout",   # 🚪 Allow logout endpoint
        "/api/auth/forgot-password",     # 🔑 Password recovery - step 1
        "/api/auth/verify-recovery-code", # 🔑 Password recovery - step 2
        "/docs",
        "/openapi.json",
        "/health",
        "/api/health",
        "/",
        "/api/accept-invite"
    }

    def __init__(self, app):
        super().__init__(app)
        self._allow_missing = os.getenv("TENANT_HEADER_OPTIONAL", "false").lower() in {"1", "true", "yes"}

    def _is_public_endpoint(self, path: str) -> bool:
        """Verifica se o endpoint é público e não requer X-Tenant-ID"""
        return (
            path in self.PUBLIC_ENDPOINTS or
            path.startswith("/api/accept-invite") or
            path.startswith("/docs") or
            path.startswith("/openapi") or
            path.startswith("/static") or
            path == "/favicon.ico"
        )

    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get(self.TENANT_HEADER)
        TENANT_CTX.set(tenant_id)
        
        # Para endpoints públicos, não exigir X-Tenant-ID
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
            
        if not tenant_id and not self._allow_missing:
            # Não permita fallback silencioso em produção para endpoints privados
            return Response(
                content='{"detail":"X-Tenant-ID ausente"}',
                media_type="application/json",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return await call_next(request)