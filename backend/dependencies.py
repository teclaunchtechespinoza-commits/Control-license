"""
🚀 SUB-FASE 2.3 - Dependency Injection System
Centralized dependencies for FastAPI endpoints

Features:
- Tenant-aware database connections
- Standardized tenant filtering
- User permission checking  
- Cache-aware dependencies
- Performance monitoring
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import Request, HTTPException, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from datetime import datetime

logger = logging.getLogger(__name__)

# Import from existing modules to avoid circular imports
def get_current_user():
    """Import current user dependency dynamically to avoid circular imports"""
    from server import get_current_user as _get_current_user
    return _get_current_user

def get_current_admin_user():
    """Import admin user dependency dynamically"""
    from server import get_current_admin_user as _get_current_admin_user
    return _get_current_admin_user

def get_current_tenant_id():
    """Import tenant ID function dynamically"""
    from server import get_current_tenant_id as _get_current_tenant_id
    return _get_current_tenant_id

def add_tenant_filter(base_filter: Dict):
    """Import tenant filter function dynamically"""
    from server import add_tenant_filter as _add_tenant_filter
    return _add_tenant_filter(base_filter)

def get_database():
    """Import database connection dynamically"""
    from server import db
    return db


class TenantAwareDB:
    """
    🏢 Tenant-aware database wrapper
    
    Provides automatic tenant filtering and isolation for all queries
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._stats = {
            'queries_executed': 0,
            'last_query_time': None
        }
    
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get collection with automatic tenant context"""
        return self.db[collection_name]
    
    async def find(self, collection_name: str, filter_dict: Dict = None, **kwargs) -> List[Dict]:
        """Find documents with automatic tenant filtering"""
        if filter_dict is None:
            filter_dict = {}
        
        # Add tenant filter automatically
        tenant_filter = {"tenant_id": self.tenant_id, **filter_dict}
        
        self._stats['queries_executed'] += 1
        self._stats['last_query_time'] = datetime.utcnow()
        
        logger.debug(f"🔍 Tenant query: {collection_name} with filter {tenant_filter}")
        
        collection = self.get_collection(collection_name)
        cursor = collection.find(tenant_filter, **kwargs)
        
        return await cursor.to_list(length=kwargs.get('limit', 1000))
    
    async def find_one(self, collection_name: str, filter_dict: Dict = None, **kwargs) -> Optional[Dict]:
        """Find one document with automatic tenant filtering"""
        if filter_dict is None:
            filter_dict = {}
        
        # Add tenant filter automatically
        tenant_filter = {"tenant_id": self.tenant_id, **filter_dict}
        
        self._stats['queries_executed'] += 1
        self._stats['last_query_time'] = datetime.utcnow()
        
        logger.debug(f"🔍 Tenant query (one): {collection_name} with filter {tenant_filter}")
        
        collection = self.get_collection(collection_name)
        return await collection.find_one(tenant_filter, **kwargs)
    
    async def count_documents(self, collection_name: str, filter_dict: Dict = None) -> int:
        """Count documents with automatic tenant filtering"""
        if filter_dict is None:
            filter_dict = {}
        
        # Add tenant filter automatically
        tenant_filter = {"tenant_id": self.tenant_id, **filter_dict}
        
        self._stats['queries_executed'] += 1
        self._stats['last_query_time'] = datetime.utcnow()
        
        logger.debug(f"🔢 Tenant count: {collection_name} with filter {tenant_filter}")
        
        collection = self.get_collection(collection_name)
        return await collection.count_documents(tenant_filter)
    
    async def insert_one(self, collection_name: str, document: Dict) -> Any:
        """Insert document with automatic tenant_id injection"""
        # Add tenant_id automatically
        document_with_tenant = {"tenant_id": self.tenant_id, **document}
        
        self._stats['queries_executed'] += 1
        self._stats['last_query_time'] = datetime.utcnow()
        
        logger.debug(f"📝 Tenant insert: {collection_name} with tenant_id {self.tenant_id}")
        
        collection = self.get_collection(collection_name)
        return await collection.insert_one(document_with_tenant)
    
    async def update_one(self, collection_name: str, filter_dict: Dict, update_dict: Dict, **kwargs) -> Any:
        """Update document with automatic tenant filtering"""
        # Add tenant filter to prevent cross-tenant updates
        tenant_filter = {"tenant_id": self.tenant_id, **filter_dict}
        
        self._stats['queries_executed'] += 1
        self._stats['last_query_time'] = datetime.utcnow()
        
        logger.debug(f"📝 Tenant update: {collection_name} with filter {tenant_filter}")
        
        collection = self.get_collection(collection_name)
        return await collection.update_one(tenant_filter, update_dict, **kwargs)
    
    async def delete_one(self, collection_name: str, filter_dict: Dict, **kwargs) -> Any:
        """Delete document with automatic tenant filtering"""
        # Add tenant filter to prevent cross-tenant deletes
        tenant_filter = {"tenant_id": self.tenant_id, **filter_dict}
        
        self._stats['queries_executed'] += 1
        self._stats['last_query_time'] = datetime.utcnow()
        
        logger.debug(f"🗑️ Tenant delete: {collection_name} with filter {tenant_filter}")
        
        collection = self.get_collection(collection_name)
        return await collection.delete_one(tenant_filter, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database usage statistics for this tenant session"""
        return {
            'tenant_id': self.tenant_id,
            'queries_executed': self._stats['queries_executed'],
            'last_query_time': self._stats['last_query_time'].isoformat() if self._stats['last_query_time'] else None
        }


