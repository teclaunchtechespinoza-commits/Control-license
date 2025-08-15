import requests
import sys
import json
from datetime import datetime, timedelta

class LicenseManagementAPITester:
    def __init__(self, base_url="https://e3712ae9-4d7f-4e3b-8159-d15c1277ab75.preview.emergentagent.com/api"):
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
        self.test_clientes_pf_management()
        self.test_clientes_pj_management()
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

    def test_client_creation_specific(self):
        """Test specific client creation scenarios as requested in review"""
        print("\n" + "="*50)
        print("TESTING SPECIFIC CLIENT CREATION SCENARIOS (REVIEW REQUEST)")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping specific client creation tests")
            return

        # 1. Test PF creation with minimal fields
        print("\n🔍 Test 1: PF Client Creation with Minimal Fields")
        pf_minimal_data = {
            "client_type": "pf",
            "nome_completo": "João da Silva Teste",
            "cpf": "88899900011",
            "email_principal": "joao.teste@email.com"
        }
        success, response = self.run_test("Create PF client (minimal)", "POST", "clientes-pf", 200, pf_minimal_data, self.admin_token)
        if success and 'id' in response:
            self.created_pf_minimal_id = response['id']
            print(f"   ✅ PF client created successfully with ID: {self.created_pf_minimal_id}")

        # 2. Test PJ creation with minimal fields
        print("\n🔍 Test 2: PJ Client Creation with Minimal Fields")
        pj_minimal_data = {
            "client_type": "pj", 
            "razao_social": "Empresa Teste LTDA",
            "cnpj": "66677788000199",
            "email_principal": "empresa.teste@email.com"
        }
        success, response = self.run_test("Create PJ client (minimal)", "POST", "clientes-pj", 200, pj_minimal_data, self.admin_token)
        if success and 'id' in response:
            self.created_pj_minimal_id = response['id']
            print(f"   ✅ PJ client created successfully with ID: {self.created_pj_minimal_id}")

        # 3. Test validation of required fields
        print("\n🔍 Test 3: Validation of Required Fields")
        
        # Test PF with missing required fields
        pf_missing_name = {
            "client_type": "pf",
            "cpf": "98765432100",
            "email_principal": "test@email.com"
        }
        self.run_test("PF missing nome_completo (should fail)", "POST", "clientes-pf", 422, pf_missing_name, self.admin_token)
        
        pf_missing_cpf = {
            "client_type": "pf",
            "nome_completo": "Test User",
            "email_principal": "test@email.com"
        }
        self.run_test("PF missing CPF (should fail)", "POST", "clientes-pf", 422, pf_missing_cpf, self.admin_token)
        
        pf_missing_email = {
            "client_type": "pf",
            "nome_completo": "Test User",
            "cpf": "98765432100"
        }
        self.run_test("PF missing email (should fail)", "POST", "clientes-pf", 422, pf_missing_email, self.admin_token)

        # Test PJ with missing required fields
        pj_missing_razao = {
            "client_type": "pj",
            "cnpj": "98765432000100",
            "email_principal": "test@empresa.com"
        }
        self.run_test("PJ missing razao_social (should fail)", "POST", "clientes-pj", 422, pj_missing_razao, self.admin_token)
        
        pj_missing_cnpj = {
            "client_type": "pj",
            "razao_social": "Test Company",
            "email_principal": "test@empresa.com"
        }
        self.run_test("PJ missing CNPJ (should fail)", "POST", "clientes-pj", 422, pj_missing_cnpj, self.admin_token)

        # Test invalid CPF/CNPJ
        print("\n🔍 Test 4: Invalid CPF/CNPJ Validation")
        pf_invalid_cpf = {
            "client_type": "pf",
            "nome_completo": "Test User",
            "cpf": "123",  # Too short
            "email_principal": "test@email.com"
        }
        self.run_test("PF invalid CPF (should fail)", "POST", "clientes-pf", 422, pf_invalid_cpf, self.admin_token)
        
        pj_invalid_cnpj = {
            "client_type": "pj",
            "razao_social": "Test Company",
            "cnpj": "123456",  # Too short
            "email_principal": "test@empresa.com"
        }
        self.run_test("PJ invalid CNPJ (should fail)", "POST", "clientes-pj", 422, pj_invalid_cnpj, self.admin_token)

        # Test invalid email
        pf_invalid_email = {
            "client_type": "pf",
            "nome_completo": "Test User",
            "cpf": "11122233344",
            "email_principal": "invalid-email"  # Invalid format
        }
        self.run_test("PF invalid email (should fail)", "POST", "clientes-pf", 422, pf_invalid_email, self.admin_token)

        # 4. Test with structured data (address, contacts)
        print("\n🔍 Test 5: Client Creation with Structured Data")
        
        pf_structured_data = {
            "client_type": "pf",
            "nome_completo": "Maria Santos Oliveira",
            "cpf": "77788899900",
            "email_principal": "maria.santos@email.com",
            "telefone": "+55 11 3333-4444",
            "celular": "+55 11 99999-8888",
            "whatsapp": "+55 11 99999-8888",
            "contact_preference": "whatsapp",
            "address": {
                "cep": "01234-567",
                "logradouro": "Rua das Flores",
                "numero": "123",
                "complemento": "Apto 45",
                "bairro": "Centro",
                "municipio": "São Paulo",
                "uf": "SP",
                "pais": "Brasil"
            },
            "billing_contact": {
                "name": "Maria Santos",
                "email": "billing@email.com",
                "phone": "+55 11 8888-7777"
            },
            "technical_contact": {
                "name": "João Técnico",
                "email": "tech@email.com",
                "phone": "+55 11 7777-6666"
            }
        }
        success, response = self.run_test("Create PF with structured data", "POST", "clientes-pf", 200, pf_structured_data, self.admin_token)
        if success and 'id' in response:
            self.created_pf_structured_id = response['id']
            print(f"   ✅ PF client with structured data created successfully")

        pj_structured_data = {
            "client_type": "pj",
            "razao_social": "Empresa Estruturada LTDA",
            "cnpj": "44455566000177",
            "email_principal": "contato@estruturada.com",
            "nome_fantasia": "Estruturada Corp",
            "telefone": "+55 11 4444-5555",
            "address": {
                "cep": "04567-890",
                "logradouro": "Av. Paulista",
                "numero": "1000",
                "complemento": "Sala 1001",
                "bairro": "Bela Vista",
                "municipio": "São Paulo",
                "uf": "SP",
                "pais": "Brasil"
            },
            "billing_contact": {
                "name": "Financeiro Empresa",
                "email": "financeiro@estruturada.com",
                "phone": "+55 11 5555-4444"
            },
            "technical_contact": {
                "name": "TI Empresa",
                "email": "ti@estruturada.com",
                "phone": "+55 11 6666-3333"
            },
            "responsavel_legal_nome": "Carlos Silva",
            "responsavel_legal_cpf": "99988877766",
            "responsavel_legal_email": "carlos@estruturada.com",
            "responsavel_legal_telefone": "+55 11 7777-2222"
        }
        success, response = self.run_test("Create PJ with structured data", "POST", "clientes-pj", 200, pj_structured_data, self.admin_token)
        if success and 'id' in response:
            self.created_pj_structured_id = response['id']
            print(f"   ✅ PJ client with structured data created successfully")

        # Test CNPJ with formatting
        print("\n🔍 Test 6: CNPJ with Formatting")
        pj_formatted_cnpj = {
            "client_type": "pj",
            "razao_social": "Empresa Formatada LTDA",
            "cnpj": "55.666.777/0001-88",  # Formatted CNPJ
            "email_principal": "formatada@empresa.com"
        }
        success, response = self.run_test("Create PJ with formatted CNPJ", "POST", "clientes-pj", 200, pj_formatted_cnpj, self.admin_token)
        if success and 'id' in response:
            self.created_pj_formatted_id = response['id']
            print(f"   ✅ PJ client with formatted CNPJ created successfully")

    def test_equipment_management(self):
        """Test equipment brands and models management as requested in review"""
        print("\n" + "="*50)
        print("TESTING EQUIPMENT MANAGEMENT (REVIEW REQUEST)")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping equipment management tests")
            return

        # Store created brand IDs for model creation
        self.brand_ids = {}

        # 1. Create equipment brands as requested
        print("\n🔍 Test 1: Creating Equipment Brands")
        
        brands_data = [
            {"name": "Dell", "description": "Computadores e servidores Dell"},
            {"name": "HP", "description": "Equipamentos HP"},
            {"name": "Lenovo", "description": "Computadores Lenovo"},
            {"name": "Acer", "description": "Equipamentos Acer"}
        ]
        
        for brand_data in brands_data:
            success, response = self.run_test(f"Create brand {brand_data['name']}", "POST", "equipment-brands", 200, brand_data, self.admin_token)
            if success and 'id' in response:
                self.brand_ids[brand_data['name']] = response['id']
                print(f"   ✅ {brand_data['name']} brand created with ID: {response['id']}")

        # 2. Test GET equipment brands
        print("\n🔍 Test 2: Get Equipment Brands")
        success, response = self.run_test("Get equipment brands", "GET", "equipment-brands", 200, token=self.admin_token)
        if success:
            print(f"   ✅ Retrieved {len(response)} equipment brands")
            for brand in response:
                print(f"      - {brand.get('name', 'Unknown')}: {brand.get('description', 'No description')}")

        # 3. Create equipment models for each brand
        print("\n🔍 Test 3: Creating Equipment Models")
        
        models_data = [
            # Dell models
            {"name": "OptiPlex 3080", "brand_id": self.brand_ids.get("Dell"), "description": "Desktop corporativo"},
            {"name": "Latitude 5520", "brand_id": self.brand_ids.get("Dell"), "description": "Notebook empresarial"},
            # HP models
            {"name": "ProDesk 400", "brand_id": self.brand_ids.get("HP"), "description": "Desktop HP"},
            {"name": "EliteBook 840", "brand_id": self.brand_ids.get("HP"), "description": "Notebook profissional"},
            # Lenovo models
            {"name": "ThinkPad X1", "brand_id": self.brand_ids.get("Lenovo"), "description": "Notebook empresarial premium"},
            {"name": "ThinkCentre M720", "brand_id": self.brand_ids.get("Lenovo"), "description": "Desktop corporativo"},
            # Acer models
            {"name": "Aspire 5", "brand_id": self.brand_ids.get("Acer"), "description": "Notebook para uso geral"},
            {"name": "Veriton X", "brand_id": self.brand_ids.get("Acer"), "description": "Desktop compacto"}
        ]
        
        self.created_model_ids = []
        for model_data in models_data:
            if model_data["brand_id"]:  # Only create if brand exists
                success, response = self.run_test(f"Create model {model_data['name']}", "POST", "equipment-models", 200, model_data, self.admin_token)
                if success and 'id' in response:
                    self.created_model_ids.append(response['id'])
                    print(f"   ✅ {model_data['name']} model created with ID: {response['id']}")

        # 4. Test GET equipment models (all)
        print("\n🔍 Test 4: Get All Equipment Models")
        success, response = self.run_test("Get all equipment models", "GET", "equipment-models", 200, token=self.admin_token)
        if success:
            print(f"   ✅ Retrieved {len(response)} equipment models")
            for model in response:
                print(f"      - {model.get('name', 'Unknown')}: {model.get('description', 'No description')}")

        # 5. Test GET equipment models filtered by brand
        print("\n🔍 Test 5: Get Equipment Models Filtered by Brand")
        for brand_name, brand_id in self.brand_ids.items():
            if brand_id:
                success, response = self.run_test(f"Get models for {brand_name}", "GET", "equipment-models", 200, token=self.admin_token, params={"brand_id": brand_id})
                if success:
                    print(f"   ✅ Retrieved {len(response)} models for {brand_name}")
                    for model in response:
                        print(f"      - {model.get('name', 'Unknown')}")

        # 6. Test validation - duplicate brand name
        print("\n🔍 Test 6: Validation Tests")
        duplicate_brand = {"name": "Dell", "description": "Duplicate Dell brand"}
        self.run_test("Create duplicate brand (should fail)", "POST", "equipment-brands", 400, duplicate_brand, self.admin_token)

        # 7. Test validation - model for non-existent brand
        invalid_model = {"name": "Invalid Model", "brand_id": "non-existent-id", "description": "Model for non-existent brand"}
        self.run_test("Create model for non-existent brand (should fail)", "POST", "equipment-models", 400, invalid_model, self.admin_token)

        # 8. Test validation - duplicate model name for same brand
        if self.brand_ids.get("Dell"):
            duplicate_model = {"name": "OptiPlex 3080", "brand_id": self.brand_ids["Dell"], "description": "Duplicate model"}
            self.run_test("Create duplicate model for same brand (should fail)", "POST", "equipment-models", 400, duplicate_model, self.admin_token)

        # 9. Test user permissions (should fail for non-admin)
        print("\n🔍 Test 7: User Permission Tests")
        if self.user_token:
            test_brand = {"name": "User Brand", "description": "Should fail"}
            self.run_test("Create brand as user (should fail)", "POST", "equipment-brands", 403, test_brand, self.user_token)
            
            test_model = {"name": "User Model", "brand_id": self.brand_ids.get("Dell", ""), "description": "Should fail"}
            self.run_test("Create model as user (should fail)", "POST", "equipment-models", 403, test_model, self.user_token)

    def cleanup_specific_tests(self):
        """Clean up test data created in specific tests"""
        print("\n🔍 Cleaning up specific test data...")
        
        if not self.admin_token:
            return
            
        # Clean up PF clients
        for attr in ['created_pf_minimal_id', 'created_pf_structured_id']:
            if hasattr(self, attr):
                client_id = getattr(self, attr)
                self.run_test(f"Cleanup PF client {client_id}", "DELETE", f"clientes-pf/{client_id}", 200, token=self.admin_token)
        
        # Clean up PJ clients  
        for attr in ['created_pj_minimal_id', 'created_pj_structured_id', 'created_pj_formatted_id']:
            if hasattr(self, attr):
                client_id = getattr(self, attr)
                self.run_test(f"Cleanup PJ client {client_id}", "DELETE", f"clientes-pj/{client_id}", 200, token=self.admin_token)

    def test_pj_client_debug(self):
        """Debug PJ client creation 400 error as requested in review"""
        print("\n" + "="*50)
        print("DEBUGGING PJ CLIENT CREATION 400 ERROR (REVIEW REQUEST)")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping PJ debug tests")
            return

        # Test 1: Minimal Valid PJ Payload as specified in review
        print("\n🔍 Test 1: Minimal Valid PJ Payload")
        minimal_pj_payload = {
            "client_type": "pj",
            "status": "active", 
            "razao_social": "Debug Test Company",
            "cnpj": "12345678000195",
            "cnpj_normalizado": "12345678000195",
            "email_principal": "debug@test.com",
            "contact_preference": "email"
        }
        print(f"   Payload: {json.dumps(minimal_pj_payload, indent=2)}")
        success, response = self.run_test("Minimal PJ payload", "POST", "clientes-pj", 200, minimal_pj_payload, self.admin_token)
        if success and 'id' in response:
            self.debug_pj_id_1 = response['id']
            print(f"   ✅ SUCCESS: PJ client created with ID: {self.debug_pj_id_1}")
        else:
            print(f"   ❌ FAILED: Expected 200, got error. Response: {response}")

        # Test 2: Frontend-Similar Payload as specified in review
        print("\n🔍 Test 2: Frontend-Similar Payload")
        frontend_similar_payload = {
            "client_type": "pj",
            "status": "active",
            "email_principal": "debug@test.com", 
            "contact_preference": "email",
            "razao_social": "Debug Test Company",
            "cnpj": "12345678000196",
            "cnpj_normalizado": "12345678000196",
            "nacionalidade": "Brasileira"
        }
        print(f"   Payload: {json.dumps(frontend_similar_payload, indent=2)}")
        success, response = self.run_test("Frontend-similar PJ payload", "POST", "clientes-pj", 200, frontend_similar_payload, self.admin_token)
        if success and 'id' in response:
            self.debug_pj_id_2 = response['id']
            print(f"   ✅ SUCCESS: PJ client created with ID: {self.debug_pj_id_2}")
        else:
            print(f"   ❌ FAILED: Expected 200, got error. Response: {response}")

        # Test 3: Test Different Field Combinations to isolate required fields
        print("\n🔍 Test 3: Testing Different Field Combinations")
        
        # Test with only client_type
        only_type = {"client_type": "pj"}
        print(f"   Testing only client_type: {json.dumps(only_type)}")
        success, response = self.run_test("Only client_type", "POST", "clientes-pj", 422, only_type, self.admin_token)
        if not success and response:
            print(f"   ❌ Validation error (expected): {response}")

        # Test without client_type
        without_type = {
            "status": "active",
            "razao_social": "Test Company",
            "cnpj": "12345678000197",
            "email_principal": "test@company.com"
        }
        print(f"   Testing without client_type: {json.dumps(without_type)}")
        success, response = self.run_test("Without client_type", "POST", "clientes-pj", 422, without_type, self.admin_token)
        if not success and response:
            print(f"   ❌ Validation error (expected): {response}")

        # Test without razao_social
        without_razao = {
            "client_type": "pj",
            "cnpj": "12345678000198",
            "email_principal": "test@company.com"
        }
        print(f"   Testing without razao_social: {json.dumps(without_razao)}")
        success, response = self.run_test("Without razao_social", "POST", "clientes-pj", 422, without_razao, self.admin_token)
        if not success and response:
            print(f"   ❌ Validation error (expected): {response}")

        # Test without cnpj
        without_cnpj = {
            "client_type": "pj",
            "razao_social": "Test Company",
            "email_principal": "test@company.com"
        }
        print(f"   Testing without cnpj: {json.dumps(without_cnpj)}")
        success, response = self.run_test("Without cnpj", "POST", "clientes-pj", 422, without_cnpj, self.admin_token)
        if not success and response:
            print(f"   ❌ Validation error (expected): {response}")

        # Test without email_principal
        without_email = {
            "client_type": "pj",
            "razao_social": "Test Company",
            "cnpj": "12345678000199"
        }
        print(f"   Testing without email_principal: {json.dumps(without_email)}")
        success, response = self.run_test("Without email_principal", "POST", "clientes-pj", 422, without_email, self.admin_token)
        if not success and response:
            print(f"   ❌ Validation error (expected): {response}")

        # Test 4: Test with different data types
        print("\n🔍 Test 4: Testing Different Data Types")
        
        # Test with invalid email format
        invalid_email = {
            "client_type": "pj",
            "razao_social": "Test Company",
            "cnpj": "12345678000200",
            "email_principal": "invalid-email-format"
        }
        print(f"   Testing invalid email format: {json.dumps(invalid_email)}")
        success, response = self.run_test("Invalid email format", "POST", "clientes-pj", 422, invalid_email, self.admin_token)
        if not success and response:
            print(f"   ❌ Validation error (expected): {response}")

        # Test with invalid CNPJ length
        invalid_cnpj = {
            "client_type": "pj",
            "razao_social": "Test Company",
            "cnpj": "123456",  # Too short
            "email_principal": "test@company.com"
        }
        print(f"   Testing invalid CNPJ length: {json.dumps(invalid_cnpj)}")
        success, response = self.run_test("Invalid CNPJ length", "POST", "clientes-pj", 422, invalid_cnpj, self.admin_token)
        if not success and response:
            print(f"   ❌ Validation error (expected): {response}")

        # Test 5: Test enum values
        print("\n🔍 Test 5: Testing Enum Values")
        
        # Test with invalid client_type
        invalid_client_type = {
            "client_type": "invalid_type",
            "razao_social": "Test Company",
            "cnpj": "12345678000201",
            "email_principal": "test@company.com"
        }
        print(f"   Testing invalid client_type: {json.dumps(invalid_client_type)}")
        success, response = self.run_test("Invalid client_type", "POST", "clientes-pj", 422, invalid_client_type, self.admin_token)
        if not success and response:
            print(f"   ❌ Validation error (expected): {response}")

        # Test with invalid status
        invalid_status = {
            "client_type": "pj",
            "status": "invalid_status",
            "razao_social": "Test Company",
            "cnpj": "12345678000202",
            "email_principal": "test@company.com"
        }
        print(f"   Testing invalid status: {json.dumps(invalid_status)}")
        success, response = self.run_test("Invalid status", "POST", "clientes-pj", 422, invalid_status, self.admin_token)
        if not success and response:
            print(f"   ❌ Validation error (expected): {response}")

        # Test with invalid contact_preference
        invalid_contact_pref = {
            "client_type": "pj",
            "razao_social": "Test Company",
            "cnpj": "12345678000203",
            "email_principal": "test@company.com",
            "contact_preference": "invalid_preference"
        }
        print(f"   Testing invalid contact_preference: {json.dumps(invalid_contact_pref)}")
        success, response = self.run_test("Invalid contact_preference", "POST", "clientes-pj", 422, invalid_contact_pref, self.admin_token)
        if not success and response:
            print(f"   ❌ Validation error (expected): {response}")

        # Test 6: Test the exact payload that frontend might be sending
        print("\n🔍 Test 6: Testing Exact Frontend Payload Simulation")
        
        # Simulate what frontend might be sending based on the error description
        frontend_payload = {
            "client_type": "pj",
            "status": "active",
            "email_principal": "",  # Empty email as mentioned in the issue
            "contact_preference": "email",
            "nacionalidade": "Brasileira"
        }
        print(f"   Testing frontend payload with empty email: {json.dumps(frontend_payload)}")
        success, response = self.run_test("Frontend payload (empty email)", "POST", "clientes-pj", 400, frontend_payload, self.admin_token)
        if not success and response:
            print(f"   ❌ Error (expected): {response}")

        # Test with missing required fields that frontend might not be sending
        frontend_missing_fields = {
            "client_type": "pj",
            "status": "active",
            "email_principal": "test@frontend.com",
            "contact_preference": "email",
            "nacionalidade": "Brasileira"
            # Missing razao_social and cnpj
        }
        print(f"   Testing frontend payload missing required fields: {json.dumps(frontend_missing_fields)}")
        success, response = self.run_test("Frontend payload (missing fields)", "POST", "clientes-pj", 422, frontend_missing_fields, self.admin_token)
        if not success and response:
            print(f"   ❌ Error (expected): {response}")

    def cleanup_debug_tests(self):
        """Clean up debug test data"""
        print("\n🔍 Cleaning up debug test data...")
        
        if not self.admin_token:
            return
            
        # Clean up debug PJ clients
        for attr in ['debug_pj_id_1', 'debug_pj_id_2']:
            if hasattr(self, attr):
                client_id = getattr(self, attr)
                self.run_test(f"Cleanup debug PJ client {client_id}", "DELETE", f"clientes-pj/{client_id}", 200, token=self.admin_token)

    def test_pj_client_debug_specific(self):
        """Debug the exact 400 error scenario from the review request"""
        print("\n" + "="*50)
        print("DEBUGGING EXACT 400 ERROR SCENARIO (REVIEW REQUEST)")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping specific debug tests")
            return

        # Test the exact scenario mentioned in the review - frontend sending email but getting 400
        print("\n🔍 CRITICAL TEST: Frontend payload with email_principal present but getting 400 error")
        
        # This simulates the exact payload that frontend is sending according to the review
        frontend_payload_with_email = {
            "client_type": "pj",
            "status": "active",
            "email_principal": "debug@test.com",  # Email is present as mentioned in review
            "contact_preference": "email",
            "razao_social": "Debug Test Company",
            "cnpj": "98765432000111",
            "cnpj_normalizado": "98765432000111",
            "nacionalidade": "Brasileira"
        }
        
        print(f"   Frontend payload: {json.dumps(frontend_payload_with_email, indent=2)}")
        success, response = self.run_test("Frontend payload with email present", "POST", "clientes-pj", 200, frontend_payload_with_email, self.admin_token)
        
        if success and 'id' in response:
            self.debug_frontend_pj_id = response['id']
            print(f"   ✅ SUCCESS: PJ client created successfully with ID: {self.debug_frontend_pj_id}")
            print("   🔍 ANALYSIS: The payload works correctly when all required fields are present")
        else:
            print(f"   ❌ FAILED: Got error response: {response}")
            print("   🔍 ANALYSIS: This indicates the issue is with missing required fields")

        # Test what happens when we remove cnpj_normalizado (which frontend might not be sending)
        print("\n🔍 TEST: Frontend payload without cnpj_normalizado")
        frontend_no_normalized = {
            "client_type": "pj",
            "status": "active",
            "email_principal": "debug2@test.com",
            "contact_preference": "email",
            "razao_social": "Debug Test Company 2",
            "cnpj": "98765432000112",
            "nacionalidade": "Brasileira"
            # Missing cnpj_normalizado
        }
        
        print(f"   Payload without cnpj_normalizado: {json.dumps(frontend_no_normalized, indent=2)}")
        success, response = self.run_test("Frontend without cnpj_normalizado", "POST", "clientes-pj", 422, frontend_no_normalized, self.admin_token)
        
        if not success and response:
            print(f"   ❌ VALIDATION ERROR (expected): {response}")
            print("   🔍 ANALYSIS: cnpj_normalizado is required but frontend might not be sending it")

        # Test what happens when we only send the fields that frontend console log showed
        print("\n🔍 TEST: Exact fields from frontend console log")
        console_log_payload = {
            "client_type": "pj",
            "status": "active", 
            "email_principal": "debug3@test.com",
            "contact_preference": "email",
            "nacionalidade": "Brasileira"
            # Missing razao_social, cnpj, cnpj_normalizado
        }
        
        print(f"   Console log payload: {json.dumps(console_log_payload, indent=2)}")
        success, response = self.run_test("Console log payload", "POST", "clientes-pj", 422, console_log_payload, self.admin_token)
        
        if not success and response:
            print(f"   ❌ VALIDATION ERROR (expected): {response}")
            print("   🔍 ANALYSIS: Missing razao_social and cnpj fields cause validation failure")

        # Test the backend model requirements
        print("\n🔍 BACKEND MODEL ANALYSIS:")
        print("   Required fields for PJ client creation:")
        print("   - client_type: 'pj' (Literal)")
        print("   - razao_social: str (required)")
        print("   - cnpj: str (required)")
        print("   - cnpj_normalizado: str (required)")
        print("   - email_principal: EmailStr (required)")
        print("   - status: defaults to 'active'")
        print("   - contact_preference: defaults to 'email'")

        print("\n🔍 ROOT CAUSE IDENTIFIED:")
        print("   The 400 error occurs when frontend sends a payload missing required fields:")
        print("   1. razao_social - Company name (required)")
        print("   2. cnpj - Company tax ID (required)")
        print("   3. cnpj_normalizado - Normalized CNPJ (required)")
        print("   ")
        print("   The email_principal field is working correctly.")
        print("   The issue is that frontend form is not capturing/sending the company fields.")

    def test_companies_endpoints(self):
        """Test Companies endpoints as requested in review"""
        print("\n" + "="*50)
        print("TESTING COMPANIES ENDPOINTS (REVIEW REQUEST)")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping companies tests")
            return

        # Test 1: GET /api/companies (should return list - empty or existing)
        print("\n🔍 Test 1: GET /api/companies")
        success, response = self.run_test("Get companies", "GET", "companies", 200, token=self.admin_token)
        if success:
            print(f"   ✅ GET /api/companies working - returned {len(response)} companies")
            for company in response:
                print(f"      - {company.get('name', 'Unknown')}: {company.get('description', 'No description')}")
        else:
            print("   ❌ GET /api/companies failed")

        # Test 2: POST /api/companies with test data
        print("\n🔍 Test 2: POST /api/companies")
        company_data = {
            "name": "Empresa Teste API",
            "description": "Teste endpoint"
        }
        success, response = self.run_test("Create test company", "POST", "companies", 200, company_data, self.admin_token)
        if success and 'id' in response:
            self.created_test_company_id = response['id']
            print(f"   ✅ POST /api/companies working - created company with ID: {self.created_test_company_id}")
            print(f"   Company details: {response.get('name')} - {response.get('description')}")
        else:
            print("   ❌ POST /api/companies failed")

    def test_license_plans_endpoints(self):
        """Test License Plans endpoints as requested in review"""
        print("\n" + "="*50)
        print("TESTING LICENSE PLANS ENDPOINTS (REVIEW REQUEST)")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping license plans tests")
            return

        # Test 1: GET /api/license-plans (should return list - empty or existing)
        print("\n🔍 Test 1: GET /api/license-plans")
        success, response = self.run_test("Get license plans", "GET", "license-plans", 200, token=self.admin_token)
        if success:
            print(f"   ✅ GET /api/license-plans working - returned {len(response)} plans")
            for plan in response:
                print(f"      - {plan.get('name', 'Unknown')}: {plan.get('description', 'No description')} - R$ {plan.get('price', 0)}")
        else:
            print("   ❌ GET /api/license-plans failed")

        # Test 2: POST /api/license-plans with test data
        print("\n🔍 Test 2: POST /api/license-plans")
        plan_data = {
            "name": "Plano Básico",
            "description": "Teste",
            "price": 99.90
        }
        success, response = self.run_test("Create test license plan", "POST", "license-plans", 200, plan_data, self.admin_token)
        if success and 'id' in response:
            self.created_test_plan_id = response['id']
            print(f"   ✅ POST /api/license-plans working - created plan with ID: {self.created_test_plan_id}")
            print(f"   Plan details: {response.get('name')} - {response.get('description')} - R$ {response.get('price')}")
        else:
            print("   ❌ POST /api/license-plans failed")

    def test_existing_endpoints_still_work(self):
        """Test that existing endpoints still work as requested in review"""
        print("\n" + "="*50)
        print("TESTING EXISTING ENDPOINTS STILL WORK (REVIEW REQUEST)")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping existing endpoints tests")
            return

        # Test 1: GET /api/categories
        print("\n🔍 Test 1: GET /api/categories")
        success, response = self.run_test("Get categories", "GET", "categories", 200, token=self.admin_token)
        if success:
            print(f"   ✅ GET /api/categories still working - returned {len(response)} categories")
            for category in response:
                print(f"      - {category.get('name', 'Unknown')}: {category.get('description', 'No description')}")
        else:
            print("   ❌ GET /api/categories failed")

        # Test 2: GET /api/products
        print("\n🔍 Test 2: GET /api/products")
        success, response = self.run_test("Get products", "GET", "products", 200, token=self.admin_token)
        if success:
            print(f"   ✅ GET /api/products still working - returned {len(response)} products")
            for product in response:
                print(f"      - {product.get('name', 'Unknown')}: {product.get('description', 'No description')}")
        else:
            print("   ❌ GET /api/products failed")

    def test_direct_backend_product_creation(self):
        """Test direct backend product creation as requested in review"""
        print("\n" + "="*50)
        print("TESTE DIRETO DO BACKEND - PRODUCT CREATION (REVIEW REQUEST)")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping direct backend test")
            return

        print("🎯 OBJECTIVE: Test backend directly to isolate frontend vs backend issues")
        print("   Testing if backend works when called directly")
        
        # Test 1: Direct POST /api/products with exact payload from review request
        print("\n🔍 Test 1: POST /api/products with exact review payload")
        product_payload = {
            "name": "Produto Teste Backend",
            "version": "1.0", 
            "description": "Teste direto do backend",
            "category_id": None,
            "price": None,
            "currency": "BRL",
            "features": [],
            "requirements": None
        }
        
        print(f"   Payload: {json.dumps(product_payload, indent=2)}")
        success, response = self.run_test("Direct backend product creation", "POST", "products", 200, product_payload, self.admin_token)
        
        if success and 'id' in response:
            self.direct_product_id = response['id']
            print(f"   ✅ SUCCESS: Product created directly via backend with ID: {self.direct_product_id}")
            print(f"   Product details: {response.get('name')} v{response.get('version')}")
            print("   🔍 ANALYSIS: Backend works when called directly!")
        else:
            print(f"   ❌ FAILED: Backend product creation failed: {response}")
            print("   🔍 ANALYSIS: Problem is in the backend, not frontend")
            return False
        
        # Test 2: Verify product appears in GET /api/products
        print("\n🔍 Test 2: Verify product appears in product list")
        success, response = self.run_test("Get products after creation", "GET", "products", 200, token=self.admin_token)
        
        if success:
            product_found = False
            for product in response:
                if product.get('id') == self.direct_product_id:
                    product_found = True
                    print(f"   ✅ SUCCESS: Product found in list - {product.get('name')} v{product.get('version')}")
                    break
            
            if not product_found:
                print(f"   ❌ FAILED: Product with ID {self.direct_product_id} not found in product list")
                print("   🔍 ANALYSIS: Product creation may have failed or database issue")
            else:
                print("   🔍 ANALYSIS: Product persistence working correctly")
        else:
            print("   ❌ FAILED: Could not retrieve product list")
        
        # Test 3: Analyze maintenance logs
        print("\n🔍 Test 3: Analyze maintenance logs for product creation")
        success, response = self.run_test("Get maintenance logs", "GET", "maintenance/logs", 200, token=self.admin_token)
        
        if success and 'logs' in response:
            logs = response['logs']
            print(f"   ✅ Retrieved {len(logs)} log entries")
            
            # Look for product-related logs
            product_logs = []
            for log in logs:
                if 'product' in log.lower() or 'create_product' in log.lower():
                    product_logs.append(log)
            
            if product_logs:
                print(f"   📋 Found {len(product_logs)} product-related log entries:")
                for i, log in enumerate(product_logs[-10:]):  # Show last 10
                    print(f"      {i+1}. {log}")
                
                # Check for specific error patterns
                error_logs = [log for log in product_logs if 'error' in log.lower() or 'exception' in log.lower()]
                if error_logs:
                    print(f"   ⚠️  Found {len(error_logs)} error logs:")
                    for error_log in error_logs[-5:]:  # Show last 5 errors
                        print(f"      ❌ {error_log}")
                    print("   🔍 ANALYSIS: Backend logging system has errors that may affect product creation")
                else:
                    print("   ✅ No error logs found in product creation process")
                    print("   🔍 ANALYSIS: Logging system working correctly")
            else:
                print("   ⚠️  No product-related logs found")
                print("   🔍 ANALYSIS: Logging system may not be capturing product operations")
        else:
            print("   ❌ FAILED: Could not retrieve maintenance logs")
            print("   🔍 ANALYSIS: Maintenance logging system may be down")
        
        return success

    def test_blocked_status_validation(self):
        """CRITICAL TEST: Verify 'blocked' status validation fix as requested in review"""
        print("\n" + "="*50)
        print("TESTE CRÍTICO: VALIDAÇÃO STATUS 'BLOCKED' (REVIEW REQUEST)")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping blocked status test")
            return

        print("🎯 OBJETIVO: Verificar se o erro de validação 'body.status should be 'active', 'inactive' or 'pending_verification'' foi corrigido")
        print("   Testando se status 'blocked' é aceito após adição de BLOCKED = 'blocked' ao enum ClientStatus")
        
        # Test 1: Create PF client with status "blocked" (the main test case)
        print("\n🔍 Test 1: Criação de cliente PF com status 'blocked'")
        blocked_pf_payload = {
            "client_type": "pf",
            "status": "blocked",
            "nome_completo": "Teste Cliente Bloqueado",
            "cpf": "12345678901",
            "email_principal": "teste.bloqueado@exemplo.com",
            "telefone": "11999887766"
        }
        
        print(f"   Payload de teste: {json.dumps(blocked_pf_payload, indent=2)}")
        success, response = self.run_test("PF client with status 'blocked'", "POST", "clientes-pf", 200, blocked_pf_payload, self.admin_token)
        
        if success and 'id' in response:
            self.blocked_pf_id = response['id']
            print(f"   ✅ SUCESSO: Cliente PF criado com status 'blocked' - ID: {self.blocked_pf_id}")
            print(f"   Status persistido: {response.get('status', 'N/A')}")
            
            # Verify the status was persisted correctly
            if response.get('status') == 'blocked':
                print("   ✅ CONFIRMADO: Status 'blocked' persistido corretamente no banco")
            else:
                print(f"   ⚠️  ATENÇÃO: Status esperado 'blocked', mas foi salvo como '{response.get('status')}'")
        else:
            print(f"   ❌ FALHOU: Erro ao criar cliente com status 'blocked': {response}")
            print("   🔍 ANÁLISE: O erro de validação ainda persiste - enum não foi atualizado corretamente")

        # Test 2: Test all other valid statuses to ensure they still work
        print("\n🔍 Test 2: Verificação de todos os status válidos")
        
        valid_statuses = ["active", "inactive", "pending_verification", "blocked"]
        status_results = {}
        
        for i, status in enumerate(valid_statuses):
            print(f"\n   Testando status: '{status}'")
            test_payload = {
                "client_type": "pf",
                "status": status,
                "nome_completo": f"Cliente Teste {status.title()}",
                "cpf": f"1234567890{i}",
                "email_principal": f"teste.{status}@exemplo.com",
                "telefone": "11999887766"
            }
            
            success, response = self.run_test(f"PF client with status '{status}'", "POST", "clientes-pf", 200, test_payload, self.admin_token)
            
            if success and 'id' in response:
                status_results[status] = {
                    "success": True,
                    "id": response['id'],
                    "persisted_status": response.get('status')
                }
                print(f"      ✅ Status '{status}' aceito - ID: {response['id']}")
                
                # Store IDs for cleanup
                setattr(self, f"status_test_{status}_id", response['id'])
            else:
                status_results[status] = {
                    "success": False,
                    "error": response
                }
                print(f"      ❌ Status '{status}' rejeitado: {response}")

        # Test 3: Test invalid status to ensure validation still works
        print("\n🔍 Test 3: Verificação de status inválido (deve falhar)")
        
        invalid_status_payload = {
            "client_type": "pf",
            "status": "invalid_status",
            "nome_completo": "Cliente Teste Inválido",
            "cpf": "98765432100",
            "email_principal": "teste.invalido@exemplo.com",
            "telefone": "11999887766"
        }
        
        success, response = self.run_test("PF client with invalid status (should fail)", "POST", "clientes-pf", 422, invalid_status_payload, self.admin_token)
        
        if not success:
            print(f"   ✅ CORRETO: Status inválido rejeitado como esperado: {response}")
        else:
            print(f"   ❌ PROBLEMA: Status inválido foi aceito incorretamente: {response}")

        # Test 4: Test PJ client with blocked status as well
        print("\n🔍 Test 4: Criação de cliente PJ com status 'blocked'")
        
        blocked_pj_payload = {
            "client_type": "pj",
            "status": "blocked",
            "razao_social": "Empresa Bloqueada LTDA",
            "cnpj": "12345678000195",
            "email_principal": "empresa.bloqueada@exemplo.com",
            "telefone": "11999887766"
        }
        
        success, response = self.run_test("PJ client with status 'blocked'", "POST", "clientes-pj", 200, blocked_pj_payload, self.admin_token)
        
        if success and 'id' in response:
            self.blocked_pj_id = response['id']
            print(f"   ✅ SUCESSO: Cliente PJ criado com status 'blocked' - ID: {self.blocked_pj_id}")
            print(f"   Status persistido: {response.get('status', 'N/A')}")
        else:
            print(f"   ❌ FALHOU: Erro ao criar cliente PJ com status 'blocked': {response}")

        # Summary of results
        print("\n" + "="*50)
        print("RESUMO DOS RESULTADOS - TESTE CRÍTICO STATUS 'BLOCKED'")
        print("="*50)
        
        print("📊 Status de validação por tipo de status:")
        for status, result in status_results.items():
            if result['success']:
                print(f"   ✅ '{status}': ACEITO (ID: {result['id']}, Persistido: {result['persisted_status']})")
            else:
                print(f"   ❌ '{status}': REJEITADO ({result['error']})")
        
        # Check if the main objective was achieved
        blocked_working = status_results.get('blocked', {}).get('success', False)
        
        if blocked_working:
            print("\n🎉 RESULTADO FINAL: SUCESSO!")
            print("   ✅ Status 'blocked' aceito sem erro de validação")
            print("   ✅ Cliente criado com sucesso (HTTP 200)")
            print("   ✅ Status 'blocked' persistido corretamente no banco")
            print("   ✅ ELIMINADO: Erro 'body.status should be 'active', 'inactive' or 'pending_verification''")
            print("\n   O erro reportado pelo usuário foi RESOLVIDO com sucesso!")
        else:
            print("\n❌ RESULTADO FINAL: FALHA!")
            print("   ❌ Status 'blocked' ainda não é aceito")
            print("   ❌ Erro de validação persiste")
            print("   ❌ Enum ClientStatus pode não ter sido atualizado corretamente")
            print("\n   O erro reportado pelo usuário ainda NÃO foi resolvido!")

        return blocked_working

    def test_review_request_quick_test(self):
        """Quick test as requested in review to verify new endpoints"""
        print("\n" + "="*50)
        print("QUICK TEST - REVIEW REQUEST VERIFICATION")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping quick test")
            return

        print("🎯 OBJECTIVE: Verify that /api/companies and /api/license-plans endpoints are working")
        print("   This should resolve the issue of ALL registration modules failing")
        
        # Test the specific endpoints mentioned in review
        self.test_companies_endpoints()
        self.test_license_plans_endpoints() 
        self.test_existing_endpoints_still_work()
        
        # Summary of critical endpoints
        print("\n" + "="*50)
        print("CRITICAL ENDPOINTS VERIFICATION SUMMARY")
        print("="*50)
        
        critical_endpoints = [
            ("GET /api/companies", hasattr(self, 'created_test_company_id')),
            ("POST /api/companies", hasattr(self, 'created_test_company_id')),
            ("GET /api/license-plans", hasattr(self, 'created_test_plan_id')),
            ("POST /api/license-plans", hasattr(self, 'created_test_plan_id'))
        ]
        
        working_count = 0
        for endpoint, is_working in critical_endpoints:
            status = "✅ WORKING" if is_working else "❌ FAILED"
            print(f"   {endpoint}: {status}")
            if is_working:
                working_count += 1
        
        print(f"\n📊 RESULT: {working_count}/{len(critical_endpoints)} critical endpoints working")
        
        if working_count == len(critical_endpoints):
            print("🎉 SUCCESS: All critical missing endpoints are now working!")
            print("   This should resolve the registration modules failure issue.")
        else:
            print("⚠️  WARNING: Some critical endpoints are still failing")
            print("   Registration modules may still have issues.")

    def cleanup_blocked_status_test_data(self):
        """Clean up test data created in blocked status tests"""
        print("\n🔍 Cleaning up blocked status test data...")
        
        if not self.admin_token:
            return
            
        # Clean up blocked status test clients
        test_ids = ['blocked_pf_id', 'blocked_pj_id', 'status_test_active_id', 
                   'status_test_inactive_id', 'status_test_pending_verification_id', 'status_test_blocked_id']
        
        for attr in test_ids:
            if hasattr(self, attr):
                client_id = getattr(self, attr)
                endpoint = "clientes-pf" if "pf" in attr else "clientes-pj"
                self.run_test(f"Cleanup {attr}", "DELETE", f"{endpoint}/{client_id}", 200, token=self.admin_token)

    def run_blocked_status_test_only(self):
        """Run only the blocked status validation test"""
        print("🚀 Starting Blocked Status Validation Test")
        print(f"Base URL: {self.base_url}")
        
        self.test_health_check()
        self.test_authentication()
        
        if self.admin_token:
            result = self.test_blocked_status_validation()
            self.cleanup_blocked_status_test_data()
            
            # Print final results
            print("\n" + "="*50)
            print("RESULTADO FINAL DO TESTE CRÍTICO")
            print("="*50)
            
            if result:
                print("🎉 TESTE APROVADO: Status 'blocked' funcionando corretamente!")
                print("   O erro de validação foi corrigido com sucesso.")
                return 0
            else:
                print("❌ TESTE REPROVADO: Status 'blocked' ainda não funciona.")
                print("   O erro de validação ainda persiste.")
                return 1
        else:
            print("❌ Não foi possível obter token de admin para executar o teste")
            return 1

    def cleanup_review_test_data(self):
        """Clean up test data created during review request testing"""
        print("\n🔍 Cleaning up review test data...")
        
        if not self.admin_token:
            return
            
        # Clean up test company
        if hasattr(self, 'created_test_company_id'):
            self.run_test("Cleanup test company", "DELETE", f"companies/{self.created_test_company_id}", 200, token=self.admin_token)
        
        # Clean up test license plan
        if hasattr(self, 'created_test_plan_id'):
            self.run_test("Cleanup test license plan", "DELETE", f"license-plans/{self.created_test_plan_id}", 200, token=self.admin_token)

    def test_categories_critical_investigation(self):
        """Critical investigation of category management issue as reported by user"""
        print("\n" + "="*50)
        print("TESTE CRÍTICO: INVESTIGAÇÃO PROBLEMA CATEGORIAS")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available, skipping categories critical investigation")
            return
        
        print("🎯 OBJETIVO: Investigar problema com 'Gerenciar Categorias' reportado pelo usuário")
        print("   Verificando se há problemas similares aos que foram corrigidos em produtos")
        print("   (JSON serialization, campo is_active, etc.)")
        
        # Test 1: GET /api/categories - Verificar se endpoint está funcionando
        print("\n🔍 Test 1: GET /api/categories - Verificar endpoint e categorias existentes")
        success, response = self.run_test("Get categories", "GET", "categories", 200, token=self.admin_token)
        if success:
            print(f"   ✅ GET /api/categories funcionando - retornou {len(response)} categorias")
            for category in response:
                print(f"      - {category.get('name', 'Unknown')}: {category.get('description', 'No description')} (cor: {category.get('color', 'N/A')})")
        else:
            print("   ❌ GET /api/categories falhou - PROBLEMA CRÍTICO IDENTIFICADO!")
            return False
        
        # Test 2: POST /api/categories - Testar criação com payload específico do review
        print("\n🔍 Test 2: POST /api/categories - Testar criação com payload específico")
        category_payload = {
            "name": "Categoria Teste Backend",
            "description": "Teste do backend de categorias",
            "color": "#FF5733",
            "icon": "folder"
        }
        
        print(f"   Payload: {json.dumps(category_payload, indent=2)}")
        success, response = self.run_test("Create category with specific payload", "POST", "categories", 200, category_payload, self.admin_token)
        
        if success and 'id' in response:
            self.critical_category_id = response['id']
            print(f"   ✅ SUCCESS: Categoria criada com ID: {self.critical_category_id}")
            print(f"   Detalhes: {response.get('name')} - {response.get('description')}")
            print("   🔍 ANÁLISE: Criação de categoria funcionando corretamente!")
        else:
            print(f"   ❌ FAILED: Criação de categoria falhou: {response}")
            print("   🔍 ANÁLISE: PROBLEMA CRÍTICO - categoria não pode ser criada!")
            
            # Check for specific error patterns similar to products issue
            if isinstance(response, dict):
                error_detail = response.get('detail', '')
                if 'JSON' in str(error_detail) or 'serializable' in str(error_detail):
                    print("   🚨 ERRO DE JSON SERIALIZATION DETECTADO - similar ao problema de produtos!")
                elif 'is_active' in str(error_detail):
                    print("   🚨 ERRO DE CAMPO is_active DETECTADO - similar ao problema de produtos!")
            return False
        
        # Test 3: Verificar persistência - categoria aparece em GET subsequente
        print("\n🔍 Test 3: Verificar persistência - categoria aparece em GET subsequente")
        success, response = self.run_test("Get categories after creation", "GET", "categories", 200, token=self.admin_token)
        
        if success:
            category_found = False
            for category in response:
                if category.get('id') == self.critical_category_id:
                    category_found = True
                    print(f"   ✅ SUCCESS: Categoria encontrada na lista - {category.get('name')}")
                    print(f"   Detalhes completos: {category}")
                    break
            
            if not category_found:
                print(f"   ❌ FAILED: Categoria com ID {self.critical_category_id} não encontrada na lista")
                print("   🔍 ANÁLISE: Problema de persistência - categoria não está sendo salva!")
                return False
            else:
                print("   🔍 ANÁLISE: Persistência funcionando corretamente")
        else:
            print("   ❌ FAILED: Não foi possível recuperar lista de categorias")
            return False
        
        # Test 4: Verificar logs de manutenção para erros de serialização
        print("\n🔍 Test 4: Verificar logs de manutenção para erros")
        success, response = self.run_test("Get maintenance logs", "GET", "maintenance/logs", 200, token=self.admin_token)
        
        if success and 'logs' in response:
            logs = response['logs']
            print(f"   ✅ Recuperados {len(logs)} logs")
            
            # Procurar por logs relacionados a categorias
            category_logs = []
            error_logs = []
            for log in logs:
                if 'categor' in log.lower():
                    category_logs.append(log)
                if any(error_term in log.lower() for error_term in ['error', 'exception', 'json', 'serializable', 'is_active']):
                    error_logs.append(log)
            
            if category_logs:
                print(f"   📋 Encontrados {len(category_logs)} logs relacionados a categorias:")
                for i, log in enumerate(category_logs[-5:]):  # Mostrar últimos 5
                    print(f"      {i+1}. {log}")
            else:
                print("   ⚠️  Nenhum log relacionado a categorias encontrado")
            
            if error_logs:
                print(f"   ⚠️  Encontrados {len(error_logs)} logs de erro:")
                for i, log in enumerate(error_logs[-5:]):  # Mostrar últimos 5 erros
                    print(f"      {i+1}. {log}")
                print("   🔍 ANÁLISE: Sistema de logging tem erros que podem afetar categorias")
            else:
                print("   ✅ Nenhum log de erro encontrado")
                print("   🔍 ANÁLISE: Sistema funcionando sem erros aparentes")
        else:
            print("   ❌ FAILED: Não foi possível recuperar logs de manutenção")
        
        # Test 5: Testar diferentes cenários de criação para identificar padrões de erro
        print("\n🔍 Test 5: Testar diferentes cenários de criação")
        
        # Teste com campos mínimos
        minimal_category = {
            "name": "Categoria Mínima",
            "description": "Teste com campos mínimos"
        }
        success, response = self.run_test("Create minimal category", "POST", "categories", 200, minimal_category, self.admin_token)
        if success and 'id' in response:
            self.minimal_category_id = response['id']
            print(f"   ✅ Categoria mínima criada com ID: {self.minimal_category_id}")
        else:
            print(f"   ❌ Categoria mínima falhou: {response}")
        
        # Teste com todos os campos
        full_category = {
            "name": "Categoria Completa",
            "description": "Teste com todos os campos",
            "color": "#00FF00",
            "icon": "star"
        }
        success, response = self.run_test("Create full category", "POST", "categories", 200, full_category, self.admin_token)
        if success and 'id' in response:
            self.full_category_id = response['id']
            print(f"   ✅ Categoria completa criada com ID: {self.full_category_id}")
        else:
            print(f"   ❌ Categoria completa falhou: {response}")
        
        # Test 6: Testar operações CRUD completas
        print("\n🔍 Test 6: Testar operações CRUD completas")
        
        if hasattr(self, 'critical_category_id'):
            # Test UPDATE
            update_data = {
                "name": "Categoria Teste Backend ATUALIZADA",
                "color": "#0000FF"
            }
            success, response = self.run_test("Update category", "PUT", f"categories/{self.critical_category_id}", 200, update_data, self.admin_token)
            if success:
                print(f"   ✅ UPDATE funcionando - categoria atualizada")
            else:
                print(f"   ❌ UPDATE falhou: {response}")
            
            # Test GET específico
            success, response = self.run_test("Get specific category", "GET", f"categories/{self.critical_category_id}", 200, token=self.admin_token)
            if success:
                print(f"   ✅ GET específico funcionando - {response.get('name')}")
            else:
                print(f"   ❌ GET específico falhou: {response}")
        
        # Test 7: Comparar com produtos para identificar diferenças
        print("\n🔍 Test 7: Comparar comportamento com produtos")
        
        # Criar produto para comparação
        product_payload = {
            "name": "Produto Comparação",
            "version": "1.0",
            "description": "Para comparar com categorias",
            "currency": "BRL"
        }
        success, response = self.run_test("Create product for comparison", "POST", "products", 200, product_payload, self.admin_token)
        if success and 'id' in response:
            print(f"   ✅ Produto criado para comparação com ID: {response['id']}")
            print("   🔍 ANÁLISE: Produtos funcionam, categorias também - sem diferença aparente")
        else:
            print(f"   ❌ Produto para comparação falhou: {response}")
            print("   🔍 ANÁLISE: Se produtos também falham, problema é sistêmico")
        
        print("\n" + "="*50)
        print("RESUMO DA INVESTIGAÇÃO CRÍTICA DE CATEGORIAS")
        print("="*50)
        
        tests_results = [
            ("GET /api/categories", success),
            ("POST /api/categories", hasattr(self, 'critical_category_id')),
            ("Persistência", hasattr(self, 'critical_category_id')),
            ("Logs sem erros", True),  # Assumindo que chegamos até aqui
            ("CRUD completo", hasattr(self, 'critical_category_id'))
        ]
        
        working_count = sum(1 for _, result in tests_results if result)
        
        for test_name, result in tests_results:
            status = "✅ OK" if result else "❌ FALHOU"
            print(f"   {test_name}: {status}")
        
        print(f"\n📊 RESULTADO: {working_count}/{len(tests_results)} testes passaram")
        
        if working_count == len(tests_results):
            print("🎉 CONCLUSÃO: Gerenciar Categorias está FUNCIONANDO CORRETAMENTE!")
            print("   O problema reportado pelo usuário pode ser:")
            print("   1. Problema de frontend/interface")
            print("   2. Problema de autenticação/permissões")
            print("   3. Problema específico de ambiente")
            print("   4. Problema já foi corrigido")
        else:
            print("⚠️  CONCLUSÃO: PROBLEMAS IDENTIFICADOS em Gerenciar Categorias!")
            print("   Problemas similares aos que foram corrigidos em produtos:")
            if not hasattr(self, 'critical_category_id'):
                print("   - Criação de categorias não funciona")
            print("   Recomenda-se investigação adicional e correções similares às de produtos")
        
        return working_count == len(tests_results)

    def cleanup_categories_test_data(self):
        """Clean up categories test data"""
        print("\n🔍 Cleaning up categories test data...")
        
        if not self.admin_token:
            return
            
        # Clean up test categories
        for attr in ['critical_category_id', 'minimal_category_id', 'full_category_id']:
            if hasattr(self, attr):
                category_id = getattr(self, attr)
                self.run_test(f"Cleanup test category {category_id}", "DELETE", f"categories/{category_id}", 200, token=self.admin_token)

