"""
Test suite for Advanced License Management features
- GET /api/admin/salespeople - List salespeople (tenant admins)
- POST /api/licenses/{id}/renew - Renew license with history
- GET /api/licenses/{id}/history - Get renewal history
- PUT /api/licenses/{id} - Update license with new fields (validity_days, salesperson_id, salesperson_name)

NOTE: This API uses HttpOnly cookies for authentication. Tests use requests.Session to preserve cookies.
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable is required")

# Test credentials from review request
SUPER_ADMIN_EMAIL = "superadmin@autotech.com"
SUPER_ADMIN_PASSWORD = "admin123"
SUPER_ADMIN_TENANT = "system"

ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"

USER_EMAIL = "user@demo.com"
USER_PASSWORD = "user123"

# Known license ID with renewal history
KNOWN_LICENSE_ID = "73120c8f-14c5-4c9c-a7ae-e193d7df8f19"


@pytest.fixture(scope="module")
def authenticated_session():
    """
    Create an authenticated session with HttpOnly cookies.
    The API uses cookies for auth, so we need to use a session that preserves them.
    """
    session = requests.Session()
    session.headers.update({
        "X-Tenant-ID": SUPER_ADMIN_TENANT,
        "Content-Type": "application/json"
    })
    
    # Login to get cookies
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
    )
    
    print(f"Login response: {response.status_code}")
    print(f"Login cookies: {dict(response.cookies)}")
    print(f"Session cookies: {dict(session.cookies)}")
    
    if response.status_code != 200:
        pytest.skip(f"Could not authenticate: {response.text}")
    
    # Verify we got the access_token cookie
    if "access_token" not in session.cookies:
        print(f"Warning: No access_token cookie found. Response: {response.text[:500]}")
    
    return session


class TestSalespeople:
    """Test GET /api/admin/salespeople endpoint"""
    
    def test_get_salespeople_success(self, authenticated_session):
        """Test listing salespeople (admins) from tenant"""
        response = authenticated_session.get(f"{BASE_URL}/api/admin/salespeople")
        print(f"Salespeople response: {response.status_code}")
        print(f"Response body: {response.text[:500] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Failed to get salespeople: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "salespeople" in data, "Missing 'salespeople' key in response"
        assert "total" in data, "Missing 'total' key in response"
        assert isinstance(data["salespeople"], list), "salespeople should be a list"
        assert isinstance(data["total"], int), "total should be an integer"
        
        # Validate salespeople data structure
        if data["salespeople"]:
            salesperson = data["salespeople"][0]
            assert "id" in salesperson, "Salesperson missing 'id'"
            assert "name" in salesperson, "Salesperson missing 'name'"
            assert "email" in salesperson, "Salesperson missing 'email'"
            assert "role" in salesperson, "Salesperson missing 'role'"
            # Verify role is admin or super_admin
            assert salesperson["role"] in ["admin", "super_admin"], f"Invalid role: {salesperson['role']}"
        
        print(f"✅ Found {data['total']} salespeople")
    
    def test_get_salespeople_unauthorized(self):
        """Test that unauthenticated requests are rejected"""
        response = requests.get(
            f"{BASE_URL}/api/admin/salespeople",
            headers={"X-Tenant-ID": SUPER_ADMIN_TENANT}
        )
        print(f"Unauthorized salespeople response: {response.status_code}")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Unauthenticated request correctly rejected")


class TestLicenseRenewal:
    """Test POST /api/licenses/{id}/renew endpoint"""
    
    @pytest.fixture(scope="class")
    def test_license_id(self, authenticated_session):
        """Get or create a test license for renewal tests"""
        # First try to get an existing license
        response = authenticated_session.get(f"{BASE_URL}/api/licenses")
        print(f"Get licenses response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            licenses = data.get("licenses", data) if isinstance(data, dict) else data
            if isinstance(licenses, list) and licenses:
                license_id = licenses[0].get("id")
                print(f"Using existing license: {license_id}")
                return license_id
        
        # Create a new test license if none exists
        new_license = {
            "name": "TEST_RenewalTestLicense",
            "description": "License for renewal testing",
            "max_users": 5,
            "validity_days": 365
        }
        response = authenticated_session.post(
            f"{BASE_URL}/api/licenses",
            json=new_license
        )
        if response.status_code in [200, 201]:
            license_id = response.json().get("id")
            print(f"Created test license: {license_id}")
            return license_id
        
        pytest.skip("Could not get or create test license")
    
    def test_renew_license_default_days(self, authenticated_session, test_license_id):
        """Test renewing a license with default validity days"""
        response = authenticated_session.post(
            f"{BASE_URL}/api/licenses/{test_license_id}/renew",
            json={"notes": "Test renewal with default days"}
        )
        print(f"Renew license response: {response.status_code}")
        print(f"Response body: {response.text[:800] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Failed to renew license: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert data.get("success") == True, "Expected success=True"
        assert "message" in data, "Missing 'message' in response"
        assert "license" in data, "Missing 'license' in response"
        assert "renewal_entry" in data, "Missing 'renewal_entry' in response"
        
        # Validate renewal entry structure
        renewal_entry = data["renewal_entry"]
        assert "id" in renewal_entry, "Renewal entry missing 'id'"
        assert "renewal_date" in renewal_entry, "Renewal entry missing 'renewal_date'"
        assert "new_expiration" in renewal_entry, "Renewal entry missing 'new_expiration'"
        assert "validity_days" in renewal_entry, "Renewal entry missing 'validity_days'"
        assert "renewed_by_id" in renewal_entry, "Renewal entry missing 'renewed_by_id'"
        assert "renewed_by_name" in renewal_entry, "Renewal entry missing 'renewed_by_name'"
        assert "renewed_by_email" in renewal_entry, "Renewal entry missing 'renewed_by_email'"
        
        print(f"✅ License renewed successfully: {data['message']}")
    
    def test_renew_license_custom_days(self, authenticated_session, test_license_id):
        """Test renewing a license with custom validity days"""
        custom_days = 180
        response = authenticated_session.post(
            f"{BASE_URL}/api/licenses/{test_license_id}/renew",
            json={
                "validity_days": custom_days,
                "notes": f"Test renewal with {custom_days} days"
            }
        )
        print(f"Renew license (custom days) response: {response.status_code}")
        print(f"Response body: {response.text[:800] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Failed to renew license: {response.text}"
        data = response.json()
        
        # Validate custom days were applied
        renewal_entry = data["renewal_entry"]
        assert renewal_entry["validity_days"] == custom_days, f"Expected {custom_days} days, got {renewal_entry['validity_days']}"
        
        print(f"✅ License renewed with {custom_days} custom days")
    
    def test_renew_license_not_found(self, authenticated_session):
        """Test renewing a non-existent license"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = authenticated_session.post(
            f"{BASE_URL}/api/licenses/{fake_id}/renew",
            json={"notes": "Test renewal for non-existent license"}
        )
        print(f"Renew non-existent license response: {response.status_code}")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ Non-existent license correctly returns 404")
    
    def test_renew_license_unauthorized(self):
        """Test that unauthenticated renewal requests are rejected"""
        response = requests.post(
            f"{BASE_URL}/api/licenses/{KNOWN_LICENSE_ID}/renew",
            json={"notes": "Unauthorized renewal attempt"},
            headers={"X-Tenant-ID": SUPER_ADMIN_TENANT, "Content-Type": "application/json"}
        )
        print(f"Unauthorized renewal response: {response.status_code}")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Unauthenticated renewal correctly rejected")


