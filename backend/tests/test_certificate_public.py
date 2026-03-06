"""
Test Suite for Public Certificate Validation Endpoints
Tests the public certificate validation feature via QR Code/link

Endpoints tested:
- GET /api/certificates/{code} - Public certificate data retrieval
- GET /api/certificates/{code}/pdf - Public PDF download
"""

import pytest
import requests
import os

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test certificate code provided in requirements
TEST_CERTIFICATE_CODE = "86fe95a60d76"


class TestPublicCertificateEndpoints:
    """Tests for public certificate validation endpoints (no auth required)"""
    
    def test_get_certificate_by_code_success(self):
        """Test GET /api/certificates/{code} returns certificate data without auth"""
        response = requests.get(f"{BASE_URL}/api/certificates/{TEST_CERTIFICATE_CODE}")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        assert "certificate" in data, "Response should contain certificate data"
        assert "validation" in data, "Response should contain validation data"
        
        # Certificate data assertions
        cert = data["certificate"]
        assert "certificate_number" in cert, "Certificate should have certificate_number"
        assert "verification_code" in cert, "Certificate should have verification_code"
        assert cert["verification_code"] == TEST_CERTIFICATE_CODE, "Verification code should match"
        assert "client_name" in cert, "Certificate should have client_name"
        assert "product_name" in cert, "Certificate should have product_name"
        assert "serial_number" in cert, "Certificate should have serial_number"
        assert "expiration_date" in cert, "Certificate should have expiration_date"
        
        # Validation data assertions
        validation = data["validation"]
        assert "status" in validation, "Validation should have status"
        assert validation["status"] in ["active", "expired", "revoked"], f"Invalid status: {validation['status']}"
        assert "days_remaining" in validation, "Validation should have days_remaining"
        assert "is_valid" in validation, "Validation should have is_valid"
        assert "server_status" in validation, "Validation should have server_status"
        assert validation["server_status"] == "online", "Server status should be online"
        
        print(f"✅ Certificate {cert['certificate_number']} retrieved successfully")
        print(f"   Status: {validation['status']}, Days remaining: {validation['days_remaining']}")
    
    def test_get_certificate_by_code_not_found(self):
        """Test GET /api/certificates/{code} returns 404 for invalid code"""
        invalid_code = "invalid_code_12345"
        response = requests.get(f"{BASE_URL}/api/certificates/{invalid_code}")
        
        # Status code assertion
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        print("✅ Invalid certificate code correctly returns 404")
    
    def test_get_certificate_pdf_success(self):
        """Test GET /api/certificates/{code}/pdf returns PDF without auth"""
        response = requests.get(f"{BASE_URL}/api/certificates/{TEST_CERTIFICATE_CODE}/pdf")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Content type assertion
        content_type = response.headers.get("content-type", "")
        assert "application/pdf" in content_type, f"Expected PDF content type, got {content_type}"
        
        # Content disposition assertion (should have filename)
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition, "Should be an attachment download"
        assert "certificado_" in content_disposition, "Filename should contain 'certificado_'"
        
        # Content length assertion (PDF should have content)
        assert len(response.content) > 0, "PDF content should not be empty"
        
        # PDF magic bytes check
        assert response.content[:4] == b'%PDF', "Content should be a valid PDF"
        
        print(f"✅ PDF downloaded successfully, size: {len(response.content)} bytes")
    
    def test_get_certificate_pdf_not_found(self):
        """Test GET /api/certificates/{code}/pdf returns 404 for invalid code"""
        invalid_code = "invalid_code_12345"
        response = requests.get(f"{BASE_URL}/api/certificates/{invalid_code}/pdf")
        
        # Status code assertion
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        print("✅ Invalid certificate code correctly returns 404 for PDF")
    
    def test_certificate_password_is_masked(self):
        """Test that password in public response is partially masked"""
        response = requests.get(f"{BASE_URL}/api/certificates/{TEST_CERTIFICATE_CODE}")
        
        assert response.status_code == 200
        data = response.json()
        cert = data["certificate"]
        
        # Check if credentials exist and password is masked
        if cert.get("credentials"):
            password = cert["credentials"].get("password", "")
            if password:
                # Password should contain asterisks (masked)
                assert "****" in password, "Password should be partially masked with ****"
                print(f"✅ Password is correctly masked: {password}")
            else:
                print("ℹ️ No password in credentials")
        else:
            print("ℹ️ No credentials in certificate")
    
    def test_certificate_view_count_increments(self):
        """Test that view_count increments on each request"""
        # First request
        response1 = requests.get(f"{BASE_URL}/api/certificates/{TEST_CERTIFICATE_CODE}")
        assert response1.status_code == 200
        view_count1 = response1.json()["certificate"].get("view_count", 0)
        
        # Second request
        response2 = requests.get(f"{BASE_URL}/api/certificates/{TEST_CERTIFICATE_CODE}")
        assert response2.status_code == 200
        view_count2 = response2.json()["certificate"].get("view_count", 0)
        
        # View count should have incremented
        assert view_count2 > view_count1, f"View count should increment: {view_count1} -> {view_count2}"
        
        print(f"✅ View count incremented: {view_count1} -> {view_count2}")


class TestCertificateValidationStatus:
    """Tests for certificate validation status logic"""
    
    def test_active_certificate_status(self):
        """Test that active certificate returns correct validation status"""
        response = requests.get(f"{BASE_URL}/api/certificates/{TEST_CERTIFICATE_CODE}")
        
        assert response.status_code == 200
        data = response.json()
        validation = data["validation"]
        
        # For the test certificate, it should be active with positive days remaining
        if validation["days_remaining"] > 0:
            assert validation["status"] == "active", "Certificate with positive days should be active"
            assert validation["is_valid"] == True, "Active certificate should be valid"
            print(f"✅ Active certificate status correct: {validation['days_remaining']} days remaining")
        else:
            print(f"ℹ️ Certificate has {validation['days_remaining']} days remaining")


class TestNoAuthRequired:
    """Tests to verify endpoints work without authentication"""
    
    def test_certificate_endpoint_no_auth_header(self):
        """Test that certificate endpoint works without Authorization header"""
        # Make request without any auth headers
        response = requests.get(
            f"{BASE_URL}/api/certificates/{TEST_CERTIFICATE_CODE}",
            headers={"Content-Type": "application/json"}  # Only content-type, no auth
        )
        
        assert response.status_code == 200, "Should work without auth header"
        print("✅ Certificate endpoint works without Authorization header")
    
    def test_pdf_endpoint_no_auth_header(self):
        """Test that PDF endpoint works without Authorization header"""
        # Make request without any auth headers
        response = requests.get(
            f"{BASE_URL}/api/certificates/{TEST_CERTIFICATE_CODE}/pdf",
            headers={"Content-Type": "application/json"}  # Only content-type, no auth
        )
        
        assert response.status_code == 200, "Should work without auth header"
        print("✅ PDF endpoint works without Authorization header")
    
    def test_certificate_endpoint_no_tenant_header(self):
        """Test that certificate endpoint works without X-Tenant-ID header"""
        # Make request without tenant header
        response = requests.get(
            f"{BASE_URL}/api/certificates/{TEST_CERTIFICATE_CODE}"
        )
        
        assert response.status_code == 200, "Should work without X-Tenant-ID header"
        print("✅ Certificate endpoint works without X-Tenant-ID header")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
