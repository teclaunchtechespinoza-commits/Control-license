# 🔌 License Manager - API Documentation v1.3.0

## 📋 API Overview

**Base URL**: `http://localhost:8001/api`  
**Version**: 1.3.0 Enterprise  
**Authentication**: JWT Bearer Token  
**Rate Limiting**: 1000 requests/minute per user  
**Response Format**: JSON  

---

## 🔐 Authentication Endpoints

### **POST /auth/login**
Authenticate user and obtain access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_uuid",
    "email": "user@example.com",
    "role": "admin",
    "tenant_id": "tenant_uuid"
  }
}
```

### **GET /auth/me**
Get current user information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "user_uuid",
  "email": "user@example.com", 
  "role": "admin",
  "tenant_id": "tenant_uuid",
  "permissions": ["read_licenses", "write_licenses", "..."],
  "is_active": true
}
```

---

## 🛡️ License Management Endpoints

### **GET /licenses**
Get all licenses (filtered by tenant and user permissions).

**Query Parameters:**
- `status` (optional): Filter by status (active, expired, pending)
- `assigned_user_id` (optional): Filter by assigned user
- `limit` (optional, default=100): Limit results

**Response (200):**
```json
[
  {
    "id": "license_uuid",
    "name": "Premium License",
    "description": "Full feature access",
    "license_key": "XXXX-XXXX-XXXX-XXXX",
    "status": "active",
    "expires_at": "2025-01-15T00:00:00Z",
    "assigned_user_id": "user_uuid",
    "tenant_id": "tenant_uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "metadata": {}
  }
]
```

### **POST /licenses**
Create a new license.

**Request Body:**
```json
{
  "name": "New License",
  "description": "License description",
  "expires_at": "2025-12-31T23:59:59Z",
  "assigned_user_id": "user_uuid",
  "plan_type": "premium",
  "metadata": {
    "features": ["feature1", "feature2"]
  }
}
```

### **PUT /licenses/{license_id}**
Update existing license.

### **DELETE /licenses/{license_id}**
Delete license (soft delete).

---

## 👥 User Management Endpoints

### **GET /users**
Get all users in tenant (Admin+ only).

**Response (200):**
```json
[
  {
    "id": "user_uuid",
    "email": "user@example.com",
    "role": "admin", 
    "tenant_id": "tenant_uuid",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-12-01T10:00:00Z"
  }
]
```

