#!/usr/bin/env python3
"""
RBAC Debug Script - Check and fix RBAC initialization
"""

import requests
import sys
import json

class RBACDebugger:
    def __init__(self, base_url="https://saasecure.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None

    def authenticate_admin(self):
        """Authenticate as admin user"""
        admin_credentials = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        
        response = requests.post(f"{self.base_url}/auth/login", json=admin_credentials)
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data['access_token']
            print(f"✅ Admin authenticated successfully")
            return True
        else:
            print(f"❌ Admin authentication failed: {response.status_code}")
            return False

    def check_admin_permissions(self):
        """Check admin user's current permissions"""
        if not self.admin_token:
            return False
            
        # Get current user info
        response = requests.get(f"{self.base_url}/auth/me", 
                              headers={'Authorization': f'Bearer {self.admin_token}'})
        
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data['id']
            print(f"✅ Current user: {user_data['name']} ({user_data['email']})")
            
            # Get user permissions
            response = requests.get(f"{self.base_url}/rbac/users/{user_id}/permissions",
                                  headers={'Authorization': f'Bearer {self.admin_token}'})
            
            if response.status_code == 200:
                perms_data = response.json()
                print(f"📋 User roles: {[role['name'] for role in perms_data.get('roles', [])]}")
                print(f"📋 User permissions: {len(perms_data.get('permissions', []))} permissions")
                
                # Check if user has rbac.manage permission
                has_rbac_manage = any(perm.get('name') == 'rbac.manage' for perm in perms_data.get('permissions', []))
                has_super_admin = any(perm.get('name') == '*' for perm in perms_data.get('permissions', []))
                
                print(f"🔍 Has rbac.manage permission: {has_rbac_manage}")
                print(f"🔍 Has super admin permission (*): {has_super_admin}")
                
                return has_rbac_manage or has_super_admin
            else:
                print(f"❌ Failed to get user permissions: {response.status_code}")
                return False
        else:
            print(f"❌ Failed to get user info: {response.status_code}")
            return False

    def check_rbac_initialization(self):
        """Check if RBAC system is properly initialized"""
        print("\n🔍 Checking RBAC system initialization...")
        
        # Check roles
        response = requests.get(f"{self.base_url}/rbac/roles",
                              headers={'Authorization': f'Bearer {self.admin_token}'})
        
        if response.status_code == 200:
            roles = response.json()
            print(f"✅ Found {len(roles)} roles")
            for role in roles:
                print(f"   - {role['name']}: {role.get('description', 'No description')} (System: {role.get('is_system', False)})")
        elif response.status_code == 403:
            print("❌ Access denied to roles endpoint - admin user lacks permissions")
            return False
        else:
            print(f"❌ Failed to get roles: {response.status_code}")
            return False
        
        # Check permissions
        response = requests.get(f"{self.base_url}/rbac/permissions",
                              headers={'Authorization': f'Bearer {self.admin_token}'})
        
        if response.status_code == 200:
            permissions = response.json()
            print(f"✅ Found {len(permissions)} permissions")
            
            # Group by resource
            resources = {}
            for perm in permissions:
                resource = perm.get('resource', 'unknown')
                if resource not in resources:
                    resources[resource] = []
                resources[resource].append(perm.get('name'))
            
            for resource, perms in resources.items():
                print(f"   - {resource}: {len(perms)} permissions")
                
        elif response.status_code == 403:
            print("❌ Access denied to permissions endpoint - admin user lacks permissions")
            return False
        else:
            print(f"❌ Failed to get permissions: {response.status_code}")
            return False
        
        return True

    def test_rbac_endpoints_with_old_admin(self):
        """Test RBAC endpoints using old admin role system"""
        print("\n🔍 Testing RBAC endpoints with old admin role...")
        
        # Try to create a test role using old admin permissions
        test_role_data = {
            "name": "Debug Test Role",
            "description": "Test role for debugging RBAC",
            "permissions": []
        }
        
        response = requests.post(f"{self.base_url}/rbac/roles",
                               json=test_role_data,
                               headers={'Authorization': f'Bearer {self.admin_token}'})
        
        if response.status_code == 200:
            print("✅ Successfully created test role with old admin permissions")
            role_data = response.json()
            role_id = role_data['id']
            
            # Clean up - delete the test role
            requests.delete(f"{self.base_url}/rbac/roles/{role_id}",
                          headers={'Authorization': f'Bearer {self.admin_token}'})
            print("✅ Cleaned up test role")
            return True
        elif response.status_code == 403:
            print("❌ Access denied - admin user needs RBAC permissions")
            return False
        else:
            print(f"❌ Failed to create test role: {response.status_code} - {response.text}")
            return False

    def run_debug(self):
        """Run complete RBAC debug check"""
        print("🚀 Starting RBAC System Debug")
        print("="*50)
        
        # Step 1: Authenticate
        if not self.authenticate_admin():
            return False
        
        # Step 2: Check admin permissions
        print("\n🔍 Checking admin user permissions...")
        has_permissions = self.check_admin_permissions()
        
        # Step 3: Check RBAC initialization
        rbac_initialized = self.check_rbac_initialization()
        
        # Step 4: Test with old admin system
        old_admin_works = self.test_rbac_endpoints_with_old_admin()
        
        # Summary
        print("\n" + "="*50)
        print("RBAC DEBUG SUMMARY")
        print("="*50)
        
        print(f"✅ Admin authentication: {'OK' if self.admin_token else 'FAILED'}")
        print(f"{'✅' if has_permissions else '❌'} Admin has RBAC permissions: {'YES' if has_permissions else 'NO'}")
        print(f"{'✅' if rbac_initialized else '❌'} RBAC system initialized: {'YES' if rbac_initialized else 'NO'}")
        print(f"{'✅' if old_admin_works else '❌'} Old admin system works: {'YES' if old_admin_works else 'NO'}")
        
        if not has_permissions and not old_admin_works:
            print("\n🔍 DIAGNOSIS:")
            print("   The admin user lacks proper RBAC permissions.")
            print("   This suggests the RBAC initialization didn't assign Super Admin role to admin@demo.com")
            print("   OR the permission checking system is not working correctly.")
            
            print("\n💡 RECOMMENDATIONS:")
            print("   1. Check if RBAC initialization completed successfully")
            print("   2. Verify admin user has Super Admin role assigned")
            print("   3. Check if permission checking logic is working")
            print("   4. Consider manual role assignment to admin user")
        
        return has_permissions or old_admin_works

def main():
    debugger = RBACDebugger()
    success = debugger.run_debug()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())