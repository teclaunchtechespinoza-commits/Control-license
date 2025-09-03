import requests
import json

# Get admin token
admin_credentials = {
    "email": "admin@demo.com",
    "password": "admin123"
}

response = requests.post("https://multitenantlms.preview.emergentagent.com/api/auth/login", json=admin_credentials)
token = response.json()['access_token']

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}

# Test complex PJ client creation step by step
print("Testing complex PJ client creation...")

# Start with minimal and add fields gradually
test_data = {
    "client_type": "pj",
    "cnpj": "88777666000155",
    "razao_social": "Empresa Debug LTDA",
    "email_principal": "debug@empresa.com"
}

print("\n1. Testing minimal data...")
response = requests.post("https://multitenantlms.preview.emergentagent.com/api/clientes-pj", json=test_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    client_id = response.json()['id']
    print(f"Success: Created client {client_id}")
    
    # Clean up
    requests.delete(f"https://multitenantlms.preview.emergentagent.com/api/clientes-pj/{client_id}", headers=headers)

# Test with address
print("\n2. Testing with address...")
test_data["endereco_matriz"] = {
    "cep": "01310-100",
    "logradouro": "Av. Paulista",
    "numero": "1000",
    "bairro": "Bela Vista",
    "municipio": "São Paulo",
    "uf": "SP"
}
test_data["cnpj"] = "88777666000156"  # Different CNPJ

response = requests.post("https://multitenantlms.preview.emergentagent.com/api/clientes-pj", json=test_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    client_id = response.json()['id']
    print(f"Success: Created client with address {client_id}")
    requests.delete(f"https://multitenantlms.preview.emergentagent.com/api/clientes-pj/{client_id}", headers=headers)

# Test with certificate
print("\n3. Testing with certificate...")
test_data["certificado_digital"] = {
    "tipo": "A3",
    "numero_serie": "CERT123456",
    "emissor": "AC Serasa",
    "validade": "2025-06-30"
}
test_data["cnpj"] = "88777666000157"  # Different CNPJ

response = requests.post("https://multitenantlms.preview.emergentagent.com/api/clientes-pj", json=test_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    client_id = response.json()['id']
    print(f"Success: Created client with certificate {client_id}")
    requests.delete(f"https://multitenantlms.preview.emergentagent.com/api/clientes-pj/{client_id}", headers=headers)

# Test with license info
print("\n4. Testing with license info...")
test_data["license_info"] = {
    "plan_type": "Premium",
    "license_quantity": 5,
    "billing_cycle": "monthly",
    "payment_method": "credit_card"
}
test_data["cnpj"] = "88777666000158"  # Different CNPJ

response = requests.post("https://multitenantlms.preview.emergentagent.com/api/clientes-pj", json=test_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    client_id = response.json()['id']
    print(f"Success: Created client with license info {client_id}")
    requests.delete(f"https://multitenantlms.preview.emergentagent.com/api/clientes-pj/{client_id}", headers=headers)

print("\nDebug test completed.")