# === DEPENDENCY FUNCTIONS ===

async def get_tenant_database(request: Request) -> TenantAwareDB:
    """
    🏢 Get tenant-aware database connection
    
    Usage:
        @app.get("/users")
        async def get_users(tenant_db: TenantAwareDB = Depends(get_tenant_database)):
            users = await tenant_db.find("users", {"is_active": True})
            return users
    """
    try:
        # Get tenant ID from request context (set by TenantValidationMiddleware)
        tenant_id = getattr(request.state, 'tenant_id', None)
        
        if not tenant_id:
            # Fallback to header-based extraction
            tenant_id = request.headers.get("X-Tenant-ID")
        
        if not tenant_id:
            # Final fallback to dynamic function
            tenant_id = get_current_tenant_id()
        
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID not available - check middleware configuration"
            )
        
        db = get_database()
        tenant_db = TenantAwareDB(db, tenant_id)
        
        logger.debug(f"🏢 Created tenant database connection for tenant: {tenant_id}")
        
        return tenant_db
        
    except Exception as e:
        logger.error(f"Failed to create tenant database connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )


async def get_tenant_filter(request: Request) -> Dict[str, Any]:
    """
    🔍 Get tenant filter for manual queries
    
    Usage:
        @app.get("/custom-query")
        async def custom_query(tenant_filter: Dict = Depends(get_tenant_filter)):
            query = {**tenant_filter, "status": "active"}
            # query will automatically include tenant_id
    """
    try:
        # Get tenant ID from request context
        tenant_id = getattr(request.state, 'tenant_id', None)
        
        if not tenant_id:
            tenant_id = request.headers.get("X-Tenant-ID")
        
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID not available for filtering"
            )
        
        return {"tenant_id": tenant_id}
        
    except Exception as e:
        logger.error(f"Failed to create tenant filter: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant filtering error"
        )


async def get_user_with_permissions(request: Request):
    """
    👤 Get current user with permissions loaded
    
    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(user_with_perms = Depends(get_user_with_permissions)):
            if "admin.users.read" not in user_with_perms.permissions:
                raise HTTPException(403, "Insufficient permissions")
    """
    try:
        # Get current user using existing dependency
        current_user_dep = get_current_user()
        current_user = await current_user_dep
        
        # Get tenant ID
        tenant_id = getattr(request.state, 'tenant_id', None) or get_current_tenant_id()
        
        # Load user permissions from cache if available
        try:
            from redis_cache_system import get_cached_user_permissions
            permissions = await get_cached_user_permissions(tenant_id, current_user.id)
        except Exception as cache_error:
            logger.warning(f"Failed to load cached permissions: {cache_error}")
            # Fallback to direct database lookup
            permissions = []
            # TODO: Implement direct permission lookup
        
        # Add permissions to user object
        current_user.permissions = permissions
        
        return current_user
        
    except Exception as e:
        logger.error(f"Failed to load user with permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User permission loading error"
        )


