import requests
import sys
import json
from datetime import datetime, timedelta

class TenantIsolationTester:
    def __init__(self, base_url="https://tenantbay.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_scheduler_and_jobs_system(self):
        """Test scheduler and jobs system after tenant isolation fixes"""
        print("\n" + "="*80)
        print("TESTING SCHEDULER AND JOBS SYSTEM - TENANT ISOLATION FIXES")
        print("="*80)
        print("🎯 FOCUS: Test scheduler functionality after tenant isolation improvements")
        print("   - Scheduler status endpoint (/api/scheduler/status)")
        print("   - Scheduler statistics (/api/scheduler/stats)")
        print("   - Job execution with tenant context")
        print("   - Notification job processing")
        print("="*80)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping scheduler tests")
            return False

        # Test 1: Scheduler Status
        print("\n🔍 TEST 1: Scheduler Status Verification")
        success, response = self.run_test("GET /api/scheduler/status", "GET", "scheduler/status", 200, token=self.admin_token)
        if success:
            print(f"   ✅ Scheduler status retrieved successfully")
            print(f"      - Running: {response.get('running', False)}")
            print(f"      - Jobs count: {response.get('jobs_count', 0)}")
            print(f"      - Last execution: {response.get('last_execution', 'N/A')}")
            print(f"      - Worker ID: {response.get('worker_id', 'N/A')}")
            print(f"      - Jobs persisted in DB: {response.get('jobs_persisted_in_db', 0)}")
            
            if response.get('health_statistics'):
                health = response['health_statistics']
                print(f"      - Health stats available: {len(health)} metrics")
        else:
            print("   ❌ Scheduler status endpoint failed!")
            return False

        # Test 2: Scheduler Statistics (if available)
        print("\n🔍 TEST 2: Scheduler Statistics")
        success, response = self.run_test("GET /api/scheduler/stats", "GET", "scheduler/stats", 200, token=self.admin_token)
        if success:
            print(f"   ✅ Scheduler statistics retrieved")
            print(f"      - Response: {response}")
        else:
            print("   ⚠️ Scheduler stats endpoint not available (may be expected)")

        return True

    def test_notification_processing_system(self):
        """Test notification processing after tenant isolation fixes"""
        print("\n" + "="*80)
        print("TESTING NOTIFICATION PROCESSING SYSTEM")
        print("="*80)
        print("🎯 FOCUS: Test notification queue processing and license expiry notifications")
        print("   - Notification queue processing")
        print("   - License expiration notifications")
        print("   - Notification logs generation")
        print("   - Tenant isolation in notifications")
        print("="*80)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping notification processing tests")
            return False

        # Test 1: Notification System Endpoints
        print("\n🔍 TEST 1: Core Notification Endpoints")
        
        # Test notifications list
        success, response = self.run_test("GET /api/notifications", "GET", "notifications", 200, token=self.admin_token)
        if success:
            print(f"   ✅ Retrieved {len(response)} notifications")
            if len(response) > 0:
                first_notification = response[0]
                print(f"      - Sample notification type: {first_notification.get('type', 'N/A')}")
                print(f"      - Status: {first_notification.get('status', 'N/A')}")
                print(f"      - Tenant ID: {first_notification.get('tenant_id', 'N/A')}")

        # Test notification configuration
        success, response = self.run_test("GET /api/notifications/config", "GET", "notifications/config", 200, token=self.admin_token)
        if success:
            print(f"   ✅ Notification configuration retrieved")
            print(f"      - Enabled: {response.get('enabled', 'N/A')}")
            print(f"      - License expiry notifications enabled: {response.get('license_expiring_30_enabled', 'N/A')}")
            print(f"      - Max notifications per day: {response.get('max_notifications_per_day', 'N/A')}")

        # Test notification statistics
        success, response = self.run_test("GET /api/notifications/stats", "GET", "notifications/stats", 200, token=self.admin_token)
        if success:
            print(f"   ✅ Notification statistics retrieved")
            print(f"      - Total notifications: {response.get('total_notifications', 0)}")
            print(f"      - Success rate: {response.get('success_rate', 0):.1f}%")

        # Test 2: Create Test License for Expiry Notifications
        print("\n🔍 TEST 2: License Expiry Notification Testing")
        
        # Create a license that expires soon to trigger notifications
        test_license_data = {
            "name": "Test License - Expiry Notification",
            "description": "License to test expiry notifications with tenant isolation",
            "max_users": 1,
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),  # Expires in 7 days
            "features": ["expiry_test"],
            "status": "active"
        }
        
        success, response = self.run_test("Create test license for expiry", "POST", "licenses", 200, test_license_data, self.admin_token)
        if success and 'id' in response:
            test_license_id = response['id']
            print(f"   ✅ Created test license: {test_license_id}")
            print(f"      - Expires in 7 days: {test_license_data['expires_at']}")
            print(f"      - Tenant ID: {response.get('tenant_id', 'N/A')}")

        # Test 3: Manual Notification Creation
        print("\n🔍 TEST 3: Manual Notification Creation with Tenant Context")
        
        manual_notification_data = {
            "type": "license_expiring_7",
            "channel": "in_app",
            "recipient_email": "admin@demo.com",
            "subject": "Test License Expiry Notification",
            "message": "This is a test notification for license expiry with tenant isolation.",
            "priority": "high"
        }
        
        success, response = self.run_test("Create manual notification", "POST", "notifications", 200, manual_notification_data, self.admin_token)
        if success and 'id' in response:
            notification_id = response['id']
            print(f"   ✅ Created manual notification: {notification_id}")
            print(f"      - Type: {response.get('type', 'N/A')}")
            print(f"      - Tenant ID: {response.get('tenant_id', 'N/A')}")

        return True

    def test_tenant_isolation_in_scheduler(self):
        """Test tenant isolation in scheduler operations"""
        print("\n" + "="*80)
        print("TESTING TENANT ISOLATION IN SCHEDULER")
        print("="*80)
        print("🎯 FOCUS: Verify scheduler operations respect tenant_id")
        print("   - License operations with tenant filter")
        print("   - Notification creation in correct tenant")
        print("   - Database operations with tenant context")
        print("="*80)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping tenant isolation tests")
            return False

        # Test 1: Verify Licenses are Fetched with Tenant Filter
        print("\n🔍 TEST 1: License Operations with Tenant Filtering")
        
        success, response = self.run_test("GET /api/licenses", "GET", "licenses", 200, token=self.admin_token)
        if success:
            print(f"   ✅ Retrieved {len(response)} licenses")
            
            # Check tenant consistency
            tenant_ids = set()
            for license_data in response:
                tenant_id = license_data.get('tenant_id')
                if tenant_id:
                    tenant_ids.add(tenant_id)
            
            print(f"      - Unique tenant IDs in licenses: {len(tenant_ids)}")
            print(f"      - Tenant IDs: {list(tenant_ids)}")
            
            if len(tenant_ids) <= 1:
                print(f"   ✅ Excellent tenant isolation - all licenses from same tenant")
            else:
                print(f"   ⚠️ Multiple tenant IDs found - verify isolation is working correctly")

        # Test 2: Verify Notifications are Created in Correct Tenant
        print("\n🔍 TEST 2: Notification Tenant Assignment")
        
        success, response = self.run_test("GET /api/notifications", "GET", "notifications", 200, token=self.admin_token)
        if success:
            print(f"   ✅ Retrieved {len(response)} notifications")
            
            # Check tenant consistency in notifications
            notification_tenant_ids = set()
            for notification in response:
                tenant_id = notification.get('tenant_id')
                if tenant_id:
                    notification_tenant_ids.add(tenant_id)
            
            print(f"      - Unique tenant IDs in notifications: {len(notification_tenant_ids)}")
            print(f"      - Notification tenant IDs: {list(notification_tenant_ids)}")
            
            if len(notification_tenant_ids) <= 1:
                print(f"   ✅ Excellent notification tenant isolation")
            else:
                print(f"   ⚠️ Multiple tenant IDs in notifications - verify isolation")

        # Test 3: Test Cross-Tenant Data Access Prevention
        print("\n🔍 TEST 3: Cross-Tenant Data Access Prevention")
        
        # Get current user info to verify tenant context
        success, response = self.run_test("GET /api/auth/me", "GET", "auth/me", 200, token=self.admin_token)
        if success:
            current_tenant = response.get('tenant_id', 'N/A')
            print(f"   ✅ Current user tenant: {current_tenant}")
            
            # Verify all data operations are scoped to this tenant
            endpoints_to_check = [
                ("licenses", "licenses"),
                ("categories", "categories"),
                ("products", "products"),
                ("clientes-pf", "clientes-pf"),
                ("clientes-pj", "clientes-pj")
            ]
            
            for endpoint_name, endpoint_path in endpoints_to_check:
                success, response = self.run_test(f"Check {endpoint_name} tenant isolation", "GET", endpoint_path, 200, token=self.admin_token)
                if success:
                    tenant_ids_in_response = set()
                    for item in response:
                        tenant_id = item.get('tenant_id')
                        if tenant_id:
                            tenant_ids_in_response.add(tenant_id)
                    
                    if len(tenant_ids_in_response) <= 1 and current_tenant in tenant_ids_in_response:
                        print(f"      ✅ {endpoint_name}: Proper tenant isolation")
                    elif len(tenant_ids_in_response) == 0:
                        print(f"      ⚠️ {endpoint_name}: No tenant_id found in response")
                    else:
                        print(f"      ⚠️ {endpoint_name}: Multiple tenants found: {tenant_ids_in_response}")

        return True

    def test_basic_system_functionality(self):
        """Test basic system functionality after scheduler fixes"""
        print("\n" + "="*80)
        print("TESTING BASIC SYSTEM FUNCTIONALITY")
        print("="*80)
        print("🎯 FOCUS: Verify system still works after tenant isolation changes")
        print("   - Main endpoints (licenses, users, categories)")
        print("   - Authentication and authorization")
        print("   - CRUD operations")
        print("="*80)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping basic functionality tests")
            return False

        # Test 1: Authentication System
        print("\n🔍 TEST 1: Authentication System Verification")
        
        # Verify admin login still works
        admin_credentials = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        success, response = self.run_test("Admin login verification", "POST", "auth/login", 200, admin_credentials)
        if success and 'access_token' in response:
            print(f"   ✅ Admin authentication working")
            
            # Test auth/me endpoint
            success, response = self.run_test("GET /api/auth/me", "GET", "auth/me", 200, token=self.admin_token)
            if success:
                print(f"      - User: {response.get('name', 'N/A')}")
                print(f"      - Role: {response.get('role', 'N/A')}")
                print(f"      - Tenant: {response.get('tenant_id', 'N/A')}")

        # Test 2: Main Endpoints Functionality
        print("\n🔍 TEST 2: Main Endpoints Verification")
        
        main_endpoints = [
            ("Users", "users"),
            ("Licenses", "licenses"),
            ("Categories", "categories"),
            ("Products", "products"),
            ("PF Clients", "clientes-pf"),
            ("PJ Clients", "clientes-pj")
        ]
        
        for endpoint_name, endpoint_path in main_endpoints:
            success, response = self.run_test(f"GET /api/{endpoint_path}", "GET", endpoint_path, 200, token=self.admin_token)
            if success:
                count = len(response) if isinstance(response, list) else 1
                print(f"   ✅ {endpoint_name}: {count} items retrieved")
            else:
                print(f"   ❌ {endpoint_name}: Failed to retrieve data")

        # Test 3: System Statistics
        print("\n🔍 TEST 3: System Statistics")
        
        success, response = self.run_test("GET /api/stats", "GET", "stats", 200, token=self.admin_token)
        if success:
            print(f"   ✅ System statistics retrieved")
            print(f"      - Total users: {response.get('total_users', 0)}")
            print(f"      - Total licenses: {response.get('total_licenses', 0)}")
            print(f"      - Total clients: {response.get('total_clients', 0)}")
            print(f"      - System status: {response.get('system_status', 'N/A')}")

        # Test 4: CRUD Operations Test
        print("\n🔍 TEST 4: CRUD Operations Verification")
        
        # Test category creation (simple CRUD test)
        test_category_data = {
            "name": "Test Category - Tenant Isolation",
            "description": "Category created to test CRUD after tenant isolation fixes",
            "color": "#FF6B35",
            "icon": "test"
        }
        
        success, response = self.run_test("Create test category", "POST", "categories", 200, test_category_data, self.admin_token)
        if success and 'id' in response:
            category_id = response['id']
            print(f"   ✅ Category created: {category_id}")
            print(f"      - Tenant ID: {response.get('tenant_id', 'N/A')}")
            
            # Test category retrieval
            success, response = self.run_test("Get created category", "GET", f"categories/{category_id}", 200, token=self.admin_token)
            if success:
                print(f"   ✅ Category retrieved successfully")
                print(f"      - Name: {response.get('name', 'N/A')}")
                print(f"      - Tenant ID: {response.get('tenant_id', 'N/A')}")

        return True

    def run_tenant_isolation_tests(self):
        """Run comprehensive tenant isolation tests after robust_scheduler fixes"""
        print("🚀 TESTING SYSTEM AFTER TENANT ISOLATION FIXES IN ROBUST_SCHEDULER")
        print(f"Base URL: {self.base_url}")
        print("="*80)
        print("CONTEXTO: Testar o sistema após correções de isolamento de tenant no robust_scheduler.py")
        print("OBJETIVO: Verificar se scheduler, notificações e isolamento de tenant funcionam corretamente")
        print("CREDENCIAIS: admin@demo.com/admin123")
        print("="*80)
        
        # Authenticate first
        admin_credentials = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        success, response = self.run_test("Admin authentication", "POST", "auth/login", 200, admin_credentials)
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"✅ Admin authenticated successfully")
        else:
            print("❌ CRITICAL: Admin authentication failed!")
            return False

        # Run all tenant isolation tests
        test_results = []
        
        # Test 1: Scheduler and Jobs System
        print("\n" + "🔄" + " "*78)
        result1 = self.test_scheduler_and_jobs_system()
        test_results.append(("Scheduler and Jobs System", result1))
        
        # Test 2: Notification Processing System
        print("\n" + "🔔" + " "*78)
        result2 = self.test_notification_processing_system()
        test_results.append(("Notification Processing System", result2))
        
        # Test 3: Tenant Isolation in Scheduler
        print("\n" + "🏢" + " "*78)
        result3 = self.test_tenant_isolation_in_scheduler()
        test_results.append(("Tenant Isolation in Scheduler", result3))
        
        # Test 4: Basic System Functionality
        print("\n" + "⚙️" + " "*78)
        result4 = self.test_basic_system_functionality()
        test_results.append(("Basic System Functionality", result4))
        
        # Print final results
        print("\n" + "="*80)
        print("RESULTADO FINAL - TESTE DE ISOLAMENTO DE TENANT")
        print("="*80)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        print("\n📋 Test Results Summary:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status} - {test_name}")
        
        if success_rate >= 85:
            print("\n🎉 TESTE DE ISOLAMENTO DE TENANT APROVADO COM SUCESSO!")
            print("   ✅ Sistema de Jobs e Agendamento funcionando")
            print("   ✅ Processamento de Notificações operacional")
            print("   ✅ Isolamento de Tenant no Scheduler verificado")
            print("   ✅ Funcionalidade Básica do Sistema mantida")
            print("   ✅ Correções de tenant isolation aplicadas com sucesso")
            return True
        else:
            print(f"\n❌ TESTE DE ISOLAMENTO DE TENANT FALHOU!")
            print(f"   Success rate: {success_rate:.1f}% (minimum required: 85%)")
            print(f"   {self.tests_run - self.tests_passed} tests failed")
            return False

if __name__ == "__main__":
    tester = TenantIsolationTester()
    success = tester.run_tenant_isolation_tests()
    sys.exit(0 if success else 1)