import requests
import sys
import json
from datetime import datetime, timedelta

class LicenseManagementAPITester:
    def __init__(self, base_url="https://ad14241b-b578-4741-8322-0be8e38a54d3.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_license_id = None

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

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n" + "="*50)
        print("TESTING HEALTH ENDPOINTS")
        print("="*50)
        
        self.run_test("Root endpoint", "GET", "", 200)
        self.run_test("Health check", "GET", "health", 200)

    def test_demo_credentials(self):
        """Test demo credentials endpoint"""
        print("\n" + "="*50)
        print("TESTING DEMO CREDENTIALS")
        print("="*50)
        
        success, response = self.run_test("Demo credentials", "GET", "demo-credentials", 200)
        if success:
            print(f"   Demo Admin: {response.get('admin', {})}")
            print(f"   Demo User: {response.get('user', {})}")

    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n" + "="*50)
        print("TESTING AUTHENTICATION")
        print("="*50)
        
        # Test admin login
        admin_credentials = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        success, response = self.run_test("Admin login", "POST", "auth/login", 200, admin_credentials)
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
        
        # Test user login
        user_credentials = {
            "email": "user@demo.com", 
            "password": "user123"
        }
        success, response = self.run_test("User login", "POST", "auth/login", 200, user_credentials)
        if success and 'access_token' in response:
            self.user_token = response['access_token']
            print(f"   User token obtained: {self.user_token[:20]}...")

        # Test invalid login
        invalid_credentials = {
            "email": "invalid@demo.com",
            "password": "wrongpass"
        }
        self.run_test("Invalid login", "POST", "auth/login", 401, invalid_credentials)

        # Test auth/me endpoints
        if self.admin_token:
            self.run_test("Admin auth/me", "GET", "auth/me", 200, token=self.admin_token)
        
        if self.user_token:
            self.run_test("User auth/me", "GET", "auth/me", 200, token=self.user_token)

    def test_user_management(self):
        """Test user management endpoints (admin only)"""
        print("\n" + "="*50)
        print("TESTING USER MANAGEMENT")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping user management tests")
            return

        # Test get users (admin)
        self.run_test("Get users (admin)", "GET", "users", 200, token=self.admin_token)
        
        # Test get users (user) - should fail
        if self.user_token:
            self.run_test("Get users (user) - should fail", "GET", "users", 403, token=self.user_token)

    def test_categories_management(self):
        """Test categories CRUD endpoints"""
        print("\n" + "="*50)
        print("TESTING CATEGORIES MANAGEMENT")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping categories tests")
            return

        # Test get categories (should show demo categories)
        success, response = self.run_test("Get categories", "GET", "categories", 200, token=self.admin_token)
        if success:
            print(f"   Found {len(response)} categories")

        # Test create category
        category_data = {
            "name": "Test Category",
            "description": "A test category for API testing",
            "color": "#FF5733",
            "icon": "test"
        }
        success, response = self.run_test("Create category", "POST", "categories", 200, category_data, self.admin_token)
        if success and 'id' in response:
            self.created_category_id = response['id']
            print(f"   Created category ID: {self.created_category_id}")

            # Test get specific category
            self.run_test("Get specific category", "GET", f"categories/{self.created_category_id}", 200, token=self.admin_token)
            
            # Test update category
            update_data = {
                "name": "Updated Test Category",
                "color": "#33FF57"
            }
            self.run_test("Update category", "PUT", f"categories/{self.created_category_id}", 200, update_data, self.admin_token)

        # Test create category (user) - should fail
        if self.user_token:
            self.run_test("Create category (user) - should fail", "POST", "categories", 403, category_data, self.user_token)

    def test_clientes_pf_management(self):
        """Test Pessoa Física (PF) client management endpoints"""
        print("\n" + "="*50)
        print("TESTING PESSOA FÍSICA (PF) CLIENT MANAGEMENT")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping PF client tests")
            return

        # Test get PF clients
        self.run_test("Get PF clients", "GET", "clientes-pf", 200, token=self.admin_token)

        # Test create PF client
        pf_data = {
            "client_type": "pf",
            "nome_completo": "João Silva Santos",
            "cpf": "12345678901",
            "email_principal": "joao.silva@email.com",
            "telefone": "+55 11 98765-4321",
            "celular": "+55 11 99999-8888",
            "whatsapp": "+55 11 99999-8888",
            "contact_preference": "whatsapp",
            "origin_channel": "website",
            "data_nascimento": "1985-03-15",
            "rg_numero": "123456789",
            "rg_orgao_emissor": "SSP",
            "rg_uf": "SP",
            "profissao": "Desenvolvedor",
            "internal_notes": "Cliente teste para API"
        }
        success, response = self.run_test("Create PF client", "POST", "clientes-pf", 200, pf_data, self.admin_token)
        if success and 'id' in response:
            self.created_pf_id = response['id']
            print(f"   Created PF client ID: {self.created_pf_id}")

            # Test get specific PF client
            self.run_test("Get specific PF client", "GET", f"clientes-pf/{self.created_pf_id}", 200, token=self.admin_token)
            
            # Test update PF client
            update_data = {
                "nome_completo": "João Silva Santos Junior",
                "profissao": "Desenvolvedor Senior"
            }
            self.run_test("Update PF client", "PUT", f"clientes-pf/{self.created_pf_id}", 200, update_data, self.admin_token)

        # Test duplicate CPF (should fail)
        duplicate_pf_data = pf_data.copy()
        duplicate_pf_data["nome_completo"] = "Outro Nome"
        duplicate_pf_data["email_principal"] = "outro@email.com"
        self.run_test("Create duplicate CPF (should fail)", "POST", "clientes-pf", 400, duplicate_pf_data, self.admin_token)

        # Test create PF client (user) - should fail
        if self.user_token:
            self.run_test("Create PF client (user) - should fail", "POST", "clientes-pf", 403, pf_data, self.user_token)

    def test_clientes_pj_management(self):
        """Test Pessoa Jurídica (PJ) client management endpoints"""
        print("\n" + "="*50)
        print("TESTING PESSOA JURÍDICA (PJ) CLIENT MANAGEMENT")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping PJ client tests")
            return

        # Test get PJ clients
        self.run_test("Get PJ clients", "GET", "clientes-pj", 200, token=self.admin_token)

        # Test create PJ client
        pj_data = {
            "client_type": "pj",
            "cnpj": "12345678000195",
            "razao_social": "Empresa Teste LTDA",
            "nome_fantasia": "Teste Corp",
            "email_principal": "contato@empresateste.com",
            "telefone": "+55 11 3333-4444",
            "celular": "+55 11 99999-7777",
            "whatsapp": "+55 11 99999-7777",
            "contact_preference": "email",
            "origin_channel": "partner",
            "regime_tributario": "simples",
            "porte_empresa": "me",
            "inscricao_estadual": "123456789",
            "ie_situacao": "contribuinte",
            "ie_uf": "SP",
            "responsavel_legal_nome": "Maria Silva",
            "responsavel_legal_cpf": "98765432100",
            "responsavel_legal_email": "maria@empresateste.com",
            "responsavel_legal_telefone": "+55 11 98888-7777",
            "internal_notes": "Cliente PJ teste para API"
        }
        success, response = self.run_test("Create PJ client", "POST", "clientes-pj", 200, pj_data, self.admin_token)
        if success and 'id' in response:
            self.created_pj_id = response['id']
            print(f"   Created PJ client ID: {self.created_pj_id}")

            # Test get specific PJ client
            self.run_test("Get specific PJ client", "GET", f"clientes-pj/{self.created_pj_id}", 200, token=self.admin_token)
            
            # Test update PJ client
            update_data = {
                "nome_fantasia": "Teste Corporation",
                "porte_empresa": "epp"
            }
            self.run_test("Update PJ client", "PUT", f"clientes-pj/{self.created_pj_id}", 200, update_data, self.admin_token)

        # Test duplicate CNPJ (should fail)
        duplicate_pj_data = pj_data.copy()
        duplicate_pj_data["razao_social"] = "Outra Empresa LTDA"
        duplicate_pj_data["email_principal"] = "outro@empresa.com"
        self.run_test("Create duplicate CNPJ (should fail)", "POST", "clientes-pj", 400, duplicate_pj_data, self.admin_token)

        # Test create PJ client (user) - should fail
        if self.user_token:
            self.run_test("Create PJ client (user) - should fail", "POST", "clientes-pj", 403, pj_data, self.user_token)

    def test_products_management(self):
        """Test products CRUD endpoints"""
        print("\n" + "="*50)
        print("TESTING PRODUCTS MANAGEMENT")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping products tests")
            return

        # Test get products
        self.run_test("Get products", "GET", "products", 200, token=self.admin_token)

        # Test create product
        product_data = {
            "name": "Test Product",
            "version": "1.0.0",
            "description": "A test product for API testing",
            "category_id": getattr(self, 'created_category_id', None),
            "price": 99.99,
            "currency": "BRL",
            "features": ["feature1", "feature2", "feature3"],
            "requirements": "Windows 10 or higher"
        }
        success, response = self.run_test("Create product", "POST", "products", 200, product_data, self.admin_token)
        if success and 'id' in response:
            self.created_product_id = response['id']
            print(f"   Created product ID: {self.created_product_id}")

            # Test get specific product
            self.run_test("Get specific product", "GET", f"products/{self.created_product_id}", 200, token=self.admin_token)
            
            # Test update product
            update_data = {
                "name": "Updated Test Product",
                "version": "1.1.0",
                "price": 149.99
            }
            self.run_test("Update product", "PUT", f"products/{self.created_product_id}", 200, update_data, self.admin_token)

        # Test create product (user) - should fail
        if self.user_token:
            self.run_test("Create product (user) - should fail", "POST", "products", 403, product_data, self.user_token)

    def test_license_plans_management(self):
        """Test license plans CRUD endpoints"""
        print("\n" + "="*50)
        print("TESTING LICENSE PLANS MANAGEMENT")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping license plans tests")
            return

        # Test get license plans
        self.run_test("Get license plans", "GET", "license-plans", 200, token=self.admin_token)

        # Test create license plan
        plan_data = {
            "name": "Test Plan",
            "description": "A test license plan for API testing",
            "max_users": 10,
            "duration_days": 365,
            "price": 299.99,
            "currency": "BRL",
            "features": ["unlimited_access", "priority_support", "advanced_features"],
            "restrictions": ["no_resale", "single_organization"]
        }
        success, response = self.run_test("Create license plan", "POST", "license-plans", 200, plan_data, self.admin_token)
        if success and 'id' in response:
            self.created_plan_id = response['id']
            print(f"   Created license plan ID: {self.created_plan_id}")

            # Test get specific license plan
            self.run_test("Get specific license plan", "GET", f"license-plans/{self.created_plan_id}", 200, token=self.admin_token)
            
            # Test update license plan
            update_data = {
                "name": "Updated Test Plan",
                "max_users": 20,
                "price": 399.99
            }
            self.run_test("Update license plan", "PUT", f"license-plans/{self.created_plan_id}", 200, update_data, self.admin_token)

        # Test create license plan (user) - should fail
        if self.user_token:
            self.run_test("Create license plan (user) - should fail", "POST", "license-plans", 403, plan_data, self.user_token)

    def test_enhanced_license_management(self):
        """Test enhanced license management with client associations"""
        print("\n" + "="*50)
        print("TESTING ENHANCED LICENSE MANAGEMENT WITH CLIENTS")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping enhanced license management tests")
            return

        # Test create enhanced license with PF client association
        license_pf_data = {
            "name": "License for PF Client",
            "description": "A test license linked to PF client",
            "max_users": 5,
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "features": ["feature1", "feature2"],
            "category_id": getattr(self, 'created_category_id', None),
            "client_pf_id": getattr(self, 'created_pf_id', None),
            "product_id": getattr(self, 'created_product_id', None),
            "plan_id": getattr(self, 'created_plan_id', None),
            "assigned_user_id": None
        }
        success, response = self.run_test("Create license with PF client", "POST", "licenses", 200, license_pf_data, self.admin_token)
        if success and 'id' in response:
            self.created_license_pf_id = response['id']
            print(f"   Created PF license ID: {self.created_license_pf_id}")

        # Test create enhanced license with PJ client association
        license_pj_data = {
            "name": "License for PJ Client",
            "description": "A test license linked to PJ client",
            "max_users": 10,
            "expires_at": (datetime.utcnow() + timedelta(days=60)).isoformat(),
            "features": ["feature1", "feature2", "feature3"],
            "category_id": getattr(self, 'created_category_id', None),
            "client_pj_id": getattr(self, 'created_pj_id', None),
            "product_id": getattr(self, 'created_product_id', None),
            "plan_id": getattr(self, 'created_plan_id', None),
            "assigned_user_id": None
        }
        success, response = self.run_test("Create license with PJ client", "POST", "licenses", 200, license_pj_data, self.admin_token)
        if success and 'id' in response:
            self.created_license_pj_id = response['id']
            print(f"   Created PJ license ID: {self.created_license_pj_id}")

        # Test get all licenses (admin)
        self.run_test("Get all licenses (admin)", "GET", "licenses", 200, token=self.admin_token)
        
        # Test get licenses (user)
        if self.user_token:
            self.run_test("Get licenses (user)", "GET", "licenses", 200, token=self.user_token)

        # Test get specific licenses
        if hasattr(self, 'created_license_pf_id'):
            self.run_test("Get specific PF license", "GET", f"licenses/{self.created_license_pf_id}", 200, token=self.admin_token)
            
        if hasattr(self, 'created_license_pj_id'):
            self.run_test("Get specific PJ license", "GET", f"licenses/{self.created_license_pj_id}", 200, token=self.admin_token)
            
            # Test update license
            update_data = {
                "name": "Updated PJ License",
                "status": "active"
            }
            self.run_test("Update PJ license", "PUT", f"licenses/{self.created_license_pj_id}", 200, update_data, self.admin_token)

        # Test create license (user) - should fail
        if self.user_token:
            self.run_test("Create license (user) - should fail", "POST", "licenses", 403, license_pf_data, self.user_token)

    def test_admin_stats(self):
        """Test admin statistics endpoint"""
        print("\n" + "="*50)
        print("TESTING ADMIN STATISTICS")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping stats tests")
            return

        # Test get stats (admin)
        self.run_test("Get stats (admin)", "GET", "stats", 200, token=self.admin_token)
        
        # Test get stats (user) - should fail
        if self.user_token:
            self.run_test("Get stats (user) - should fail", "GET", "stats", 403, token=self.user_token)

    def test_cleanup(self):
        """Clean up created test data"""
        print("\n" + "="*50)
        print("TESTING CLEANUP")
        print("="*50)
        
        if not self.admin_token:
            return
            
        # Delete test licenses
        if hasattr(self, 'created_license_pf_id'):
            self.run_test("Delete PF test license", "DELETE", f"licenses/{self.created_license_pf_id}", 200, token=self.admin_token)
            
        if hasattr(self, 'created_license_pj_id'):
            self.run_test("Delete PJ test license", "DELETE", f"licenses/{self.created_license_pj_id}", 200, token=self.admin_token)

        # Inactivate test clients (soft delete)
        if hasattr(self, 'created_pf_id'):
            self.run_test("Inactivate PF test client", "DELETE", f"clientes-pf/{self.created_pf_id}", 200, token=self.admin_token)
            
        if hasattr(self, 'created_pj_id'):
            self.run_test("Inactivate PJ test client", "DELETE", f"clientes-pj/{self.created_pj_id}", 200, token=self.admin_token)

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting License Management API Tests")
        print(f"Base URL: {self.base_url}")
        
        self.test_health_check()
        self.test_demo_credentials()
        self.test_authentication()
        self.test_user_management()
        self.test_categories_management()
        self.test_companies_management()
        self.test_products_management()
        self.test_license_plans_management()
        self.test_enhanced_license_management()
        self.test_admin_stats()
        self.test_cleanup()
        
        # Print final results
        print("\n" + "="*50)
        print("FINAL RESULTS")
        print("="*50)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = LicenseManagementAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())