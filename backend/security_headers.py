"""
Enterprise Security Headers Middleware
Implements comprehensive security headers following OWASP recommendations
"""
from fastapi import Request
from fastapi.responses import Response
from typing import Callable
import os

class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses
    Follows OWASP Secure Headers Guidelines
    """
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                # Add security headers
                headers = dict(message.get("headers", []))
                
                # Content Security Policy (CSP)
                csp_policy = self.get_csp_policy()
                headers[b"content-security-policy"] = csp_policy.encode()
                
                # HTTP Strict Transport Security (HSTS)
                headers[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                
                # X-Content-Type-Options
                headers[b"x-content-type-options"] = b"nosniff"
                
                # X-Frame-Options
                headers[b"x-frame-options"] = b"DENY"
                
                # Referrer Policy
                headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                
                # X-XSS-Protection (legacy but still useful)
                headers[b"x-xss-protection"] = b"1; mode=block"
                
                # Server header (remove version info)
                headers[b"server"] = b"LicenseManager"
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, receive, send_with_headers)
    
    def add_security_headers(self, response: Response) -> None:
        """Add all security headers to response"""
        
        # Content Security Policy (CSP)
        csp_policy = self.get_csp_policy()
        response.headers["Content-Security-Policy"] = csp_policy
        
        # HTTP Strict Transport Security (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # X-XSS-Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Permissions Policy (modern replacement for Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "accelerometer=(), "
            "gyroscope=()"
        )
        
        # Cross-Origin Embedder Policy
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        
        # Cross-Origin Opener Policy
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        
        # Cross-Origin Resource Policy
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        
        # Server header (remove version info)
        response.headers["Server"] = "LicenseManager"
        
        # Cache Control for security-sensitive endpoints
        if self.is_sensitive_endpoint(response):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
    
    def get_csp_policy(self) -> str:
        """
        Generate Content Security Policy
        Customize based on environment and needs
        """
        environment = os.getenv("ENVIRONMENT", "development")
        
        if environment == "development":
            # More permissive CSP for development
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' http://localhost:* ws://localhost:*; "
                "frame-src 'none'; "
                "object-src 'none'; "
                "base-uri 'self';"
            )
        else:
            # Strict CSP for production
            return (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-src 'none'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "upgrade-insecure-requests;"
            )
    
    def is_sensitive_endpoint(self, response: Response) -> bool:
        """
        Determine if the response is from a security-sensitive endpoint
        """
        # Get the response headers to check content type
        content_type = response.headers.get("content-type", "")
        
        # Apply strict caching policies to API responses
        return "application/json" in content_type

# Rate limiting middleware
class RateLimitMiddleware:
    """
    Simple rate limiting middleware for security-sensitive endpoints
    """
    
    def __init__(self, app):
        self.app = app
        self.request_counts = {}  # In production, use Redis
        self.rate_limits = {
            "/api/auth/login": {"requests": 5, "window": 300},  # 5 requests per 5 minutes
            "/api/auth/register": {"requests": 3, "window": 600},  # 3 requests per 10 minutes
            "/api/users": {"requests": 100, "window": 60},  # 100 requests per minute
            "/api/licenses": {"requests": 200, "window": 60},  # 200 requests per minute
        }
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        from fastapi import Request
        request = Request(scope, receive)
        
        async def call_next(request):
            return await self.app(scope, receive, send)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # Check if path needs rate limiting
        if self.should_rate_limit(path):
            if self.is_rate_limited(client_ip, path):
                from starlette.responses import JSONResponse
                response = JSONResponse(
                    content={"error": "Rate limit exceeded"},
                    status_code=429
                )
                await response(scope, receive, send)
                return
        
        # Process request normally
        await self.app(scope, receive, send)
    
    def should_rate_limit(self, path: str) -> bool:
        """Check if path should be rate limited"""
        return any(path.startswith(rate_path) for rate_path in self.rate_limits.keys())
    
    def is_rate_limited(self, client_ip: str, path: str) -> bool:
        """Check if client is rate limited for the path"""
        import time
        
        # Find matching rate limit configuration
        rate_config = None
        for rate_path, config in self.rate_limits.items():
            if path.startswith(rate_path):
                rate_config = config
                break
        
        if not rate_config:
            return False
        
        current_time = int(time.time())
        window_start = current_time - rate_config["window"]
        
        # Clean old entries
        key = f"{client_ip}:{path}"
        if key in self.request_counts:
            self.request_counts[key] = [
                timestamp for timestamp in self.request_counts[key]
                if timestamp > window_start
            ]
        else:
            self.request_counts[key] = []
        
        # Check if limit exceeded
        if len(self.request_counts[key]) >= rate_config["requests"]:
            return True
        
        # Add current request
        self.request_counts[key].append(current_time)
        return False
    
    def add_rate_limit_headers(self, response: Response, client_ip: str, path: str) -> None:
        """Add rate limit headers to response"""
        # Find matching rate limit configuration
        rate_config = None
        for rate_path, config in self.rate_limits.items():
            if path.startswith(rate_path):
                rate_config = config
                break
        
        if rate_config:
            key = f"{client_ip}:{path}"
            remaining = max(0, rate_config["requests"] - len(self.request_counts.get(key, [])))
            
            response.headers["X-RateLimit-Limit"] = str(rate_config["requests"])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(rate_config["window"])