import requests
import sys
import json
from datetime import datetime, timedelta

class PJClientFocusedTester:
    def __init__(self, base_url="https://licensemanager-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_clients = []

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
                    if isinstance(response_data, dict) and len(str(response_data)) < 1000:
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

    def authenticate(self):
        """Get admin token"""
        admin_credentials = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        success, response = self.run_test("Admin login", "POST", "auth/login", 200, admin_credentials)
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
            return True
        return False

    def test_cnpj_validation(self):
        """Test CNPJ validation with various formats"""
        print("\n" + "="*60)
        print("TESTING CNPJ VALIDATION")
        print("="*60)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return

        # Test valid CNPJ formats
        valid_cnpj_tests = [
            {
                "name": "Valid CNPJ - formatted",
                "cnpj": "11.222.333/0001-81",
                "should_pass": True
            },
            {
                "name": "Valid CNPJ - unformatted", 
                "cnpj": "11222333000181",
                "should_pass": True
            },
            {
                "name": "Valid CNPJ - mixed format",
                "cnpj": "11222333/0001-81",
                "should_pass": True
            }
        ]

        for i, test_case in enumerate(valid_cnpj_tests):
            pj_data = {
                "client_type": "pj",
                "cnpj": test_case["cnpj"],
                "razao_social": f"Empresa Teste {i+1} LTDA",
                "nome_fantasia": f"Teste Corp {i+1}",
                "email_principal": f"contato{i+1}@empresateste.com",
                "telefone": "+55 11 3333-4444",
                "contact_preference": "email",
                "origin_channel": "website"
            }
            
            expected_status = 200 if test_case["should_pass"] else 400
            success, response = self.run_test(
                test_case["name"], 
                "POST", 
                "clientes-pj", 
                expected_status, 
                pj_data, 
                self.admin_token
            )
            
            if success and expected_status == 200 and 'id' in response:
                self.created_clients.append(response['id'])
                print(f"   Created client ID: {response['id']}")
                print(f"   CNPJ stored as: {response.get('cnpj', 'N/A')}")
                print(f"   CNPJ normalized: {response.get('cnpj_normalizado', 'N/A')}")

        # Test invalid CNPJ formats
        invalid_cnpj_tests = [
            {
                "name": "Invalid CNPJ - too short",
                "cnpj": "1122233300018",
                "should_pass": False
            },
            {
                "name": "Invalid CNPJ - too long", 
                "cnpj": "112223330001811",
                "should_pass": False
            },
            {
                "name": "Invalid CNPJ - empty",
                "cnpj": "",
                "should_pass": False
            }
        ]

        for i, test_case in enumerate(invalid_cnpj_tests):
            pj_data = {
                "client_type": "pj",
                "cnpj": test_case["cnpj"],
                "razao_social": f"Empresa Invalida {i+1} LTDA",
                "nome_fantasia": f"Invalida Corp {i+1}",
                "email_principal": f"invalida{i+1}@empresateste.com",
                "telefone": "+55 11 3333-4444",
                "contact_preference": "email",
                "origin_channel": "website"
            }
            
            self.run_test(
                test_case["name"], 
                "POST", 
                "clientes-pj", 
                422,  # Validation error
                pj_data, 
                self.admin_token
            )

    def test_required_vs_optional_fields(self):
        """Test required vs optional fields for PJ clients"""
        print("\n" + "="*60)
        print("TESTING REQUIRED VS OPTIONAL FIELDS")
        print("="*60)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return

        # Test minimal required fields only
        minimal_data = {
            "client_type": "pj",
            "cnpj": "99888777000166",
            "razao_social": "Empresa Minima LTDA",
            "email_principal": "minima@empresa.com"
        }
        
        success, response = self.run_test(
            "Create PJ with minimal required fields", 
            "POST", 
            "clientes-pj", 
            200, 
            minimal_data, 
            self.admin_token
        )
        
        if success and 'id' in response:
            self.created_clients.append(response['id'])
            print(f"   Created minimal client ID: {response['id']}")

        # Test with all optional fields
        complete_data = {
            "client_type": "pj",
            "cnpj": "88777666000155",
            "razao_social": "Empresa Completa LTDA",
            "nome_fantasia": "Completa Corp",
            "email_principal": "completa@empresa.com",
            "telefone": "+55 11 3333-4444",
            "celular": "+55 11 99999-7777",
            "whatsapp": "+55 11 99999-7777",
            "contact_preference": "whatsapp",
            "origin_channel": "partner",
            "data_abertura": "2020-01-15",
            "natureza_juridica": "Sociedade Limitada",
            "cnae_principal": "6201-5/00",
            "cnaes_secundarios": ["6202-3/00", "6203-1/00"],
            "regime_tributario": "simples",
            "porte_empresa": "me",
            "inscricao_estadual": "123456789",
            "ie_situacao": "contribuinte",
            "ie_uf": "SP",
            "inscricao_municipal": "987654321",
            "inscricao_municipal_ccm": "CCM123456",
            "endereco_matriz": {
                "cep": "01310-100",
                "logradouro": "Av. Paulista",
                "numero": "1000",
                "complemento": "Sala 100",
                "bairro": "Bela Vista",
                "municipio": "São Paulo",
                "uf": "SP",
                "pais": "Brasil"
            },
            "responsavel_legal_nome": "Maria Silva",
            "responsavel_legal_cpf": "98765432100",
            "responsavel_legal_email": "maria@empresa.com",
            "responsavel_legal_telefone": "+55 11 98888-7777",
            "procurador_nome": "João Santos",
            "procurador_cpf": "12345678900",
            "procurador_email": "joao@procurador.com",
            "procurador_telefone": "+55 11 97777-6666",
            "procuracao_validade": "2025-12-31",
            "procuracao_numero": "PROC123456",
            "certificado_digital": {
                "tipo": "A3",
                "numero_serie": "CERT123456",
                "emissor": "AC Serasa",
                "validade": "2025-06-30"
            },
            "documentos_societarios": {
                "contrato_social_url": "https://docs.empresa.com/contrato.pdf",
                "ultima_alteracao_data": "2024-01-15",
                "observacoes": "Documentos atualizados"
            },
            "municipio_emissor_nfse": "São Paulo",
            "codigo_servico_lc": "14.01",
            "aliquota_iss": 2.0,
            "serie_nfse": "001",
            "internal_notes": "Cliente completo com todos os campos preenchidos",
            "license_info": {
                "plan_type": "Premium",
                "license_quantity": 5,
                "equipment_brand": "Dell",
                "equipment_model": "OptiPlex 7090",
                "billing_cycle": "monthly",
                "billing_day": 15,
                "payment_method": "credit_card",
                "nfe_email": "nfe@empresa.com"
            },
            "remote_access": {
                "system_type": "teamviewer",
                "access_id": "123456789",
                "is_host": True
            }
        }
        
        success, response = self.run_test(
            "Create PJ with all optional fields", 
            "POST", 
            "clientes-pj", 
            200, 
            complete_data, 
            self.admin_token
        )
        
        if success and 'id' in response:
            self.created_clients.append(response['id'])
            print(f"   Created complete client ID: {response['id']}")

        # Test missing required fields
        missing_required_tests = [
            {
                "name": "Missing CNPJ",
                "data": {
                    "client_type": "pj",
                    "razao_social": "Empresa Sem CNPJ LTDA",
                    "email_principal": "sem.cnpj@empresa.com"
                }
            },
            {
                "name": "Missing razao_social",
                "data": {
                    "client_type": "pj",
                    "cnpj": "77666555000144",
                    "email_principal": "sem.razao@empresa.com"
                }
            },
            {
                "name": "Missing email_principal",
                "data": {
                    "client_type": "pj",
                    "cnpj": "66555444000133",
                    "razao_social": "Empresa Sem Email LTDA"
                }
            }
        ]

        for test_case in missing_required_tests:
            self.run_test(
                test_case["name"], 
                "POST", 
                "clientes-pj", 
                422,  # Validation error
                test_case["data"], 
                self.admin_token
            )

    def test_crud_operations(self):
        """Test full CRUD operations for PJ clients"""
        print("\n" + "="*60)
        print("TESTING CRUD OPERATIONS")
        print("="*60)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return

        # CREATE - Already tested above, but let's create one more for CRUD testing
        crud_data = {
            "client_type": "pj",
            "cnpj": "55444333000122",
            "razao_social": "Empresa CRUD LTDA",
            "nome_fantasia": "CRUD Corp",
            "email_principal": "crud@empresa.com",
            "telefone": "+55 11 3333-4444",
            "contact_preference": "email",
            "origin_channel": "website",
            "regime_tributario": "simples",
            "porte_empresa": "me",
            "responsavel_legal_nome": "Ana Silva",
            "responsavel_legal_cpf": "11122233344",
            "internal_notes": "Cliente para teste CRUD"
        }
        
        success, response = self.run_test(
            "CREATE - PJ client for CRUD testing", 
            "POST", 
            "clientes-pj", 
            200, 
            crud_data, 
            self.admin_token
        )
        
        if not success or 'id' not in response:
            print("❌ Failed to create client for CRUD testing")
            return
            
        client_id = response['id']
        self.created_clients.append(client_id)
        print(f"   Created CRUD client ID: {client_id}")

        # READ - Get specific client
        success, response = self.run_test(
            "READ - Get specific PJ client", 
            "GET", 
            f"clientes-pj/{client_id}", 
            200, 
            token=self.admin_token
        )
        
        if success:
            print(f"   Retrieved client: {response.get('razao_social', 'N/A')}")

        # UPDATE - Update client information
        update_data = {
            "nome_fantasia": "CRUD Corporation Updated",
            "porte_empresa": "epp",
            "regime_tributario": "lucro_presumido",
            "responsavel_legal_nome": "Ana Silva Santos",
            "internal_notes": "Cliente CRUD atualizado com sucesso"
        }
        
        success, response = self.run_test(
            "UPDATE - Update PJ client", 
            "PUT", 
            f"clientes-pj/{client_id}", 
            200, 
            update_data, 
            self.admin_token
        )
        
        if success:
            print(f"   Updated client: {response.get('nome_fantasia', 'N/A')}")
            print(f"   New porte_empresa: {response.get('porte_empresa', 'N/A')}")

        # READ again to verify update
        success, response = self.run_test(
            "READ - Verify update", 
            "GET", 
            f"clientes-pj/{client_id}", 
            200, 
            token=self.admin_token
        )
        
        if success:
            print(f"   Verified update - nome_fantasia: {response.get('nome_fantasia', 'N/A')}")

        # DELETE (soft delete - inactivate)
        success, response = self.run_test(
            "DELETE - Inactivate PJ client", 
            "DELETE", 
            f"clientes-pj/{client_id}", 
            200, 
            token=self.admin_token
        )
        
        if success:
            print(f"   Client inactivated: {response.get('message', 'N/A')}")

        # Try to get inactivated client (should still exist but inactive)
        success, response = self.run_test(
            "READ - Get inactivated client", 
            "GET", 
            f"clientes-pj/{client_id}", 
            200, 
            token=self.admin_token
        )
        
        if success:
            print(f"   Inactivated client status: {response.get('status', 'N/A')}")

    def test_duplicate_prevention(self):
        """Test duplicate CNPJ prevention"""
        print("\n" + "="*60)
        print("TESTING DUPLICATE CNPJ PREVENTION")
        print("="*60)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return

        # Create first client
        original_data = {
            "client_type": "pj",
            "cnpj": "44333222000111",
            "razao_social": "Empresa Original LTDA",
            "email_principal": "original@empresa.com"
        }
        
        success, response = self.run_test(
            "Create original PJ client", 
            "POST", 
            "clientes-pj", 
            200, 
            original_data, 
            self.admin_token
        )
        
        if success and 'id' in response:
            self.created_clients.append(response['id'])
            print(f"   Created original client ID: {response['id']}")

            # Try to create duplicate with same CNPJ
            duplicate_data = {
                "client_type": "pj",
                "cnpj": "44333222000111",  # Same CNPJ
                "razao_social": "Empresa Duplicada LTDA",
                "email_principal": "duplicada@empresa.com"
            }
            
            self.run_test(
                "Try to create duplicate CNPJ (should fail)", 
                "POST", 
                "clientes-pj", 
                400, 
                duplicate_data, 
                self.admin_token
            )

            # Try with formatted CNPJ (should also fail)
            duplicate_formatted_data = {
                "client_type": "pj",
                "cnpj": "44.333.222/0001-11",  # Same CNPJ but formatted
                "razao_social": "Empresa Duplicada Formatada LTDA",
                "email_principal": "duplicada.formatada@empresa.com"
            }
            
            self.run_test(
                "Try to create duplicate formatted CNPJ (should fail)", 
                "POST", 
                "clientes-pj", 
                400, 
                duplicate_formatted_data, 
                self.admin_token
            )

    def cleanup(self):
        """Clean up created test clients"""
        print("\n" + "="*60)
        print("CLEANUP - INACTIVATING TEST CLIENTS")
        print("="*60)
        
        if not self.admin_token:
            return

        for client_id in self.created_clients:
            self.run_test(
                f"Inactivate test client {client_id[:8]}...", 
                "DELETE", 
                f"clientes-pj/{client_id}", 
                200, 
                token=self.admin_token
            )

    def run_all_tests(self):
        """Run all focused PJ client tests"""
        print("🚀 Starting Focused PJ Client API Tests")
        print(f"Base URL: {self.base_url}")
        
        if not self.authenticate():
            print("❌ Failed to authenticate, stopping tests")
            return 1
            
        self.test_cnpj_validation()
        self.test_required_vs_optional_fields()
        self.test_crud_operations()
        self.test_duplicate_prevention()
        self.cleanup()
        
        # Print final results
        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All focused PJ client tests passed!")
            return 0
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = PJClientFocusedTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())