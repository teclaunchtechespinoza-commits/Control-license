import requests
import json

def test_stats_endpoint():
    """Test the stats endpoint specifically"""
    base_url = "https://licensehub-23.preview.emergentagent.com/api"
    session = requests.Session()
    
    print("🔍 Testing Stats Endpoint Issue")
    print("="*50)
    
    # Login as admin
    admin_credentials = {"email": "admin@demo.com", "password": "admin123"}
    
    login_response = session.post(
        f"{base_url}/auth/login",
        json=admin_credentials,
        headers={'Content-Type': 'application/json', 'X-Tenant-ID': 'default'}
    )
    
    print(f"Login Status: {login_response.status_code}")
    if login_response.status_code == 200:
        login_data = login_response.json()
        print(f"Login Success: {login_data.get('success')}")
        print(f"User Role: {login_data.get('user', {}).get('role')}")
        print(f"User Tenant: {login_data.get('user', {}).get('tenant_id')}")
        
        # Test stats endpoint
        stats_response = session.get(
            f"{base_url}/stats",
            headers={'Content-Type': 'application/json', 'X-Tenant-ID': 'default'}
        )
        
        print(f"\nStats Status: {stats_response.status_code}")
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print(f"Stats Data: {stats_data}")
        else:
            print(f"Stats Error: {stats_response.text}")
            
        # Test licenses endpoint
        licenses_response = session.get(
            f"{base_url}/licenses",
            headers={'Content-Type': 'application/json', 'X-Tenant-ID': 'default'}
        )
        
        print(f"\nLicenses Status: {licenses_response.status_code}")
        if licenses_response.status_code == 200:
            licenses_data = licenses_response.json()
            print(f"Licenses Count: {len(licenses_data) if isinstance(licenses_data, list) else 'Not a list'}")
        else:
            print(f"Licenses Error: {licenses_response.text}")
    else:
        print(f"Login Failed: {login_response.text}")

if __name__ == "__main__":
    test_stats_endpoint()