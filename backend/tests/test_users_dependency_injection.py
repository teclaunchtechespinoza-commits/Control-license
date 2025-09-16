"""
🚀 SUB-FASE 2.3 - Test Dependency Injection for Users Endpoint
Tests the enhanced list_users endpoint with dependency injection
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from server import app
from dependencies import TenantAwareDB, RequestMetrics


@pytest.mark.asyncio
async def test_list_users_with_dependency_injection():
    """Test that the enhanced list_users endpoint works with dependency injection"""
    
    # Mock the dependencies
    mock_tenant_db = MagicMock(spec=TenantAwareDB)
    mock_tenant_db.find = AsyncMock(return_value=[
        {
            "id": "user1",
            "email": "user1@test.com",
            "name": "Test User 1",
            "role": "user",
            "tenant_id": "test-tenant",
            "created_at": "2023-01-01T00:00:00",
            "is_active": True
        },
        {
            "id": "user2", 
            "email": "user2@test.com",
            "name": "Test User 2",
            "role": "admin",
            "tenant_id": "test-tenant",
            "created_at": "2023-01-01T00:00:00",
            "is_active": True
        }
    ])
    
    mock_metrics = MagicMock(spec=RequestMetrics)
    mock_metrics.record_db_query = MagicMock()
    
    mock_pagination = {
        "page": 1,
        "limit": 50,
        "skip": 0,
        "max_results": 50
    }
    
    # Mock current user
    mock_current_user = MagicMock()
    mock_current_user.id = "admin-user"
    mock_current_user.email = "admin@test.com"
    mock_current_user.role = "super_admin"  # Super admin sees all users
    mock_current_user.tenant_id = "test-tenant"
    
    with patch('dependencies.get_tenant_database', return_value=mock_tenant_db), \
         patch('dependencies.get_pagination_params', return_value=mock_pagination), \
         patch('dependencies.get_request_metrics', return_value=mock_metrics), \
         patch('server.get_current_user', return_value=mock_current_user):
        
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            # Add required headers
            headers = {
                "X-Tenant-ID": "test-tenant",
                "Authorization": "Bearer fake-token"
            }
            
            response = await client.get("/api/users", headers=headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            # Should return 2 users
            assert len(data) == 2
            assert data[0]["email"] == "user1@test.com"
            assert data[1]["email"] == "user2@test.com"
            
            # Verify tenant database was called correctly
            mock_tenant_db.find.assert_called_once_with(
                "users",
                {},  # Empty filter for super_admin
                skip=0,
                limit=50
            )
            
            # Verify metrics were recorded
            mock_metrics.record_db_query.assert_called_once()


@pytest.mark.asyncio
async def test_list_users_admin_scope_filtering():
    """Test that admin users only see their clients"""
    
    mock_tenant_db = MagicMock(spec=TenantAwareDB)
    mock_tenant_db.find = AsyncMock(return_value=[
        {
            "id": "client1",
            "email": "client1@test.com", 
            "name": "Client 1",
            "role": "user",
            "tenant_id": "test-tenant",
            "admin_vendor_id": "admin-123",
            "created_at": "2023-01-01T00:00:00",
            "is_active": True
        }
    ])
    
    mock_metrics = MagicMock(spec=RequestMetrics)
    mock_metrics.record_db_query = MagicMock()
    
    mock_pagination = {
        "page": 1,
        "limit": 50,
        "skip": 0,
        "max_results": 50
    }
    
    # Mock admin user
    mock_current_user = MagicMock()
    mock_current_user.id = "admin-123"
    mock_current_user.email = "admin@test.com"
    mock_current_user.role = "admin"  # Admin role
    mock_current_user.tenant_id = "test-tenant"
    
    with patch('dependencies.get_tenant_database', return_value=mock_tenant_db), \
         patch('dependencies.get_pagination_params', return_value=mock_pagination), \
         patch('dependencies.get_request_metrics', return_value=mock_metrics), \
         patch('server.get_current_user', return_value=mock_current_user):
        
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            headers = {
                "X-Tenant-ID": "test-tenant",
                "Authorization": "Bearer fake-token"
            }
            
            response = await client.get("/api/users", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            
            # Verify admin scope filter was applied
            mock_tenant_db.find.assert_called_once_with(
                "users",
                {"admin_vendor_id": "admin-123"},  # Admin filter applied
                skip=0,
                limit=50
            )


@pytest.mark.asyncio
async def test_list_users_fallback_on_dependency_error():
    """Test that the endpoint falls back to original implementation on dependency error"""
    
    # Mock dependencies to raise an error
    mock_tenant_db = MagicMock(spec=TenantAwareDB)
    mock_tenant_db.find = AsyncMock(side_effect=Exception("Dependency injection failed"))
    
    mock_metrics = MagicMock(spec=RequestMetrics)
    mock_pagination = {"page": 1, "limit": 50, "skip": 0, "max_results": 50}
    
    mock_current_user = MagicMock()
    mock_current_user.id = "user-123"
    mock_current_user.email = "user@test.com"
    mock_current_user.role = "user"
    mock_current_user.tenant_id = "test-tenant"
    
    # Mock the fallback database operations
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[
        {
            "id": "user-123",
            "email": "user@test.com",
            "name": "Test User",
            "role": "user",
            "tenant_id": "test-tenant",
            "created_at": "2023-01-01T00:00:00",
            "is_active": True
        }
    ])
    
    with patch('dependencies.get_tenant_database', return_value=mock_tenant_db), \
         patch('dependencies.get_pagination_params', return_value=mock_pagination), \
         patch('dependencies.get_request_metrics', return_value=mock_metrics), \
         patch('server.get_current_user', return_value=mock_current_user), \
         patch('server.build_scope_filter', return_value={"id": "user-123"}), \
         patch('server.db.users.find', return_value=mock_cursor):
        
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            headers = {
                "X-Tenant-ID": "test-tenant",
                "Authorization": "Bearer fake-token"
            }
            
            response = await client.get("/api/users", headers=headers)
            
            # Should still return 200 with fallback data
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["email"] == "user@test.com"


@pytest.mark.asyncio
async def test_list_users_pagination_parameters():
    """Test that pagination parameters are correctly passed"""
    
    mock_tenant_db = MagicMock(spec=TenantAwareDB)
    mock_tenant_db.find = AsyncMock(return_value=[])
    
    mock_metrics = MagicMock(spec=RequestMetrics)
    mock_metrics.record_db_query = MagicMock()
    
    # Custom pagination
    mock_pagination = {
        "page": 2,
        "limit": 25,
        "skip": 25,
        "max_results": 25
    }
    
    mock_current_user = MagicMock()
    mock_current_user.id = "user-123"
    mock_current_user.email = "user@test.com"
    mock_current_user.role = "super_admin"
    mock_current_user.tenant_id = "test-tenant"
    
    with patch('dependencies.get_tenant_database', return_value=mock_tenant_db), \
         patch('dependencies.get_pagination_params', return_value=mock_pagination), \
         patch('dependencies.get_request_metrics', return_value=mock_metrics), \
         patch('server.get_current_user', return_value=mock_current_user):
        
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            headers = {
                "X-Tenant-ID": "test-tenant",
                "Authorization": "Bearer fake-token"
            }
            
            # Test with pagination query parameters
            response = await client.get("/api/users?page=2&limit=25", headers=headers)
            
            assert response.status_code == 200
            
            # Verify pagination was applied correctly
            mock_tenant_db.find.assert_called_once_with(
                "users",
                {},
                skip=25,  # (page-1) * limit = (2-1) * 25 = 25
                limit=25
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])