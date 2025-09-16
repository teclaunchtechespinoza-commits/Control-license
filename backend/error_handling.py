"""
🚨 Global Error Handling Middleware
Provides consistent error handling across all endpoints

Features:
- Standardized error responses
- Security-safe error messages
- Comprehensive logging
- User-friendly error codes
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
import json
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    🛡️ Global error handling middleware for consistent error responses
    
    Handles:
    - Unhandled exceptions with safe error messages
    - HTTP exceptions with enhanced details
    - Validation errors with clear feedback
    - Security errors without information disclosure
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions with enhanced details
            return await self._handle_http_exception(request, e)
            
        except Exception as e:
            # Handle unexpected exceptions safely
            return await self._handle_unexpected_exception(request, e)
    
    async def _handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions with enhanced context"""
        
        # Get enhanced error details based on status code
        error_details = self._get_enhanced_error_details(exc.status_code, str(exc.detail))
        
        # Log the error with context
        logger.warning(
            f"HTTP {exc.status_code} - {request.method} {request.url.path} - {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "method": request.method,
                "path": request.url.path,
                "user_agent": request.headers.get("user-agent"),
                "tenant_id": getattr(request.state, "tenant_id", "unknown")
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": error_details["message"],
                "error_code": error_details["code"],
                "timestamp": datetime.utcnow().isoformat(),
                "suggestion": error_details["suggestion"],
                "documentation": error_details.get("docs_url")
            }
        )
    
    async def _handle_unexpected_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions with safe error messages"""
        
        # Generate unique error ID for tracking
        error_id = f"err_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Log full exception details for debugging
        logger.error(
            f"Unexpected error {error_id} - {request.method} {request.url.path}",
            extra={
                "error_id": error_id,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "method": request.method,
                "path": request.url.path,
                "tenant_id": getattr(request.state, "tenant_id", "unknown"),
                "traceback": traceback.format_exc()
            }
        )
        
        # Return safe error message to user
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred. Please try again.",
                "error_code": "INTERNAL_SERVER_ERROR",
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat(),
                "suggestion": "If this problem persists, contact support with the error ID"
            }
        )
    
    def _get_enhanced_error_details(self, status_code: int, detail: str) -> Dict[str, Any]:
        """Get enhanced error details based on status code and message"""
        
        # Common error patterns and their enhanced details
        error_patterns = {
            400: {
                "X-Tenant-ID ausente": {
                    "code": "TENANT_ID_REQUIRED",
                    "message": "Organization ID is required for this action",
                    "suggestion": "Make sure you're logged in and your session is active"
                },
                "default": {
                    "code": "BAD_REQUEST", 
                    "message": "Invalid request data provided",
                    "suggestion": "Check your input data and try again"
                }
            },
            401: {
                "default": {
                    "code": "AUTHENTICATION_REQUIRED",
                    "message": "Authentication required to access this resource", 
                    "suggestion": "Please log in to continue"
                }
            },
            403: {
                "Not enough permissions": {
                    "code": "INSUFFICIENT_PERMISSIONS",
                    "message": "You don't have permission to perform this action",
                    "suggestion": "Contact your administrator for access"
                },
                "default": {
                    "code": "ACCESS_FORBIDDEN",
                    "message": "Access to this resource is forbidden",
                    "suggestion": "Verify your permissions with your administrator"
                }
            },
            404: {
                "default": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": "The requested resource was not found",
                    "suggestion": "Check the resource ID and try again"
                }
            },
            422: {
                "default": {
                    "code": "VALIDATION_ERROR",
                    "message": "Data validation failed",
                    "suggestion": "Check the required fields and data formats"
                }
            },
            429: {
                "default": {
                    "code": "RATE_LIMIT_EXCEEDED", 
                    "message": "Too many requests. Please slow down.",
                    "suggestion": "Wait a moment before trying again"
                }
            },
            500: {
                "default": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Internal server error occurred",
                    "suggestion": "Please try again in a few moments"
                }
            }
        }
        
        # Get status code specific patterns
        status_patterns = error_patterns.get(status_code, {})
        
        # Try to match specific error message
        for pattern, details in status_patterns.items():
            if pattern == "default":
                continue
            if pattern in detail:
                return details
        
        # Return default for status code
        return status_patterns.get("default", {
            "code": f"HTTP_{status_code}",
            "message": detail,
            "suggestion": "Contact support if this problem persists"
        })


class ValidationErrorHandler:
    """
    🔍 Enhanced validation error handling for Pydantic and FastAPI
    """
    
    @staticmethod
    def format_pydantic_error(exc_info) -> Dict[str, Any]:
        """Format Pydantic validation errors for better UX"""
        errors = []
        
        for error in exc_info.get("body", []):
            field_path = " → ".join(str(loc) for loc in error.get("loc", []))
            error_msg = error.get("msg", "Invalid value")
            error_type = error.get("type", "validation_error")
            
            errors.append({
                "field": field_path,
                "message": error_msg,
                "type": error_type,
                "input": error.get("input")
            })
        
        return {
            "detail": "Validation failed for the provided data",
            "error_code": "VALIDATION_FAILED",
            "errors": errors,
            "suggestion": "Please check the highlighted fields and correct the data"
        }


# Custom exception classes for better error handling

class TenantError(HTTPException):
    """Custom exception for tenant-related errors"""
    
    def __init__(self, message: str, tenant_id: str = None):
        super().__init__(status_code=403, detail=message)
        self.tenant_id = tenant_id


class BusinessLogicError(HTTPException):
    """Custom exception for business logic violations"""
    
    def __init__(self, message: str, error_code: str = "BUSINESS_LOGIC_ERROR"):
        super().__init__(status_code=422, detail=message)
        self.error_code = error_code


class DataIntegrityError(HTTPException):
    """Custom exception for data integrity violations"""
    
    def __init__(self, message: str, entity: str = None):
        super().__init__(status_code=409, detail=message)
        self.entity = entity


# Error logging utilities

def log_business_error(error_type: str, details: Dict[str, Any], tenant_id: str = None):
    """Log business errors for analytics and monitoring"""
    logger.info(
        f"Business error: {error_type}",
        extra={
            "error_type": error_type,
            "tenant_id": tenant_id,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "warning"):
    """Log security-related events"""
    log_func = getattr(logger, severity, logger.warning)
    log_func(
        f"Security event: {event_type}",
        extra={
            "event_type": event_type,
            "severity": severity,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )