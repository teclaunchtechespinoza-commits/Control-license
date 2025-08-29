#!/usr/bin/env python3
"""
Database Optimizer - MongoDB Indexes & Performance
Implementação de índices críticos e verificação de limites de plano
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from datetime import datetime
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    def __init__(self):
        load_dotenv('backend/.env')
        self.mongo_url = os.environ['MONGO_URL']
        self.db_name = os.environ['DB_NAME']
        self.client = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.db_name]
        logger.info(f"Connected to MongoDB: {self.db_name}")
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def clean_duplicate_data(self):
        """Clean duplicate data before creating unique indexes"""
        logger.info("🧹 Cleaning duplicate data...")
        
        try:
            # Clean duplicate CPF in clientes_pf
            logger.info("Cleaning duplicate CPF in clientes_pf...")
            
            # Find duplicates by CPF within same tenant
            pipeline = [
                {"$group": {
                    "_id": {"tenant_id": "$tenant_id", "cpf": "$cpf"},
                    "count": {"$sum": 1},
                    "docs": {"$push": "$_id"}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            duplicates = await self.db.clientes_pf.aggregate(pipeline).to_list(None)
            
            for duplicate in duplicates:
                # Keep the first document, remove the rest
                docs_to_remove = duplicate["docs"][1:]  # Skip first, remove rest
                if docs_to_remove:
                    logger.info(f"Removing {len(docs_to_remove)} duplicate CPF entries: {duplicate['_id']['cpf']}")
                    await self.db.clientes_pf.delete_many({"_id": {"$in": docs_to_remove}})
            
            # Clean duplicate CNPJ in clientes_pj
            logger.info("Cleaning duplicate CNPJ in clientes_pj...")
            
            pipeline = [
                {"$group": {
                    "_id": {"tenant_id": "$tenant_id", "cnpj": "$cnpj"},
                    "count": {"$sum": 1},
                    "docs": {"$push": "$_id"}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            duplicates = await self.db.clientes_pj.aggregate(pipeline).to_list(None)
            
            for duplicate in duplicates:
                docs_to_remove = duplicate["docs"][1:]
                if docs_to_remove:
                    logger.info(f"Removing {len(docs_to_remove)} duplicate CNPJ entries: {duplicate['_id']['cnpj']}")
                    await self.db.clientes_pj.delete_many({"_id": {"$in": docs_to_remove}})
            
            # Clean duplicate emails in users
            logger.info("Cleaning duplicate emails in users...")
            
            pipeline = [
                {"$group": {
                    "_id": {"email": "$email"},
                    "count": {"$sum": 1},
                    "docs": {"$push": "$_id"}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            duplicates = await self.db.users.aggregate(pipeline).to_list(None)
            
            for duplicate in duplicates:
                docs_to_remove = duplicate["docs"][1:]
                if docs_to_remove:
                    logger.info(f"Removing {len(docs_to_remove)} duplicate email entries: {duplicate['_id']['email']}")
                    await self.db.users.delete_many({"_id": {"$in": docs_to_remove}})
            
            # Clean duplicate category names within tenant
            logger.info("Cleaning duplicate category names...")
            
            pipeline = [
                {"$group": {
                    "_id": {"tenant_id": "$tenant_id", "name": "$name"},
                    "count": {"$sum": 1},
                    "docs": {"$push": "$_id"}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            duplicates = await self.db.categories.aggregate(pipeline).to_list(None)
            
            for duplicate in duplicates:
                docs_to_remove = duplicate["docs"][1:]
                if docs_to_remove:
                    logger.info(f"Removing {len(docs_to_remove)} duplicate category entries: {duplicate['_id']['name']}")
                    await self.db.categories.delete_many({"_id": {"$in": docs_to_remove}})
            
            # Clean duplicate product names within tenant
            logger.info("Cleaning duplicate product names...")
            
            pipeline = [
                {"$group": {
                    "_id": {"tenant_id": "$tenant_id", "name": "$name"},
                    "count": {"$sum": 1},
                    "docs": {"$push": "$_id"}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            duplicates = await self.db.products.aggregate(pipeline).to_list(None)
            
            for duplicate in duplicates:
                docs_to_remove = duplicate["docs"][1:]
                if docs_to_remove:
                    logger.info(f"Removing {len(docs_to_remove)} duplicate product entries: {duplicate['_id']['name']}")
                    await self.db.products.delete_many({"_id": {"$in": docs_to_remove}})
            
            logger.info("✅ Duplicate data cleanup completed")
            
        except Exception as e:
            logger.warning(f"Duplicate cleanup failed (non-critical): {e}")
    
    async def create_critical_indexes(self):
        """Create critical performance indexes"""
        logger.info("🚀 Creating critical MongoDB indexes...")
        
        # Clean duplicates first
        await self.clean_duplicate_data()
        
        # 1. LICENSES COLLECTION - Critical for expiry checks and tenant isolation
        licenses_indexes = [
            # Tenant isolation + expiry queries (most critical)
            IndexModel([("tenant_id", ASCENDING), ("expires_at", ASCENDING)], 
                      name="tenant_expires_idx", background=True),
            
            # Tenant isolation + status queries  
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], 
                      name="tenant_status_idx", background=True),
            
            # Tenant isolation + assigned user (user dashboard)
            IndexModel([("tenant_id", ASCENDING), ("assigned_user_id", ASCENDING)], 
                      name="tenant_user_idx", background=True),
            
            # License key uniqueness (global) - make sparse for existing data
            IndexModel([("license_key", ASCENDING)], 
                      name="license_key_unique_idx", unique=True, sparse=True, background=True),
            
            # Full-text search on license names
            IndexModel([("name", TEXT), ("description", TEXT)], 
                      name="license_text_search_idx", background=True),
            
            # Created date for reporting
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], 
                      name="tenant_created_desc_idx", background=True)
        ]
        
        await self.db.licenses.create_indexes(licenses_indexes)
        logger.info("✅ Licenses indexes created")
        
        # 2. USERS COLLECTION - Critical for auth and tenant queries
        users_indexes = [
            # Email uniqueness (login)
            IndexModel([("email", ASCENDING)], 
                      name="email_unique_idx", unique=True, background=True),
            
            # Tenant isolation + active status
            IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING)], 
                      name="tenant_active_users_idx", background=True),
            
            # Role-based queries
            IndexModel([("tenant_id", ASCENDING), ("role", ASCENDING)], 
                      name="tenant_role_idx", background=True),
            
            # Last login tracking
            IndexModel([("tenant_id", ASCENDING), ("last_login", DESCENDING)], 
                      name="tenant_last_login_idx", background=True)
        ]
        
        await self.db.users.create_indexes(users_indexes)
        logger.info("✅ Users indexes created")
        
        # 3. CLIENTES_PF COLLECTION - Critical for client management
        clientes_pf_indexes = [
            # Tenant isolation + status
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], 
                      name="tenant_status_pf_idx", background=True),
            
            # CPF uniqueness within tenant - make sparse for existing data
            IndexModel([("tenant_id", ASCENDING), ("cpf", ASCENDING)], 
                      name="tenant_cpf_idx", unique=True, sparse=True, background=True),
            
            # Name search within tenant
            IndexModel([("tenant_id", ASCENDING), ("nome_completo", ASCENDING)], 
                      name="tenant_name_pf_idx", background=True),
            
            # Text search for clients
            IndexModel([("nome_completo", TEXT), ("email_principal", TEXT)], 
                      name="client_pf_text_search_idx", background=True)
        ]
        
        await self.db.clientes_pf.create_indexes(clientes_pf_indexes)
        logger.info("✅ Clientes PF indexes created")
        
        # 4. CLIENTES_PJ COLLECTION - Critical for business client management
        clientes_pj_indexes = [
            # Tenant isolation + status
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], 
                      name="tenant_status_pj_idx", background=True),
            
            # CNPJ uniqueness within tenant - make sparse for existing data
            IndexModel([("tenant_id", ASCENDING), ("cnpj", ASCENDING)], 
                      name="tenant_cnpj_idx", unique=True, sparse=True, background=True),
            
            # CNPJ normalized for exact matches (remove this problematic index)
            # IndexModel([("tenant_id", ASCENDING), ("cnpj_normalizado", ASCENDING)], 
            #           name="tenant_cnpj_norm_idx", unique=True, sparse=True, background=True),
            
            # Company name search within tenant
            IndexModel([("tenant_id", ASCENDING), ("razao_social", ASCENDING)], 
                      name="tenant_razao_social_idx", background=True),
            
            # Text search for business clients
            IndexModel([("razao_social", TEXT), ("nome_fantasia", TEXT)], 
                      name="client_pj_text_search_idx", background=True)
        ]
        
        await self.db.clientes_pj.create_indexes(clientes_pj_indexes)
        logger.info("✅ Clientes PJ indexes created")
        
        # 5. CATEGORIES COLLECTION - Registry module optimization
        categories_indexes = [
            # Tenant isolation + active status
            IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING)], 
                      name="tenant_active_categories_idx", background=True),
            
            # Name uniqueness within tenant
            IndexModel([("tenant_id", ASCENDING), ("name", ASCENDING)], 
                      name="tenant_category_name_idx", unique=True, background=True)
        ]
        
        await self.db.categories.create_indexes(categories_indexes)
        logger.info("✅ Categories indexes created")
        
        # 6. PRODUCTS COLLECTION - Product management optimization
        products_indexes = [
            # Tenant isolation + active status
            IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING)], 
                      name="tenant_active_products_idx", background=True),
            
            # Category relationship
            IndexModel([("tenant_id", ASCENDING), ("category_id", ASCENDING)], 
                      name="tenant_category_products_idx", background=True),
            
            # Product name search within tenant
            IndexModel([("tenant_id", ASCENDING), ("name", ASCENDING)], 
                      name="tenant_product_name_idx", background=True),
            
            # Text search for products
            IndexModel([("name", TEXT), ("description", TEXT)], 
                      name="product_text_search_idx", background=True)
        ]
        
        await self.db.products.create_indexes(products_indexes)
        logger.info("✅ Products indexes created")
        
        # 7. NOTIFICATION SYSTEM - Job processing optimization
        notification_indexes = [
            # Queue processing (most critical for job system)
            IndexModel([("tenant_id", ASCENDING), ("process_after", ASCENDING), ("is_processing", ASCENDING)], 
                      name="notification_queue_idx", background=True),
            
            # Notification logs for debugging
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], 
                      name="notification_logs_idx", background=True),
            
            # Notification status tracking
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)], 
                      name="notification_status_idx", background=True)
        ]
        
        # Only create if collections exist
        collections = await self.db.list_collection_names()
        if "notification_queue" in collections:
            await self.db.notification_queue.create_indexes([notification_indexes[0]])
        if "notification_logs" in collections:
            await self.db.notification_logs.create_indexes([notification_indexes[1]])
        if "notifications" in collections:
            await self.db.notifications.create_indexes([notification_indexes[2]])
        
        logger.info("✅ Notification system indexes created")
        
        # 8. RBAC SYSTEM - Permissions and roles optimization
        rbac_indexes = [
            # Role name uniqueness within tenant
            IndexModel([("tenant_id", ASCENDING), ("name", ASCENDING)], 
                      name="tenant_role_name_idx", unique=True, sparse=True, background=True),
            
            # Permission name for fast lookups
            IndexModel([("name", ASCENDING)], 
                      name="permission_name_idx", unique=True, background=True),
            
            # System roles (global)
            IndexModel([("is_system", ASCENDING), ("name", ASCENDING)], 
                      name="system_roles_idx", background=True)
        ]
        
        if "roles" in collections:
            await self.db.roles.create_indexes([rbac_indexes[0], rbac_indexes[2]])
        if "permissions" in collections:
            await self.db.permissions.create_indexes([rbac_indexes[1]])
        
        logger.info("✅ RBAC system indexes created")
        
        # 9. TENANTS COLLECTION - Multi-tenancy management
        if "tenants" in collections:
            tenant_indexes = [
                # Subdomain uniqueness (routing)
                IndexModel([("subdomain", ASCENDING)], 
                          name="subdomain_unique_idx", unique=True, background=True),
                
                # Status + plan for billing queries
                IndexModel([("status", ASCENDING), ("plan", ASCENDING)], 
                          name="status_plan_idx", background=True),
                
                # Active tenants only
                IndexModel([("is_active", ASCENDING), ("status", ASCENDING)], 
                          name="active_tenants_idx", background=True)
            ]
            
            await self.db.tenants.create_indexes(tenant_indexes)
            logger.info("✅ Tenants indexes created")
        
        logger.info("🎉 All critical indexes created successfully!")
    
    async def create_plan_limits_enforcement(self):
        """Create database-level plan limit enforcement"""
        logger.info("🔒 Implementing plan limits enforcement...")
        
        # Create a validation schema for tenant limits
        tenant_validation = {
            "$jsonSchema": {
                "bsonType": "object",
                "properties": {
                    "current_users": {
                        "bsonType": "int",
                        "minimum": 0,
                        "description": "Current user count must be non-negative"
                    },
                    "current_licenses": {
                        "bsonType": "int", 
                        "minimum": 0,
                        "description": "Current license count must be non-negative"
                    },
                    "current_clients": {
                        "bsonType": "int",
                        "minimum": 0, 
                        "description": "Current client count must be non-negative"
                    },
                    "max_users": {
                        "bsonType": "int",
                        "minimum": -1,
                        "description": "Max users limit (-1 for unlimited)"
                    },
                    "max_licenses": {
                        "bsonType": "int",
                        "minimum": -1,
                        "description": "Max licenses limit (-1 for unlimited)"
                    },
                    "max_clients": {
                        "bsonType": "int", 
                        "minimum": -1,
                        "description": "Max clients limit (-1 for unlimited)"
                    }
                }
            }
        }
        
        try:
            # Apply validation to tenants collection
            await self.db.command({
                "collMod": "tenants",
                "validator": tenant_validation,
                "validationLevel": "moderate",  # Don't break existing data
                "validationAction": "warn"      # Log violations instead of rejecting
            })
            logger.info("✅ Tenant validation rules applied")
        except Exception as e:
            logger.warning(f"Could not apply tenant validation: {e}")
        
        # Create helper indexes for limit checking
        limit_check_indexes = [
            # Fast tenant metrics updates
            IndexModel([("id", ASCENDING)], name="tenant_id_idx", background=True),
            
            # Plan-based queries for billing
            IndexModel([("plan", ASCENDING), ("status", ASCENDING)], 
                      name="plan_status_idx", background=True)
        ]
        
        try:
            collections = await self.db.list_collection_names()
            if "tenants" in collections:
                await self.db.tenants.create_indexes(limit_check_indexes)
                logger.info("✅ Plan limits indexes created")
        except Exception as e:
            logger.warning(f"Could not create limit indexes: {e}")
    
    async def analyze_query_performance(self):
        """Analyze query performance with new indexes"""
        logger.info("📊 Analyzing query performance...")
        
        try:
            # Test critical queries with explain()
            test_queries = [
                # Expiring licenses query (most critical)
                ("licenses", {"tenant_id": "default", "expires_at": {"$lt": datetime.utcnow()}}),
                
                # User lookup by email  
                ("users", {"email": "superadmin@autotech.com"}),
                
                # Active clients by tenant
                ("clientes_pf", {"tenant_id": "default", "status": {"$ne": "inactive"}}),
                
                # Product search by category
                ("products", {"tenant_id": "default", "category_id": {"$exists": True}})
            ]
            
            for collection_name, query in test_queries:
                if collection_name in await self.db.list_collection_names():
                    collection = self.db[collection_name]
                    explain_result = await collection.find(query).explain()
                    
                    execution_stats = explain_result.get("executionStats", {})
                    winning_plan = explain_result.get("queryPlanner", {}).get("winningPlan", {})
                    
                    logger.info(f"Query on {collection_name}:")
                    logger.info(f"  - Execution time: {execution_stats.get('executionTimeMillis', 0)}ms")
                    logger.info(f"  - Documents examined: {execution_stats.get('totalDocsExamined', 0)}")
                    logger.info(f"  - Index used: {winning_plan.get('inputStage', {}).get('indexName', 'Collection scan')}")
            
        except Exception as e:
            logger.warning(f"Performance analysis failed: {e}")
    
    async def get_index_statistics(self):
        """Get comprehensive index statistics"""
        logger.info("📈 Gathering index statistics...")
        
        try:
            collections = await self.db.list_collection_names()
            main_collections = ["licenses", "users", "clientes_pf", "clientes_pj", "products", "categories"]
            
            total_indexes = 0
            for collection_name in main_collections:
                if collection_name in collections:
                    collection = self.db[collection_name]
                    indexes = await collection.list_indexes().to_list(None)
                    
                    logger.info(f"\n📁 {collection_name.upper()} ({len(indexes)} indexes):")
                    for idx in indexes:
                        idx_name = idx.get("name", "unknown")
                        idx_keys = idx.get("key", {})
                        idx_unique = "UNIQUE" if idx.get("unique", False) else ""
                        idx_sparse = "SPARSE" if idx.get("sparse", False) else ""
                        
                        key_str = ", ".join([f"{k}:{v}" for k, v in idx_keys.items()])
                        flags = " ".join(filter(None, [idx_unique, idx_sparse]))
                        
                        logger.info(f"  ✅ {idx_name}: ({key_str}) {flags}")
                        total_indexes += 1
            
            logger.info(f"\n🎯 SUMMARY: {total_indexes} indexes created across {len(main_collections)} collections")
            
        except Exception as e:
            logger.error(f"Failed to get index statistics: {e}")
    
    async def optimize_database(self):
        """Main optimization routine"""
        logger.info("🚀 Starting MongoDB Database Optimization...")
        
        await self.connect()
        
        try:
            # Step 1: Create critical indexes
            await self.create_critical_indexes()
            
            # Step 2: Implement plan limits
            await self.create_plan_limits_enforcement()
            
            # Step 3: Analyze performance
            await self.analyze_query_performance()
            
            # Step 4: Get statistics
            await self.get_index_statistics()
            
            logger.info("✅ Database optimization completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Database optimization failed: {e}")
            raise
        finally:
            await self.close()

# Helper function for use in FastAPI startup
async def initialize_database_optimization():
    """Initialize database optimization (for use in FastAPI startup)"""
    optimizer = DatabaseOptimizer()
    await optimizer.optimize_database()

# CLI usage
if __name__ == "__main__":
    async def main():
        optimizer = DatabaseOptimizer()
        await optimizer.optimize_database()
    
    asyncio.run(main())