#!/usr/bin/env python3
"""
Simple test script to verify health check endpoints work correctly
"""
import asyncio
import sys
import os
sys.path.append('/app/backend')

from fastapi.testclient import TestClient

async def test_health_endpoints():
    try:
        # Import the app
        from server import app
        
        # Create test client
        client = TestClient(app)
        
        print("Testing health check endpoints...")
        
        # Test root-level health check
        print("\n1. Testing /health (root-level):")
        try:
            response = client.get("/health")
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
                
                # Verify expected fields
                expected_fields = ["status", "timestamp", "version", "service"]
                for field in expected_fields:
                    if field in data:
                        print(f"   ✅ {field}: {data[field]}")
                    else:
                        print(f"   ❌ Missing field: {field}")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error testing /health: {e}")
        
        # Test API health check
        print("\n2. Testing /api/health:")
        try:
            response = client.get("/api/health")
            print(f"   Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
                
                # Verify expected fields
                expected_fields = ["status", "timestamp", "version", "service"]
                for field in expected_fields:
                    if field in data:
                        print(f"   ✅ {field}: {data[field]}")
                    else:
                        print(f"   ❌ Missing field: {field}")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error testing /api/health: {e}")
            
        print("\n✅ Health check endpoint tests completed!")
        
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_health_endpoints())