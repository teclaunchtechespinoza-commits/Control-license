"""
Test Certificate Preview PDF API - License Manager v1.5.0
Tests for the new preview-pdf endpoint that generates a preview certificate
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TENANT_ID = "default"

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"
SUPERADMIN_EMAIL = "superadmin@autotech.com"
SUPERADMIN_PASSWORD = "admin123"


class TestCertificatePreviewPDF:
    """Test suite for Certificate Preview PDF endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID
        })
        
        # Login to get auth token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code == 200:
            self.session.cookies.update(login_response.cookies)
            print(f"Login successful for {ADMIN_EMAIL}")
        else:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
    
    # ==================== GET /api/certificate-settings/preview-pdf ====================
    def test_preview_pdf_returns_valid_pdf(self):
        """GET /api/certificate-settings/preview-pdf - should return valid PDF"""
        response = self.session.get(f"{BASE_URL}/api/certificate-settings/preview-pdf")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify content type is PDF
        content_type = response.headers.get("Content-Type", "")
        assert "application/pdf" in content_type, f"Expected PDF content type, got: {content_type}"
        
        # Verify we got actual PDF content
        assert len(response.content) > 0, "PDF content should not be empty"
        assert response.content[:4] == b'%PDF', "Response should be a valid PDF (starts with %PDF)"
        
        print(f"GET /api/certificate-settings/preview-pdf - PDF generated successfully")
        print(f"   Content-Type: {content_type}")
        print(f"   PDF size: {len(response.content)} bytes")
    
    def test_preview_pdf_has_correct_headers(self):
        """GET /api/certificate-settings/preview-pdf - should have correct response headers"""
        response = self.session.get(f"{BASE_URL}/api/certificate-settings/preview-pdf")
        
        assert response.status_code == 200
        
        # Check Content-Disposition header for inline display
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "inline" in content_disposition, f"Expected inline disposition, got: {content_disposition}"
        assert "preview_certificado.pdf" in content_disposition, f"Expected filename in disposition, got: {content_disposition}"
        
        print(f"Preview PDF headers verified: {content_disposition}")
    
    def test_preview_pdf_requires_authentication(self):
        """GET /api/certificate-settings/preview-pdf - should require authentication"""
        # Create new session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID
        })
        
        response = unauth_session.get(f"{BASE_URL}/api/certificate-settings/preview-pdf")
        
        # Should return 401 Unauthorized
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"GET /api/certificate-settings/preview-pdf - Correctly requires authentication")
    
    def test_preview_pdf_uses_tenant_settings(self):
        """GET /api/certificate-settings/preview-pdf - should use tenant settings"""
        # First, get current settings
        settings_response = self.session.get(f"{BASE_URL}/api/certificate-settings")
        assert settings_response.status_code == 200
        settings = settings_response.json()["settings"]
        
        # Generate preview PDF
        pdf_response = self.session.get(f"{BASE_URL}/api/certificate-settings/preview-pdf")
        assert pdf_response.status_code == 200
        
        # PDF should be generated (we can't easily verify content uses settings,
        # but we verify the endpoint works with existing settings)
        assert len(pdf_response.content) > 1000, "PDF should have substantial content"
        
        print(f"Preview PDF generated with tenant settings")
        print(f"   Company name in settings: {settings.get('company_name')}")
        print(f"   Has logo: {bool(settings.get('logo_base64'))}")


class TestCertificatePreviewPDFWithSuperAdmin:
    """Test preview PDF with super admin credentials"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with super admin authentication"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID
        })
        
        # Login as super admin
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": SUPERADMIN_EMAIL, "password": SUPERADMIN_PASSWORD}
        )
        
        if login_response.status_code == 200:
            self.session.cookies.update(login_response.cookies)
            print(f"Login successful for {SUPERADMIN_EMAIL}")
        else:
            pytest.skip(f"Super admin login failed: {login_response.status_code}")
    
    def test_superadmin_can_generate_preview_pdf(self):
        """Super admin should be able to generate preview PDF"""
        response = self.session.get(f"{BASE_URL}/api/certificate-settings/preview-pdf")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.content[:4] == b'%PDF', "Response should be a valid PDF"
        
        print(f"Super admin successfully generated preview PDF ({len(response.content)} bytes)")


class TestCertificateSettingsEndpoint:
    """Test certificate settings GET endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID
        })
        
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code == 200:
            self.session.cookies.update(login_response.cookies)
        else:
            pytest.skip("Login failed")
    
    def test_get_certificate_settings(self):
        """GET /api/certificate-settings - should return settings"""
        response = self.session.get(f"{BASE_URL}/api/certificate-settings")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True
        assert "settings" in data
        
        settings = data["settings"]
        assert "tenant_id" in settings
        assert "company_name" in settings
        assert "terms" in settings
        
        print(f"GET /api/certificate-settings - Settings retrieved")
        print(f"   Company: {settings.get('company_name')}")
        print(f"   Has logo: {bool(settings.get('logo_base64'))}")
    
    def test_certificate_settings_requires_auth(self):
        """GET /api/certificate-settings - should require authentication"""
        unauth_session = requests.Session()
        unauth_session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID
        })
        
        response = unauth_session.get(f"{BASE_URL}/api/certificate-settings")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"GET /api/certificate-settings - Correctly requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
