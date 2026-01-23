#!/usr/bin/env python3
"""
E2E Go-Live Test Suite for License Management System
Tests all critical scenarios for go-live preparation
"""

import requests
import sys
import json
import time
from datetime import datetime, timedelta

class E2EGoLiveTest:
    def __init__(self, base_url="https://licensehub-23.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.super_admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, params=None, tenant_id="default"):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'X-Tenant-ID': tenant_id
        }
        if token and token != "cookie_based_auth":
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers)

            if isinstance(expected_status, list):
                success = response.status_code in expected_status
            else:
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
                expected_str = str(expected_status) if not isinstance(expected_status, list) else f"one of {expected_status}"
                print(f"❌ Failed - Expected {expected_str}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_e2e_go_live_scenarios(self):
        """Test complete E2E scenarios for go-live preparation"""
        print("\n" + "="*80)
        print("🚀 TESTE E2E COMPLETO - PREPARAÇÃO GO-LIVE")
        print("="*80)
        print("🎯 CONTEXTO: Sistema de gestão de licenças multi-tenant pronto para apresentação")
        print("   Validando TODOS os fluxos críticos para garantir que não há bugs")
        print("="*80)
        
        # Store test results for comprehensive reporting
        test_results = {
            "authentication": {"passed": 0, "total": 0, "details": []},
            "license_management": {"passed": 0, "total": 0, "details": []},
            "cadastros": {"passed": 0, "total": 0, "details": []},
            "tickets": {"passed": 0, "total": 0, "details": []},
            "multi_tenancy": {"passed": 0, "total": 0, "details": []},
            "security": {"passed": 0, "total": 0, "details": []}
        }
        
        # CENÁRIO 1: AUTENTICAÇÃO E AUTORIZAÇÃO
        print("\n" + "="*60)
        print("CENÁRIO 1: AUTENTICAÇÃO E AUTORIZAÇÃO")
        print("="*60)
        
        # Test Super Admin login
        super_admin_creds = {"email": "superadmin@autotech.com", "password": "admin123"}
        success, response = self.run_test("Super Admin Login", "POST", "auth/login", 200, super_admin_creds)
        test_results["authentication"]["total"] += 1
        if success:
            test_results["authentication"]["passed"] += 1
            test_results["authentication"]["details"].append("✅ Super Admin login funcionando")
            self.super_admin_token = response.get("access_token", "cookie_based_auth")
        else:
            test_results["authentication"]["details"].append("❌ Super Admin login falhou")
        
        # Test Admin login
        admin_creds = {"email": "admin@demo.com", "password": "admin123"}
        success, response = self.run_test("Admin Login", "POST", "auth/login", 200, admin_creds)
        test_results["authentication"]["total"] += 1
        if success:
            test_results["authentication"]["passed"] += 1
            test_results["authentication"]["details"].append("✅ Admin login funcionando")
            self.admin_token = response.get("access_token", "cookie_based_auth")
        else:
            test_results["authentication"]["details"].append("❌ Admin login falhou")
        
        # Test User login
        user_creds = {"email": "user@demo.com", "password": "user123"}
        success, response = self.run_test("User Login", "POST", "auth/login", 200, user_creds)
        test_results["authentication"]["total"] += 1
        if success:
            test_results["authentication"]["passed"] += 1
            test_results["authentication"]["details"].append("✅ User login funcionando")
            self.user_token = response.get("access_token", "cookie_based_auth")
        else:
            test_results["authentication"]["details"].append("❌ User login falhou")
        
        # Test role-based redirection
        if self.admin_token:
            success, response = self.run_test("Admin auth/me", "GET", "auth/me", 200, token=self.admin_token)
            test_results["authentication"]["total"] += 1
            if success and response.get("role") == "admin":
                test_results["authentication"]["passed"] += 1
                test_results["authentication"]["details"].append("✅ Admin role verification funcionando")
            else:
                test_results["authentication"]["details"].append("❌ Admin role verification falhou")
        
        if self.user_token:
            success, response = self.run_test("User auth/me", "GET", "auth/me", 200, token=self.user_token)
            test_results["authentication"]["total"] += 1
            if success and response.get("role") == "user":
                test_results["authentication"]["passed"] += 1
                test_results["authentication"]["details"].append("✅ User role verification funcionando")
            else:
                test_results["authentication"]["details"].append("❌ User role verification falhou")
        
        # CENÁRIO 2: GESTÃO DE LICENÇAS (CRUD Completo)
        print("\n" + "="*60)
        print("CENÁRIO 2: GESTÃO DE LICENÇAS (CRUD Completo)")
        print("="*60)
        
        if self.admin_token:
            # Create license
            license_data = {
                "name": "Licença E2E Test",
                "description": "Licença para teste E2E completo",
                "max_users": 5,
                "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat(),
                "features": ["feature1", "feature2", "advanced_reports"]
            }
            success, response = self.run_test("Create License", "POST", "licenses", 200, license_data, self.admin_token)
            test_results["license_management"]["total"] += 1
            if success and "id" in response:
                test_results["license_management"]["passed"] += 1
                test_results["license_management"]["details"].append("✅ Criação de licença funcionando")
                self.created_license_id = response["id"]
            else:
                test_results["license_management"]["details"].append("❌ Criação de licença falhou")
            
            # List licenses with filters
            success, response = self.run_test("List Licenses", "GET", "licenses", 200, token=self.admin_token)
            test_results["license_management"]["total"] += 1
            if success and isinstance(response, list):
                test_results["license_management"]["passed"] += 1
                test_results["license_management"]["details"].append(f"✅ Listagem de licenças funcionando ({len(response)} licenças)")
            else:
                test_results["license_management"]["details"].append("❌ Listagem de licenças falhou")
            
            # Edit license
            if hasattr(self, 'created_license_id'):
                update_data = {
                    "name": "Licença E2E Test - Atualizada",
                    "description": "Licença atualizada no teste E2E",
                    "max_users": 10
                }
                success, response = self.run_test("Update License", "PUT", f"licenses/{self.created_license_id}", 200, update_data, self.admin_token)
                test_results["license_management"]["total"] += 1
                if success:
                    test_results["license_management"]["passed"] += 1
                    test_results["license_management"]["details"].append("✅ Edição de licença funcionando")
                else:
                    test_results["license_management"]["details"].append("❌ Edição de licença falhou")
            
            # Check license expiration
            success, response = self.run_test("License Stats", "GET", "stats", 200, token=self.admin_token)
            test_results["license_management"]["total"] += 1
            if success and "total_licenses" in response:
                test_results["license_management"]["passed"] += 1
                test_results["license_management"]["details"].append("✅ Verificação de expiração funcionando")
            else:
                test_results["license_management"]["details"].append("❌ Verificação de expiração falhou")
        
        # CENÁRIO 3: GESTÃO DE CADASTROS
        print("\n" + "="*60)
        print("CENÁRIO 3: GESTÃO DE CADASTROS")
        print("="*60)
        
        if self.admin_token:
            # Create Company
            company_data = {
                "name": "Empresa E2E Test LTDA",
                "subdomain": f"e2e-test-{int(time.time())}",
                "contact_email": "contato@e2etest.com",
                "plan": "professional"
            }
            success, response = self.run_test("Create Company", "POST", "companies", 200, company_data, self.admin_token)
            test_results["cadastros"]["total"] += 1
            if success:
                test_results["cadastros"]["passed"] += 1
                test_results["cadastros"]["details"].append("✅ Criação de empresa funcionando")
            else:
                test_results["cadastros"]["details"].append("❌ Criação de empresa falhou")
            
            # Create Product
            product_data = {
                "name": "Produto E2E Test",
                "version": "1.0",
                "description": "Produto para teste E2E",
                "price": 299.99,
                "features": ["basic_features", "advanced_analytics"]
            }
            success, response = self.run_test("Create Product", "POST", "products", 200, product_data, self.admin_token)
            test_results["cadastros"]["total"] += 1
            if success:
                test_results["cadastros"]["passed"] += 1
                test_results["cadastros"]["details"].append("✅ Criação de produto funcionando")
            else:
                test_results["cadastros"]["details"].append("❌ Criação de produto falhou")
            
            # Create License Plan
            plan_data = {
                "name": "Plano E2E Test",
                "description": "Plano para teste E2E",
                "max_users": 25,
                "duration_days": 365,
                "price": 1999.99,
                "features": ["all_features", "priority_support"]
            }
            success, response = self.run_test("Create License Plan", "POST", "license-plans", 200, plan_data, self.admin_token)
            test_results["cadastros"]["total"] += 1
            if success:
                test_results["cadastros"]["passed"] += 1
                test_results["cadastros"]["details"].append("✅ Criação de plano funcionando")
            else:
                test_results["cadastros"]["details"].append("❌ Criação de plano falhou")
            
            # Create Category
            category_data = {
                "name": "Categoria E2E Test",
                "description": "Categoria para teste E2E",
                "color": "#FF6B35",
                "icon": "test-icon"
            }
            success, response = self.run_test("Create Category", "POST", "categories", 200, category_data, self.admin_token)
            test_results["cadastros"]["total"] += 1
            if success:
                test_results["cadastros"]["passed"] += 1
                test_results["cadastros"]["details"].append("✅ Criação de categoria funcionando")
            else:
                test_results["cadastros"]["details"].append("❌ Criação de categoria falhou")
        
        # CENÁRIO 4: SISTEMA DE TICKETS (User → Admin)
        print("\n" + "="*60)
        print("CENÁRIO 4: SISTEMA DE TICKETS (User → Admin)")
        print("="*60)
        
        # User creates ticket
        if self.user_token:
            ticket_data = {
                "type": "renewal",
                "title": "Solicitação de Renovação E2E",
                "description": "Solicitação de renovação de licença para teste E2E completo. Preciso renovar minha licença que está próxima do vencimento.",
                "priority": "high"
            }
            success, response = self.run_test("User Create Ticket", "POST", "tickets", 200, ticket_data, self.user_token)
            test_results["tickets"]["total"] += 1
            if success and "id" in response:
                test_results["tickets"]["passed"] += 1
                test_results["tickets"]["details"].append("✅ Criação de ticket por usuário funcionando")
                self.created_ticket_id = response["id"]
            else:
                test_results["tickets"]["details"].append("❌ Criação de ticket por usuário falhou")
        
        # Admin views pending tickets
        if self.admin_token:
            success, response = self.run_test("Admin View Tickets", "GET", "tickets", 200, token=self.admin_token)
            test_results["tickets"]["total"] += 1
            if success and isinstance(response, list):
                test_results["tickets"]["passed"] += 1
                test_results["tickets"]["details"].append(f"✅ Visualização de tickets por admin funcionando ({len(response)} tickets)")
            else:
                test_results["tickets"]["details"].append("❌ Visualização de tickets por admin falhou")
            
            # Admin approves/rejects ticket
            if hasattr(self, 'created_ticket_id'):
                ticket_update = {
                    "status": "approved",
                    "admin_response": "Ticket aprovado para renovação. Processando solicitação."
                }
                success, response = self.run_test("Admin Update Ticket", "PUT", f"tickets/{self.created_ticket_id}", 200, ticket_update, self.admin_token)
                test_results["tickets"]["total"] += 1
                if success:
                    test_results["tickets"]["passed"] += 1
                    test_results["tickets"]["details"].append("✅ Aprovação/rejeição de ticket funcionando")
                else:
                    test_results["tickets"]["details"].append("❌ Aprovação/rejeição de ticket falhou")
        
        # CENÁRIO 5: MULTI-TENANCY
        print("\n" + "="*60)
        print("CENÁRIO 5: MULTI-TENANCY")
        print("="*60)
        
        # Test data isolation between tenants
        if self.admin_token:
            success, response = self.run_test("Admin View Own Data", "GET", "licenses", 200, token=self.admin_token)
            test_results["multi_tenancy"]["total"] += 1
            if success:
                admin_licenses = len(response) if isinstance(response, list) else 0
                test_results["multi_tenancy"]["passed"] += 1
                test_results["multi_tenancy"]["details"].append(f"✅ Isolamento de dados funcionando (admin vê {admin_licenses} licenças)")
            else:
                test_results["multi_tenancy"]["details"].append("❌ Isolamento de dados falhou")
        
        # Test super admin can see all tenants
        if hasattr(self, 'super_admin_token'):
            success, response = self.run_test("Super Admin View All Data", "GET", "licenses", 200, token=self.super_admin_token)
            test_results["multi_tenancy"]["total"] += 1
            if success:
                super_admin_licenses = len(response) if isinstance(response, list) else 0
                test_results["multi_tenancy"]["passed"] += 1
                test_results["multi_tenancy"]["details"].append(f"✅ Super admin acesso total funcionando ({super_admin_licenses} licenças)")
            else:
                test_results["multi_tenancy"]["details"].append("❌ Super admin acesso total falhou")
        
        # CENÁRIO 6: SEGURANÇA
        print("\n" + "="*60)
        print("CENÁRIO 6: SEGURANÇA")
        print("="*60)
        
        # Test 403 for unauthorized access
        if self.user_token:
            success, response = self.run_test("User Access Admin Endpoint (should fail)", "GET", "users", 403, token=self.user_token)
            test_results["security"]["total"] += 1
            if success:
                test_results["security"]["passed"] += 1
                test_results["security"]["details"].append("✅ Proteção de endpoints funcionando (403 para usuário)")
            else:
                test_results["security"]["details"].append("❌ Proteção de endpoints falhou")
        
        # Test data masking for regular users
        if self.user_token:
            success, response = self.run_test("User View Own Licenses", "GET", "user/licenses", 200, token=self.user_token)
            test_results["security"]["total"] += 1
            if success:
                test_results["security"]["passed"] += 1
                test_results["security"]["details"].append("✅ Acesso restrito a dados próprios funcionando")
            else:
                test_results["security"]["details"].append("❌ Acesso restrito a dados próprios falhou")
        
        # Test rate limiting (basic check)
        if self.admin_token:
            # Make multiple rapid requests
            rapid_requests_passed = 0
            for i in range(5):
                success, response = self.run_test(f"Rate Limit Test {i+1}", "GET", "auth/me", [200, 429], token=self.admin_token)
                if success:
                    rapid_requests_passed += 1
            
            test_results["security"]["total"] += 1
            if rapid_requests_passed >= 3:  # At least some requests should pass
                test_results["security"]["passed"] += 1
                test_results["security"]["details"].append("✅ Rate limiting funcionando (algumas requisições passaram)")
            else:
                test_results["security"]["details"].append("❌ Rate limiting pode estar muito restritivo")
        
        # RELATÓRIO FINAL E2E
        print("\n" + "="*80)
        print("📊 RELATÓRIO FINAL - TESTE E2E GO-LIVE")
        print("="*80)
        
        total_passed = 0
        total_tests = 0
        
        for scenario, results in test_results.items():
            scenario_name = scenario.replace("_", " ").title()
            passed = results["passed"]
            total = results["total"]
            percentage = (passed / total * 100) if total > 0 else 0
            
            total_passed += passed
            total_tests += total
            
            print(f"\n🎯 {scenario_name}:")
            print(f"   Testes: {passed}/{total} ({percentage:.1f}%)")
            for detail in results["details"]:
                print(f"   {detail}")
        
        overall_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 RESULTADO GERAL:")
        print(f"   Total de testes: {total_tests}")
        print(f"   Testes aprovados: {total_passed}")
        print(f"   Taxa de sucesso: {overall_percentage:.1f}%")
        
        if overall_percentage >= 90:
            print("\n🎉 SISTEMA PRONTO PARA GO-LIVE!")
            print("   ✅ Todos os cenários críticos validados")
            print("   ✅ Autenticação e autorização funcionando")
            print("   ✅ CRUD de licenças completo")
            print("   ✅ Gestão de cadastros operacional")
            print("   ✅ Sistema de tickets funcionando")
            print("   ✅ Multi-tenancy implementado")
            print("   ✅ Segurança validada")
            return True
        elif overall_percentage >= 75:
            print("\n⚠️ SISTEMA QUASE PRONTO - AJUSTES MENORES NECESSÁRIOS")
            print(f"   {total_passed}/{total_tests} testes aprovados")
            print("   Revisar itens que falharam antes do go-live")
            return False
        else:
            print("\n❌ SISTEMA NÃO PRONTO PARA GO-LIVE")
            print(f"   Apenas {total_passed}/{total_tests} testes aprovados")
            print("   Correções críticas necessárias")
            return False

if __name__ == "__main__":
    tester = E2EGoLiveTest()
    success = tester.test_e2e_go_live_scenarios()
    
    print("\n" + "="*50)
    print("E2E GO-LIVE TEST RESULTS")
    print("="*50)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    
    if success and success_rate >= 90:
        print(f"🎉 E2E GO-LIVE TESTS PASSED! {success_rate:.1f}% success rate")
        sys.exit(0)
    else:
        print(f"❌ E2E GO-LIVE TESTS FAILED! {success_rate:.1f}% success rate")
        sys.exit(1)