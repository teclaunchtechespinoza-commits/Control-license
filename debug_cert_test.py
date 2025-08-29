import requests
import json

# Get admin token
admin_credentials = {
    "email": "admin@demo.com",
    "password": "admin123"
}

response = requests.post("https://multitenant-saas-1.preview.emergentagent.com/api/auth/login", json=admin_credentials)
token = response.json()['access_token']

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}

print("Testing certificate field step by step...")

# Test certificate without date
print("\n1. Testing certificate without date...")
test_data = {
    "client_type": "pj",
    "cnpj": "88777666000162",
    "razao_social": "Empresa Debug Cert No Date LTDA",
    "email_principal": "debug.cert.nodate@empresa.com",
    "certificado_digital": {
        "tipo": "A3",
        "numero_serie": "CERT123456",
        "emissor": "AC Serasa"
    }
}

response = requests.post("https://multitenant-saas-1.preview.emergentagent.com/api/clientes-pj", json=test_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    client_id = response.json()['id']
    print(f"Success: Created client without cert date {client_id}")
    requests.delete(f"https://multitenant-saas-1.preview.emergentagent.com/api/clientes-pj/{client_id}", headers=headers)

# Test certificate with date as null
print("\n2. Testing certificate with null date...")
test_data = {
    "client_type": "pj",
    "cnpj": "88777666000163",
    "razao_social": "Empresa Debug Cert Null Date LTDA",
    "email_principal": "debug.cert.null@empresa.com",
    "certificado_digital": {
        "tipo": "A3",
        "numero_serie": "CERT123456",
        "emissor": "AC Serasa",
        "validade": None
    }
}

response = requests.post("https://multitenant-saas-1.preview.emergentagent.com/api/clientes-pj", json=test_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    client_id = response.json()['id']
    print(f"Success: Created client with null cert date {client_id}")
    requests.delete(f"https://multitenant-saas-1.preview.emergentagent.com/api/clientes-pj/{client_id}", headers=headers)

print("\nCertificate debug test completed.")