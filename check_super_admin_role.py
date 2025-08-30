import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://saasecure.preview.emergentagent.com')
base_url = f"{backend_url}/api"

# Login as admin to get access
admin_credentials = {
    "email": "admin@demo.com",
    "password": "admin123"
}

response = requests.post(f"{base_url}/auth/login", json=admin_credentials)
if response.status_code == 200:
    admin_data = response.json()
    admin_token = admin_data['access_token']
    
    # Get all users
    headers = {'Authorization': f'Bearer {admin_token}'}
    users_response = requests.get(f"{base_url}/users", headers=headers)
    
    if users_response.status_code == 200:
        users = users_response.json()
        
        # Look for any user with super_admin role
        super_admin_users = []
        for user in users:
            if user.get('role') == 'super_admin':
                super_admin_users.append(user)
        
        print(f"Found {len(super_admin_users)} users with super_admin role:")
        for user in super_admin_users:
            print(f"  - ID: {user.get('id', 'N/A')}")
            print(f"  - Email: {user.get('email', 'N/A')}")
            print(f"  - Name: {user.get('name', 'N/A')}")
            print(f"  - Tenant ID: {user.get('tenant_id', 'N/A')}")
            print(f"  - Is Active: {user.get('is_active', 'N/A')}")
            print("  ---")
        
        if len(super_admin_users) == 0:
            print("No super_admin users found in database!")
            print("This explains why the superadmin creation is being skipped.")
        else:
            print("Super admin users exist, but none with email superadmin@autotech.com")
    else:
        print(f"Failed to get users: {users_response.status_code}")
else:
    print(f"Admin login failed: {response.status_code}")