async def get_pagination_params(
    page: int = 1, 
    limit: int = 50,
    max_limit: int = 100
) -> Dict[str, int]:
    """
    📄 Get pagination parameters with validation
    
    Usage:
        @app.get("/users")
        async def get_users(pagination: Dict = Depends(get_pagination_params)):
            skip = pagination["skip"]
            limit = pagination["limit"]
    """
    # Validate parameters
    if page < 1:
        page = 1
    
    if limit < 1:
        limit = 1
    elif limit > max_limit:
        limit = max_limit
    
    skip = (page - 1) * limit
    
    return {
        "page": page,
        "limit": limit,
        "skip": skip,
        "max_results": limit
    }


class PermissionChecker:
    """
    🔐 Permission checking utilities
    """
    
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions
    
    def __call__(self, user_with_perms = Depends(get_user_with_permissions)):
        """Check if user has required permissions"""
        user_permissions = getattr(user_with_perms, 'permissions', [])
        
        missing_permissions = []
        for required_perm in self.required_permissions:
            if required_perm not in user_permissions:
                missing_permissions.append(required_perm)
        
        if missing_permissions:
            logger.warning(f"User {user_with_perms.email} missing permissions: {missing_permissions}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        
        return user_with_perms


def require_permissions(*permissions: str):
    """
    🔐 Decorator-style permission requirement
    
    Usage:
        @app.get("/admin-users")
        async def get_admin_users(user = Depends(require_permissions("admin.users.read"))):
            # User is guaranteed to have admin.users.read permission
    """
    return PermissionChecker(list(permissions))


# === PERFORMANCE MONITORING DEPENDENCIES ===

class RequestMetrics:
    """📊 Request performance metrics"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.db_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def record_db_query(self):
        self.db_queries += 1
    
    def record_cache_hit(self):
        self.cache_hits += 1
    
    def record_cache_miss(self):
        self.cache_misses += 1
    
    def get_duration_ms(self) -> float:
        return (datetime.utcnow() - self.start_time).total_seconds() * 1000
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            'duration_ms': self.get_duration_ms(),
            'db_queries': self.db_queries,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': (self.cache_hits / (self.cache_hits + self.cache_misses)) * 100 if (self.cache_hits + self.cache_misses) > 0 else 0
        }


async def get_request_metrics(request: Request) -> RequestMetrics:
    """
    📊 Get request performance metrics tracker
    
    Usage:
        @app.get("/users")
        async def get_users(metrics: RequestMetrics = Depends(get_request_metrics)):
            # metrics will track the performance of this request
            return {"users": users, "metrics": metrics.get_summary()}
    """
    if not hasattr(request.state, 'metrics'):
        request.state.metrics = RequestMetrics()
    
    return request.state.metrics


# === COMMON QUERY BUILDERS ===

class QueryBuilder:
    """
    🔧 Common query builder for complex operations
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.base_filter = {"tenant_id": tenant_id}
    
    def active_only(self) -> "QueryBuilder":
        """Add active filter"""
        self.base_filter["is_active"] = True
        return self
    
    def by_status(self, status: str) -> "QueryBuilder":
        """Add status filter"""
        self.base_filter["status"] = status
        return self
    
    def by_date_range(self, field: str, start_date: datetime, end_date: datetime) -> "QueryBuilder":
        """Add date range filter"""
        self.base_filter[field] = {
            "$gte": start_date,
            "$lte": end_date
        }
        return self
    
    def search_text(self, fields: List[str], search_term: str) -> "QueryBuilder":
        """Add text search across multiple fields"""
        if search_term:
            search_conditions = []
            for field in fields:
                search_conditions.append({
                    field: {"$regex": search_term, "$options": "i"}
                })
            
            if search_conditions:
                self.base_filter["$or"] = search_conditions
        
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build final query filter"""
        return self.base_filter.copy()


async def get_query_builder(request: Request) -> QueryBuilder:
    """
    🔧 Get query builder with tenant context
    
    Usage:
        @app.get("/search")
        async def search_users(
            q: str = "",
            query_builder: QueryBuilder = Depends(get_query_builder)
        ):
            filter_dict = query_builder.active_only().search_text(["name", "email"], q).build()
    """
    tenant_id = getattr(request.state, 'tenant_id', None) or get_current_tenant_id()
    return QueryBuilder(tenant_id)


# Export commonly used dependencies
__all__ = [
    "TenantAwareDB",
    "get_tenant_database",
    "get_tenant_filter", 
    "get_user_with_permissions",
    "get_pagination_params",
    "require_permissions",
    "PermissionChecker",
    "RequestMetrics",
    "get_request_metrics",
    "QueryBuilder",
    "get_query_builder"
]