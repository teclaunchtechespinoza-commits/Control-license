import requests
import json

# Get admin token
admin_credentials = {
    "email": "admin@demo.com",
    "password": "admin123"
}

response = requests.post("https://licensemaster-3.preview.emergentagent.com/api/auth/login", json=admin_credentials)
token = response.json()['access_token']

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}

print("Testing complex PJ client creation with proper date formats...")

# Test with certificate (fixed date format)
print("\n1. Testing with certificate (fixed date)...")
test_data = {
    "client_type": "pj",
    "cnpj": "88777666000159",
    "razao_social": "Empresa Debug Cert LTDA",
    "email_principal": "debug.cert@empresa.com",
    "certificado_digital": {
        "tipo": "A3",
        "numero_serie": "CERT123456",
        "emissor": "AC Serasa",
        "validade": "2025-06-30"  # ISO date format
    }
}

response = requests.post("https://licensemaster-3.preview.emergentagent.com/api/clientes-pj", json=test_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    client_id = response.json()['id']
    print(f"Success: Created client with certificate {client_id}")
    requests.delete(f"https://licensemaster-3.preview.emergentagent.com/api/clientes-pj/{client_id}", headers=headers)

# Test with license info (check enum values)
print("\n2. Testing with license info (check enums)...")
test_data = {
    "client_type": "pj",
    "cnpj": "88777666000160",
    "razao_social": "Empresa Debug License LTDA",
    "email_principal": "debug.license@empresa.com",
    "license_info": {
        "plan_type": "Premium",
        "license_quantity": 5,
        "billing_cycle": "monthly",  # Check if this enum value exists
        "payment_method": "credit_card"  # Check if this enum value exists
    }
}

response = requests.post("https://licensemaster-3.preview.emergentagent.com/api/clientes-pj", json=test_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    client_id = response.json()['id']
    print(f"Success: Created client with license info {client_id}")
    requests.delete(f"https://licensemaster-3.preview.emergentagent.com/api/clientes-pj/{client_id}", headers=headers)

# Test with remote access
print("\n3. Testing with remote access...")
test_data = {
    "client_type": "pj",
    "cnpj": "88777666000161",
    "razao_social": "Empresa Debug Remote LTDA",
    "email_principal": "debug.remote@empresa.com",
    "remote_access": {
        "system_type": "teamviewer",
        "access_id": "123456789",
        "is_host": True
    }
}

response = requests.post("https://licensemaster-3.preview.emergentagent.com/api/clientes-pj", json=test_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    client_id = response.json()['id']
    print(f"Success: Created client with remote access {client_id}")
    requests.delete(f"https://licensemaster-3.preview.emergentagent.com/api/clientes-pj/{client_id}", headers=headers)

print("\nDebug test completed.")