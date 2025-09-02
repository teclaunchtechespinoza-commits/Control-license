from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
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