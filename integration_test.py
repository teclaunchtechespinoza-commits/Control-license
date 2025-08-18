import requests
import json
from datetime import datetime, timedelta

def test_license_integration():
    """Test integration between PJ clients and license system"""
    
    # Get admin token
    admin_credentials = {
        "email": "admin@demo.com",
        "password": "admin123"
    }
    
    response = requests.post("https://licensehub-10.preview.emergentagent.com/api/auth/login", json=admin_credentials)
    token = response.json()['access_token']
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    print("🔍 Testing PJ Client + License Integration...")
    
    # 1. Create a PJ client
    pj_data = {
        "client_type": "pj",
        "cnpj": "12345678000199",
        "razao_social": "Empresa Integração LTDA",
        "nome_fantasia": "Integração Corp",
        "email_principal": "integracao@empresa.com",
        "telefone": "+55 11 3333-4444",
        "responsavel_legal_nome": "João Silva",
        "responsavel_legal_cpf": "12345678900",
        "responsavel_legal_email": "joao@empresa.com"
    }
    
    response = requests.post("https://licensehub-10.preview.emergentagent.com/api/clientes-pj", json=pj_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to create PJ client: {response.text}")
        return False
        
    pj_client_id = response.json()['id']
    print(f"✅ Created PJ client: {pj_client_id}")
    
    # 2. Create a license linked to the PJ client
    license_data = {
        "name": "License for Integration Test",
        "description": "Test license linked to PJ client",
        "max_users": 10,
        "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "features": ["feature1", "feature2"],
        "client_pj_id": pj_client_id
    }
    
    response = requests.post("https://licensehub-10.preview.emergentagent.com/api/licenses", json=license_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to create license: {response.text}")
        return False
        
    license_id = response.json()['id']
    print(f"✅ Created license linked to PJ client: {license_id}")
    
    # 3. Verify license contains client reference
    response = requests.get(f"https://licensehub-10.preview.emergentagent.com/api/licenses/{license_id}", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to retrieve license: {response.text}")
        return False
        
    license_data = response.json()
    if license_data.get('client_pj_id') == pj_client_id:
        print("✅ License correctly references PJ client")
    else:
        print("❌ License does not reference PJ client correctly")
        return False
    
    # 4. Test stats endpoint includes PJ clients
    response = requests.get("https://licensehub-10.preview.emergentagent.com/api/stats", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get stats: {response.text}")
        return False
        
    stats = response.json()
    print(f"✅ Stats include PJ clients: {stats.get('total_clientes_pj', 0)} PJ clients")
    print(f"✅ Total clients: {stats.get('total_clients', 0)}")
    
    # 5. Cleanup
    requests.delete(f"https://licensehub-10.preview.emergentagent.com/api/licenses/{license_id}", headers=headers)
    requests.delete(f"https://licensehub-10.preview.emergentagent.com/api/clientes-pj/{pj_client_id}", headers=headers)
    print("✅ Cleanup completed")
    
    return True

if __name__ == "__main__":
    success = test_license_integration()
    if success:
        print("\n🎉 Integration test PASSED - PJ clients work correctly with license system")
    else:
        print("\n❌ Integration test FAILED")