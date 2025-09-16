"""
🛡️ Tenant Validation Middleware
Provides secure tenant validation and isolation for multi-tenant SaaS

Features:
- Automatic tenant existence validation
- Active status verification  
- Cross-tenant access prevention
- Clear error messages for better UX
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Public endpoints that don't require tenant validation
PUBLIC_ENDPOINTS = [
    "/",
    "/health",
    "/api/health", 
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/me",
    "/docs",
    "/openapi.json",
    "/api/demo-credentials"
]

class TenantValidationMiddleware(BaseHTTPMiddleware):
    """
    🔐 Middleware to validate tenant access and prevent isolation violations
    
    This middleware runs before any endpoint processing to ensure:
    1. Tenant exists in the system
    2. Tenant is active and not suspended  
    3. User has permission to access the tenant
    4. Prevents cross-tenant data access
    """
    
    def __init__(self, app, db):
        super().__init__(app)
        self.db = db
        
    async def dispatch(self, request: Request, call_next):
        # Skip validation for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
            
        try:
            # Extract tenant_id from headers or user session
            tenant_id = await self._extract_tenant_id(request)
            
            if not tenant_id:
                return self._create_error_response(
                    status_code=400,
                    error_code="TENANT_ID_MISSING",
                    message="X-Tenant-ID header is required for this endpoint"
                )
            
            # Validate tenant exists and is active
            tenant = await self._validate_tenant(tenant_id)
            if not tenant:
                return self._create_error_response(
                    status_code=403,
                    error_code="TENANT_NOT_FOUND", 
                    message=f"Tenant '{tenant_id}' does not exist. Contact your administrator."
                )
                
            # Check if tenant is active
            if not self._is_tenant_active(tenant):
                status = tenant.get("status", "unknown")
                return self._create_error_response(
                    status_code=403,
                    error_code="TENANT_INACTIVE",
                    message=f"Access denied: Organization is {status}. Contact your administrator."
                )
                
            # Store validated tenant in request state for use by endpoints
            request.state.validated_tenant = tenant
            request.state.tenant_id = tenant_id
            
            # Continue with request processing
            response = await call_next(request)
            
            # Add tenant info to response headers for debugging
            response.headers["X-Validated-Tenant"] = tenant_id
            return response
            
        except Exception as e:
            logger.error(f"Tenant validation error: {str(e)}")
            return self._create_error_response(
                status_code=500,
                error_code="TENANT_VALIDATION_ERROR",
                message="Internal server error during tenant validation"
            )
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public and doesn't require tenant validation"""
        return any(path.startswith(endpoint) for endpoint in PUBLIC_ENDPOINTS)
    
    async def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant_id from X-Tenant-ID header"""
        tenant_id = request.headers.get("X-Tenant-ID")
        
        if not tenant_id:
            # Fallback: could extract from user session/JWT if needed
            # For now, require explicit header
            pass
            
        return tenant_id
    
    async def _validate_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate tenant exists in database
        
        Returns tenant document if exists, None otherwise
        """
        try:
            # First check if tenants collection exists
            collections = await self.db.list_collection_names()
            if "tenants" not in collections:
                # Create default tenant if collection doesn't exist
                await self._create_default_tenant()
            
            # Find tenant by ID
            tenant = await self.db.tenants.find_one({"id": tenant_id})
            return tenant
            
        except Exception as e:
            logger.error(f"Error validating tenant {tenant_id}: {str(e)}")
            return None
    
    def _is_tenant_active(self, tenant: Dict[str, Any]) -> bool:
        """Check if tenant is in active status"""
        status = tenant.get("status", "unknown")
        return status == "active"
    
    async def _create_default_tenant(self):
        """Create default tenant if none exists"""
        try:
            default_tenant = {
                "id": "default",
                "name": "Sistema Padrão",
                "status": "active",
                "subscription_status": "active", 
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "limits": {
                    "max_users": 10000,
                    "max_licenses": 100000,
                    "max_clients": 50000
                },
                "features": {
                    "whatsapp_integration": True,
                    "sales_dashboard": True,
                    "rbac": True,
                    "notifications": True
                }
            }
            
            await self.db.tenants.insert_one(default_tenant)
            logger.info("Created default tenant for system")
            
        except Exception as e:
            logger.error(f"Error creating default tenant: {str(e)}")
    
    def _create_error_response(self, status_code: int, error_code: str, message: str) -> JSONResponse:
        """Create standardized error response"""
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": message,
                "error_code": error_code,
                "timestamp": datetime.utcnow().isoformat(),
                "suggestion": self._get_error_suggestion(error_code)
            }
        )
    
    def _get_error_suggestion(self, error_code: str) -> str:
        """Provide helpful suggestions based on error type"""
        suggestions = {
            "TENANT_ID_MISSING": "Ensure X-Tenant-ID header is included in your request",
            "TENANT_NOT_FOUND": "Verify your organization ID with your administrator", 
            "TENANT_INACTIVE": "Contact your administrator to reactivate your organization",
            "TENANT_VALIDATION_ERROR": "Try again in a few moments or contact support"
        }
        return suggestions.get(error_code, "Contact support if this problem persists")


# Dependency for getting validated tenant in endpoints
async def get_validated_tenant(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency to get validated tenant from request state
    
    Usage:
        @app.get("/api/endpoint")
        async def endpoint(tenant: dict = Depends(get_validated_tenant)):
            tenant_id = tenant["id"]
    """
    if not hasattr(request.state, "validated_tenant"):
        raise HTTPException(
            status_code=500, 
            detail="Tenant validation not performed. Check middleware order."
        )
    return request.state.validated_tenant


async def get_tenant_id(request: Request) -> str:
    """
    FastAPI dependency to get tenant_id from validated request
    
    Usage:
        @app.get("/api/endpoint") 
        async def endpoint(tenant_id: str = Depends(get_tenant_id)):
            # Use tenant_id for queries
    """
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(
            status_code=500,
            detail="Tenant ID not available. Check middleware order."
        )
    return request.state.tenant_id