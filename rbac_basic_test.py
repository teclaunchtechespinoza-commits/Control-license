#!/usr/bin/env python3
"""
RBAC Basic Test - Test what we can with current permissions
"""

import requests
import sys
import json

class RBACBasicTester:
    def __init__(self, base_url="https://8b36eb56-9975-4f00-b897-658cc3f40e27.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_passed = 0
        self.tests_run = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
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

    def authenticate_admin(self):
        """Authenticate as admin user"""
        admin_credentials = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        
        success, response = self.run_test("Admin login", "POST", "auth/login", 200, admin_credentials)
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   ✅ Admin token obtained")
            return True
        else:
            print("   ❌ Failed to authenticate as admin")
            return False

    def test_basic_rbac_functionality(self):
        """Test basic RBAC functionality that we can access"""
        print("\n" + "="*50)
        print("TESTING BASIC RBAC FUNCTIONALITY")
        print("="*50)
        
        results = []
        
        # Test 1: Authentication works
        print("\n🔍 Test 1: Authentication with admin@demo.com/admin123")
        auth_success = self.authenticate_admin()
        results.append(auth_success)
        
        if not auth_success:
            return False
        
        # Test 2: Get current user info
        print("\n🔍 Test 2: Get current user info")
        success, user_data = self.run_test("Get current user", "GET", "auth/me", 200, token=self.admin_token)
        if success:
            print(f"   User: {user_data.get('name')} ({user_data.get('email')})")
            print(f"   Role: {user_data.get('role')}")
            print(f"   ID: {user_data.get('id')}")
        results.append(success)
        
        # Test 3: Try to access RBAC roles (might fail due to permissions)
        print("\n🔍 Test 3: Attempt to access RBAC roles")
        success, roles_data = self.run_test("Get RBAC roles", "GET", "rbac/roles", 200, token=self.admin_token)
        if success:
            print(f"   ✅ Successfully retrieved {len(roles_data)} roles")
            for role in roles_data:
                is_system = role.get('is_system', False)
                system_flag = " (SYSTEM)" if is_system else ""
                print(f"      - {role.get('name')}: {role.get('description')}{system_flag}")
        else:
            print("   ❌ Access denied to RBAC roles - permission issue")
        results.append(success)
        
        # Test 4: Try to access RBAC permissions
        print("\n🔍 Test 4: Attempt to access RBAC permissions")
        success, perms_data = self.run_test("Get RBAC permissions", "GET", "rbac/permissions", 200, token=self.admin_token)
        if success:
            print(f"   ✅ Successfully retrieved {len(perms_data)} permissions")
            # Group by resource
            resources = {}
            for perm in perms_data:
                resource = perm.get('resource', 'unknown')
                if resource not in resources:
                    resources[resource] = 0
                resources[resource] += 1
            
            for resource, count in resources.items():
                print(f"      - {resource}: {count} permissions")
        else:
            print("   ❌ Access denied to RBAC permissions - permission issue")
        results.append(success)
        
        # Test 5: Check user permissions endpoint
        if success and user_data and 'id' in user_data:
            print("\n🔍 Test 5: Check user permissions endpoint")
            user_id = user_data['id']
            success, user_perms = self.run_test("Get user permissions", "GET", f"rbac/users/{user_id}/permissions", 200, token=self.admin_token)
            if success:
                roles = user_perms.get('roles', [])
                permissions = user_perms.get('permissions', [])
                print(f"   ✅ User has {len(roles)} roles and {len(permissions)} permissions")
                print(f"   Roles: {[role.get('name') for role in roles]}")
                print(f"   Has permissions: {user_perms.get('has_permissions', False)}")
            else:
                print("   ❌ Failed to get user permissions")
            results.append(success)
        
        # Test 6: Test old admin system endpoints
        print("\n🔍 Test 6: Test old admin system endpoints")
        success, users_data = self.run_test("Get users (old admin)", "GET", "users", 200, token=self.admin_token)
        if success:
            print(f"   ✅ Old admin system works - retrieved {len(users_data)} users")
        else:
            print("   ❌ Old admin system also failing")
        results.append(success)
        
        return results

    def run_comprehensive_test(self):
        """Run comprehensive RBAC test"""
        print("🚀 Starting RBAC Basic Functionality Test")
        print(f"Base URL: {self.base_url}")
        
        results = self.test_basic_rbac_functionality()
        
        # Print final results
        print("\n" + "="*50)
        print("RBAC BASIC TEST RESULTS")
        print("="*50)
        print(f"📊 Individual tests passed: {self.tests_passed}/{self.tests_run}")
        
        if isinstance(results, list):
            passed_major = sum(1 for r in results if r)
            total_major = len(results)
            print(f"📊 Major components passed: {passed_major}/{total_major}")
            
            # Analyze results
            auth_works = results[0] if len(results) > 0 else False
            user_info_works = results[1] if len(results) > 1 else False
            rbac_roles_works = results[2] if len(results) > 2 else False
            rbac_perms_works = results[3] if len(results) > 3 else False
            user_perms_works = results[4] if len(results) > 4 else False
            old_admin_works = results[5] if len(results) > 5 else False
            
            print("\n📋 COMPONENT ANALYSIS:")
            print(f"   ✅ Authentication: {'WORKING' if auth_works else 'FAILED'}")
            print(f"   {'✅' if user_info_works else '❌'} User info: {'WORKING' if user_info_works else 'FAILED'}")
            print(f"   {'✅' if rbac_roles_works else '❌'} RBAC roles: {'WORKING' if rbac_roles_works else 'FAILED'}")
            print(f"   {'✅' if rbac_perms_works else '❌'} RBAC permissions: {'WORKING' if rbac_perms_works else 'FAILED'}")
            print(f"   {'✅' if user_perms_works else '❌'} User permissions: {'WORKING' if user_perms_works else 'FAILED'}")
            print(f"   {'✅' if old_admin_works else '❌'} Old admin system: {'WORKING' if old_admin_works else 'FAILED'}")
            
            # Determine overall status
            if auth_works and (rbac_roles_works and rbac_perms_works):
                print("\n🎉 RBAC SYSTEM STATUS: FULLY FUNCTIONAL")
                print("   ✅ Authentication working with admin@demo.com/admin123")
                print("   ✅ RBAC endpoints accessible")
                print("   ✅ Default roles and permissions available")
                print("   ✅ System ready for frontend integration")
                return True
            elif auth_works and old_admin_works:
                print("\n⚠️  RBAC SYSTEM STATUS: PARTIALLY FUNCTIONAL")
                print("   ✅ Authentication working with admin@demo.com/admin123")
                print("   ❌ RBAC endpoints not accessible (permission issue)")
                print("   ✅ Old admin system still working")
                print("   ⚠️  RBAC initialization may be incomplete")
                return False
            else:
                print("\n❌ RBAC SYSTEM STATUS: NOT FUNCTIONAL")
                print("   ❌ Critical authentication or permission issues")
                return False
        else:
            return results

def main():
    tester = RBACBasicTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())