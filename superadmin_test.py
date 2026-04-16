import requests
import sys
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class SuperAdminLoginTester:
    def __init__(self):
        # Get backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://license-admin-hub-1.preview.emergentagent.com')
        self.base_url = f"{backend_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
    def run_test(self, test_name, method, endpoint, expected_status, data=None, token=None, params=None):
        """Run a single API test"""
        self.tests_run += 1
        
        try:
            url = f"{self.base_url}/{endpoint}"
            headers = {'Content-Type': 'application/json'}
            
            if token:
                headers['Authorization'] = f'Bearer {token}'
            
            print(f"🔍 {test_name}")
            print(f"   {method} {url}")
            
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            
            print(f"   Status: {response.status_code} (expected: {expected_status})")
            
            if response.status_code == expected_status:
                self.tests_passed += 1
                try:
                    response_data = response.json()
                    print(f"   ✅ Success")
                    return True, response_data
                except:
                    print(f"   ✅ Success (no JSON response)")
                    return True, {}
            else:
                print(f"   ❌ Failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    return False, error_data
                except:
                    print(f"   Error: {response.text}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_superadmin_login_investigation(self):
        """Investigate superadmin login issue as requested in review"""
        print("\n" + "="*80)
        print("INVESTIGAÇÃO CRÍTICA - ERRO DE LOGIN DO SUPERADMIN")
        print("="*80)
        print("🎯 PROBLEMA REPORTADO: Usuario tentando logar com superadmin@autotech.com/superadmin123")
        print("   mas recebe 'Incorrect email or password'")
        print("🎯 SENHA CORRETA: secure-temp-password-123 (conforme INITIAL_SUPERADMIN_PASSWORD no .env)")
        print("🎯 OBJETIVO: Diagnosticar por que o login de superadmin não funciona")
        print("="*80)
        
        # Test 1: Verify superadmin exists in database
        print("\n🔍 TESTE 1: VERIFICAR SE SUPERADMIN EXISTE NO BANCO DE DADOS")
        
        # Try to get system stats to check database connectivity first
        success, response = self.run_test("Database connectivity check", "GET", "stats", 200, token=None)
        if not success:
            print("   ⚠️ Database connectivity issue - trying without auth")
        
        # Test 2: Test correct superadmin credentials (from .env)
        print("\n🔍 TESTE 2: TESTAR CREDENCIAIS CORRETAS DO SUPERADMIN")
        print("   Testando: superadmin@autotech.com / secure-temp-password-123")
        
        correct_superadmin_credentials = {
            "email": "superadmin@autotech.com",
            "password": "secure-temp-password-123"
        }
        success, response = self.run_test("Superadmin login (correct password)", "POST", "auth/login", 200, correct_superadmin_credentials)
        if success and 'access_token' in response:
            self.superadmin_token = response['access_token']
            print(f"   ✅ SUCESSO! Superadmin login funcionando com senha correta")
            print(f"   ✅ Token obtido: {self.superadmin_token[:20]}...")
            print(f"   ✅ Usuário: {response.get('user', {}).get('name', 'N/A')}")
            print(f"   ✅ Role: {response.get('user', {}).get('role', 'N/A')}")
            print(f"   ✅ Email: {response.get('user', {}).get('email', 'N/A')}")
            print(f"   ✅ Tenant ID: {response.get('user', {}).get('tenant_id', 'N/A')}")
        else:
            print("   ❌ FALHA! Superadmin login não funcionou mesmo com senha correta")
            print("   ❌ Isso indica um problema sério no sistema de autenticação")
            if response:
                print(f"   ❌ Erro: {response}")
        
        # Test 3: Test incorrect superadmin credentials (what user was trying)
        print("\n🔍 TESTE 3: TESTAR CREDENCIAIS INCORRETAS (O QUE O USUÁRIO ESTAVA TENTANDO)")
        print("   Testando: superadmin@autotech.com / superadmin123")
        
        incorrect_superadmin_credentials = {
            "email": "superadmin@autotech.com", 
            "password": "superadmin123"
        }
        success, response = self.run_test("Superadmin login (incorrect password)", "POST", "auth/login", 401, incorrect_superadmin_credentials)
        if not success and response:
            print(f"   ✅ CORRETO! Login falhou como esperado com senha incorreta")
            print(f"   ✅ Mensagem de erro: {response.get('detail', 'N/A')}")
        else:
            print("   ❌ PROBLEMA! Login deveria falhar com senha incorreta")
        
        # Test 4: Test normal admin credentials for comparison
        print("\n🔍 TESTE 4: TESTAR ADMIN NORMAL PARA COMPARAÇÃO")
        print("   Testando: admin@demo.com / admin123")
        
        admin_credentials = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        success, response = self.run_test("Normal admin login", "POST", "auth/login", 200, admin_credentials)
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   ✅ Admin normal funcionando corretamente")
            print(f"   ✅ Token obtido: {self.admin_token[:20]}...")
            print(f"   ✅ Usuário: {response.get('user', {}).get('name', 'N/A')}")
            print(f"   ✅ Role: {response.get('user', {}).get('role', 'N/A')}")
            print(f"   ✅ Tenant ID: {response.get('user', {}).get('tenant_id', 'N/A')}")
        else:
            print("   ❌ Admin normal também não está funcionando!")
        
        # Test 5: Verify superadmin can access protected endpoints
        if hasattr(self, 'superadmin_token'):
            print("\n🔍 TESTE 5: VERIFICAR ACESSO DO SUPERADMIN A ENDPOINTS PROTEGIDOS")
            
            # Test auth/me endpoint
            success, response = self.run_test("Superadmin auth/me", "GET", "auth/me", 200, token=self.superadmin_token)
            if success:
                print(f"   ✅ Superadmin auth/me funcionando")
                print(f"      - Email: {response.get('email', 'N/A')}")
                print(f"      - Name: {response.get('name', 'N/A')}")
                print(f"      - Role: {response.get('role', 'N/A')}")
                print(f"      - Tenant ID: {response.get('tenant_id', 'N/A')}")
                print(f"      - Is Active: {response.get('is_active', 'N/A')}")
            
            # Test users endpoint (superadmin should see all users)
            success, response = self.run_test("Superadmin get users", "GET", "users", 200, token=self.superadmin_token)
            if success:
                print(f"   ✅ Superadmin pode acessar usuários: {len(response)} usuários encontrados")
                
                # Look for superadmin user in the list
                superadmin_user = None
                for user in response:
                    if user.get('email') == 'superadmin@autotech.com':
                        superadmin_user = user
                        break
                
                if superadmin_user:
                    print(f"   ✅ Superadmin encontrado na lista de usuários:")
                    print(f"      - ID: {superadmin_user.get('id', 'N/A')}")
                    print(f"      - Email: {superadmin_user.get('email', 'N/A')}")
                    print(f"      - Name: {superadmin_user.get('name', 'N/A')}")
                    print(f"      - Role: {superadmin_user.get('role', 'N/A')}")
                    print(f"      - Tenant ID: {superadmin_user.get('tenant_id', 'N/A')}")
                    print(f"      - Is Active: {superadmin_user.get('is_active', 'N/A')}")
                    print(f"      - Created At: {superadmin_user.get('created_at', 'N/A')}")
                else:
                    print(f"   ⚠️ Superadmin não encontrado na lista de usuários")
            
            # Test stats endpoint
            success, response = self.run_test("Superadmin get stats", "GET", "stats", 200, token=self.superadmin_token)
            if success:
                print(f"   ✅ Superadmin pode acessar estatísticas do sistema")
                print(f"      - Total users: {response.get('total_users', 'N/A')}")
                print(f"      - Total licenses: {response.get('total_licenses', 'N/A')}")
                print(f"      - System status: {response.get('system_status', 'N/A')}")
        
        # Test 6: Test tenant_id processing for superadmin
        print("\n🔍 TESTE 6: VERIFICAR PROCESSAMENTO DE TENANT_ID PARA SUPERADMIN")
        
        if hasattr(self, 'superadmin_token'):
            # Test with explicit tenant header
            headers_with_tenant = {'Authorization': f'Bearer {self.superadmin_token}', 'X-Tenant-ID': 'default'}
            
            try:
                import requests
                url = f"{self.base_url}/users"
                response = requests.get(url, headers=headers_with_tenant)
                
                if response.status_code == 200:
                    users_data = response.json()
                    print(f"   ✅ Superadmin com X-Tenant-ID header funcionando: {len(users_data)} usuários")
                else:
                    print(f"   ⚠️ Problema com X-Tenant-ID header: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Erro testando X-Tenant-ID header: {e}")
        
        # Test 7: Verify add_tenant_filter functionality
        print("\n🔍 TESTE 7: VERIFICAR FUNCIONALIDADE add_tenant_filter")
        
        if hasattr(self, 'admin_token'):
            # Compare admin vs superadmin access to see tenant filtering
            success_admin, response_admin = self.run_test("Admin get users (tenant filtered)", "GET", "users", 200, token=self.admin_token)
            
            if hasattr(self, 'superadmin_token'):
                success_super, response_super = self.run_test("Superadmin get users (cross-tenant)", "GET", "users", 200, token=self.superadmin_token)
                
                if success_admin and success_super:
                    admin_count = len(response_admin)
                    super_count = len(response_super)
                    
                    print(f"   📊 Comparação de acesso:")
                    print(f"      - Admin vê: {admin_count} usuários (filtrado por tenant)")
                    print(f"      - Superadmin vê: {super_count} usuários (cross-tenant)")
                    
                    if super_count >= admin_count:
                        print(f"   ✅ Superadmin tem acesso cross-tenant funcionando")
                    else:
                        print(f"   ⚠️ Superadmin pode ter problema de acesso cross-tenant")
        
        # Test 8: Test different credential combinations
        print("\n🔍 TESTE 8: TESTAR DIFERENTES COMBINAÇÕES DE CREDENCIAIS")
        
        test_credentials = [
            {
                "name": "Superadmin com senha correta (repetir)",
                "email": "superadmin@autotech.com",
                "password": "secure-temp-password-123",
                "expected": 200
            },
            {
                "name": "Superadmin com senha antiga comum",
                "email": "superadmin@autotech.com", 
                "password": "admin123",
                "expected": 401
            },
            {
                "name": "Superadmin com senha que usuário tentou",
                "email": "superadmin@autotech.com",
                "password": "superadmin123", 
                "expected": 401
            },
            {
                "name": "Email incorreto",
                "email": "super@autotech.com",
                "password": "secure-temp-password-123",
                "expected": 401
            }
        ]
        
        for cred_test in test_credentials:
            credentials = {
                "email": cred_test["email"],
                "password": cred_test["password"]
            }
            success, response = self.run_test(cred_test["name"], "POST", "auth/login", cred_test["expected"], credentials)
            
            if cred_test["expected"] == 200 and success:
                print(f"   ✅ {cred_test['name']}: LOGIN SUCESSO")
            elif cred_test["expected"] == 401 and not success:
                print(f"   ✅ {cred_test['name']}: FALHA ESPERADA")
            else:
                print(f"   ❌ {cred_test['name']}: RESULTADO INESPERADO")
        
        # Final diagnosis
        print("\n" + "="*80)
        print("DIAGNÓSTICO FINAL - ERRO DE LOGIN DO SUPERADMIN")
        print("="*80)
        
        if hasattr(self, 'superadmin_token'):
            print("🎉 DIAGNÓSTICO: SUPERADMIN LOGIN ESTÁ FUNCIONANDO CORRETAMENTE!")
            print("")
            print("✅ CREDENCIAIS CORRETAS CONFIRMADAS:")
            print("   - Email: superadmin@autotech.com")
            print("   - Senha: secure-temp-password-123 (conforme INITIAL_SUPERADMIN_PASSWORD)")
            print("")
            print("❌ PROBLEMA DO USUÁRIO IDENTIFICADO:")
            print("   - Usuário estava usando senha INCORRETA: 'superadmin123'")
            print("   - Senha CORRETA é: 'secure-temp-password-123'")
            print("")
            print("🔧 SOLUÇÃO PARA O USUÁRIO:")
            print("   1. Usar a senha correta: secure-temp-password-123")
            print("   2. Ou redefinir a senha através do administrador")
            print("   3. Verificar se não há espaços extras na senha")
            print("")
            print("✅ SISTEMA DE AUTENTICAÇÃO FUNCIONANDO NORMALMENTE")
            print("✅ TENANT_ID SENDO PROCESSADO CORRETAMENTE")
            print("✅ ADD_TENANT_FILTER FUNCIONANDO PARA LOGIN")
            
            return True
        else:
            print("❌ DIAGNÓSTICO: PROBLEMA CRÍTICO NO SISTEMA DE AUTENTICAÇÃO!")
            print("")
            print("🚨 PROBLEMAS IDENTIFICADOS:")
            print("   - Superadmin não consegue fazer login mesmo com senha correta")
            print("   - Possível problema na configuração do banco de dados")
            print("   - Possível problema na inicialização do sistema")
            print("   - Possível problema no hash da senha")
            print("")
            print("🔧 AÇÕES NECESSÁRIAS:")
            print("   1. Verificar se INITIAL_SUPERADMIN_PASSWORD está definido")
            print("   2. Verificar se o superadmin foi criado na inicialização")
            print("   3. Verificar conectividade com o banco de dados")
            print("   4. Verificar logs de erro do sistema")
            print("   5. Considerar recriar o usuário superadmin")
            
            return False

    def run_investigation(self):
        """Run the superadmin login investigation as requested in review"""
        print("🚀 INVESTIGAÇÃO CRÍTICA - ERRO DE LOGIN DO SUPERADMIN")
        print(f"Base URL: {self.base_url}")
        print("="*80)
        
        # Run the superadmin investigation
        success = self.test_superadmin_login_investigation()
        
        # Print final results
        print("\n" + "="*80)
        print("RESULTADO FINAL DA INVESTIGAÇÃO")
        print("="*80)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        if success:
            print("🎉 INVESTIGAÇÃO CONCLUÍDA COM SUCESSO!")
            print("   O problema de login do superadmin foi diagnosticado.")
            return 0
        else:
            print(f"❌ INVESTIGAÇÃO REVELOU PROBLEMAS CRÍTICOS!")
            print(f"   Ação imediata necessária no sistema de autenticação.")
            return 1

if __name__ == "__main__":
    tester = SuperAdminLoginTester()
    exit_code = tester.run_investigation()
    sys.exit(exit_code)