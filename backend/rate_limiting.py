"""
🚀 SPRINT 1.2 - Advanced Rate Limiting System
Enterprise-grade rate limiting with Redis backend and tenant-aware limits
"""

import asyncio
import time
from typing import Dict, Tuple, Optional, Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
from datetime import datetime, timedelta
import json
import hashlib

from structured_logger import structured_logger, EventCategory


class AdvancedRateLimiter:
    """
    Advanced Rate Limiter with Redis backend
    Supports multiple rate limiting strategies and tenant-aware limits
    """
    
    # Flag para evitar tentativas repetidas de conexão ao Redis quando não disponível
    _redis_connection_failed = False
    _last_redis_attempt = 0
    _redis_retry_interval = 300  # Tentar reconectar ao Redis a cada 5 minutos
    
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        """Initialize with Redis connection for rate limiting data"""
        self.redis_url = redis_url
        self._redis_client = None
        
        # Rate limiting rules (requests per time window in seconds)
        self.rules = {
            # Authentication endpoints - Critical protection
            "auth_login": {"limit": 5, "window": 60, "description": "Login attempts per minute per IP"},
            "auth_register": {"limit": 3, "window": 60, "description": "Register attempts per minute per IP"},
            
            # API endpoints by user role
            "api_user": {"limit": 100, "window": 60, "description": "API calls per minute per user"},
            "api_admin": {"limit": 200, "window": 60, "description": "API calls per minute per admin"},
            "api_super_admin": {"limit": 500, "window": 60, "description": "API calls per minute per super admin"},
            
            # Public endpoints (no auth required)
            "public": {"limit": 20, "window": 60, "description": "Public API per minute per IP"},
            
            # Bulk operations - Special limits
            "whatsapp_bulk": {"limit": 10, "window": 300, "description": "Bulk WhatsApp per 5min per user"},
            "export_data": {"limit": 5, "window": 300, "description": "Data export per 5min per user"},
        }
    
    async def get_redis_client(self) -> redis.Redis:
        """Get Redis client with connection pooling - with smart retry logic"""
        import time as time_module
        current_time = time_module.time()
        
        # Se Redis já falhou, não tentar novamente por um tempo
        if AdvancedRateLimiter._redis_connection_failed:
            if current_time - AdvancedRateLimiter._last_redis_attempt < AdvancedRateLimiter._redis_retry_interval:
                return None  # Retorna imediatamente sem tentar conexão
            # Tempo de retry passou, tentar novamente
            AdvancedRateLimiter._redis_connection_failed = False
        
        if not self._redis_client:
            try:
                AdvancedRateLimiter._last_redis_attempt = current_time
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    max_connections=20,
                    retry_on_timeout=False,  # Não retry em timeout para evitar demora
                    socket_connect_timeout=1,  # Timeout de 1 segundo para conexão
                    socket_timeout=1  # Timeout de 1 segundo para operações
                )
                # Test connection com timeout curto
                await asyncio.wait_for(self._redis_client.ping(), timeout=1.0)
                structured_logger.info(
                    EventCategory.SYSTEM,
                    "rate_limiter_redis_connected",
                    "Rate limiter connected to Redis successfully"
                )
            except Exception as e:
                structured_logger.warning(
                    EventCategory.SYSTEM,
                    "rate_limiter_redis_unavailable",
                    f"Redis not available, using in-memory fallback: {str(e)}"
                )
                # Marcar como falha para não tentar novamente
                AdvancedRateLimiter._redis_connection_failed = True
                self._redis_client = None
        
        return self._redis_client
    
    def get_client_identifier(self, request: Request) -> str:
        """
        Get client identifier for rate limiting
        Priority: User ID > API Key > IP Address
        """
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Try to get API key from headers
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # Hash API key for privacy
            hashed_key = hashlib.md5(api_key.encode()).hexdigest()[:16]
            return f"api_key:{hashed_key}"
        
        # Fall back to IP address
        # Handle potential proxy headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            ip = forwarded_for.split(',')[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def get_rate_rule(self, request: Request) -> str:
        """
        Determine which rate limiting rule to apply based on request
        """
        path = request.url.path
        method = request.method
        
        # Authentication endpoints
        if path == "/api/auth/login" and method == "POST":
            return "auth_login"
        elif path == "/api/auth/register" and method == "POST":
            return "auth_register"
        
        # Check if user is authenticated
        user_role = getattr(request.state, 'user_role', None)
        if user_role:
            # Bulk operations
            if "bulk" in path or "export" in path:
                if "whatsapp" in path:
                    return "whatsapp_bulk"
                else:
                    return "export_data"
            
            # Role-based API limits
            if user_role == "super_admin":
                return "api_super_admin"
            elif user_role == "admin":
                return "api_admin"
            else:
                return "api_user"
        
        # Public endpoints (no authentication)
        return "public"
    
    async def is_allowed(self, request: Request) -> Tuple[bool, Dict]:
        """
        Check if request is allowed based on rate limits
        Returns: (is_allowed, rate_limit_info)
        """
        client_id = self.get_client_identifier(request)
        rule_name = self.get_rate_rule(request)
        rule = self.rules[rule_name]
        
        redis_client = await self.get_redis_client()
        current_time = int(time.time())
        window_start = current_time - rule["window"]
        
        # Create unique key for this client + rule combination
        cache_key = f"rate_limit:{rule_name}:{client_id}"
        
        if redis_client:
            try:
                # Use Redis for distributed rate limiting
                pipe = redis_client.pipeline()
                
                # Remove old entries outside the window
                pipe.zremrangebyscore(cache_key, 0, window_start)
                
                # Count current requests in window
                pipe.zcard(cache_key)
                
                # Add current request timestamp
                pipe.zadd(cache_key, {str(current_time): current_time})
                
                # Set expiration on key
                pipe.expire(cache_key, rule["window"] + 60)  # Add buffer
                
                results = await pipe.execute()
                current_count = results[1] + 1  # +1 for current request
                
            except Exception as e:
                structured_logger.warning(
                    EventCategory.SECURITY,
                    "rate_limit_redis_fallback",
                    f"Redis rate limiting failed, allowing request: {str(e)}"
                )
                # Allow request if Redis fails (fail-open for availability) 
                return True, {
                    "limit": rule["limit"],
                    "remaining": rule["limit"],
                    "reset": current_time + rule["window"],
                    "window": rule["window"],
                    "rule": rule_name,
                    "client_id": client_id,
                    "current_count": 0
                }
        else:
            # In-memory fallback (not recommended for production)
            current_count = 0
        
        # Calculate rate limit info
        allowed = current_count <= rule["limit"]
        remaining = max(0, rule["limit"] - current_count)
        reset_time = current_time + rule["window"]
        
        rate_info = {
            "limit": rule["limit"],
            "remaining": remaining,
            "reset": reset_time,
            "window": rule["window"],
            "rule": rule_name,
            "client_id": client_id,
            "current_count": current_count
        }
        
        # Log rate limiting events
        if not allowed:
            structured_logger.warning(
                EventCategory.SECURITY,
                "rate_limit_exceeded",
                f"Rate limit exceeded for {client_id} on {rule_name}",
                details={
                    "client_id": client_id,
                    "rule": rule_name,
                    "limit": rule["limit"],
                    "current_count": current_count,
                    "window_seconds": rule["window"],
                    "path": request.url.path,
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent", "")[:100]
                }
            )
        
        return allowed, rate_info


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Rate Limiting Middleware for FastAPI
    Integrates with Advanced Rate Limiter
    """
    
    def __init__(self, app, redis_url: str = "redis://localhost:6379/1"):
        super().__init__(app)
        self.rate_limiter = AdvancedRateLimiter(redis_url)
        
        # Paths to exclude from rate limiting
        self.excluded_paths = {
            "/docs", "/redoc", "/openapi.json", 
            "/health", "/metrics", "/favicon.ico"
        }
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request through rate limiter"""
        
        # Skip rate limiting for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Check rate limit
        allowed, rate_info = await self.rate_limiter.is_allowed(request)
        
        if not allowed:
            # Return rate limit exceeded response
            headers = {
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(rate_info["reset"]),
                "X-RateLimit-Window": str(rate_info["window"]),
                "Retry-After": str(rate_info["window"])
            }
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {rate_info['limit']} per {rate_info['window']} seconds",
                    "limit": rate_info["limit"], 
                    "window": rate_info["window"],
                    "reset": rate_info["reset"],
                    "rule": rate_info["rule"]
                },
                headers=headers
            )
        
        # Process request normally
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
        response.headers["X-RateLimit-Window"] = str(rate_info["window"])
        
        return response


# Decorator for specific endpoints that need custom rate limits
def rate_limit(rule_name: str):
    """
    Decorator to apply specific rate limit rule to endpoint
    Usage: @rate_limit("custom_rule_name")
    """
    def decorator(func):
        # Mark function with rate limit rule
        func._rate_limit_rule = rule_name
        return func
    return decorator


# Helper function for manual rate limit checking
async def check_rate_limit(request: Request, rule_name: str = None) -> Dict:
    """
    Manual rate limit check for custom logic
    Returns rate limit info dictionary
    """
    rate_limiter = AdvancedRateLimiter()
    
    if rule_name:
        # Temporarily override rule for this check
        original_get_rule = rate_limiter.get_rate_rule
        rate_limiter.get_rate_rule = lambda req: rule_name
    
    allowed, rate_info = await rate_limiter.is_allowed(request)
    
    if rule_name:
        # Restore original rule method
        rate_limiter.get_rate_rule = original_get_rule
    
    return {
        "allowed": allowed,
        **rate_info
    }