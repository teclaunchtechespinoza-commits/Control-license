import requests
import sys
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class SuperAdminChecker:
    def __init__(self):
        # Get backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://licensemanager-6.preview.emergentagent.com')
        self.base_url = f"{backend_url}/api"
        
    def check_superadmin_exists(self):
        """Check if superadmin user exists in database"""
        print("🔍 VERIFICANDO SE SUPERADMIN EXISTE NO BANCO DE DADOS")
        print("="*60)
        
        # First login as admin to get access
        admin_credentials = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        
        try:
            response = requests.post(f"{self.base_url}/auth/login", json=admin_credentials)
            if response.status_code == 200:
                admin_data = response.json()
                admin_token = admin_data['access_token']
                print("✅ Admin login successful")
                
                # Get all users
                headers = {'Authorization': f'Bearer {admin_token}'}
                users_response = requests.get(f"{self.base_url}/users", headers=headers)
                
                if users_response.status_code == 200:
                    users = users_response.json()
                    print(f"✅ Found {len(users)} users in database")
                    
                    # Look for superadmin
                    superadmin_user = None
                    for user in users:
                        if user.get('email') == 'superadmin@autotech.com':
                            superadmin_user = user
                            break
                    
                    if superadmin_user:
                        print("\n🎯 SUPERADMIN ENCONTRADO NO BANCO DE DADOS:")
                        print(f"   - ID: {superadmin_user.get('id', 'N/A')}")
                        print(f"   - Email: {superadmin_user.get('email', 'N/A')}")
                        print(f"   - Name: {superadmin_user.get('name', 'N/A')}")
                        print(f"   - Role: {superadmin_user.get('role', 'N/A')}")
                        print(f"   - Tenant ID: {superadmin_user.get('tenant_id', 'N/A')}")
                        print(f"   - Is Active: {superadmin_user.get('is_active', 'N/A')}")
                        print(f"   - Created At: {superadmin_user.get('created_at', 'N/A')}")
                        print(f"   - Password Hash: {superadmin_user.get('password_hash', 'N/A')[:20]}...")
                        
                        return True, superadmin_user
                    else:
                        print("\n❌ SUPERADMIN NÃO ENCONTRADO NO BANCO DE DADOS!")
                        print("   Isso explica por que o login falha.")
                        print("   O usuário superadmin precisa ser criado.")
                        
                        # Show some other users for reference
                        print("\n📋 Outros usuários encontrados:")
                        for user in users[:5]:
                            print(f"   - {user.get('email', 'N/A')} ({user.get('role', 'N/A')})")
                        
                        return False, None
                else:
                    print(f"❌ Failed to get users: {users_response.status_code}")
                    return False, None
            else:
                print(f"❌ Admin login failed: {response.status_code}")
                return False, None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False, None

if __name__ == "__main__":
    checker = SuperAdminChecker()
    exists, user_data = checker.check_superadmin_exists()
    
    if not exists:
        print("\n🔧 SOLUÇÃO RECOMENDADA:")
        print("   1. O superadmin precisa ser criado no banco de dados")
        print("   2. Verificar se o script de inicialização está funcionando")
        print("   3. Verificar se INITIAL_SUPERADMIN_PASSWORD está definido no .env")
        print("   4. Executar manualmente a criação do superadmin")
        sys.exit(1)
    else:
        print("\n✅ SUPERADMIN EXISTE - PROBLEMA PODE SER NA SENHA")
        print("   Verificar se a senha está sendo hasheada corretamente")
        sys.exit(0)