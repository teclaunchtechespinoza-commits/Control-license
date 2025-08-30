#!/usr/bin/env python3

import requests
import json
import uuid
from datetime import datetime

class ProductCreationTester:
    def __init__(self, base_url="https://saasecure.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.test_results = []

    def authenticate(self):
        """Authenticate as admin user"""
        print("🔐 Authenticating as admin...")
        
        admin_credentials = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        
        response = requests.post(f"{self.base_url}/auth/login", json=admin_credentials)
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data['access_token']
            print(f"✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False

    def test_product_creation(self):
        """Test product creation with unique name"""
        print("\n🧪 Testing Product Creation...")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False

        # Create unique product name to avoid duplicates
        unique_id = str(uuid.uuid4())[:8]
        product_data = {
            "name": f"Test Product {unique_id}",
            "version": "1.0",
            "description": "Testing JSON serialization fix",
            "category_id": None,
            "price": 99.99,
            "currency": "BRL",
            "features": ["feature1", "feature2"],
            "requirements": "Test requirements"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        print(f"📤 Creating product: {product_data['name']}")
        print(f"   Payload: {json.dumps(product_data, indent=2)}")
        
        try:
            response = requests.post(f"{self.base_url}/products", json=product_data, headers=headers)
            
            print(f"📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                product_id = response_data.get('id')
                print(f"✅ Product created successfully!")
                print(f"   Product ID: {product_id}")
                print(f"   Product Name: {response_data.get('name')}")
                print(f"   Created At: {response_data.get('created_at')}")
                
                self.test_results.append({
                    "test": "product_creation",
                    "status": "success",
                    "product_id": product_id,
                    "product_name": response_data.get('name')
                })
                
                return product_id
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"❌ Product creation failed!")
                print(f"   Error: {error_data}")
                
                self.test_results.append({
                    "test": "product_creation",
                    "status": "failed",
                    "error": error_data
                })
                
                return None
                
        except Exception as e:
            print(f"❌ Exception during product creation: {str(e)}")
            self.test_results.append({
                "test": "product_creation",
                "status": "exception",
                "error": str(e)
            })
            return None

    def test_product_persistence(self, product_id):
        """Test if created product appears in product list"""
        print("\n🔍 Testing Product Persistence...")
        
        if not product_id:
            print("❌ No product ID to test")
            return False
            
        headers = {
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        try:
            response = requests.get(f"{self.base_url}/products", headers=headers)
            
            if response.status_code == 200:
                products = response.json()
                print(f"📋 Retrieved {len(products)} products from database")
                
                # Look for our created product
                found_product = None
                for product in products:
                    if product.get('id') == product_id:
                        found_product = product
                        break
                
                if found_product:
                    print(f"✅ Product found in database!")
                    print(f"   ID: {found_product.get('id')}")
                    print(f"   Name: {found_product.get('name')}")
                    print(f"   Version: {found_product.get('version')}")
                    
                    self.test_results.append({
                        "test": "product_persistence",
                        "status": "success",
                        "found": True
                    })
                    return True
                else:
                    print(f"❌ Product with ID {product_id} not found in database!")
                    print("   This indicates a persistence issue")
                    
                    self.test_results.append({
                        "test": "product_persistence", 
                        "status": "failed",
                        "found": False,
                        "total_products": len(products)
                    })
                    return False
            else:
                print(f"❌ Failed to retrieve products: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during persistence test: {str(e)}")
            return False

    def check_maintenance_logs(self):
        """Check maintenance logs for JSON serialization errors"""
        print("\n📋 Checking Maintenance Logs...")
        
        headers = {
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        try:
            response = requests.get(f"{self.base_url}/maintenance/logs?lines=50", headers=headers)
            
            if response.status_code == 200:
                log_data = response.json()
                logs = log_data.get('logs', [])
                
                print(f"📄 Retrieved {len(logs)} log entries")
                
                # Look for product-related logs
                product_logs = []
                error_logs = []
                serialization_errors = []
                
                for log in logs:
                    log_lower = log.lower()
                    if 'product' in log_lower or 'create_product' in log_lower:
                        product_logs.append(log)
                    
                    if 'error' in log_lower or 'exception' in log_lower:
                        error_logs.append(log)
                    
                    if 'json serializable' in log_lower or 'datetime' in log_lower:
                        serialization_errors.append(log)
                
                print(f"🔍 Analysis:")
                print(f"   Product-related logs: {len(product_logs)}")
                print(f"   Error logs: {len(error_logs)}")
                print(f"   Serialization errors: {len(serialization_errors)}")
                
                if serialization_errors:
                    print(f"\n⚠️  JSON SERIALIZATION ERRORS FOUND:")
                    for i, error in enumerate(serialization_errors[-5:], 1):
                        print(f"   {i}. {error}")
                    
                    self.test_results.append({
                        "test": "maintenance_logs",
                        "status": "serialization_errors_found",
                        "error_count": len(serialization_errors)
                    })
                    return False
                else:
                    print(f"✅ No JSON serialization errors found!")
                    
                    self.test_results.append({
                        "test": "maintenance_logs",
                        "status": "no_serialization_errors"
                    })
                
                if product_logs:
                    print(f"\n📋 Recent Product Logs:")
                    for i, log in enumerate(product_logs[-10:], 1):
                        print(f"   {i}. {log}")
                
                if error_logs and not serialization_errors:
                    print(f"\n⚠️  Other Error Logs Found:")
                    for i, error in enumerate(error_logs[-5:], 1):
                        print(f"   {i}. {error}")
                
                return len(serialization_errors) == 0
                
            else:
                print(f"❌ Failed to retrieve maintenance logs: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during log check: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run comprehensive product creation test"""
        print("🚀 CRITICAL PRODUCT CREATION TEST")
        print("=" * 60)
        print("🎯 OBJECTIVE: Verify JSON serialization fix in maintenance_logger.py")
        print("   Testing product creation end-to-end with logging analysis")
        print()
        
        # Step 1: Authenticate
        if not self.authenticate():
            return False
        
        # Step 2: Test product creation
        product_id = self.test_product_creation()
        
        # Step 3: Test product persistence
        persistence_ok = self.test_product_persistence(product_id)
        
        # Step 4: Check maintenance logs
        logs_ok = self.check_maintenance_logs()
        
        # Step 5: Summary
        print("\n" + "=" * 60)
        print("🏁 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        all_tests_passed = True
        
        for result in self.test_results:
            test_name = result['test'].replace('_', ' ').title()
            status = result['status']
            
            if status == 'success' or status == 'no_serialization_errors':
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                all_tests_passed = False
                
                if 'error' in result:
                    print(f"   Error: {result['error']}")
        
        print()
        if all_tests_passed:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Product creation successful (HTTP 200/201)")
            print("✅ No JSON serialization errors in logs")
            print("✅ Products persist in database")
            print("✅ Products appear in GET /api/products response")
            print("✅ Maintenance logging works without breaking product creation")
            print()
            print("🔧 CONCLUSION: The JSON serialization fix in maintenance_logger.py")
            print("   has successfully resolved the blocking issue!")
        else:
            print("❌ SOME TESTS FAILED!")
            print("🔧 CONCLUSION: The JSON serialization issue may still exist")
            print("   or there are other blocking issues preventing product creation.")
        
        return all_tests_passed

if __name__ == "__main__":
    tester = ProductCreationTester()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)