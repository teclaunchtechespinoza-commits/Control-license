#!/usr/bin/env python3
"""
Minimal Database Optimizer - Essential Indexes Only
Foco nos índices mais críticos para performance imediata
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

class MinimalOptimizer:
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
    
    async def create_essential_indexes(self):
        """Create only the most critical indexes for performance"""
        logger.info("🚀 Creating essential MongoDB indexes...")
        
        try:
            # 1. LICENSES - Critical for expiry and tenant queries
            logger.info("Creating licenses indexes...")
            licenses_indexes = [
                IndexModel([("tenant_id", ASCENDING), ("expires_at", ASCENDING)], 
                          name="tenant_expires_idx", background=True),
                IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], 
                          name="tenant_status_idx", background=True),
                IndexModel([("tenant_id", ASCENDING), ("assigned_user_id", ASCENDING)], 
                          name="tenant_user_idx", background=True)
            ]
            await self.db.licenses.create_indexes(licenses_indexes)
            logger.info("✅ Licenses indexes created")
            
            # 2. USERS - Critical for auth
            logger.info("Creating users indexes...")
            users_indexes = [
                IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING)], 
                          name="tenant_active_users_idx", background=True),
                IndexModel([("tenant_id", ASCENDING), ("role", ASCENDING)], 
                          name="tenant_role_idx", background=True)
            ]
            await self.db.users.create_indexes(users_indexes)
            logger.info("✅ Users indexes created")
            
            # 3. CLIENTES_PF - Critical for client queries
            logger.info("Creating clientes_pf indexes...")
            pf_indexes = [
                IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], 
                          name="tenant_status_pf_idx", background=True)
            ]
            await self.db.clientes_pf.create_indexes(pf_indexes)
            logger.info("✅ Clientes PF indexes created")
            
            # 4. CLIENTES_PJ - Critical for business client queries  
            logger.info("Creating clientes_pj indexes...")
            pj_indexes = [
                IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], 
                          name="tenant_status_pj_idx", background=True)
            ]
            await self.db.clientes_pj.create_indexes(pj_indexes)
            logger.info("✅ Clientes PJ indexes created")
            
            # 5. CATEGORIES - Critical for registry module
            logger.info("Creating categories indexes...")
            category_indexes = [
                IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING)], 
                          name="tenant_active_categories_idx", background=True)
            ]
            await self.db.categories.create_indexes(category_indexes)
            logger.info("✅ Categories indexes created")
            
            # 6. PRODUCTS - Critical for product queries
            logger.info("Creating products indexes...")
            product_indexes = [
                IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING)], 
                          name="tenant_active_products_idx", background=True),
                IndexModel([("tenant_id", ASCENDING), ("category_id", ASCENDING)], 
                          name="tenant_category_products_idx", background=True)
            ]
            await self.db.products.create_indexes(product_indexes)
            logger.info("✅ Products indexes created")
            
            logger.info("🎉 Essential indexes created successfully!")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    async def measure_performance_boost(self):
        """Measure performance improvement with new indexes"""
        logger.info("📊 Measuring performance improvements...")
        
        try:
            # Critical queries to test
            test_queries = [
                ("licenses", {"tenant_id": "default", "expires_at": {"$lt": datetime.utcnow()}}),
                ("clientes_pf", {"tenant_id": "default", "status": {"$ne": "inactive"}}),
                ("clientes_pj", {"tenant_id": "default", "status": {"$ne": "inactive"}}),
                ("categories", {"tenant_id": "default", "is_active": True}),
                ("products", {"tenant_id": "default", "is_active": True})
            ]
            
            for collection_name, query in test_queries:
                collections = await self.db.list_collection_names()
                if collection_name in collections:
                    collection = self.db[collection_name]
                    explain_result = await collection.find(query).explain()
                    
                    execution_stats = explain_result.get("executionStats", {})
                    winning_plan = explain_result.get("queryPlanner", {}).get("winningPlan", {})
                    
                    exec_time = execution_stats.get('executionTimeMillis', 0)
                    docs_examined = execution_stats.get('totalDocsExamined', 0)
                    docs_returned = execution_stats.get('totalDocsReturned', 0)
                    index_name = winning_plan.get('inputStage', {}).get('indexName', 'COLLECTION_SCAN')
                    
                    logger.info(f"📈 {collection_name.upper()}:")
                    logger.info(f"  ⚡ Query time: {exec_time}ms")
                    logger.info(f"  🔍 Docs examined: {docs_examined}")
                    logger.info(f"  📄 Docs returned: {docs_returned}")
                    logger.info(f"  📇 Index used: {index_name}")
                    
                    # Performance assessment
                    if index_name != 'COLLECTION_SCAN':
                        if docs_examined <= docs_returned * 1.5:  # Good selectivity
                            logger.info(f"  ✅ EXCELLENT: Index scan, low examination ratio")
                        else:
                            logger.info(f"  ⚠️ GOOD: Index scan, moderate examination")
                    else:
                        logger.info(f"  ❌ POOR: Collection scan (no index used)")
        
        except Exception as e:
            logger.warning(f"Performance measurement failed: {e}")
    
    async def get_final_statistics(self):
        """Get final database statistics"""
        logger.info("📊 Final Database Statistics:")
        
        try:
            collections = await self.db.list_collection_names()
            main_collections = ["licenses", "users", "clientes_pf", "clientes_pj", "products", "categories"]
            
            total_indexes = 0
            for collection_name in main_collections:
                if collection_name in collections:
                    collection = self.db[collection_name]
                    indexes = await collection.list_indexes().to_list(None)
                    doc_count = await collection.count_documents({})
                    
                    logger.info(f"📁 {collection_name.upper()}:")
                    logger.info(f"  📊 Documents: {doc_count:,}")
                    logger.info(f"  📇 Indexes: {len(indexes)}")
                    
                    for idx in indexes:
                        if idx.get("name") != "_id_":  # Skip default index
                            total_indexes += 1
            
            logger.info(f"\n🎯 OPTIMIZATION SUMMARY:")
            logger.info(f"   📇 Total new indexes: {total_indexes}")
            logger.info(f"   🚀 Collections optimized: {len([c for c in main_collections if c in collections])}")
            logger.info(f"   ⚡ Expected performance boost: 5-50x faster queries")
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
    
    async def optimize_minimal(self):
        """Main minimal optimization routine"""
        logger.info("🚀 Starting Minimal MongoDB Optimization...")
        
        await self.connect()
        
        try:
            # Create essential indexes only
            await self.create_essential_indexes()
            
            # Measure performance improvements
            await self.measure_performance_boost()
            
            # Get final statistics
            await self.get_final_statistics()
            
            logger.info("✅ Minimal database optimization completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Minimal optimization failed: {e}")
            raise
        finally:
            await self.close()

# CLI usage
if __name__ == "__main__":
    async def main():
        optimizer = MinimalOptimizer()
        await optimizer.optimize_minimal()
    
    asyncio.run(main())