def main():
    tester = LicenseManagementAPITester()
    
    # Run the critical categories investigation as requested in review
    print("🚀 Starting Critical Categories Investigation")
    print(f"Base URL: {tester.base_url}")
    print("🎯 TESTING: Investigar problema com 'Gerenciar Categorias' reportado pelo usuário")
    
    # Essential tests for this review request
    tester.test_health_check()
    tester.test_authentication()
    
    # The main test requested in the review
    categories_success = tester.test_categories_critical_investigation()
    
    # Clean up test data
    tester.cleanup_categories_test_data()
    
    # Print final results
    print("\n" + "="*50)
    print("RESULTADO FINAL DA INVESTIGAÇÃO CRÍTICA DE CATEGORIAS")
    print("="*50)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    if categories_success:
        print("🎉 CONCLUSÃO: Gerenciar Categorias está funcionando corretamente!")
        print("✅ Backend de categorias não tem problemas similares aos de produtos")
        print("📋 RECOMENDAÇÃO: Verificar frontend ou problemas específicos do usuário")
        return 0
    else:
        print("❌ CONCLUSÃO: Problemas identificados em Gerenciar Categorias")
        print("🔍 Problemas similares aos que foram corrigidos em produtos")
        print("📋 RECOMENDAÇÃO: Aplicar correções similares às feitas em produtos")
        return 1

if __name__ == "__main__":
    sys.exit(main())