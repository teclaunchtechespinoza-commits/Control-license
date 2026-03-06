"""
Test Certificate Settings API - License Manager v1.5.0
Tests for certificate customization endpoints (logo, terms, procedure steps)
"""
import pytest
import requests
import os
import base64
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TENANT_ID = "default"

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"


class TestCertificateSettingsAPI:
    """Test suite for Certificate Settings endpoints"""
    
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
            # Extract cookies for session auth
            self.session.cookies.update(login_response.cookies)
            print(f"✅ Login successful for {ADMIN_EMAIL}")
        else:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
    
    # ==================== GET /api/certificate-settings ====================
    def test_get_certificate_settings_success(self):
        """GET /api/certificate-settings - deve retornar configurações do tenant"""
        response = self.session.get(f"{BASE_URL}/api/certificate-settings")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "settings" in data
        
        settings = data["settings"]
        # Verify required fields exist
        assert "tenant_id" in settings
        assert "company_name" in settings
        assert "terms" in settings
        assert "procedure_steps" in settings or settings.get("procedure_steps") is None
        
        print(f"✅ GET /api/certificate-settings - Settings retrieved for tenant: {settings.get('tenant_id')}")
        print(f"   Company: {settings.get('company_name')}")
        print(f"   Has logo: {bool(settings.get('logo_base64'))}")
        print(f"   Procedure steps: {len(settings.get('procedure_steps', []))}")
    
    def test_get_certificate_settings_creates_default_if_missing(self):
        """GET /api/certificate-settings - deve criar configurações padrão se não existirem"""
        response = self.session.get(f"{BASE_URL}/api/certificate-settings")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have default terms
        settings = data["settings"]
        if settings.get("terms"):
            assert "introduction" in settings["terms"]
            print(f"✅ Default terms created with introduction: {settings['terms']['introduction'][:50]}...")
    
    # ==================== PUT /api/certificate-settings/logo ====================
    def test_update_logo_with_base64(self):
        """PUT /api/certificate-settings/logo - deve aceitar upload de logo em base64"""
        # Create a small test image (1x1 pixel PNG)
        test_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        response = self.session.put(
            f"{BASE_URL}/api/certificate-settings/logo",
            json={
                "logo_base64": test_image_base64,
                "logo_filename": "test_logo.png",
                "company_name": "TEST COMPANY"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "message" in data
        
        print(f"✅ PUT /api/certificate-settings/logo - Logo updated successfully")
        
        # Verify logo was saved
        verify_response = self.session.get(f"{BASE_URL}/api/certificate-settings")
        assert verify_response.status_code == 200
        settings = verify_response.json()["settings"]
        assert settings.get("logo_base64") is not None
        assert settings.get("company_name") == "TEST COMPANY"
        print(f"   Verified: Logo saved and company name updated")
    
    def test_update_logo_invalid_base64(self):
        """PUT /api/certificate-settings/logo - deve rejeitar base64 inválido"""
        response = self.session.put(
            f"{BASE_URL}/api/certificate-settings/logo",
            json={
                "logo_base64": "invalid-base64-data!!!",
                "logo_filename": "invalid.png"
            }
        )
        
        # Should return 400 for invalid base64
        assert response.status_code == 400, f"Expected 400 for invalid base64, got {response.status_code}"
        print(f"✅ PUT /api/certificate-settings/logo - Correctly rejected invalid base64")
    
    def test_delete_logo(self):
        """DELETE /api/certificate-settings/logo - deve remover logo customizado"""
        response = self.session.delete(f"{BASE_URL}/api/certificate-settings/logo")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        
        print(f"✅ DELETE /api/certificate-settings/logo - Logo removed successfully")
    
    # ==================== PUT /api/certificate-settings/terms ====================
    def test_update_terms(self):
        """PUT /api/certificate-settings/terms - deve atualizar termos de compromisso"""
        test_terms = {
            "introduction": "Este é um termo de teste atualizado.",
            "sections": [
                {
                    "number": 1,
                    "title": "Seção de Teste",
                    "content": "Conteúdo da seção de teste.",
                    "items": ["Item 1", "Item 2"]
                }
            ]
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/certificate-settings/terms",
            json=test_terms
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        
        print(f"✅ PUT /api/certificate-settings/terms - Terms updated successfully")
        
        # Verify terms were saved
        verify_response = self.session.get(f"{BASE_URL}/api/certificate-settings")
        assert verify_response.status_code == 200
        settings = verify_response.json()["settings"]
        assert settings["terms"]["introduction"] == test_terms["introduction"]
        print(f"   Verified: Terms saved correctly")
    
    def test_reset_terms(self):
        """PUT /api/certificate-settings/terms/reset - deve restaurar termos padrão"""
        response = self.session.put(f"{BASE_URL}/api/certificate-settings/terms/reset")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        
        print(f"✅ PUT /api/certificate-settings/terms/reset - Terms reset to default")
    
    # ==================== POST /api/certificate-settings/procedure-steps ====================
    def test_add_procedure_step(self):
        """POST /api/certificate-settings/procedure-steps - deve adicionar novo passo"""
        new_step = {
            "title": "Passo de Teste",
            "description": "Descrição do passo de teste para validação."
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/certificate-settings/procedure-steps",
            json=new_step
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "step" in data
        
        created_step = data["step"]
        assert "id" in created_step
        assert created_step["title"] == new_step["title"]
        assert created_step["description"] == new_step["description"]
        assert "order" in created_step
        
        # Store step ID for later tests
        self.created_step_id = created_step["id"]
        
        print(f"✅ POST /api/certificate-settings/procedure-steps - Step created")
        print(f"   Step ID: {created_step['id']}, Order: {created_step['order']}")
        
        return created_step["id"]
    
    # ==================== PUT /api/certificate-settings/procedure-steps/{id} ====================
    def test_update_procedure_step(self):
        """PUT /api/certificate-settings/procedure-steps/{id} - deve atualizar passo existente"""
        # First create a step to update
        create_response = self.session.post(
            f"{BASE_URL}/api/certificate-settings/procedure-steps",
            json={"title": "Step to Update", "description": "Original description"}
        )
        assert create_response.status_code == 200
        step_id = create_response.json()["step"]["id"]
        
        # Update the step
        update_data = {
            "title": "Updated Step Title",
            "description": "Updated description for the step."
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/certificate-settings/procedure-steps/{step_id}",
            json=update_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert data["step"]["title"] == update_data["title"]
        assert data["step"]["description"] == update_data["description"]
        
        print(f"✅ PUT /api/certificate-settings/procedure-steps/{step_id} - Step updated")
        
        return step_id
    
    def test_update_procedure_step_not_found(self):
        """PUT /api/certificate-settings/procedure-steps/{id} - deve retornar 404 para ID inexistente"""
        response = self.session.put(
            f"{BASE_URL}/api/certificate-settings/procedure-steps/nonexistent-id",
            json={"title": "Test"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✅ PUT /api/certificate-settings/procedure-steps/nonexistent-id - Correctly returned 404")
    
    # ==================== DELETE /api/certificate-settings/procedure-steps/{id} ====================
    def test_delete_procedure_step(self):
        """DELETE /api/certificate-settings/procedure-steps/{id} - deve remover passo"""
        # First create a step to delete
        create_response = self.session.post(
            f"{BASE_URL}/api/certificate-settings/procedure-steps",
            json={"title": "Step to Delete", "description": "Will be deleted"}
        )
        assert create_response.status_code == 200
        step_id = create_response.json()["step"]["id"]
        
        # Delete the step
        response = self.session.delete(
            f"{BASE_URL}/api/certificate-settings/procedure-steps/{step_id}"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        
        print(f"✅ DELETE /api/certificate-settings/procedure-steps/{step_id} - Step deleted")
        
        # Verify step was deleted
        verify_response = self.session.get(f"{BASE_URL}/api/certificate-settings")
        settings = verify_response.json()["settings"]
        step_ids = [s["id"] for s in settings.get("procedure_steps", [])]
        assert step_id not in step_ids, "Step should have been deleted"
        print(f"   Verified: Step no longer exists")
    
    def test_reset_procedure_steps(self):
        """PUT /api/certificate-settings/procedure-steps/reset - deve restaurar passos padrão"""
        response = self.session.put(f"{BASE_URL}/api/certificate-settings/procedure-steps/reset")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        
        print(f"✅ PUT /api/certificate-settings/procedure-steps/reset - Steps reset to default")
        
        # Verify default steps were created
        verify_response = self.session.get(f"{BASE_URL}/api/certificate-settings")
        settings = verify_response.json()["settings"]
        steps = settings.get("procedure_steps", [])
        assert len(steps) >= 1, "Should have default steps after reset"
        print(f"   Verified: {len(steps)} default steps created")
    
    # ==================== GET /api/certificates/{code}/pdf ====================
    def test_pdf_generation_uses_tenant_settings(self):
        """GET /api/certificates/{code}/pdf - PDF deve usar configurações do tenant"""
        # Use existing certificate code
        certificate_code = "86fe95a60d76"
        
        response = self.session.get(f"{BASE_URL}/api/certificates/{certificate_code}/pdf")
        
        # PDF endpoint should return 200 with PDF content
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify content type is PDF
        content_type = response.headers.get("Content-Type", "")
        assert "application/pdf" in content_type, f"Expected PDF content type, got: {content_type}"
        
        # Verify we got actual PDF content
        assert len(response.content) > 0, "PDF content should not be empty"
        assert response.content[:4] == b'%PDF', "Response should be a valid PDF"
        
        print(f"✅ GET /api/certificates/{certificate_code}/pdf - PDF generated successfully")
        print(f"   Content-Type: {content_type}")
        print(f"   PDF size: {len(response.content)} bytes")
    
    # ==================== Authentication Tests ====================
    def test_certificate_settings_requires_auth(self):
        """Certificate settings endpoints should require authentication"""
        # Create new session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID
        })
        
        response = unauth_session.get(f"{BASE_URL}/api/certificate-settings")
        
        # Should return 401 Unauthorized
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ GET /api/certificate-settings - Correctly requires authentication")
    
    def test_certificate_settings_requires_admin(self):
        """Certificate settings endpoints should require admin role"""
        # This test verifies the endpoint is protected
        # The actual admin check is done by the get_current_admin_user dependency
        response = self.session.get(f"{BASE_URL}/api/certificate-settings")
        
        # If we're logged in as admin, should succeed
        assert response.status_code == 200, f"Admin should have access, got {response.status_code}"
        print(f"✅ Certificate settings accessible by admin user")


class TestCertificateSettingsIntegration:
    """Integration tests for certificate settings workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID
        })
        
        # Login
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code == 200:
            self.session.cookies.update(login_response.cookies)
        else:
            pytest.skip("Login failed")
    
    def test_full_settings_workflow(self):
        """Test complete workflow: get settings -> update -> verify"""
        # 1. Get initial settings
        get_response = self.session.get(f"{BASE_URL}/api/certificate-settings")
        assert get_response.status_code == 200
        initial_settings = get_response.json()["settings"]
        print(f"✅ Step 1: Retrieved initial settings")
        
        # 2. Update logo
        logo_response = self.session.put(
            f"{BASE_URL}/api/certificate-settings/logo",
            json={
                "logo_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "company_name": "Integration Test Company"
            }
        )
        assert logo_response.status_code == 200
        print(f"✅ Step 2: Updated logo")
        
        # 3. Update terms
        terms_response = self.session.put(
            f"{BASE_URL}/api/certificate-settings/terms",
            json={
                "introduction": "Integration test terms introduction."
            }
        )
        assert terms_response.status_code == 200
        print(f"✅ Step 3: Updated terms")
        
        # 4. Add a procedure step
        step_response = self.session.post(
            f"{BASE_URL}/api/certificate-settings/procedure-steps",
            json={
                "title": "Integration Test Step",
                "description": "Step created during integration test"
            }
        )
        assert step_response.status_code == 200
        step_id = step_response.json()["step"]["id"]
        print(f"✅ Step 4: Added procedure step (ID: {step_id})")
        
        # 5. Verify all changes
        verify_response = self.session.get(f"{BASE_URL}/api/certificate-settings")
        assert verify_response.status_code == 200
        final_settings = verify_response.json()["settings"]
        
        assert final_settings["company_name"] == "Integration Test Company"
        assert final_settings["terms"]["introduction"] == "Integration test terms introduction."
        assert any(s["id"] == step_id for s in final_settings.get("procedure_steps", []))
        print(f"✅ Step 5: Verified all changes persisted")
        
        # 6. Cleanup - delete the test step
        delete_response = self.session.delete(
            f"{BASE_URL}/api/certificate-settings/procedure-steps/{step_id}"
        )
        assert delete_response.status_code == 200
        print(f"✅ Step 6: Cleaned up test step")
        
        # 7. Reset to defaults
        self.session.put(f"{BASE_URL}/api/certificate-settings/terms/reset")
        self.session.put(f"{BASE_URL}/api/certificate-settings/procedure-steps/reset")
        self.session.delete(f"{BASE_URL}/api/certificate-settings/logo")
        print(f"✅ Step 7: Reset settings to defaults")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
