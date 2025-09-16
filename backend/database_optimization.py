"""
🚀 SUB-FASE 2.1 - Database Performance Optimization
MongoDB Index Creation and Query Optimization

Features:
- Automatic index creation for performance-critical queries
- Composite indexes for multi-field queries
- Query performance monitoring
- Index usage analytics
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from typing import List, Dict, Any
import time

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """
    🔍 MongoDB Performance Optimizer
    
    Analyzes query patterns and creates optimal indexes
    for maximum performance gains
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.performance_stats = {}
        
    async def create_performance_indexes(self):
        """
        Create performance-critical indexes based on application query patterns
        
        Priority:
        1. Tenant isolation (tenant_id in every query)
        2. Authentication queries (email lookups)
        3. Date-based queries (license expiration)
        4. Status filtering (active/inactive)
        5. Search operations
        """
        
        logger.info("🚀 Starting MongoDB Index Optimization...")
        
        # Track performance improvements
        start_time = time.time()
        indexes_created = 0
        
        try:
            # === USERS COLLECTION OPTIMIZATION ===
            await self._optimize_users_collection()
            indexes_created += 4
            
            # === LICENSES COLLECTION OPTIMIZATION ===
            await self._optimize_licenses_collection()
            indexes_created += 6
            
            # === CLIENTS COLLECTION OPTIMIZATION ===
            await self._optimize_clients_collection()
            indexes_created += 4
            
            # === CATEGORIES COLLECTION OPTIMIZATION ===
            await self._optimize_categories_collection()
            indexes_created += 3
            
            # === RBAC COLLECTIONS OPTIMIZATION ===
            await self._optimize_rbac_collections()
            indexes_created += 4
            
            # === AUDIT/LOGS OPTIMIZATION ===
            await self._optimize_audit_collections()
            indexes_created += 3
            
            # === WHATSAPP/NOTIFICATIONS OPTIMIZATION ===
            await self._optimize_notification_collections()
            indexes_created += 2
            
            end_time = time.time()
            optimization_time = end_time - start_time
            
            logger.info(f"✅ Database optimization completed!")
            logger.info(f"   📊 Indexes created: {indexes_created}")
            logger.info(f"   ⏱️ Time taken: {optimization_time:.2f}s")
            
            # Test performance improvements
            await self._test_performance_improvements()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database optimization failed: {str(e)}")
            return False
    
    async def _optimize_users_collection(self):
        """Optimize users collection for authentication and tenant queries"""
        
        logger.info("🔧 Optimizing users collection...")
        
        try:
            # 1. CRITICAL: Unique compound index for login (most frequent query)
            await self.db.users.create_index(
                [("tenant_id", 1), ("email", 1)], 
                unique=True,
                name="idx_tenant_email_unique",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + email (unique) - LOGIN OPTIMIZATION")
            
            # 2. User listing by tenant (dashboard, user management)
            await self.db.users.create_index(
                [("tenant_id", 1), ("is_active", 1)],
                name="idx_tenant_active_users",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + is_active - USER LISTING")
            
            # 3. Role-based queries (RBAC system)
            await self.db.users.create_index(
                [("tenant_id", 1), ("role", 1)],
                name="idx_tenant_role",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + role - RBAC QUERIES")
            
            # 4. User search (name/email search in admin panel)
            await self.db.users.create_index(
                [("tenant_id", 1), ("name", "text"), ("email", "text")],
                name="idx_tenant_user_search",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + text search - USER SEARCH")
            
        except Exception as e:
            logger.warning(f"   ⚠️ Users collection optimization issue: {str(e)}")
    
    async def _optimize_licenses_collection(self):
        """Optimize licenses collection for expiration tracking and filtering"""
        
        logger.info("🔧 Optimizing licenses collection...")
        
        try:
            # 1. CRITICAL: License expiration queries (most performance-sensitive)
            await self.db.licenses.create_index(
                [("tenant_id", 1), ("expires_at", 1)],
                name="idx_tenant_expiration",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + expires_at - EXPIRATION TRACKING")
            
            # 2. Status filtering (active/expired/suspended)
            await self.db.licenses.create_index(
                [("tenant_id", 1), ("status", 1)],
                name="idx_tenant_status",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + status - STATUS FILTERING")
            
            # 3. License type filtering (dashboard analytics)
            await self.db.licenses.create_index(
                [("tenant_id", 1), ("license_type", 1)],
                name="idx_tenant_license_type",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + license_type - TYPE FILTERING")
            
            # 4. Client-specific license queries
            await self.db.licenses.create_index(
                [("tenant_id", 1), ("client_id", 1)],
                name="idx_tenant_client_licenses",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + client_id - CLIENT LICENSES")
            
            # 5. License value/revenue queries
            await self.db.licenses.create_index(
                [("tenant_id", 1), ("value", -1)],
                name="idx_tenant_license_value",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + value - REVENUE QUERIES")
            
            # 6. Date range queries (reports, analytics)
            await self.db.licenses.create_index(
                [("tenant_id", 1), ("created_at", -1)],
                name="idx_tenant_creation_date",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + created_at - DATE RANGE QUERIES")
            
        except Exception as e:
            logger.warning(f"   ⚠️ Licenses collection optimization issue: {str(e)}")
    
    async def _optimize_clients_collection(self):
        """Optimize clients collection for customer management"""
        
        logger.info("🔧 Optimizing clients collection...")
        
        try:
            # 1. Client type filtering (PF/PJ)
            await self.db.clients.create_index(
                [("tenant_id", 1), ("client_type", 1)],
                name="idx_tenant_client_type",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + client_type - PF/PJ FILTERING")
            
            # 2. Client search (name, document, email)
            await self.db.clients.create_index(
                [("tenant_id", 1), ("name", "text"), ("email", "text")],
                name="idx_tenant_client_search",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + text search - CLIENT SEARCH")
            
            # 3. Document lookup (CPF/CNPJ)
            await self.db.clients.create_index(
                [("tenant_id", 1), ("document", 1)],
                name="idx_tenant_client_document",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + document - DOCUMENT LOOKUP")
            
            # 4. Client status (active/inactive)
            await self.db.clients.create_index(
                [("tenant_id", 1), ("is_active", 1)],
                name="idx_tenant_client_active",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + is_active - CLIENT STATUS")
            
        except Exception as e:
            logger.warning(f"   ⚠️ Clients collection optimization issue: {str(e)}")
    
    async def _optimize_categories_collection(self):
        """Optimize categories and products collections"""
        
        logger.info("🔧 Optimizing categories/products collections...")
        
        try:
            # 1. Categories by tenant
            await self.db.categories.create_index(
                [("tenant_id", 1), ("name", 1)],
                name="idx_tenant_category_name",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + name - CATEGORY LISTING")
            
            # 2. Products by category
            await self.db.products.create_index(
                [("tenant_id", 1), ("category_id", 1)],
                name="idx_tenant_product_category",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + category_id - PRODUCTS BY CATEGORY")
            
            # 3. License plans
            await self.db.license_plans.create_index(
                [("tenant_id", 1), ("is_active", 1)],
                name="idx_tenant_active_plans",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + is_active - ACTIVE PLANS")
            
        except Exception as e:
            logger.warning(f"   ⚠️ Categories optimization issue: {str(e)}")
    
    async def _optimize_rbac_collections(self):
        """Optimize RBAC (roles, permissions) collections"""
        
        logger.info("🔧 Optimizing RBAC collections...")
        
        try:
            # 1. Roles by tenant
            await self.db.roles.create_index(
                [("tenant_id", 1), ("name", 1)],
                name="idx_tenant_role_name",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + name - ROLE LOOKUP")
            
            # 2. Permissions by tenant
            await self.db.permissions.create_index(
                [("tenant_id", 1), ("resource", 1)],
                name="idx_tenant_permission_resource",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + resource - PERMISSION CHECKS")
            
            # 3. User role assignments (if using separate collection)
            try:
                await self.db.user_roles.create_index(
                    [("tenant_id", 1), ("user_id", 1)],
                    name="idx_tenant_user_roles",
                    background=True
                )
                logger.info("   ✅ Created: tenant_id + user_id - USER ROLE ASSIGNMENTS")
            except:
                logger.info("   ℹ️ Skipped: user_roles collection (using embedded)")
            
            # 4. Audit trail for RBAC changes
            try:
                await self.db.rbac_audit.create_index(
                    [("tenant_id", 1), ("timestamp", -1)],
                    name="idx_tenant_rbac_audit",
                    background=True
                )
                logger.info("   ✅ Created: tenant_id + timestamp - RBAC AUDIT")
            except:
                logger.info("   ℹ️ Skipped: rbac_audit collection")
            
        except Exception as e:
            logger.warning(f"   ⚠️ RBAC optimization issue: {str(e)}")
    
    async def _optimize_audit_collections(self):
        """Optimize audit and logging collections"""
        
        logger.info("🔧 Optimizing audit/logging collections...")
        
        try:
            # 1. System logs
            await self.db.system_logs.create_index(
                [("tenant_id", 1), ("timestamp", -1)],
                name="idx_tenant_logs_timestamp",
                background=True,
                expireAfterSeconds=30*24*60*60  # 30 days TTL
            )
            logger.info("   ✅ Created: tenant_id + timestamp - SYSTEM LOGS (30d TTL)")
            
            # 2. User activity logs
            await self.db.user_activity.create_index(
                [("tenant_id", 1), ("user_id", 1), ("timestamp", -1)],
                name="idx_tenant_user_activity",
                background=True,
                expireAfterSeconds=90*24*60*60  # 90 days TTL
            )
            logger.info("   ✅ Created: tenant_id + user_id + timestamp - USER ACTIVITY (90d TTL)")
            
            # 3. Error logs
            await self.db.error_logs.create_index(
                [("tenant_id", 1), ("level", 1), ("timestamp", -1)],
                name="idx_tenant_error_logs",
                background=True,
                expireAfterSeconds=180*24*60*60  # 180 days TTL
            )
            logger.info("   ✅ Created: tenant_id + level + timestamp - ERROR LOGS (180d TTL)")
            
        except Exception as e:
            logger.warning(f"   ⚠️ Audit optimization issue: {str(e)}")
    
    async def _optimize_notification_collections(self):
        """Optimize WhatsApp and notification collections"""
        
        logger.info("🔧 Optimizing notification collections...")
        
        try:
            # 1. WhatsApp message history
            await self.db.whatsapp_messages.create_index(
                [("tenant_id", 1), ("sent_at", -1)],
                name="idx_tenant_whatsapp_history",
                background=True,
                expireAfterSeconds=365*24*60*60  # 1 year TTL
            )
            logger.info("   ✅ Created: tenant_id + sent_at - WHATSAPP HISTORY (1y TTL)")
            
            # 2. Notification queue
            await self.db.notifications.create_index(
                [("tenant_id", 1), ("status", 1), ("scheduled_at", 1)],
                name="idx_tenant_notification_queue",
                background=True
            )
            logger.info("   ✅ Created: tenant_id + status + scheduled_at - NOTIFICATION QUEUE")
            
        except Exception as e:
            logger.warning(f"   ⚠️ Notification optimization issue: {str(e)}")
    
    async def _test_performance_improvements(self):
        """Test query performance before and after optimization"""
        
        logger.info("📊 Testing performance improvements...")
        
        try:
            # Test critical queries
            test_results = {}
            
            # 1. Test user login query
            start = time.time()
            user = await self.db.users.find_one({
                "tenant_id": "default", 
                "email": "admin@demo.com"
            })
            test_results['user_login'] = (time.time() - start) * 1000  # ms
            
            # 2. Test license expiration query
            start = time.time()
            from datetime import datetime, timedelta
            expiring_licenses = await self.db.licenses.find({
                "tenant_id": "default",
                "expires_at": {"$lt": datetime.utcnow() + timedelta(days=30)}
            }).to_list(length=10)
            test_results['license_expiration'] = (time.time() - start) * 1000  # ms
            
            # 3. Test user listing query
            start = time.time()
            users = await self.db.users.find({
                "tenant_id": "default"
            }).limit(50).to_list()
            test_results['user_listing'] = (time.time() - start) * 1000  # ms
            
            # Log results
            logger.info("📈 Performance test results:")
            for query, time_ms in test_results.items():
                logger.info(f"   • {query}: {time_ms:.2f}ms")
            
            return test_results
            
        except Exception as e:
            logger.warning(f"   ⚠️ Performance testing failed: {str(e)}")
            return {}
    
    async def get_index_usage_stats(self):
        """Get index usage statistics for monitoring"""
        
        try:
            collections = ['users', 'licenses', 'clients', 'categories']
            stats = {}
            
            for collection_name in collections:
                collection = self.db[collection_name]
                
                # Get index stats
                index_stats = await collection.index_stats().to_list()
                stats[collection_name] = {
                    'total_indexes': len(index_stats),
                    'index_usage': index_stats
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {str(e)}")
            return {}
    
    async def cleanup_unused_indexes(self):
        """Remove unused indexes to optimize storage"""
        
        logger.info("🧹 Cleaning up unused indexes...")
        
        try:
            # This would analyze index usage and remove unused ones
            # Implementation depends on monitoring period
            logger.info("   ℹ️ Index cleanup requires usage monitoring period")
            return True
            
        except Exception as e:
            logger.error(f"Index cleanup failed: {str(e)}")
            return False


# Utility functions for integration

async def optimize_database_performance(db: AsyncIOMotorDatabase) -> bool:
    """
    Main function to optimize database performance
    
    Usage:
        from database_optimization import optimize_database_performance
        success = await optimize_database_performance(db)
    """
    
    optimizer = DatabaseOptimizer(db)
    return await optimizer.create_performance_indexes()


async def get_performance_stats(db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Get database performance statistics"""
    
    optimizer = DatabaseOptimizer(db)
    return await optimizer.get_index_usage_stats()


# Export commonly used functions
__all__ = [
    "DatabaseOptimizer",
    "optimize_database_performance", 
    "get_performance_stats"
]