class TestLicenseHistory:
    """Test GET /api/licenses/{id}/history endpoint"""
    
    @pytest.fixture(scope="class")
    def license_with_history(self, authenticated_session):
        """Get a license that has renewal history"""
        # First try the known license ID
        response = authenticated_session.get(f"{BASE_URL}/api/licenses/{KNOWN_LICENSE_ID}/history")
        if response.status_code == 200:
            return KNOWN_LICENSE_ID
        
        # Otherwise get any license and renew it to create history
        response = authenticated_session.get(f"{BASE_URL}/api/licenses")
        if response.status_code == 200:
            data = response.json()
            licenses = data.get("licenses", data) if isinstance(data, dict) else data
            if isinstance(licenses, list) and licenses:
                license_id = licenses[0].get("id")
                # Renew to create history
                authenticated_session.post(
                    f"{BASE_URL}/api/licenses/{license_id}/renew",
                    json={"notes": "Creating history for test"}
                )
                return license_id
        
        pytest.skip("Could not find or create license with history")
    
    def test_get_license_history_success(self, authenticated_session, license_with_history):
        """Test getting renewal history for a license"""
        response = authenticated_session.get(f"{BASE_URL}/api/licenses/{license_with_history}/history")
        print(f"License history response: {response.status_code}")
        print(f"Response body: {response.text[:800] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Failed to get history: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "license_id" in data, "Missing 'license_id' in response"
        assert "license_name" in data, "Missing 'license_name' in response"
        assert "current_expiration" in data, "Missing 'current_expiration' in response"
        assert "validity_days" in data, "Missing 'validity_days' in response"
        assert "total_renewals" in data, "Missing 'total_renewals' in response"
        assert "renewal_history" in data, "Missing 'renewal_history' in response"
        
        # Validate history is a list
        assert isinstance(data["renewal_history"], list), "renewal_history should be a list"
        assert isinstance(data["total_renewals"], int), "total_renewals should be an integer"
        
        # If there's history, validate entry structure
        if data["renewal_history"]:
            entry = data["renewal_history"][0]
            assert "id" in entry, "History entry missing 'id'"
            assert "renewal_date" in entry, "History entry missing 'renewal_date'"
            assert "validity_days" in entry, "History entry missing 'validity_days'"
            assert "renewed_by_name" in entry, "History entry missing 'renewed_by_name'"
        
        print(f"✅ License has {data['total_renewals']} renewals in history")
    
    def test_get_license_history_not_found(self, authenticated_session):
        """Test getting history for non-existent license"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = authenticated_session.get(f"{BASE_URL}/api/licenses/{fake_id}/history")
        print(f"History for non-existent license response: {response.status_code}")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ Non-existent license history correctly returns 404")
    
    def test_get_license_history_unauthorized(self):
        """Test that unauthenticated history requests are rejected"""
        response = requests.get(
            f"{BASE_URL}/api/licenses/{KNOWN_LICENSE_ID}/history",
            headers={"X-Tenant-ID": SUPER_ADMIN_TENANT}
        )
        print(f"Unauthorized history response: {response.status_code}")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Unauthenticated history request correctly rejected")


class TestLicenseUpdateNewFields:
    """Test PUT /api/licenses/{id} with new fields (validity_days, salesperson_id, salesperson_name)"""
    
    @pytest.fixture(scope="class")
    def test_license_id(self, authenticated_session):
        """Get or create a test license for update tests"""
        # First try to get an existing license
        response = authenticated_session.get(f"{BASE_URL}/api/licenses")
        if response.status_code == 200:
            data = response.json()
            licenses = data.get("licenses", data) if isinstance(data, dict) else data
            if isinstance(licenses, list) and licenses:
                license_id = licenses[0].get("id")
                print(f"Using existing license for update tests: {license_id}")
                return license_id
        
        pytest.skip("Could not get test license")
    
    @pytest.fixture(scope="class")
    def salesperson_data(self, authenticated_session):
        """Get a salesperson to use in tests"""
        response = authenticated_session.get(f"{BASE_URL}/api/admin/salespeople")
        if response.status_code == 200:
            data = response.json()
            if data.get("salespeople"):
                sp = data["salespeople"][0]
                return {"id": sp["id"], "name": sp["name"]}
        return {"id": "test-salesperson-id", "name": "Test Salesperson"}
    
    def test_update_license_validity_days(self, authenticated_session, test_license_id):
        """Test updating license validity_days field"""
        new_validity = 730  # 2 years
        response = authenticated_session.put(
            f"{BASE_URL}/api/licenses/{test_license_id}",
            json={"validity_days": new_validity}
        )
        print(f"Update validity_days response: {response.status_code}")
        print(f"Response body: {response.text[:500] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Failed to update license: {response.text}"
        data = response.json()
        
        # Verify the field was updated
        assert data.get("validity_days") == new_validity, f"Expected validity_days={new_validity}, got {data.get('validity_days')}"
        print(f"✅ License validity_days updated to {new_validity}")
    
    def test_update_license_salesperson(self, authenticated_session, test_license_id, salesperson_data):
        """Test updating license salesperson fields"""
        response = authenticated_session.put(
            f"{BASE_URL}/api/licenses/{test_license_id}",
            json={
                "salesperson_id": salesperson_data["id"],
                "salesperson_name": salesperson_data["name"]
            }
        )
        print(f"Update salesperson response: {response.status_code}")
        print(f"Response body: {response.text[:500] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Failed to update license: {response.text}"
        data = response.json()
        
        # Verify the fields were updated
        assert data.get("salesperson_id") == salesperson_data["id"], f"salesperson_id mismatch"
        assert data.get("salesperson_name") == salesperson_data["name"], f"salesperson_name mismatch"
        print(f"✅ License salesperson updated to {salesperson_data['name']}")
    
    def test_update_license_all_new_fields(self, authenticated_session, test_license_id, salesperson_data):
        """Test updating all new license management fields at once"""
        update_data = {
            "validity_days": 365,
            "salesperson_id": salesperson_data["id"],
            "salesperson_name": salesperson_data["name"]
        }
        response = authenticated_session.put(
            f"{BASE_URL}/api/licenses/{test_license_id}",
            json=update_data
        )
        print(f"Update all new fields response: {response.status_code}")
        print(f"Response body: {response.text[:500] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Failed to update license: {response.text}"
        data = response.json()
        
        # Verify all fields were updated
        assert data.get("validity_days") == 365, "validity_days not updated"
        assert data.get("salesperson_id") == salesperson_data["id"], "salesperson_id not updated"
        assert data.get("salesperson_name") == salesperson_data["name"], "salesperson_name not updated"
        print("✅ All new license management fields updated successfully")


class TestKnownLicenseHistory:
    """Test the known license ID mentioned in the review request"""
    
    def test_known_license_exists(self, authenticated_session):
        """Test that the known license ID exists and has history"""
        response = authenticated_session.get(f"{BASE_URL}/api/licenses/{KNOWN_LICENSE_ID}/history")
        print(f"Known license history response: {response.status_code}")
        print(f"Response body: {response.text[:800] if response.text else 'empty'}")
        
        # This test is informational - the license may or may not exist
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Known license '{data.get('license_name')}' has {data.get('total_renewals', 0)} renewals")
            if data.get("renewal_history"):
                print(f"First renewal: {data['renewal_history'][0]}")
        else:
            print(f"ℹ️ Known license {KNOWN_LICENSE_ID} not found (status {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
