"""
🚀 SUB-FASE 2.2 - Redis Cache System
Strategic caching for maximum performance gains

Features:
- Smart cache invalidation
- Tenant-aware caching
- Performance monitoring
- Automatic fallback to database
- Cache warming strategies
"""

import asyncio
import json
import logging
import time
import hashlib
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

class RedisCacheManager:
    """
    🔄 Advanced Redis Cache Manager
    
    Provides intelligent caching with:
    - Tenant isolation
    - Smart invalidation
    - Performance tracking
    - Fallback mechanisms
    """
    
    def __init__(self, redis_url: str = "redis://127.0.0.1:6379/0", db: AsyncIOMotorDatabase = None):
        self.redis_url = redis_url
        self.db = db
        self.redis_client = None
        self.performance_stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'total_requests': 0
        }
        self.is_connected = False
        
    async def connect(self):
        """Connect to Redis with fallback handling"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("🔄 Redis cache system connected successfully")
            
            # Initialize cache warming for critical data
            await self._warm_critical_cache()
            
        except Exception as e:
            logger.warning(f"🔄 Redis connection failed: {str(e)}")
            logger.warning("🔄 Cache system will fallback to database queries")
            self.is_connected = False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("🔄 Redis cache system disconnected")
    
    def _generate_cache_key(self, tenant_id: str, key_type: str, identifier: str = "") -> str:
        """Generate tenant-aware cache key"""
        base_key = f"cache:{tenant_id}:{key_type}"
        if identifier:
            # Use hash for long identifiers to keep keys manageable
            if len(identifier) > 50:
                identifier = hashlib.md5(identifier.encode()).hexdigest()
            base_key += f":{identifier}"
        return base_key
    
    async def get(self, tenant_id: str, key_type: str, identifier: str = "") -> Optional[Any]:
        """Get data from cache"""
        if not self.is_connected:
            return None
            
        try:
            cache_key = self._generate_cache_key(tenant_id, key_type, identifier)
            
            # Get data with expiration info
            pipe = self.redis_client.pipeline()
            pipe.get(cache_key)
            pipe.ttl(cache_key)
            cached_data, ttl = await pipe.execute()
            
            self.performance_stats['total_requests'] += 1
            
            if cached_data is not None:
                self.performance_stats['hits'] += 1
                
                # Log cache hit with performance info
                logger.debug(f"🎯 Cache HIT: {key_type} (TTL: {ttl}s)")
                
                return json.loads(cached_data)
            else:
                self.performance_stats['misses'] += 1
                logger.debug(f"🎯 Cache MISS: {key_type}")
                return None
                
        except Exception as e:
            self.performance_stats['errors'] += 1
            logger.warning(f"🔄 Cache GET error for {key_type}: {str(e)}")
            return None
    
    async def set(self, tenant_id: str, key_type: str, data: Any, ttl: int = 3600, identifier: str = ""):
        """Set data in cache with TTL"""
        if not self.is_connected:
            return False
            
        try:
            cache_key = self._generate_cache_key(tenant_id, key_type, identifier)
            serialized_data = json.dumps(data, default=str)  # Handle datetime objects
            
            await self.redis_client.setex(cache_key, ttl, serialized_data)
            
            logger.debug(f"🔄 Cache SET: {key_type} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.warning(f"🔄 Cache SET error for {key_type}: {str(e)}")
            return False
    
    async def delete(self, tenant_id: str, key_type: str, identifier: str = ""):
        """Delete specific cache entry"""
        if not self.is_connected:
            return False
            
        try:
            cache_key = self._generate_cache_key(tenant_id, key_type, identifier)
            deleted = await self.redis_client.delete(cache_key)
            
            if deleted:
                logger.debug(f"🗑️ Cache DELETED: {key_type}")
            
            return deleted > 0
            
        except Exception as e:
            logger.warning(f"🔄 Cache DELETE error for {key_type}: {str(e)}")
            return False
    
    async def invalidate_tenant_cache(self, tenant_id: str, pattern: str = "*"):
        """Invalidate all cache entries for a tenant"""
        if not self.is_connected:
            return 0
            
        try:
            search_pattern = f"cache:{tenant_id}:{pattern}"
            keys = await self.redis_client.keys(search_pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"🗑️ Invalidated {deleted} cache entries for tenant {tenant_id}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.warning(f"🔄 Cache invalidation error for tenant {tenant_id}: {str(e)}")
            return 0
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total = self.performance_stats['total_requests']
        if total == 0:
            hit_rate = 0
        else:
            hit_rate = (self.performance_stats['hits'] / total) * 100
        
        return {
            'connected': self.is_connected,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total,
            'hits': self.performance_stats['hits'],
            'misses': self.performance_stats['misses'],
            'errors': self.performance_stats['errors']
        }
    
    async def _warm_critical_cache(self):
        """Warm cache with critical data on startup"""
        if not self.db:
            return
            
        try:
            logger.info("🔥 Warming critical cache data...")
            
            # Get all tenants to warm their cache
            tenants = await self.db.tenants.find({}).to_list(length=10)  # Limit to 10 tenants
            
            for tenant in tenants[:3]:  # Warm only first 3 tenants to avoid startup delay
                tenant_id = tenant.get('id', 'default')
                
                # Warm categories cache
                categories = await self.db.categories.find({"tenant_id": tenant_id}).to_list(length=100)
                if categories:
                    await self.set(tenant_id, "categories", categories, ttl=3600)  # 1 hour
                
                # Warm license plans cache
                plans = await self.db.license_plans.find({"tenant_id": tenant_id}).to_list(length=50)
                if plans:
                    await self.set(tenant_id, "license_plans", plans, ttl=3600)  # 1 hour
                
                # Warm roles cache
                roles = await self.db.roles.find({"tenant_id": tenant_id}).to_list(length=20)
                if roles:
                    await self.set(tenant_id, "roles", roles, ttl=1800)  # 30 minutes
            
            logger.info("🔥 Critical cache warming completed")
            
        except Exception as e:
            logger.warning(f"🔥 Cache warming failed: {str(e)}")


# Global cache manager instance
cache_manager = None

async def get_cache_manager() -> RedisCacheManager:
    """Get global cache manager instance"""
    global cache_manager
    if cache_manager is None:
        from settings import settings
        from server import db  # Import here to avoid circular imports
        
        cache_manager = RedisCacheManager(settings.redis_url, db)
        await cache_manager.connect()
    
    return cache_manager


def cached(
    key_type: str,
    ttl: int = 3600,
    identifier_func: Optional[Callable] = None,
    tenant_aware: bool = True
):
    """
    🎯 Decorator for automatic caching of function results
    
    Usage:
        @cached("users", ttl=1800)
        async def get_users(tenant_id: str):
            return await db.users.find({"tenant_id": tenant_id}).to_list()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = await get_cache_manager()
            
            # Extract tenant_id (first arg or from kwargs)
            tenant_id = "default"
            if tenant_aware:
                if args and len(args) > 0:
                    tenant_id = args[0]
                elif 'tenant_id' in kwargs:
                    tenant_id = kwargs['tenant_id']
            
            # Generate identifier
            identifier = ""
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                # Use function args as identifier
                identifier = hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()[:16]
            
            # Try to get from cache
            start_time = time.time()
            cached_result = await cache.get(tenant_id, key_type, identifier)
            
            if cached_result is not None:
                cache_time = (time.time() - start_time) * 1000
                logger.debug(f"🎯 Cache hit for {func.__name__}: {cache_time:.2f}ms")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            if result is not None:
                await cache.set(tenant_id, key_type, result, ttl, identifier)
            
            exec_time = (time.time() - start_time) * 1000
            logger.debug(f"🔄 Cache miss for {func.__name__}: {exec_time:.2f}ms")
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate_on_write(key_types: List[str]):
    """
    🗑️ Decorator to invalidate cache on write operations
    
    Usage:
        @cache_invalidate_on_write(["users", "stats"])
        async def create_user(user_data, tenant_id):
            # This will invalidate users and stats cache after execution
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the function first
            result = await func(*args, **kwargs)
            
            # Extract tenant_id
            tenant_id = "default"
            if args and len(args) > 0 and isinstance(args[0], str):
                tenant_id = args[0]
            elif 'tenant_id' in kwargs:
                tenant_id = kwargs['tenant_id']
            
            # Invalidate specified cache types
            cache = await get_cache_manager()
            for key_type in key_types:
                await cache.invalidate_tenant_cache(tenant_id, key_type)
            
            return result
        
        return wrapper
    return decorator


# 🚀 HIGH-IMPACT CACHE FUNCTIONS

async def get_cached_categories(tenant_id: str) -> List[Dict]:
    """Get categories with caching (1 hour TTL)"""
    cache = await get_cache_manager()
    
    cached_data = await cache.get(tenant_id, "categories")
    if cached_data:
        return cached_data
    
    # Fetch from database
    from server import db
    categories = await db.categories.find({"tenant_id": tenant_id}).to_list(length=None)
    
    # Cache for 1 hour (categories rarely change)
    await cache.set(tenant_id, "categories", categories, ttl=3600)
    
    return categories


async def get_cached_license_plans(tenant_id: str) -> List[Dict]:
    """Get license plans with caching (1 hour TTL)"""
    cache = await get_cache_manager()
    
    cached_data = await cache.get(tenant_id, "license_plans")
    if cached_data:
        return cached_data
    
    # Fetch from database
    from server import db
    plans = await db.license_plans.find({"tenant_id": tenant_id}).to_list(length=None)
    
    # Cache for 1 hour
    await cache.set(tenant_id, "license_plans", plans, ttl=3600)
    
    return plans


async def get_cached_dashboard_stats(tenant_id: str) -> Dict[str, Any]:
    """Get dashboard stats with caching (5 minutes TTL)"""
    cache = await get_cache_manager()
    
    cached_data = await cache.get(tenant_id, "dashboard_stats")
    if cached_data:
        return cached_data
    
    # Calculate stats from database
    from server import db
    
    total_users = await db.users.count_documents({"tenant_id": tenant_id})
    total_licenses = await db.licenses.count_documents({"tenant_id": tenant_id})
    total_clients = await db.clients.count_documents({"tenant_id": tenant_id})
    
    # Count expiring licenses (next 30 days)
    thirty_days_from_now = datetime.utcnow() + timedelta(days=30)
    expiring_licenses = await db.licenses.count_documents({
        "tenant_id": tenant_id,
        "expires_at": {"$lt": thirty_days_from_now, "$gt": datetime.utcnow()}
    })
    
    stats = {
        "total_users": total_users,
        "total_licenses": total_licenses,
        "total_clients": total_clients,
        "expiring_licenses": expiring_licenses,
        "status": "operational",
        "last_updated": datetime.utcnow().isoformat()
    }
    
    # Cache for 5 minutes (stats change frequently)
    await cache.set(tenant_id, "dashboard_stats", stats, ttl=300)
    
    return stats


async def get_cached_user_permissions(tenant_id: str, user_id: str) -> List[str]:
    """Get user permissions with caching (15 minutes TTL)"""
    cache = await get_cache_manager()
    
    cached_data = await cache.get(tenant_id, "user_permissions", user_id)
    if cached_data:
        return cached_data
    
    # Fetch user with roles and permissions
    from server import db
    
    user = await db.users.find_one({"id": user_id, "tenant_id": tenant_id})
    if not user:
        return []
    
    permissions = []
    user_roles = user.get("rbac", {}).get("roles", [])
    
    if user_roles:
        roles = await db.roles.find({
            "id": {"$in": user_roles},
            "tenant_id": tenant_id
        }).to_list(length=None)
        
        for role in roles:
            role_permissions = role.get("permissions", [])
            permissions.extend(role_permissions)
    
    # Remove duplicates
    unique_permissions = list(set(permissions))
    
    # Cache for 15 minutes (permissions change moderately)
    await cache.set(tenant_id, "user_permissions", unique_permissions, ttl=900, identifier=user_id)
    
    return unique_permissions


# Performance monitoring endpoint data
async def get_cache_performance_report() -> Dict[str, Any]:
    """Get comprehensive cache performance report"""
    cache = await get_cache_manager()
    stats = await cache.get_performance_stats()
    
    # Add Redis info if connected
    redis_info = {}
    if cache.is_connected and cache.redis_client:
        try:
            info = await cache.redis_client.info()
            redis_info = {
                'used_memory': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0)
            }
        except:
            redis_info = {'status': 'info_unavailable'}
    
    return {
        'cache_stats': stats,
        'redis_info': redis_info,
        'recommendations': _get_performance_recommendations(stats)
    }


def _get_performance_recommendations(stats: Dict) -> List[str]:
    """Generate performance recommendations based on cache stats"""
    recommendations = []
    
    hit_rate = stats.get('hit_rate', 0)
    if hit_rate < 70:
        recommendations.append("Consider increasing TTL for frequently accessed data")
    if hit_rate > 95:
        recommendations.append("Excellent cache performance - consider expanding cache coverage")
    
    errors = stats.get('errors', 0)
    if errors > 0:
        recommendations.append("Redis connection issues detected - check Redis server status")
    
    if not stats.get('connected', False):
        recommendations.append("Redis cache is not connected - system falling back to database queries")
    
    return recommendations


# Export commonly used functions
__all__ = [
    "RedisCacheManager",
    "get_cache_manager",
    "cached",
    "cache_invalidate_on_write",
    "get_cached_categories",
    "get_cached_license_plans", 
    "get_cached_dashboard_stats",
    "get_cached_user_permissions",
    "get_cache_performance_report"
]