### **POST /users**
Create new user (Admin+ only).

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "secure_password",
  "role": "user",
  "is_active": true
}
```

---

## 👤 Client Management Endpoints

### **GET /clientes-pf**
Get Pessoa Física (individual) clients.

**Query Parameters:**
- `status` (optional): Filter by status  
- `search` (optional): Search by name or CPF
- `limit` (optional): Limit results

**Response (200):**
```json
[
  {
    "id": "client_uuid",
    "nome_completo": "João Silva Santos",
    "cpf": "123***901", // Masked for non-admin users
    "email_principal": "joao@email.com",
    "telefone_principal": "(11) 99999-9999",
    "status": "active",
    "tenant_id": "tenant_uuid",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### **GET /clientes-pj**  
Get Pessoa Jurídica (business) clients.

**Response (200):**
```json
[
  {
    "id": "client_uuid",
    "razao_social": "Empresa LTDA",
    "nome_fantasia": "Empresa", 
    "cnpj": "12***99", // Masked for non-admin users
    "status": "active",
    "tenant_id": "tenant_uuid",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

## 📦 Registry Endpoints

### **GET /categories**
Get product categories.

**Response (200):**
```json
[
  {
    "id": "category_uuid",
    "name": "Software Licenses",
    "description": "Software licensing products",
    "is_active": true,
    "tenant_id": "tenant_uuid",
    "parent_id": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### **GET /products**
Get products catalog.

**Response (200):**
```json
[
  {
    "id": "product_uuid", 
    "name": "Premium Software",
    "description": "Full-featured software license",
    "category_id": "category_uuid",
    "is_active": true,
    "tenant_id": "tenant_uuid",
    "pricing": {
      "monthly": 99.99,
      "yearly": 999.99
    },
    "features": ["feature1", "feature2"]
  }
]
```

---

## 🔔 Notification Endpoints

### **GET /notifications**
Get user notifications.

**Response (200):**
```json
[
  {
    "id": "notification_uuid",
    "title": "License Expiring Soon", 
    "message": "Your license expires in 7 days",
    "type": "LICENSE_EXPIRING_7",
    "channels": ["email", "whatsapp"],
    "status": "sent",
    "created_at": "2024-12-01T00:00:00Z",
    "metadata": {
      "license_id": "license_uuid"
    }
  }
]
```

### **POST /notifications**
Create custom notification (Admin+ only).

---

## 🔒 RBAC Endpoints

### **GET /rbac/roles**
Get available roles (Admin+ only).

**Response (200):**
```json
[
  {
    "id": "role_uuid",
    "name": "Super Admin",
    "description": "Full system access",
    "permissions": ["*"],
    "is_system": true,
    "tenant_id": null
  },
  {
    "id": "role_uuid", 
    "name": "Admin",
    "description": "Tenant administration", 
    "permissions": ["read_*", "write_*"],
    "is_system": false,
    "tenant_id": "tenant_uuid"
  }
]
```

### **GET /rbac/permissions**
Get available permissions (Admin+ only).

**Response (200):**
```json
[
  {
    "id": "permission_uuid",
    "name": "read_licenses",
    "description": "Read license data",
    "category": "licenses"
  },
  {
    "id": "permission_uuid",
    "name": "*", 
    "description": "All permissions",
    "category": "system"
  }
]
```

---

## 🏢 Multi-Tenant Endpoints

### **GET /tenants** 
Get tenant information (Super Admin only).

**Response (200):**
```json
[
  {
    "id": "tenant_uuid",
    "name": "Acme Corporation",
    "subdomain": "acme", 
    "plan": "premium",
    "status": "active",
    "max_users": 100,
    "current_users": 25,
    "max_licenses": 1000,
    "current_licenses": 150,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### **POST /tenants**
Create new tenant (Super Admin only).

---

## 📊 System Monitoring Endpoints

### **GET /stats**
Get system statistics.

**Response (200):**
```json
{
  "total_users": 211,
  "total_licenses": 675,
  "total_clients": 231,
  "total_categories": 81,
  "total_products": 308,
  "active_users": 195,
  "expired_licenses": 12,
  "pending_licenses": 5,
  "system_status": "operational"
}
```

### **GET /scheduler/status**
Get job scheduler status.

**Response (200):**
```json
{
  "scheduler_running": true,
  "total_jobs": 4,
  "jobs": [
    {
      "id": "license_expiry_check",
      "name": "License Expiry Checker", 
      "next_run": "2024-12-01T15:00:00Z",
      "trigger": "cron[hour=*, minute=0]"
    }
  ],
  "statistics": {
    "total_executions": 156,
    "successful_executions": 148,
    "failed_executions": 8,
    "success_rate": 94.87,
    "uptime_hours": 24.5
  }
}
```

---

## 📋 Logging & Analytics Endpoints

### **GET /logs/structured**
Get structured logs with filtering.

**Query Parameters:**
- `limit` (optional, default=50): Number of logs to return
- `level` (optional): Filter by log level (DEBUG, INFO, WARNING, ERROR)
- `category` (optional): Filter by category (auth, system, data_*)

**Response (200):**
```json
{
  "total_logs": 150,
  "limit": 50,
  "filters": {
    "level": "INFO", 
    "category": "system"
  },
  "logs": [
    {
      "timestamp": "2024-12-01T15:30:45Z",
      "event_id": "event_uuid",
      "level": "INFO",
      "category": "system", 
      "action": "request_completed",
      "message": "GET /api/licenses - 200",
      "tenant_id": "tenant_uuid",
      "request_id": "request_uuid",
      "user_id": "user_uuid",
      "details": {
        "method": "GET",
        "path": "/api/licenses", 
        "status_code": 200,
        "duration_ms": 45.2
      }
    }
  ]
}
```

### **GET /logs/audit**
Get audit logs for sensitive operations.

**Response (200):**
```json
{
  "total_audit_logs": 25,
  "limit": 50,
  "logs": [
    {
      "timestamp": "2024-12-01T15:25:30Z",
      "level": "AUDIT",
      "action": "user_authentication_success",
      "message": "User successfully authenticated",
      "tenant_id": "tenant_uuid", 
      "user_id": "user_uuid",
      "audit_required": true,
      "details": {
        "login_method": "password",
        "ip_address": "192.168.1.100"
      }
    }
  ]
}
```

### **GET /logs/analytics**
Get log analytics and performance metrics.

**Response (200):**
```json
{
  "total_logs": 1250,
  "by_level": {
    "INFO": 1100,
    "WARNING": 120, 
    "ERROR": 25,
    "AUDIT": 5
  },
  "by_category": {
    "system": 800,
    "auth": 200,
    "data_read": 150,
    "security": 100
  },
  "performance_metrics": {
    "avg_response_time": 67.5,
    "slow_requests": 3
  },
  "security_events": 15,
  "audit_events": 45,
  "recent_errors": [
    {
      "timestamp": "2024-12-01T14:30:00Z",
      "action": "database_error",
      "message": "Connection timeout to MongoDB"
    }
  ]
}
```

---

## 🔧 Health Check Endpoints

### **GET /health**
Simple health check (no authentication required).

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-01T15:45:00Z",
  "version": "1.3.0"
}
```

### **GET /ping**
Simple ping endpoint (no authentication required).

**Response (200):**
```json
{
  "message": "pong",
  "timestamp": "2024-12-01T15:45:00Z"
}
```

---

## 📝 Error Responses

### **Standard Error Format**
All errors follow this format:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-12-01T15:45:00Z",
  "request_id": "request_uuid"
}
```

### **Common HTTP Status Codes**
- `200` - Success
- `201` - Created  
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error

### **Authentication Errors**
```json
{
  "detail": "Invalid credentials",
  "error_code": "INVALID_CREDENTIALS"
}
```

### **Authorization Errors**
```json
{
  "detail": "Insufficient permissions for this operation",
  "error_code": "INSUFFICIENT_PERMISSIONS", 
  "required_permission": "write_licenses"
}
```

### **Validation Errors**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required", 
      "type": "value_error.missing"
    }
  ],
  "error_code": "VALIDATION_ERROR"
}
```

---

## 🔑 Rate Limiting

### **Rate Limit Headers**
All responses include rate limiting headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1641024000
```

### **Rate Limit Exceeded**
```json
{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

---

## 🔒 Security Considerations  

### **Authentication**
- Use HTTPS in production
- Store tokens securely (httpOnly cookies recommended)
- Implement token refresh logic
- Handle token expiration gracefully

### **Authorization**  
- Check user permissions before API calls
- Implement proper error handling for 403 errors
- Respect tenant isolation

### **Data Privacy**
- Sensitive data is automatically masked for non-admin users
- All operations are logged for audit purposes
- LGPD compliance is enforced automatically

---

## 📚 SDK & Integration Examples

### **JavaScript/Node.js Example**
```javascript
const API_BASE = 'http://localhost:8001/api';

class LicenseManagerAPI {
  constructor(token) {
    this.token = token;
  }

  async getLicenses() {
    const response = await fetch(`${API_BASE}/licenses`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.json();
  }

  async createLicense(licenseData) {
    const response = await fetch(`${API_BASE}/licenses`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(licenseData)
    });
    return response.json();
  }
}
```

### **Python Example**
```python
import requests

class LicenseManagerAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get_licenses(self):
        response = requests.get(f'{self.base_url}/licenses', headers=self.headers)
        return response.json()
    
    def create_license(self, license_data):
        response = requests.post(f'{self.base_url}/licenses', 
                               json=license_data, headers=self.headers)
        return response.json()
```

---

## 🔧 Testing the API

### **Using cURL**
```bash
# Get access token
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.com","password":"admin123"}'

# Use token to get licenses  
curl -X GET http://localhost:8001/api/licenses \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **Using Postman**
1. Create new request
2. Set Authorization type to "Bearer Token"
3. Enter your JWT token
4. Make requests to endpoints

---

*API Documentation v1.3.0 - License Manager Enterprise*  
*For technical support: api-support@licensemanager.com*