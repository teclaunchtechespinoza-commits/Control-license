#!/usr/bin/env python3

import asyncio
import redis.asyncio as redis
import sys

async def test_redis_connection():
    """Test Redis connection directly"""
    try:
        # Test connection to Redis
        redis_client = redis.from_url(
            "redis://localhost:6379/0",
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test ping
        result = await redis_client.ping()
        print(f"✅ Redis PING successful: {result}")
        
        # Test set/get
        await redis_client.set("test_key", "test_value", ex=60)
        value = await redis_client.get("test_key")
        print(f"✅ Redis SET/GET successful: {value}")
        
        # Test info
        info = await redis_client.info()
        print(f"✅ Redis INFO successful:")
        print(f"   - Used memory: {info.get('used_memory_human', 'N/A')}")
        print(f"   - Connected clients: {info.get('connected_clients', 0)}")
        print(f"   - Total commands: {info.get('total_commands_processed', 0)}")
        
        # Clean up
        await redis_client.delete("test_key")
        await redis_client.close()
        
        print("✅ Redis connection test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection test FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_redis_connection())
    sys.exit(0 if success else 1)