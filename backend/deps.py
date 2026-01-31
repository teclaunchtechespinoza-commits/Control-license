"""
Dependency system for enforced tenant isolation
Critical security module - ensures 100% tenant data isolation
"""
from fastapi import HTTPException, Request, status
from typing import Optional

TENANT_HEADER = "X-Tenant-ID"

def require_tenant(request: Request) -> str:
    """
    CRITICAL: Ensure every request runs under a tenant context
    This dependency MUST be used on all data-related endpoints
    Priority: 1. X-Tenant-ID header, 2. request.state.tenant_id, 3. default
    """
    # Primeiro, verificar header X-Tenant-ID
    tid = request.headers.get(TENANT_HEADER)
    
    # Fallback para request.state (setado pelo middleware)
    if not tid:
        tid = getattr(request.state, "tenant_id", None)
    
    # Para desenvolvimento/demo, usar 'default' se nenhum tenant
    if not tid:
        tid = "default"
        request.state.tenant_id = tid
    
    return tid

def add_tenant_filter(base: dict, tenant_id: Optional[str] = None) -> dict:
    """
    CRITICAL: Merge tenant_id into any MongoDB filter (idempotent)
    This function MUST be used on all MongoDB queries
    """
    if base is None:
        base = {}
    else:
        base = dict(base)
    
    if tenant_id:
        if "tenant_id" in base and base["tenant_id"] != tenant_id:
            raise ValueError(f"Conflicting tenant_id in filter: existing={base['tenant_id']}, new={tenant_id}")
        base["tenant_id"] = tenant_id
    return base

def add_tenant_to_document(doc: dict, tenant_id: Optional[str] = None) -> dict:
    """
    CRITICAL: Add tenant_id to document before insertion
    This function MUST be used on all MongoDB inserts
    """
    if doc is None:
        doc = {}
    else:
        doc = dict(doc)
    
    if tenant_id:
        doc["tenant_id"] = tenant_id
    return doc

def enforce_super_admin_or_tenant_filter(base: dict, current_user, tenant_id: Optional[str] = None) -> dict:
    """
    CRITICAL: Super admin can bypass tenant filter, regular users cannot
    """
    if hasattr(current_user, 'role') and current_user.role == 'super_admin':
        return base  # Super admin sees all data
    else:
        return add_tenant_filter(base, tenant_id)  # Regular users only see their tenant

# Validation functions for critical operations
def validate_tenant_access(resource_tenant_id: str, user_tenant_id: str, user_role: str) -> bool:
    """
    CRITICAL: Validate if user can access resource from specific tenant
    """
    if user_role == 'super_admin':
        return True  # Super admin has access to all tenants
    
    return resource_tenant_id == user_tenant_id

def get_tenant_safe_filter(user_tenant_id: str, user_role: str, base_filter: Optional[dict] = None) -> dict:
    """
    CRITICAL: Get a tenant-safe filter based on user permissions
    """
    if base_filter is None:
        base_filter = {}
    
    if user_role == 'super_admin':
        return base_filter  # Super admin sees all
    else:
        return add_tenant_filter(base_filter, user_tenant_id)  # Regular users filtered by tenant