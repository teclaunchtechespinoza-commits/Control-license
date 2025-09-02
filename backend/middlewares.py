from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, status
import time

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
    Copia o header de tenant do request para a resposta usando o nome padronizado 'X-Tenant-ID'.
    Não faz fallback automático para 'default'; se ausente, deixa a view/dependency (require_tenant)
    decidir o que fazer (por ex., retornar 400).
    """
    TENANT_HEADER = "X-Tenant-ID"

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        tenant_id = request.headers.get(self.TENANT_HEADER)
        if tenant_id:
            response.headers[self.TENANT_HEADER] = tenant_id
        return response