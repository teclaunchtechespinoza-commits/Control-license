#!/usr/bin/env python3
"""
Logging Middleware - FastAPI Integration for Structured Logging
Middleware para integração automática do sistema de logs estruturados
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from structured_logger import (
    RequestContext, structured_logger, EventCategory, 
    log_performance_metric, set_request_context
)
from tenant_system import get_current_tenant_id

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic request correlation and structured logging
    
    Features:
    - Auto-generate request IDs for correlation
    - Extract tenant_id and user context from requests  
    - Log all API requests with timing
    - Capture request/response metadata
    - Performance monitoring
    - Security event detection
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.excluded_paths = {
            '/docs', '/redoc', '/openapi.json', '/favicon.ico',
            '/health', '/ping'  # Health check endpoints
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with structured logging context"""
        
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Generate request correlation ID
        request_id = str(uuid.uuid4())
        
        # Extract context from request
        tenant_id = await self._extract_tenant_id(request)
        user_id, user_email = await self._extract_user_context(request)
        
        # Performance timing
        start_time = time.time()
        
        # Set logging context for the entire request
        with RequestContext(
            tenant_id=tenant_id,
            user_id=user_id,
            user_email=user_email
        ) as ctx:
            ctx.request_id = request_id
            
            # Log request start
            await self._log_request_start(request, request_id)
            
            try:
                # Process request
                response = await call_next(request)
                
                # Calculate timing
                duration_ms = (time.time() - start_time) * 1000
                
                # Log successful request completion
                await self._log_request_success(
                    request, response, request_id, duration_ms
                )
                
                # Log performance metrics for slow requests
                if duration_ms > 1000:  # > 1 second
                    log_performance_metric(
                        operation=f"{request.method} {request.url.path}",
                        duration_ms=duration_ms,
                        tenant_id=tenant_id,
                        details={
                            "slow_request": True,
                            "status_code": response.status_code
                        }
                    )
                
                return response
                
            except Exception as e:
                # Calculate timing for errors too
                duration_ms = (time.time() - start_time) * 1000
                
                # Log request error
                await self._log_request_error(
                    request, e, request_id, duration_ms
                )
                raise
    
    async def _extract_tenant_id(self, request: Request) -> str:
        """Extract tenant_id from request context"""
        try:
            # Try to get from tenant context (set by tenant middleware)
            tenant_id = get_current_tenant_id()
            if tenant_id:
                return tenant_id
            
            # Fallback to header or query param
            tenant_id = (
                request.headers.get('X-Tenant-ID') or
                request.query_params.get('tenant_id') or
                'default'
            )
            return tenant_id
            
        except Exception:
            return 'default'
    
    async def _extract_user_context(self, request: Request):
        """Extract user context from request"""
        try:
            # Try to get user from request state (set by auth middleware)
            user = getattr(request.state, 'user', None)
            if user:
                return getattr(user, 'id', None), getattr(user, 'email', None)
            
            # Fallback to headers
            user_id = request.headers.get('X-User-ID')
            user_email = request.headers.get('X-User-Email')
            
            return user_id, user_email
            
        except Exception:
            return None, None
    
    async def _log_request_start(self, request: Request, request_id: str):
        """Log request start with metadata"""
        try:
            # Extract request metadata
            details = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "user_agent": request.headers.get('user-agent'),
                "client_ip": self._get_client_ip(request),
                "content_type": request.headers.get('content-type'),
                "content_length": request.headers.get('content-length')
            }
            
            # Remove sensitive data from query params
            if 'password' in details["query_params"]:
                details["query_params"]["password"] = "***"
            if 'token' in details["query_params"]:
                details["query_params"]["token"] = "***"
            
            structured_logger.info(
                EventCategory.SYSTEM,
                "request_start", 
                f"{request.method} {request.url.path}",
                details=details
            )
            
        except Exception as e:
            structured_logger.error(
                EventCategory.SYSTEM,
                "logging_error",
                "Failed to log request start",
                error=e
            )
    
    async def _log_request_success(
        self, 
        request: Request, 
        response: Response, 
        request_id: str,
        duration_ms: float
    ):
        """Log successful request completion"""
        try:
            details = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "response_size": response.headers.get('content-length')
            }
            
            # Determine log level based on status code
            if response.status_code >= 400:
                structured_logger.warning(
                    EventCategory.SYSTEM,
                    "request_client_error",
                    f"{request.method} {request.url.path} - {response.status_code}",
                    details=details
                )
            else:
                structured_logger.info(
                    EventCategory.SYSTEM,
                    "request_success",
                    f"{request.method} {request.url.path} - {response.status_code}",
                    details=details
                )
            
            # Log security events for sensitive operations
            await self._check_security_events(request, response, details)
            
        except Exception as e:
            structured_logger.error(
                EventCategory.SYSTEM,
                "logging_error", 
                "Failed to log request success",
                error=e
            )
    
    async def _log_request_error(
        self,
        request: Request,
        error: Exception, 
        request_id: str,
        duration_ms: float
    ):
        """Log request errors"""
        try:
            details = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration_ms, 2),
                "error_type": error.__class__.__name__
            }
            
            structured_logger.error(
                EventCategory.SYSTEM,
                "request_error",
                f"{request.method} {request.url.path} - Server Error",
                error=error,
                details=details
            )
            
        except Exception as logging_error:
            # Fallback logging if structured logging fails
            print(f"Logging error: {logging_error}")
    
    async def _check_security_events(self, request: Request, response: Response, details: dict):
        """Check for security-relevant events to log"""
        try:
            path = request.url.path
            method = request.method
            status_code = response.status_code
            
            # Authentication events
            if '/auth/login' in path:
                if status_code == 200:
                    structured_logger.audit(
                        "user_authentication_success",
                        "User successfully authenticated",
                        details={"login_method": "password", **details},
                        sensitive=True
                    )
                elif status_code == 401:
                    structured_logger.audit(
                        "user_authentication_failed", 
                        "Authentication attempt failed",
                        details={"failure_reason": "invalid_credentials", **details},
                        sensitive=True
                    )
            
            # Data export events  
            elif '/export' in path or 'download' in path:
                structured_logger.audit(
                    "data_export_attempt",
                    "User attempted data export",
                    details={"export_endpoint": path, **details}
                )
            
            # Admin operations
            elif '/admin' in path or '/rbac' in path:
                structured_logger.audit(
                    "admin_operation",
                    "Admin operation performed",
                    details={"admin_endpoint": path, **details}
                )
            
            # Tenant management
            elif '/tenant' in path:
                structured_logger.audit(
                    "tenant_management",
                    "Tenant management operation",
                    details={"tenant_endpoint": path, **details}
                )
            
            # High privilege operations
            elif method in ['DELETE'] or '/delete' in path:
                structured_logger.audit(
                    "data_deletion",
                    "Data deletion operation", 
                    details={"deletion_endpoint": path, **details}
                )
            
            # Rate limiting / suspicious activity  
            elif status_code == 429:
                structured_logger.warning(
                    EventCategory.SECURITY,
                    "rate_limit_exceeded",
                    "Rate limit exceeded for request",
                    details=details
                )
            
            # Permission errors
            elif status_code == 403:
                structured_logger.warning(
                    EventCategory.SECURITY,
                    "permission_denied",
                    "Access denied for request",
                    details=details
                )
                
        except Exception as e:
            structured_logger.error(
                EventCategory.SYSTEM,
                "security_logging_error",
                "Failed to log security event",
                error=e
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address considering proxies"""
        # Check for forwarded headers (behind load balancer/proxy)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return str(request.client.host) if request.client else 'unknown'

# Performance monitoring middleware
class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Dedicated middleware for performance monitoring and alerting
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.slow_request_threshold = 2000  # 2 seconds
        self.very_slow_threshold = 5000     # 5 seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Log performance alerts for slow requests
        if duration_ms > self.very_slow_threshold:
            structured_logger.critical(
                EventCategory.SYSTEM,
                "very_slow_request",
                f"Very slow request detected: {duration_ms:.2f}ms",
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "threshold_exceeded": "very_slow"
                }
            )
        elif duration_ms > self.slow_request_threshold:
            structured_logger.warning(
                EventCategory.SYSTEM, 
                "slow_request",
                f"Slow request detected: {duration_ms:.2f}ms",
                details={
                    "method": request.method,
                    "path": request.url.path, 
                    "duration_ms": duration_ms,
                    "threshold_exceeded": "slow"
                }
            )
        
        return response

# Error handling middleware
class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive error logging and tracking
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log unhandled exceptions with full context
            structured_logger.critical(
                EventCategory.SYSTEM,
                "unhandled_exception",
                f"Unhandled exception in {request.method} {request.url.path}",
                error=e,
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "user_agent": request.headers.get('user-agent')
                }
            )
            raise