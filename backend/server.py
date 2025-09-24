from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime, timedelta, date, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from enum import Enum
import os
import logging
import uuid
import secrets
import re
import json
import asyncio
import bcrypt
import sys
import random
import time  # 🚀 SUB-FASE 2.4 - Added for performance timing
from starlette.responses import JSONResponse

# 🚀 PHASE 1 SECURITY IMPROVEMENTS - Import new middlewares
from tenant_validation import TenantValidationMiddleware, get_validated_tenant, get_tenant_id
from error_handling import ErrorHandlingMiddleware, TenantError, BusinessLogicError
from settings import settings, validate_production_settings, get_security_info

# Import tenant system
from tenant_system import (
    Tenant, TenantCreate, TenantUpdate, TenantStatus, TenantPlan,
    TenantMixin, tenant_context, get_current_tenant_id, is_super_admin,
    add_tenant_filter, add_tenant_to_document, require_tenant,
    get_plan_config, apply_plan_limits
)

# Import middlewares
from middlewares import (
    ObservabilityMiddleware,
    RateLimitMiddleware,
    ResponseTenantHeaderMiddleware,
    TenantContextMiddleware,
    TENANT_CTX,
)

# Import authorization module
from authz import build_scope_filter, enforce_object_scope
from filters import whitelist_filter, merge_with_scope
from invitations import generate_invite_token, verify_invite, token_hash
from email_service import send_invitation_email
from bson import ObjectId
from datetime import datetime
import uuid
import time

# ---------- Models ----------
class PageParams(BaseModel):
    page: int = 1
    size: int = 50

# ---------- Helpers de Tenant ----------
TENANT_HEADER = "X-Tenant-ID"

def require_tenant(request: Request) -> str:
    """
    Obtém tenant do header padronizado 'X-Tenant-ID'.
    Em paralelo, suporta fallback via ContextVar para cobrir pontos legados.
    """
    tenant_id = request.headers.get(TENANT_HEADER) or TENANT_CTX.get()
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{TENANT_HEADER} ausente")
    return tenant_id

def add_tenant_filter(base: Dict[str, Any] | None = None, tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Helper legado: agora *exige* tenant. Se não for fornecido, tenta obter do ContextVar (middleware).
    Isso corrige chamadas antigas como add_tenant_filter({...}) que antes deixavam passar sem filtro.
    """
    f = dict(base or {})
    tid = tenant_id or TENANT_CTX.get()
    if not tid:
        # Segurança em profundidade: nunca prosseguir sem tenant
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{TENANT_HEADER} ausente")
    f["tenant_id"] = tid
    return f

# Import notification system
from notification_system import (
    Notification, NotificationTemplate, NotificationConfig, NotificationQueue,
    NotificationLog, NotificationType, NotificationChannel, NotificationStatus,
    NotificationPriority, CreateNotificationRequest, NotificationStats,
    get_default_template, calculate_notification_trigger_dates,
    should_send_notification, format_template_variables
)

# Import robust scheduler
from robust_scheduler import start_robust_scheduler, stop_robust_scheduler, get_scheduler

# Import sales dashboard
from sales_dashboard import (
    ExpirationAlert, SalesMetrics, SalesDashboardSummary, 
    WhatsAppMessageTemplate, WhatsAppCampaign, SalesContact,
    calculate_days_to_expire, get_alert_type, get_alert_priority,
    DEFAULT_WHATSAPP_TEMPLATES
)

# Import WhatsApp integration
from whatsapp_integration import (
    WhatsAppMessage, WhatsAppContact, WhatsAppSession, WhatsAppStats,
    whatsapp_service, template_service, send_renewal_whatsapp
)

# 🚀 SUB-FASE 2.3 - Import Dependency Injection system
try:
    from dependencies import get_tenant_database, get_pagination_params, RequestMetrics, get_request_metrics
except ImportError:
    # Fallback for development
    get_tenant_database = None
    get_pagination_params = None
    RequestMetrics = None
    get_request_metrics = None

# Import critical security modules
try:
    from deps import (
        require_tenant, 
        add_tenant_filter, 
        add_tenant_to_document,
        enforce_super_admin_or_tenant_filter,
        get_tenant_safe_filter,
        validate_tenant_access
    )
except ImportError:
    from .deps import (
        require_tenant, 
        add_tenant_filter, 
        add_tenant_to_document,
        enforce_super_admin_or_tenant_filter,
        get_tenant_safe_filter,
        validate_tenant_access
    )

# Import security headers middleware
try:
    from security_headers import SecurityHeadersMiddleware, RateLimitMiddleware
except ImportError:
    from .security_headers import SecurityHeadersMiddleware, RateLimitMiddleware

# Import observability components
try:
    from observability import (
        ObservabilityMiddleware, 
        metrics_collector, 
        get_database_health,
        get_tenant_health,
        get_security_health
    )
except ImportError:
    from .observability import (
        ObservabilityMiddleware, 
        metrics_collector, 
        get_database_health,
        get_tenant_health,
        get_security_health
    )

import time
tz = os.getenv('TZ', 'America/Recife')
os.environ['TZ'] = tz
try:
    time.tzset()
except:
    pass  # tzset not available on Windows

# Import WhatsApp Service (Real Integration) - Commented out to avoid circular imports
# from whatsapp_service import whatsapp_router, send_renewal_whatsapp_message

# Utilitário para mascaramento de dados sensíveis
def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mascara dados sensíveis mostrando apenas os primeiros/últimos caracteres
    """
    if not data or len(data) <= visible_chars:
        return mask_char * 8  # Retorna máscara padrão
    
    if len(data) <= visible_chars * 2:
        # Para strings pequenas, mostra início e fim
        visible_start = visible_chars // 2
        visible_end = visible_chars // 2
        return data[:visible_start] + mask_char * 6 + data[-visible_end:]
    else:
        # Para strings maiores, mostra mais caracteres
        return data[:visible_chars] + mask_char * 6 + data[-visible_chars:]

def generate_license_reference(client_data: dict, license_key: Optional[str] = None) -> str:
    """
    Gera uma referência única baseada na chave de licença para mascaramento
    """
    if license_key:
        # Usar parte da chave de licença como referência
        return f"LIC-{license_key[:8].upper()}"
    
    # Fallback: gerar referência baseada em dados do cliente
    client_id = client_data.get('id', 'UNKNOWN')[:8]
    client_type = client_data.get('client_type', 'XX')
    return f"REF-{client_type.upper()}{client_id}"

def apply_data_masking(client_data: dict, user_role: str, license_reference: str) -> dict:
    """
    Aplica mascaramento baseado no role do usuário
    """
    # Roles que podem ver dados sensíveis
    privileged_roles = ['admin', 'super_admin', 'technical_lead']
    
    if user_role in privileged_roles:
        # Usuário privilegiado: dados reais
        return client_data
    
    # Usuário comum: dados mascarados
    masked_data = client_data.copy()
    
    if 'sensitive_data' in masked_data and masked_data['sensitive_data']:
        sensitive = masked_data['sensitive_data']
        
        # Mascarar campos sensíveis
        for field_name, field_value in sensitive.items():
            if isinstance(field_value, str) and field_value:
                if field_name in ['admin_password', 'service_password', 'wifi_password']:
                    # Senhas: mascaramento total com referência
                    masked_data['sensitive_data'][field_name] = f"[PROTEGIDO-{license_reference}]"
                elif field_name in ['internal_equipment_id', 'serial_number', 'mac_address', 'hardware_key']:
                    # IDs: mascaramento parcial
                    masked_data['sensitive_data'][field_name] = mask_sensitive_data(field_value)
                elif field_name in ['api_keys', 'recovery_codes', 'encryption_keys']:
                    # Arrays: mascarar conteúdo
                    if isinstance(field_value, list):
                        masked_data['sensitive_data'][field_name] = [f"[PROTEGIDO-{license_reference}-{i+1}]" for i in range(len(field_value))]
    
    return masked_data

# Import structured logging system  
from structured_logger import (
    structured_logger, auth_logger, data_logger, audit_logger,
    log_user_login, log_data_access, log_data_export, 
    log_permission_change, log_system_error, EventCategory
)
from logging_middleware import (
    StructuredLoggingMiddleware, PerformanceMonitoringMiddleware, 
    ErrorLoggingMiddleware
)

# Initialize structured logger with compatibility adapter
class MaintenanceLoggerAdapter:
    """Adapter for backward compatibility with old maintenance_logger calls"""
    
    def __init__(self, structured_logger):
        self._logger = structured_logger
    
    def _convert_category(self, module: str) -> EventCategory:
        """Convert old module names to EventCategory"""
        category_map = {
            "system": EventCategory.SYSTEM,
            "auth": EventCategory.AUTH, 
            "scheduler": EventCategory.SCHEDULER,
            "jobs": EventCategory.SCHEDULER,
            "health": EventCategory.HEALTH,
            "notifications": EventCategory.NOTIFICATION,
            "licenses": EventCategory.LICENSE,
            "clients": EventCategory.CLIENT,
            "rbac": EventCategory.RBAC,
            "security": EventCategory.SECURITY,
            "cleanup": EventCategory.SYSTEM,
            "whatsapp": EventCategory.NOTIFICATION,  # 🔧 Added WhatsApp mapping
            "whatsapp_status_check": EventCategory.NOTIFICATION,
            "whatsapp_qr_request": EventCategory.NOTIFICATION,
            "whatsapp_send_attempt": EventCategory.NOTIFICATION,
            "whatsapp_send_result": EventCategory.NOTIFICATION,
            "whatsapp_bulk_send_attempt": EventCategory.NOTIFICATION,
            "whatsapp_bulk_send_result": EventCategory.NOTIFICATION,
            "whatsapp_restart": EventCategory.NOTIFICATION,
            "whatsapp_renewal_sent": EventCategory.NOTIFICATION,
            "bulk_whatsapp_campaign": EventCategory.NOTIFICATION
        }
        return category_map.get(module, EventCategory.SYSTEM)
    
    def log(self, action: str, details: dict):
        """🔧 FIX: Added missing log() method for backward compatibility"""
        # Extract module from action if it contains underscores
        if "_" in action:
            module_parts = action.split("_")
            module = module_parts[0] if module_parts else "system"
        else:
            module = "system"
        
        self._logger.info(
            self._convert_category(action),
            action,
            f"{module}: {action}",
            details=details
        )
    
    def info(self, module: str, action: str, details: dict):
        """Compatibility method for info logs"""
        self._logger.info(
            self._convert_category(module),
            action,
            f"{module}: {action}",
            details=details
        )
    
    def error(self, module: str, action: str, details: dict, error_msg: str = None):
        """Compatibility method for error logs"""
        self._logger.error(
            self._convert_category(module),
            action,
            f"{module}: {action}" + (f" - {error_msg}" if error_msg else ""),
            details=details
        )
    
    def warning(self, module: str, action: str, details: dict):
        """Compatibility method for warning logs"""
        self._logger.warning(
            self._convert_category(module),
            action,
            f"{module}: {action}",
            details=details
        )
    
    def debug(self, module: str, action: str, details: dict):
        """Compatibility method for debug logs"""
        self._logger.debug(
            self._convert_category(module),
            action,
            f"{module}: {action}",
            details=details
        )

# Initialize with adapter
maintenance_logger = MaintenanceLoggerAdapter(structured_logger)

# Sistema de Prevenção de Duplicatas e Logs Avançados
import traceback
from datetime import datetime
from enum import Enum

class ErrorLevel(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"  
    WARNING = "WARNING"
    INFO = "INFO"

class ErrorCategory(str, Enum):
    DUPLICATE_DATA = "DUPLICATE_DATA"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    VALIDATION = "VALIDATION"
    SYSTEM = "SYSTEM"

# Log estruturado para monitoramento avançado
def log_advanced_error(level: ErrorLevel, category: ErrorCategory, message: str, 
                      user_email: str = None, details: dict = None, exception: Exception = None):
    timestamp = datetime.utcnow().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "level": level.value,
        "category": category.value,
        "message": message,
        "user_email": user_email,
        "details": details or {},
        "stack_trace": traceback.format_exc() if exception else None
    }
    
    # Log para arquivo específico baseado na categoria
    log_message = f"[{timestamp}] [{level.value}] [{category.value}] {message}"
    if user_email:
        log_message += f" | User: {user_email}"
    if details:
        log_message += f" | Details: {details}"
        
    # Escrever para maintenance_logger
    maintenance_logger.info("system", "tenant_operation", {"message": log_message, "details": details})
    
    # Se for CRITICAL, também alertar no console
    if level == ErrorLevel.CRITICAL:
        print(f"🚨 CRITICAL ERROR: {log_message}")
        
    return log_entry

# Verificação de duplicatas para usuários
async def check_user_duplicates(email: str, name: str = None, exclude_id: str = None, tenant_id: str = "default") -> dict:
    """
    Verifica duplicatas de usuários por email e opcionalmente por nome
    Retorna informações sobre duplicatas encontradas
    """
    try:
        # CRÍTICO: Usar tenant_id específico para isolamento
        query_filter = add_tenant_filter({}, tenant_id)
        
        # Verificar email duplicado
        email_query = {**query_filter, "email": email}
        if exclude_id:
            email_query["id"] = {"$ne": exclude_id}
            
        existing_user = await db.users.find_one(email_query)
        
        result = {
            "has_duplicates": False,
            "duplicate_email": None,
            "duplicate_name": None,
            "suggestions": []
        }
        
        if existing_user:
            result["has_duplicates"] = True
            result["duplicate_email"] = {
                "id": existing_user["id"],
                "email": existing_user["email"], 
                "name": existing_user["name"],
                "is_active": existing_user.get("is_active", False)
            }
            
            # Log da tentativa de duplicação
            log_advanced_error(
                ErrorLevel.WARNING,
                ErrorCategory.DUPLICATE_DATA,
                f"Tentativa de criar usuário com email duplicado: {email}",
                details={"existing_user_id": existing_user["id"], "existing_name": existing_user["name"]}
            )
            
            # Sugerir emails alternativos
            base_email = email.split('@')[0]
            domain = email.split('@')[1]
            result["suggestions"] = [
                f"{base_email}1@{domain}",
                f"{base_email}.new@{domain}",
                f"{base_email}_{datetime.now().strftime('%Y%m%d')}@{domain}"
            ]
        
        # Verificar nome similar (opcional)
        if name and not result["has_duplicates"]:
            name_query = {**query_filter, "name": {"$regex": f"^{name}$", "$options": "i"}}
            if exclude_id:
                name_query["id"] = {"$ne": exclude_id}
                
            similar_name = await db.users.find_one(name_query)
            if similar_name:
                result["duplicate_name"] = {
                    "id": similar_name["id"],
                    "email": similar_name["email"],
                    "name": similar_name["name"]
                }
                
        return result
        
    except Exception as e:
        log_advanced_error(
            ErrorLevel.ERROR,
            ErrorCategory.DATABASE,
            "Erro ao verificar duplicatas de usuário",
            details={"email": email, "name": name},
            exception=e
        )
        return {"has_duplicates": False, "error": str(e)}

# Verificação de duplicatas para roles
async def check_role_duplicates(name: str, exclude_id: str = None, tenant_id: str = "default") -> dict:
    """Verifica duplicatas de roles por nome"""
    try:
        # CRÍTICO: Usar tenant_id específico para isolamento
        query_filter = add_tenant_filter({"name": {"$regex": f"^{name}$", "$options": "i"}}, tenant_id)
        if exclude_id:
            query_filter["id"] = {"$ne": exclude_id}
            
        existing_role = await db.roles.find_one(query_filter)
        
        if existing_role:
            log_advanced_error(
                ErrorLevel.WARNING,
                ErrorCategory.DUPLICATE_DATA,
                f"Tentativa de criar role com nome duplicado: {name}",
                details={"existing_role_id": existing_role["id"]}
            )
            
            return {
                "has_duplicates": True,
                "existing_role": {
                    "id": existing_role["id"],
                    "name": existing_role["name"],
                    "is_system": existing_role.get("is_system", False)
                }
            }
            
        return {"has_duplicates": False}
        
    except Exception as e:
        log_advanced_error(
            ErrorLevel.ERROR,
            ErrorCategory.DATABASE,
            "Erro ao verificar duplicatas de role",
            details={"name": name},
            exception=e
        )
        return {"has_duplicates": False, "error": str(e)}

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# 🚀 PHASE 1 SECURITY IMPROVEMENTS - Use Pydantic Settings
# Replace manual environment variable loading with secure settings validation

# Validate production settings if needed
if settings.is_production:
    validate_production_settings()

# Use settings from secure configuration
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days

# Log security configuration (safe information only)  
structured_logger.info(
    EventCategory.SECURITY,
    "security_config_loaded",
    "Security configuration loaded",
    details=get_security_info()
)

# Redis Configuration for Refresh Tokens
REDIS_URL = settings.redis_url
redis_client = None

# Initialize Redis connection for refresh tokens
async def init_redis():
    global redis_client
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        print("✅ Redis connected successfully for refresh tokens")
    except ImportError:
        print("⚠️ Redis not available - installing redis package")
        import subprocess
        subprocess.run(["pip", "install", "redis"], check=True)
        import redis.asyncio as redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        print("✅ Redis installed and connected successfully")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("⚠️ Falling back to in-memory store (not recommended for production)")
        redis_client = None

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MongoDB connection with timeout and keepalive settings
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=5000,  # 5 seconds timeout for server selection
    connectTimeoutMS=10000,         # 10 seconds connection timeout
    socketTimeoutMS=60000,          # 60 seconds socket timeout
    maxPoolSize=10,                 # Maximum 10 connections in pool
    minPoolSize=1,                  # Minimum 1 connection in pool
    maxIdleTimeMS=300000,           # 5 minutes max idle time (300000ms)
    heartbeatFrequencyMS=10000      # Heartbeat every 10 seconds
)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="License Management System", version="1.0.0")

# Tenant Isolation Middleware
class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Limpar contexto anterior
        tenant_context.clear()
        
        # Extrair tenant_id do header, subdomain ou token JWT
        tenant_id = None
        is_super_admin_user = False
        
        # 1. Tentar obter tenant do header X-Tenant-ID
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # 2. Se não encontrou, tentar obter do token JWT
        if not tenant_id:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    token = auth_header.split(" ")[1]
                    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                    user_email = payload.get("sub")
                    
                    # Buscar usuário no banco para obter tenant_id
                    if user_email:
                        user_doc = await db.users.find_one({"email": user_email})
                        if user_doc:
                            tenant_id = user_doc.get("tenant_id")
                            # Verificar se é super admin (pode acessar todos os tenants)
                            is_super_admin_user = user_doc.get("role") == "super_admin"
                except:
                    pass  # Token inválido ou erro de decode
        
        # 3. Para endpoints públicos ou de sistema, usar tenant padrão
        public_endpoints = ["/docs", "/openapi.json", "/health", "/"]
        if request.url.path in public_endpoints:
            tenant_id = "system"
        
        # Se ainda não encontrou tenant_id, usar tenant padrão para compatibilidade
        if not tenant_id:
            tenant_id = "default"
        
        # Configurar contexto do tenant
        tenant_context.set_tenant(
            tenant_id=tenant_id, 
            is_super_admin=is_super_admin_user
        )
        
        # Processar request
        response = await call_next(request)
        
        # Adicionar header com tenant atual na resposta
        response.headers["X-Current-Tenant"] = tenant_id
        
        return response

# Adicionar middleware à aplicação
app.add_middleware(TenantMiddleware)

# Create API router
api_router = APIRouter(prefix="/api")

# Enums
# RBAC Models - Sistema de Controle de Acesso Baseado em Papéis
class Permission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # ex: "users.create", "licenses.read", "reports.delete"
    description: str  # Descrição amigável da permissão
    resource: str  # Recurso que a permissão afeta (users, licenses, clients, etc)
    action: str  # Ação permitida (create, read, update, delete, manage)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Role(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # ex: "Admin", "Manager", "Viewer", "Sales"
    description: str  # Descrição do papel
    permissions: List[str] = []  # Lista de IDs de permissões
    is_system: bool = False  # True para roles do sistema (não editáveis)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Estender o modelo User existente com RBAC
class UserRBACInfo(BaseModel):
    roles: List[str] = []  # Lista de IDs de roles
    direct_permissions: List[str] = []  # Permissões diretas (além das do role)
    is_active: bool = True  # Flag para ativar/desativar usuário
    last_permission_update: datetime = Field(default_factory=datetime.utcnow)

# Request models para RBAC
class AssignRoleRequest(BaseModel):
    user_id: str
    role_ids: List[str]

class AssignPermissionRequest(BaseModel):
    user_id: str
    permission_ids: List[str]

class CreateRoleRequest(BaseModel):
    name: str
    description: str
    permissions: List[str] = []

class UpdateRoleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None  
    permissions: Optional[List[str]] = None

# Verificador de permissões
def check_permission(user_permissions: List[str], required_permission: str) -> bool:
    """
    Verifica se o usuário tem a permissão necessária
    Suporta wildcards: 'users.*' permite 'users.create', 'users.read', etc.
    """
    if not required_permission:
        return True
        
    # Verificar permissão exata
    if required_permission in user_permissions:
        return True
    
    # Verificar wildcards
    resource, action = required_permission.split('.', 1) if '.' in required_permission else (required_permission, '')
    
    for perm in user_permissions:
        if perm.endswith('.*'):  # Permissão wildcard
            perm_resource = perm[:-2]  # Remove '.*'
            if resource == perm_resource:
                return True
        elif perm == f"{resource}.*":  # Todas ações no recurso
            return True
        elif perm == "*":  # Super admin
            return True
    
    return False

# Dependency para verificar permissões
def require_permission(permission: str):
    async def permission_checker(current_user: User = Depends(get_current_user)):
        # RBAC deve considerar o tenant do usuário
        user_permissions = await get_user_permissions(current_user.email, current_user.tenant_id)
        if not check_permission(user_permissions, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Permission required: {permission}")
        return current_user
    return permission_checker

async def get_user_permissions(user_email: str, tenant_id: str = "default") -> List[str]:
    """
    Busca todas as permissões do usuário (roles + diretas)
    """
    # CRÍTICO: Adicionar filtro de tenant para busca de usuário
    user_filter = add_tenant_filter({"email": user_email}, tenant_id)
    user_doc = await db.users.find_one(user_filter)
    if not user_doc:
        return []
    
    all_permissions = set()
    
    # Permissões diretas
    rbac_info = user_doc.get('rbac', {})
    direct_permissions = rbac_info.get('direct_permissions', [])
    all_permissions.update(direct_permissions)
    
    # Permissões dos roles
    role_ids = rbac_info.get('roles', [])
    if role_ids:
        # CRÍTICO: Adicionar filtro de tenant para busca de roles
        roles_filter = add_tenant_filter({"id": {"$in": role_ids}}, tenant_id)
        roles = await db.roles.find(roles_filter).to_list(1000)
        for role in roles:
            role_permissions = role.get('permissions', [])
            # Buscar permissões por ID
            if role_permissions:
                # CRÍTICO: Adicionar filtro de tenant para busca de permissões
                permissions_filter = add_tenant_filter({"id": {"$in": role_permissions}}, tenant_id)
                permissions = await db.permissions.find(permissions_filter).to_list(1000)
                permission_names = [p.get('name') for p in permissions]
                all_permissions.update(permission_names)
    
    return list(all_permissions)

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"

class LicenseStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CANCELLED = "cancelled"

class ClientType(str, Enum):
    PF = "pf"  # Pessoa Física
    PJ = "pj"  # Pessoa Jurídica

class ClientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_VERIFICATION = "pending_verification"
    BLOCKED = "blocked"

class ContactPreference(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    WHATSAPP = "whatsapp"

class OriginChannel(str, Enum):
    WEBSITE = "website"
    WHATSAPP = "whatsapp"
    PARTNER = "partner"
    REFERRAL = "referral"
    PHONE = "phone"
    EMAIL = "email"

class TaxRegime(str, Enum):
    MEI = "mei"
    SIMPLES = "simples"
    LUCRO_PRESUMIDO = "lucro_presumido"
    LUCRO_REAL = "lucro_real"

class CompanySize(str, Enum):
    MEI = "mei"
    ME = "me"  # Microempresa
    EPP = "epp"  # Empresa de Pequeno Porte
    MEDIO = "medio"
    GRANDE = "grande"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    BOLETO = "boleto"
    PIX = "pix"
    BANK_TRANSFER = "bank_transfer"

class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"

class RemoteAccessType(str, Enum):
    TEAMVIEWER = "teamviewer"
    ANYDESK = "anydesk"
    CHROME_REMOTE = "chrome_remote"
    WINDOWS_REMOTE = "windows_remote"
    VNC = "vnc"
    OTHER = "other"

# Base Models with Multi-tenancy support
class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="ID do tenant proprietário dos dados")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

# Address Model
class Address(BaseModel):
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    municipio: Optional[str] = None
    uf: Optional[str] = None
    pais: str = "Brasil"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# Contact Model
class Contact(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

# LGPD Consent Model
class LGPDConsent(BaseModel):
    finalidade: str
    base_legal: str
    consentimento_timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    terms_version: Optional[str] = None
    privacy_policy_accepted: bool = False
    marketing_opt_in: bool = False
    marketing_channels: List[str] = []

# Document Model
class Document(BaseModel):
    type: str  # "cpf", "cnpj", "rg", "ie", "im", etc.
    number: str
    issuer: Optional[str] = None
    uf: Optional[str] = None
    file_url: Optional[str] = None

# Remote Access Info
# Sensitive Data Model - Dados Sensíveis Mascaráveis
class SensitiveEquipmentData(BaseModel):
    # IDs e números confidenciais
    internal_equipment_id: Optional[str] = None  # ID interno confidencial
    serial_number: Optional[str] = None  # Número de série
    mac_address: Optional[str] = None  # Endereço MAC
    hardware_key: Optional[str] = None  # Chave de hardware
    
    # Credenciais de acesso
    admin_username: Optional[str] = None  # Usuário administrador
    admin_password: Optional[str] = None  # Senha administrador
    service_password: Optional[str] = None  # Senha de serviço
    wifi_password: Optional[str] = None  # Senha WiFi
    
    # Outros dados sensíveis
    security_questions: Optional[Dict[str, str]] = None  # Perguntas de segurança
    recovery_codes: Optional[List[str]] = None  # Códigos de recuperação
    api_keys: Optional[List[str]] = None  # Chaves de API
    encryption_keys: Optional[List[str]] = None  # Chaves de criptografia
    
    # Configurações de acesso
    vpn_config: Optional[str] = None  # Configuração VPN
    network_settings: Optional[Dict[str, str]] = None  # Configurações de rede
    
    # Metadados de segurança
    data_classification: str = "confidential"  # Classificação dos dados
    access_level: str = "admin_only"  # Nível de acesso necessário
    last_updated: Optional[datetime] = None
    updated_by: Optional[str] = None

class RemoteAccessInfo(BaseModel):
    system_type: RemoteAccessType
    access_id: Optional[str] = None  # TeamViewer ID, AnyDesk ID, etc.
    is_host: bool = False
    last_analyst: Optional[str] = None
    last_access: Optional[datetime] = None

# License Info Model
class LicenseInfo(BaseModel):
    plan_type: Optional[str] = None
    license_quantity: int = 1
    equipment_brand: Optional[str] = None
    equipment_model: Optional[str] = None
    equipment_id: Optional[str] = None  # ID interno do equipamento
    equipment_serial: Optional[str] = None  # Número de série
    authorized_serials: List[str] = []
    activation_keys: List[str] = []
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    billing_day: int = 1
    payment_method: PaymentMethod = PaymentMethod.BOLETO
    nfe_email: Optional[EmailStr] = None

# Verification Controls
class VerificationControls(BaseModel):
    document_status: str = "pending"  # valid, invalid, pending
    address_status: str = "pending"
    risk_score: Optional[int] = None
    is_blocked: bool = False
    blocked_reason: Optional[str] = None
    blocked_date: Optional[datetime] = None

# Client Base Model
class ClientBase(BaseModel):
    client_type: ClientType
    status: ClientStatus = ClientStatus.ACTIVE
    origin_channel: Optional[OriginChannel] = None
    email_principal: EmailStr
    telefone: Optional[str] = None
    celular: Optional[str] = None
    whatsapp: Optional[str] = None
    contact_preference: ContactPreference = ContactPreference.EMAIL
    
    # Address
    address: Optional[Address] = None
    
    # Contacts
    billing_contact: Optional[Contact] = None
    technical_contact: Optional[Contact] = None
    
    # LGPD
    lgpd_consent: Optional[LGPDConsent] = None
    
    # Internal notes
    internal_notes: Optional[str] = None
    
    # License info
    license_info: Optional[LicenseInfo] = None
    
    # Remote access
    remote_access: Optional[RemoteAccessInfo] = None
    
    # Sensitive data (dados mascaráveis)
    sensitive_data: Optional[SensitiveEquipmentData] = None
    
    # Verification
    verification: Optional[VerificationControls] = None

# Pessoa Física Model
class PessoaFisicaBase(ClientBase):
    client_type: Literal[ClientType.PF] = ClientType.PF
    nome_completo: str
    cpf: str
    rg_numero: Optional[str] = None
    rg_orgao_emissor: Optional[str] = None
    rg_uf: Optional[str] = None
    data_nascimento: Optional[date] = None
    nacionalidade: str = "Brasileira"
    nome_mae: Optional[str] = None
    profissao: Optional[str] = None
    
    @validator('cpf')
    def validate_cpf(cls, v):
        # Remove formatting
        cpf = re.sub(r'[^0-9]', '', v)
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        return cpf

class PessoaFisicaCreate(PessoaFisicaBase):
    pass

class PessoaFisica(PessoaFisicaBase, BaseEntity):
    pass

class PessoaFisicaUpdate(BaseModel):
    status: Optional[ClientStatus] = None
    origin_channel: Optional[OriginChannel] = None
    email_principal: Optional[EmailStr] = None
    telefone: Optional[str] = None
    celular: Optional[str] = None
    whatsapp: Optional[str] = None
    contact_preference: Optional[ContactPreference] = None
    nome_completo: Optional[str] = None
    rg_numero: Optional[str] = None
    rg_orgao_emissor: Optional[str] = None
    rg_uf: Optional[str] = None
    data_nascimento: Optional[date] = None
    nacionalidade: Optional[str] = None
    nome_mae: Optional[str] = None
    profissao: Optional[str] = None
    address: Optional[Address] = None
    billing_contact: Optional[Contact] = None
    technical_contact: Optional[Contact] = None
    internal_notes: Optional[str] = None
    license_info: Optional[LicenseInfo] = None
    remote_access: Optional[RemoteAccessInfo] = None

# Branch Model for Filiais
class Filial(BaseModel):
    cnpj_filial: str
    ordem: str  # Ordem da filial (001, 002, etc.)
    nome_fantasia: Optional[str] = None
    endereco: Address
    is_active: bool = True

# Digital Certificate Model
class CertificadoDigital(BaseModel):
    tipo: Optional[str] = None  # A1, A3
    numero_serie: Optional[str] = None
    emissor: Optional[str] = None
    validade: Optional[date] = None
    
# Corporate Documents Model
class DocumentosSocietarios(BaseModel):
    contrato_social_url: Optional[str] = None
    estatuto_social_url: Optional[str] = None
    ultima_alteracao_url: Optional[str] = None
    ultima_alteracao_data: Optional[date] = None
    observacoes: Optional[str] = None

# Local Registrations Model
class InscricoesLocais(BaseModel):
    numero: str
    municipio: str
    tipo: Optional[str] = None  # Alvará, licença, etc.
    validade: Optional[date] = None

# Pessoa Jurídica Model
class PessoaJuridicaBase(ClientBase):
    client_type: Literal[ClientType.PJ] = ClientType.PJ
    # Documento CNPJ com formato informado e normalizado
    cnpj: str
    cnpj_formato_informado: Optional[str] = None  # Como o usuário digitou
    cnpj_normalizado: str  # Formato padronizado para busca
    
    razao_social: str
    nome_fantasia: Optional[str] = None
    data_abertura: Optional[date] = None
    natureza_juridica: Optional[str] = None
    cnae_principal: Optional[str] = None
    cnaes_secundarios: List[str] = []
    regime_tributario: Optional[TaxRegime] = None
    porte_empresa: Optional[CompanySize] = None
    
    # Inscrições Estaduais
    inscricao_estadual: Optional[str] = None
    ie_situacao: Optional[str] = None  # contribuinte, isento, nao_obrigado
    ie_uf: Optional[str] = None
    
    # Inscrição Municipal
    inscricao_municipal: Optional[str] = None
    inscricao_municipal_ccm: Optional[str] = None  # CCM específico
    
    # Inscrições e Alvarás Locais
    inscricoes_locais: List[InscricoesLocais] = []
    
    # Endereços estruturados
    endereco_matriz: Optional[Address] = None
    filiais: List[Filial] = []  # Lista estruturada de filiais
    
    # Representantes legais
    responsavel_legal_nome: Optional[str] = None
    responsavel_legal_cpf: Optional[str] = None
    responsavel_legal_email: Optional[EmailStr] = None
    responsavel_legal_telefone: Optional[str] = None
    
    # Procurador/Representante
    procurador_nome: Optional[str] = None
    procurador_cpf: Optional[str] = None
    procurador_contato: Optional[str] = None
    procurador_email: Optional[EmailStr] = None
    procurador_telefone: Optional[str] = None
    procuracao_validade: Optional[date] = None
    procuracao_numero: Optional[str] = None
    
    # Certificado Digital para integrações fiscais
    certificado_digital: Optional[CertificadoDigital] = None
    
    # Documentos Societários
    documentos_societarios: Optional[DocumentosSocietarios] = None
    
    # NFe/NFSe (mantendo campos existentes)
    municipio_emissor_nfse: Optional[str] = None
    codigo_servico_lc: Optional[str] = None
    aliquota_iss: Optional[float] = None
    serie_nfse: Optional[str] = None
    
    @validator('cnpj')
    def validate_cnpj(cls, v):
        if v:
            # Remove formatting - prepare for future alphanumeric CNPJ
            normalized = re.sub(r'[^0-9A-Za-z]', '', str(v).upper())
            if len(normalized) != 14:
                raise ValueError('CNPJ deve ter 14 caracteres')
            return normalized
        return v
    
    def __init__(self, **data):
        if 'cnpj' in data and data['cnpj']:
            # Store original format before validation
            data['cnpj_formato_informado'] = data['cnpj']
            # Normalize for storage
            normalized = re.sub(r'[^0-9A-Za-z]', '', str(data['cnpj']).upper())
            data['cnpj_normalizado'] = normalized
            data['cnpj'] = normalized
        super().__init__(**data)

class PessoaJuridicaCreate(PessoaJuridicaBase):
    pass

class PessoaJuridica(PessoaJuridicaBase, BaseEntity):
    pass

class PessoaJuridicaUpdate(BaseModel):
    status: Optional[ClientStatus] = None
    origin_channel: Optional[OriginChannel] = None
    email_principal: Optional[EmailStr] = None
    telefone: Optional[str] = None
    celular: Optional[str] = None
    whatsapp: Optional[str] = None
    contact_preference: Optional[ContactPreference] = None
    # CNPJ com formatos
    cnpj: Optional[str] = None
    cnpj_formato_informado: Optional[str] = None
    cnpj_normalizado: Optional[str] = None
    # Dados da empresa
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    data_abertura: Optional[date] = None
    natureza_juridica: Optional[str] = None
    cnae_principal: Optional[str] = None
    cnaes_secundarios: Optional[List[str]] = None
    regime_tributario: Optional[TaxRegime] = None
    porte_empresa: Optional[CompanySize] = None
    # Inscrições
    inscricao_estadual: Optional[str] = None
    ie_situacao: Optional[str] = None
    ie_uf: Optional[str] = None
    inscricao_municipal: Optional[str] = None
    inscricao_municipal_ccm: Optional[str] = None
    inscricoes_locais: Optional[List[InscricoesLocais]] = None
    # Endereços
    endereco_matriz: Optional[Address] = None
    filiais: Optional[List[Filial]] = None
    # Representantes
    responsavel_legal_nome: Optional[str] = None
    responsavel_legal_cpf: Optional[str] = None
    responsavel_legal_email: Optional[EmailStr] = None
    responsavel_legal_telefone: Optional[str] = None
    # Procurador
    procurador_nome: Optional[str] = None
    procurador_cpf: Optional[str] = None
    procurador_contato: Optional[str] = None
    procurador_email: Optional[EmailStr] = None
    procurador_telefone: Optional[str] = None
    procuracao_validade: Optional[date] = None
    procuracao_numero: Optional[str] = None
    # Certificado digital
    certificado_digital: Optional[CertificadoDigital] = None
    # Documentos societários
    documentos_societarios: Optional[DocumentosSocietarios] = None
    # Outros campos
    internal_notes: Optional[str] = None
    license_info: Optional[LicenseInfo] = None
    remote_access: Optional[RemoteAccessInfo] = None

# User Models (keeping existing)
class UserBase(BaseModel):
    email: str
    name: Optional[str] = "User"  # Made optional for legacy data compatibility
    role: UserRole = UserRole.USER
    
    @validator('role', pre=True)
    def normalize_role(cls, v):
        """Normalize role to lowercase for compatibility with legacy data"""
        if isinstance(v, str):
            return v.lower()
        return v
    
    @validator('name', pre=True)
    def normalize_name(cls, v):
        """Provide default name for legacy data without name field"""
        if v is None or v == "":
            return "User"
        return v

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    email: str
    password: str

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="ID do tenant do usuário")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    last_login: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Category Models (keeping existing)
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#3B82F6"
    icon: Optional[str] = "folder"

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase, BaseEntity):
    is_active: bool = True

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None

# Product Models (keeping existing)
class ProductBase(BaseModel):
    name: str
    version: Optional[str] = "1.0"
    description: Optional[str] = None
    category_id: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "BRL"
    features: List[str] = []
    requirements: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase, BaseEntity):
    is_active: bool = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    features: Optional[List[str]] = None
    requirements: Optional[str] = None
    is_active: Optional[bool] = None

# License Plan Models (keeping existing)
class LicensePlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    max_users: int = 1
    duration_days: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = "BRL"
    features: List[str] = []
    restrictions: List[str] = []

class LicensePlanCreate(LicensePlanBase):
    pass

class LicensePlan(LicensePlanBase, BaseEntity):
    pass

class LicensePlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_users: Optional[int] = None
    duration_days: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    features: Optional[List[str]] = None
    restrictions: Optional[List[str]] = None
    is_active: Optional[bool] = None

# Enhanced License Models (updated to use new client system)
class LicenseBase(BaseModel):
    name: str
    description: Optional[str] = None
    max_users: int = 1
    expires_at: Optional[datetime] = None
    features: List[str] = []
    category_id: Optional[str] = None
    client_pf_id: Optional[str] = None  # Link to Pessoa Física
    client_pj_id: Optional[str] = None  # Link to Pessoa Jurídica
    product_id: Optional[str] = None
    plan_id: Optional[str] = None

class LicenseCreate(LicenseBase):
    assigned_user_id: Optional[str] = None

class License(LicenseBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    license_key: str = Field(default_factory=lambda: f"LIC-{uuid.uuid4().hex[:16].upper()}")
    status: LicenseStatus = LicenseStatus.PENDING
    assigned_user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str

class LicenseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[LicenseStatus] = None
    max_users: Optional[int] = None
    expires_at: Optional[datetime] = None
    assigned_user_id: Optional[str] = None
    features: Optional[List[str]] = None
    category_id: Optional[str] = None
    client_pf_id: Optional[str] = None
    client_pj_id: Optional[str] = None
    product_id: Optional[str] = None
    plan_id: Optional[str] = None

# Utility Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: str, tenant_id: str) -> str:
    """Create a refresh token with JTI for revocation"""
    jti = str(uuid.uuid4())  # Unique token ID for revocation
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "jti": jti,
        "type": "refresh",
        "exp": expire
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def store_refresh_token(jti: str, user_id: str, tenant_id: str, ttl_seconds: int = None):
    """Store refresh token in Redis with TTL"""
    if not ttl_seconds:
        ttl_seconds = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    
    token_data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "created_at": datetime.utcnow().isoformat(),
        "active": "true"  # Redis requires string values
    }
    
    if redis_client:
        try:
            await redis_client.hset(f"refresh_token:{jti}", mapping=token_data)
            await redis_client.expire(f"refresh_token:{jti}", ttl_seconds)
            return True
        except Exception as e:
            print(f"❌ Failed to store refresh token: {e}")
            return False
    else:
        # Fallback to in-memory storage (not recommended for production)
        if not hasattr(store_refresh_token, "_memory_store"):
            store_refresh_token._memory_store = {}
        store_refresh_token._memory_store[jti] = token_data
        return True

async def verify_refresh_token(refresh_token: str) -> Optional[dict]:
    """Verify and decode refresh token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            return None
            
        jti = payload.get("jti")
        if not jti:
            return None
        
        # Check if token exists and is active in store
        if redis_client:
            try:
                token_data = await redis_client.hgetall(f"refresh_token:{jti}")
                if not token_data or token_data.get("active") != "true":
                    return None
            except Exception as e:
                print(f"❌ Failed to verify refresh token: {e}")
                return None
        else:
            # Fallback to in-memory storage
            memory_store = getattr(store_refresh_token, "_memory_store", {})
            if jti not in memory_store or not memory_store[jti].get("active"):
                return None
        
        return payload
        
    except jwt.JWTError:
        return None

async def revoke_refresh_token(jti: str):
    """Revoke a refresh token"""
    if redis_client:
        try:
            await redis_client.hset(f"refresh_token:{jti}", "active", "false")
            return True
        except Exception as e:
            print(f"❌ Failed to revoke refresh token: {e}")
            return False
    else:
        # Fallback to in-memory storage
        memory_store = getattr(store_refresh_token, "_memory_store", {})
        if jti in memory_store:
            memory_store[jti]["active"] = False
        return True

async def get_current_user(request: Request):
    """🔐 Get current user from HttpOnly cookie (more secure than Authorization header)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    
    # Try to get token from HttpOnly cookie first (preferred)
    token = request.cookies.get("access_token")
    
    # Fallback to Authorization header for API compatibility
    if not token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    
    # CRÍTICO: Usar tenant_id do token para buscar usuário
    tenant_id = payload.get("tenant_id", "default")
    user_filter = add_tenant_filter({"email": email}, tenant_id)
    user = await db.users.find_one(user_filter)
    
    if user is None:
        raise credentials_exception
    
    # MIGRAÇÃO AUTOMÁTICA: Adicionar tenant_id se não existe
    if "tenant_id" not in user or not user["tenant_id"]:
        # Migrar usuário para tenant padrão
        await db.users.update_one(
            {"email": email},
            {"$set": {"tenant_id": "default"}}
        )
        user["tenant_id"] = "default"
        logger.info(f"User {email} migrated to default tenant")
    
    return User(**user)

async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    # Allow both admin and super_admin roles
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Authentication Routes (keeping existing)
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user already exists globally (not filtered by tenant)
    # NOTA: Esta verificação deve ser global para evitar emails duplicados
    # mas vou usar um filtro vazio com tenant "global" para consistência
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create a new tenant for the user
    tenant_id = str(uuid.uuid4())
    
    # Extract company name from email domain or use user name
    email_domain = user_data.email.split("@")[1] if "@" in user_data.email else "user"
    company_name = email_domain.split(".")[0].title() if "." in email_domain else email_domain.title()
    
    # Create tenant data
    tenant_data = {
        "id": tenant_id,
        "name": f"{company_name} - {user_data.name}",
        "subdomain": f"user-{tenant_id[:8]}",
        "contact_email": user_data.email,
        "status": "active",
        "plan": "free",
        "max_users": 2,
        "max_licenses": 50,
        "max_clients": 25,
        "custom_logo_url": None,
        "primary_color": "#3B82F6",
        "company_name": company_name,
        "timezone": "America/Sao_Paulo",
        "locale": "pt_BR",
        "currency": "BRL",
        "features": {
            "api_access": False,
            "webhooks": False,
            "advanced_reports": False,
            "white_label": False,
            "priority_support": False,
            "audit_logs": False,
            "sso": False
        },
        "billing_info": {
            "plan_start_date": datetime.utcnow().isoformat(),
            "next_billing_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "trial_expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Insert new tenant
    await db.tenants.insert_one(tenant_data)
    
    # Create user with the new tenant_id
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict(exclude={"password"})
    user_dict["password_hash"] = hashed_password
    user_dict["tenant_id"] = tenant_id
    user_dict["role"] = "admin"  # First user in tenant is admin
    
    user = User(**user_dict)
    # CRÍTICO: Garantir tenant_id no documento antes de inserir
    user_dict_with_tenant = add_tenant_to_document(user.dict(), tenant_id)
    await db.users.insert_one(user_dict_with_tenant)
    
    return user

@api_router.post("/auth/login")
async def login(user_credentials: UserLogin, response: Response):
    # CRÍTICO: Para login, buscar usuário em qualquer tenant
    user_doc = None
    
    # Estratégia: buscar diretamente por email sem filtro de tenant
    # Isso permite login de usuários de qualquer tenant
    user_doc = await db.users.find_one({"email": user_credentials.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Security: Require password_hash to exist (no unsafe migration)
    if "password_hash" not in user_doc or not user_doc["password_hash"]:
        logger.warning(f"User {user_credentials.email} missing password_hash - login blocked")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account requires password reset. Please contact administrator."
        )
    
    if not verify_password(user_credentials.password, user_doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # CRÍTICO: Adicionar filtro de tenant para atualização do último login
    user_tenant_id = user_doc.get("tenant_id", "default")
    login_filter = add_tenant_filter({"email": user_credentials.email}, user_tenant_id)
    await db.users.update_one(
        login_filter,
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # 🔐 SECURITY UPGRADE: Create short-lived access token + long-lived refresh token
    access_token = create_access_token(
        data={
            "sub": user_credentials.email,
            "tenant_id": user_tenant_id,
            "role": user_doc.get("role", "user")
        }, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Create refresh token with unique JTI
    refresh_token = create_refresh_token(user_credentials.email, user_tenant_id)
    
    # Store refresh token in Redis
    refresh_payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    jti = refresh_payload.get("jti")
    await store_refresh_token(jti, user_credentials.email, user_tenant_id)
    
    # 🍪 SECURITY: Set HttpOnly cookies (no localStorage exposure to XSS)
    is_secure = os.getenv("HTTPS_ENABLED", "false").lower() == "true"
    
    # Access token cookie (short-lived)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    
    # Refresh token cookie (long-lived, more secure)
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",  # 🔐 Changed from "strict" to "lax" for better cross-origin compatibility
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/api/auth"  # Only sent to auth endpoints
    )
    
    user = User(**user_doc)
    return {
        "success": True,
        "message": "Login successful",
        "user": user,
        "token_expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@api_router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    """🔄 Refresh access token using HttpOnly refresh token"""
    
    # Get refresh token from HttpOnly cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    # Verify refresh token
    payload = await verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_email = payload.get("sub")
    tenant_id = payload.get("tenant_id", "default")
    old_jti = payload.get("jti")
    
    # Get user data for role
    user_filter = add_tenant_filter({"email": user_email}, tenant_id)
    user_doc = await db.users.find_one(user_filter)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # 🔄 SECURITY: Rotate refresh token (revoke old, create new)
    await revoke_refresh_token(old_jti)
    
    # Create new tokens
    new_access_token = create_access_token(
        data={
            "sub": user_email,
            "tenant_id": tenant_id,
            "role": user_doc.get("role", "user")
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    new_refresh_token = create_refresh_token(user_email, tenant_id)
    
    # Store new refresh token
    new_refresh_payload = jwt.decode(new_refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    new_jti = new_refresh_payload.get("jti")
    await store_refresh_token(new_jti, user_email, tenant_id)
    
    # Set new cookies
    is_secure = os.getenv("HTTPS_ENABLED", "false").lower() == "true"
    
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",  # 🔐 Changed from "strict" to "lax" for better cross-origin compatibility
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/api/auth"
    )
    
    return {
        "success": True,
        "message": "Token refreshed successfully",
        "token_expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """🚪 Logout user and revoke refresh token"""
    
    # Get refresh token to revoke it
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            if jti:
                await revoke_refresh_token(jti)
        except jwt.JWTError:
            pass  # Token already invalid
    
    # Clear cookies
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth")
    
    return {"success": True, "message": "Logged out successfully"}

# Initialize System - Create default data on first run
async def initialize_system():
    """Inicializa dados padrão do sistema se não existirem"""
    try:
        # Verificar se já existe um super admin
        super_admin = await db.users.find_one({"role": "super_admin"})
        if not super_admin:
            # Security: Require INITIAL_SUPERADMIN_PASSWORD for first boot
            initial_password = os.getenv("INITIAL_SUPERADMIN_PASSWORD")
            if not initial_password:
                logger.warning("INITIAL_SUPERADMIN_PASSWORD not set - skipping superadmin creation for security")
                logger.info("To create superadmin: set INITIAL_SUPERADMIN_PASSWORD environment variable and restart")
            else:
                # Criar super admin com senha da variável de ambiente
                super_admin_data = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": "system",  # Super admin é do tenant system
                    "email": "superadmin@autotech.com",
                    "name": "Super Administrator",
                    "role": "super_admin",
                    "is_active": True,
                    "require_password_reset": True,  # Force password reset on first login
                    "created_at": datetime.utcnow(),
                    "password_hash": get_password_hash(initial_password)
                }
                # CRÍTICO: Garantir tenant_id no documento do super admin
                super_admin_with_tenant = add_tenant_to_document(super_admin_data, "system")
                await db.users.insert_one(super_admin_with_tenant)
                logger.info("Super admin created: superadmin@autotech.com (password reset required)")
                logger.warning("SECURITY: Set new password on first login!")
        
        # Criar tenant padrão se não existir
        default_tenant = await db.tenants.find_one({"id": "default"})
        if not default_tenant:
            tenant_data = {
                "id": "default",
                "name": "AutoTech Services - Sistema Principal",
                "subdomain": "autotech",
                "contact_email": "admin@autotech.com",
                "status": TenantStatus.ACTIVE,
                "plan": TenantPlan.ENTERPRISE,
                "max_users": -1,  # Ilimitado
                "max_licenses": -1,  # Ilimitado
                "max_clients": -1,  # Ilimitado
                "features": get_plan_config(TenantPlan.ENTERPRISE)["features"],
                "created_at": datetime.utcnow(),
                "is_active": True,
                "current_users": 0,
                "current_licenses": 0,
                "current_clients": 0
            }
            await db.tenants.insert_one(tenant_data)
            logger.info("Tenant padrão criado: default (AutoTech Services)")
            
        logger.info("Sistema inicializado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar sistema: {e}")

# Executar inicialização na startup
import asyncio
@app.on_event("startup")
async def startup_event():
    # 🔐 Initialize Redis for refresh tokens
    await init_redis()
    
    # 🚀 SUB-FASE 2.2 - Initialize Redis Cache Manager
    try:
        from redis_cache_system import cache_manager
        from settings import settings
        
        if cache_manager is None:
            # Import the class and create instance
            from redis_cache_system import RedisCacheManager
            import redis_cache_system
            
            # Create and connect cache manager with database
            redis_cache_system.cache_manager = RedisCacheManager(settings.redis_url, db)
            await redis_cache_system.cache_manager.connect()
            
            logger.info("🚀 Redis Cache Manager initialized successfully")
        
    except Exception as e:
        logger.warning(f"🚀 Redis Cache Manager initialization failed: {str(e)}")
        logger.warning("🚀 Cache system will use fallback mode")
    
    await initialize_system()
    
    # Desabilitar seed/demo fora de desenvolvimento
    app_env = os.getenv("APP_ENV", os.getenv("ENV", "development")).lower()
    seed_demo = os.getenv("SEED_DEMO", "false").lower() in {"1", "true", "yes"}
    if app_env not in {"dev", "development"} and seed_demo:
        # Apenas alerta em runtime; a recomendação é remover a flag do env de prod.
        print("[warn] SEED_DEMO está habilitado, mas o APP_ENV não é desenvolvimento. Ignorando seed.")
        os.environ["SEED_DEMO"] = "false"

    # Sinaliza header padronizado no app (para debug/observabilidade)
    app.state.TENANT_HEADER = TENANT_HEADER

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# System Stats Endpoint
class SystemStats(BaseModel):
    total_users: int
    total_licenses: int
    total_clients: int
    total_categories: int
    total_products: int
    active_users: int
    expired_licenses: int
    pending_licenses: int
    system_status: str = "operational"

# Structured Logs Viewer Endpoint
@api_router.get("/logs/structured")
async def get_structured_logs(
    limit: int = 50,
    level: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get structured logs with filtering"""
    try:
        import json
        
        logs = []
        
        # Read structured logs file
        try:
            with open('/app/structured_logs.json', 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            log_entry = json.loads(line)
                            
                            # Apply filters
                            if level and log_entry.get('level') != level.upper():
                                continue
                            if category and log_entry.get('category') != category.lower():
                                continue
                            
                            logs.append(log_entry)
                            
                            if len(logs) >= limit:
                                break
                                
                        except json.JSONDecodeError:
                            continue
        
        except FileNotFoundError:
            logs = []
        
        # Reverse to get most recent first
        logs.reverse()
        
        return {
            "total_logs": len(logs),
            "limit": limit,
            "filters": {"level": level, "category": category},
            "logs": logs[:limit]
        }
        
    except Exception as e:
        logger.error(f"Error reading structured logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")

# Audit Logs Viewer Endpoint
@api_router.get("/logs/audit")
async def get_audit_logs(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get audit logs (sensitive operations only)"""
    try:
        import json
        
        logs = []
        
        # Read audit logs file
        try:
            with open('/app/audit_logs.json', 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            log_entry = json.loads(line)
                            logs.append(log_entry)
                            
                            if len(logs) >= limit:
                                break
                                
                        except json.JSONDecodeError:
                            continue
        
        except FileNotFoundError:
            logs = []
        
        # Reverse to get most recent first
        logs.reverse()
        
        return {
            "total_audit_logs": len(logs),
            "limit": limit,
            "logs": logs[:limit]
        }
        
    except Exception as e:
        logger.error(f"Error reading audit logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading audit logs: {str(e)}")

# Log Analytics Endpoint
@api_router.get("/logs/analytics")
async def get_log_analytics(current_user: User = Depends(get_current_user)):
    """Get log analytics and metrics"""
    try:
        import json
        from collections import Counter, defaultdict
        from datetime import datetime, timedelta
        
        analytics = {
            "total_logs": 0,
            "by_level": Counter(),
            "by_category": Counter(),
            "recent_errors": [],
            "performance_metrics": {
                "avg_response_time": 0,
                "slow_requests": 0
            },
            "security_events": 0,
            "audit_events": 0
        }
        
        performance_data = []
        
        # Analyze structured logs
        try:
            with open('/app/structured_logs.json', 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            log_entry = json.loads(line)
                            analytics["total_logs"] += 1
                            
                            # Count by level and category
                            analytics["by_level"][log_entry.get("level", "UNKNOWN")] += 1
                            analytics["by_category"][log_entry.get("category", "unknown")] += 1
                            
                            # Collect recent errors
                            if log_entry.get("level") == "ERROR":
                                analytics["recent_errors"].append({
                                    "timestamp": log_entry.get("timestamp"),
                                    "action": log_entry.get("action"),
                                    "message": log_entry.get("message")
                                })
                            
                            # Performance metrics
                            if log_entry.get("action") == "request_completed":
                                details = log_entry.get("details", {})
                                duration = details.get("duration_ms", 0)
                                if duration:
                                    performance_data.append(duration)
                                    if duration > 1000:  # > 1 second
                                        analytics["performance_metrics"]["slow_requests"] += 1
                            
                            # Security events
                            if log_entry.get("category") == "security":
                                analytics["security_events"] += 1
                            
                            # Audit events
                            if log_entry.get("audit_required"):
                                analytics["audit_events"] += 1
                                
                        except json.JSONDecodeError:
                            continue
        
        except FileNotFoundError:
            pass
        
        # Calculate average response time
        if performance_data:
            analytics["performance_metrics"]["avg_response_time"] = round(
                sum(performance_data) / len(performance_data), 2
            )
        
        # Convert counters to regular dicts for JSON serialization
        analytics["by_level"] = dict(analytics["by_level"])
        analytics["by_category"] = dict(analytics["by_category"])
        
        # Limit recent errors to last 10
        analytics["recent_errors"] = analytics["recent_errors"][-10:]
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error generating log analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")

# Robust scheduler status endpoint (already exists)
@api_router.get("/scheduler/status")
async def get_scheduler_status(current_user: User = Depends(get_current_user)):
    """Get current scheduler status and job information"""
    try:
        scheduler = await get_scheduler()
        status = await scheduler.get_job_status()
        
        # Add database job persistence info
        jobs_in_db = await db.scheduler_jobs.count_documents({})
        status["jobs_persisted_in_db"] = jobs_in_db
        
        # Add health stats if available
        health_stats = await db.scheduler_stats.find_one({"type": "current_stats"})
        if health_stats:
            # Remove MongoDB internal fields
            health_stats.pop("_id", None)
            health_stats.pop("type", None)
            status["health_statistics"] = health_stats
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scheduler status: {str(e)}")

# 🚀 SUB-FASE 2.2 - Import Redis cache system
from redis_cache_system import get_cached_dashboard_stats

@api_router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: User = Depends(get_current_user),
    tenant_db = Depends(get_tenant_database) if get_tenant_database else None,
    metrics: RequestMetrics = Depends(get_request_metrics) if get_request_metrics else None
):
    """
    Get system-wide statistics
    🚀 SUB-FASE 2.3 - Enhanced with Dependency Injection and Redis caching for massive performance boost
    """
    try:
        # 🚀 NEW: Try to get from cache first (5-minute TTL)
        if tenant_db:
            tenant_id = tenant_db.tenant_id
        else:
            tenant_id = get_current_tenant_id()
        cached_stats = await get_cached_dashboard_stats(tenant_id)
        
        if cached_stats:
            logger.debug("📊 Dashboard stats served from Redis cache")
            if metrics:
                metrics.record_cache_hit()
            return SystemStats(
                total_users=cached_stats["total_users"],
                total_licenses=cached_stats["total_licenses"],  
                total_clients=cached_stats["total_clients"],
                total_categories=cached_stats.get("total_categories", 0),
                total_products=cached_stats.get("total_products", 0),
                active_users=cached_stats.get("active_users", cached_stats["total_users"]),
                expired_licenses=cached_stats.get("expired_licenses", 0),
                pending_licenses=cached_stats.get("pending_licenses", 0),
                system_status="operational"
            )
        
        # 🔄 FALLBACK: Calculate from database if cache miss
        logger.debug("📊 Dashboard stats calculated from database (cache miss)")
        if metrics:
            metrics.record_cache_miss()
        
        if tenant_db:
            # 🚀 NEW: Use tenant-aware database for automatic tenant filtering
            # Count documents with automatic tenant isolation
            total_users = await tenant_db.count_documents("users", {})
            total_licenses = await tenant_db.count_documents("licenses", {})
            
            # Count clients (PF + PJ) with tenant filtering
            pf_clients = await tenant_db.count_documents("clientes_pf", {})
            pj_clients = await tenant_db.count_documents("clientes_pj", {})
            total_clients = pf_clients + pj_clients
            
            total_categories = await tenant_db.count_documents("categories", {"is_active": True})
            total_products = await tenant_db.count_documents("products", {"is_active": True})
            
            # Active users
            active_users = await tenant_db.count_documents("users", {"is_active": True})
            
            # License stats
            expired_licenses = await tenant_db.count_documents("licenses", {"status": "expired"})
            pending_licenses = await tenant_db.count_documents("licenses", {"status": "pending"})
            
            # Record multiple database queries
            if metrics:
                for _ in range(8):  # We made 8 database queries
                    metrics.record_db_query()
            
            logger.debug(f"📊 Dashboard stats calculated: users={total_users}, licenses={total_licenses}, clients={total_clients}")
        else:
            # Fallback to original implementation
            # Apply tenant filter for data isolation
            tenant_filter = add_tenant_filter({})
            
            # Count documents
            total_users = await db.users.count_documents(tenant_filter)
            total_licenses = await db.licenses.count_documents(tenant_filter)
            
            # Count clients (PF + PJ)
            pf_clients = await db.clientes_pf.count_documents(tenant_filter)
            pj_clients = await db.clientes_pj.count_documents(tenant_filter)
            total_clients = pf_clients + pj_clients
            
            total_categories = await db.categories.count_documents({**tenant_filter, "is_active": True})
            total_products = await db.products.count_documents({**tenant_filter, "is_active": True})
            
            # Active users
            active_users = await db.users.count_documents({**tenant_filter, "is_active": True})
            
            # License stats
            expired_licenses = await db.licenses.count_documents({
                **tenant_filter, 
                "status": "expired"
            })
            pending_licenses = await db.licenses.count_documents({
                **tenant_filter, 
                "status": "pending"
            })
        
        return SystemStats(
            total_users=total_users,
            total_licenses=total_licenses,
            total_clients=total_clients,
            total_categories=total_categories,
            total_products=total_products,
            active_users=active_users,
            expired_licenses=expired_licenses,
            pending_licenses=pending_licenses,
            system_status="operational"
        )
        
    except Exception as e:
        logger.error(f"Error getting system stats with dependency injection: {e}")
        # 🔄 FALLBACK: Use original implementation if dependency injection fails
        logger.warning("Falling back to original stats implementation")
        
        try:
            # Apply tenant filter for data isolation
            tenant_filter = add_tenant_filter({})
            
            # Count documents
            total_users = await db.users.count_documents(tenant_filter)
            total_licenses = await db.licenses.count_documents(tenant_filter)
            
            # Count clients (PF + PJ)
            pf_clients = await db.clientes_pf.count_documents(tenant_filter)
            pj_clients = await db.clientes_pj.count_documents(tenant_filter)
            total_clients = pf_clients + pj_clients
            
            total_categories = await db.categories.count_documents({**tenant_filter, "is_active": True})
            total_products = await db.products.count_documents({**tenant_filter, "is_active": True})
            
            # Active users
            active_users = await db.users.count_documents({**tenant_filter, "is_active": True})
            
            # License stats
            expired_licenses = await db.licenses.count_documents({
                **tenant_filter, 
                "status": "expired"
            })
            pending_licenses = await db.licenses.count_documents({
                **tenant_filter, 
                "status": "pending"
            })
            
            return SystemStats(
                total_users=total_users,
                total_licenses=total_licenses,
                total_clients=total_clients,
                total_categories=total_categories,
                total_products=total_products,
                active_users=active_users,
                expired_licenses=expired_licenses,
                pending_licenses=pending_licenses,
                system_status="operational"
            )
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {str(fallback_error)}")
            raise HTTPException(status_code=500, detail="Error retrieving system statistics")


# 🚀 SUB-FASE 2.2 - Cache Performance Monitoring Endpoint
@api_router.get("/cache/performance")
async def get_cache_performance(current_user: User = Depends(get_current_admin_user)):
    """
    Get Redis cache performance statistics
    🚀 SUB-FASE 2.2 - Monitor cache hit rates and performance
    """
    try:
        from redis_cache_system import get_cache_performance_report
        
        performance_report = await get_cache_performance_report()
        
        return {
            "cache_performance": performance_report,
            "system_info": {
                "timestamp": datetime.utcnow().isoformat(),
                "tenant_id": get_current_tenant_id(),
                "user": current_user.email
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting cache performance: {str(e)}")
        return {
            "error": "Cache performance monitoring unavailable",
            "details": str(e),
            "fallback_mode": True
        }

# User Management Routes (keeping existing)

# 🚀 SUB-FASE 2.4 - Import Aggregation Queries system  
from aggregation_queries import (
    get_users_with_complete_data, 
    get_licenses_with_relationships,
    get_dashboard_analytics_aggregated,
    get_expiring_licenses_with_clients,
    aggregation_monitor
)

# 🚀 SUB-FASE 2.4 - Enhanced Users Endpoint with Aggregation
@api_router.get("/users/complete", response_model=List[Dict])
async def get_users_with_full_data(
    current_user: User = Depends(get_current_user),
    pagination: Dict = Depends(get_pagination_params),
    metrics: RequestMetrics = Depends(get_request_metrics)
):
    """
    Get users with complete role and permission data in ONE query
    🚀 SUB-FASE 2.4 - Eliminates N+1 queries using MongoDB aggregation
    
    BEFORE: 1 + N + (N*M) queries = ~500+ queries for 230 users
    AFTER: 1 optimized aggregation query
    """
    try:
        tenant_id = get_current_tenant_id()
        
        # 🔥 CRITICAL OPTIMIZATION: Get all user data in one aggregation
        start_time = time.time()
        
        users_complete = await get_users_with_complete_data(
            db, 
            tenant_id, 
            limit=pagination["limit"], 
            skip=pagination["skip"]
        )
        
        execution_time = (time.time() - start_time) * 1000
        queries_eliminated = len(users_complete) * 10  # Estimated N+1 queries eliminated
        
        # Record performance metrics
        metrics.record_db_query()
        aggregation_monitor.record_aggregation(queries_eliminated, execution_time)
        
        logger.info(f"🚀 Users complete data: {len(users_complete)} users in {execution_time:.2f}ms")
        logger.info(f"🚀 Eliminated ~{queries_eliminated} individual queries")
        
        return users_complete
        
    except Exception as e:
        logger.error(f"Error getting users with complete data: {str(e)}")
        # Fallback to basic user listing - convert to dict format
        try:
            request = Request({"type": "http", "query_string": b""})  # Mock request
            users_list = await list_users(request, current_user, None, pagination, metrics)
            # Convert Pydantic models to dictionaries
            return [user.dict() if hasattr(user, 'dict') else user for user in users_list]
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {str(fallback_error)}")
            return []


# 🚀 SUB-FASE 2.4 - Enhanced Licenses Endpoint with Aggregation  
@api_router.get("/licenses/complete", response_model=List[Dict])
async def get_licenses_with_full_relationships(
    current_user: User = Depends(get_current_user),
    pagination: Dict = Depends(get_pagination_params),
    metrics: RequestMetrics = Depends(get_request_metrics)
):
    """
    Get licenses with complete client, plan, and category data in ONE query
    🚀 SUB-FASE 2.4 - Eliminates N+1 queries using MongoDB aggregation
    
    BEFORE: 1 + 3N queries = ~1500+ queries for 500 licenses  
    AFTER: 1 optimized aggregation query
    """
    try:
        tenant_id = get_current_tenant_id()
        
        # 🔥 CRITICAL OPTIMIZATION: Get all license relationships in one aggregation
        start_time = time.time()
        
        licenses_complete = await get_licenses_with_relationships(
            db,
            tenant_id,
            limit=pagination["limit"],
            skip=pagination["skip"]
        )
        
        execution_time = (time.time() - start_time) * 1000
        queries_eliminated = len(licenses_complete) * 3  # Client + Plan + Category per license
        
        # Record performance metrics
        metrics.record_db_query()
        aggregation_monitor.record_aggregation(queries_eliminated, execution_time)
        
        logger.info(f"🚀 Licenses complete data: {len(licenses_complete)} licenses in {execution_time:.2f}ms")
        logger.info(f"🚀 Eliminated ~{queries_eliminated} individual queries")
        
        return licenses_complete
        
    except Exception as e:
        logger.error(f"Error getting licenses with relationships: {str(e)}")
        # Fallback to basic license listing - convert to dict format
        try:
            request = Request({"type": "http", "query_string": b""})  # Mock request
            licenses_list = await get_licenses(request, current_user, None, pagination, metrics)
            # Convert Pydantic models to dictionaries
            return [license.dict() if hasattr(license, 'dict') else license for license in licenses_list]
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {str(fallback_error)}")
            return []


# 🚀 SUB-FASE 2.4 - Enhanced Dashboard with Aggregated Analytics
@api_router.get("/dashboard/analytics")
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    metrics: RequestMetrics = Depends(get_request_metrics)
):
    """
    Get comprehensive dashboard analytics in ONE aggregation
    🚀 SUB-FASE 2.4 - Eliminates multiple count queries
    
    BEFORE: 10+ separate count and calculation queries
    AFTER: Optimized aggregation pipeline
    """
    try:
        tenant_id = get_current_tenant_id()
        
        # 🔥 CRITICAL OPTIMIZATION: Get all dashboard stats in aggregated queries
        start_time = time.time()
        
        analytics = await get_dashboard_analytics_aggregated(db, tenant_id)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Record performance metrics
        metrics.record_db_query()
        aggregation_monitor.record_aggregation(10, execution_time)  # 10+ queries eliminated
        
        logger.info(f"🚀 Dashboard analytics: Complete in {execution_time:.2f}ms")
        logger.info(f"🚀 Eliminated 10+ individual count queries")
        
        return {
            "analytics": analytics,
            "performance": {
                "execution_time_ms": execution_time,
                "queries_eliminated": 10,
                "optimization_level": "aggregated"
            },
            "last_updated": analytics["last_updated"]
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard analytics")


# 🚀 SUB-FASE 2.4 - Expiring Licenses with Client Data
@api_router.get("/licenses/expiring", response_model=List[Dict])
async def get_expiring_licenses_complete(
    days_ahead: int = 30,
    current_user: User = Depends(get_current_user),
    metrics: RequestMetrics = Depends(get_request_metrics)
):
    """
    Get expiring licenses with complete client information
    🚀 SUB-FASE 2.4 - Eliminates N+1 queries for expiration alerts
    
    BEFORE: N+1 queries for each expiring license + client data
    AFTER: 1 aggregation with all client information
    """
    try:
        tenant_id = get_current_tenant_id()
        
        # 🔥 OPTIMIZATION: Get expiring licenses with client data in one query
        start_time = time.time()
        
        expiring_licenses = await get_expiring_licenses_with_clients(
            db, 
            tenant_id, 
            days_ahead=days_ahead
        )
        
        execution_time = (time.time() - start_time) * 1000
        queries_eliminated = len(expiring_licenses) * 2  # License + Client per item
        
        # Record performance metrics  
        metrics.record_db_query()
        aggregation_monitor.record_aggregation(queries_eliminated, execution_time)
        
        logger.info(f"🚀 Expiring licenses: {len(expiring_licenses)} licenses in {execution_time:.2f}ms")
        logger.info(f"🚀 Eliminated ~{queries_eliminated} individual queries")
        
        return expiring_licenses
        
    except Exception as e:
        logger.error(f"Error getting expiring licenses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve expiring licenses")


# 🚀 SUB-FASE 2.4 - Aggregation Performance Monitoring
@api_router.get("/performance/aggregations") 
async def get_aggregation_performance(current_user: User = Depends(get_current_admin_user)):
    """
    Get aggregation performance statistics
    🚀 SUB-FASE 2.4 - Monitor query optimization effectiveness
    """
    try:
        performance_stats = aggregation_monitor.get_stats()
        
        return {
            "aggregation_performance": performance_stats,
            "system_info": {
                "timestamp": datetime.utcnow().isoformat(),
                "tenant_id": get_current_tenant_id(),
                "user": current_user.email
            },
            "recommendations": _get_aggregation_recommendations(performance_stats)
        }
        
    except Exception as e:
        logger.error(f"Error getting aggregation performance: {str(e)}")
        return {
            "error": "Aggregation performance monitoring unavailable",
            "details": str(e)
        }


def _get_aggregation_recommendations(stats: Dict) -> List[str]:
    """Generate recommendations based on aggregation performance"""
    recommendations = []
    
    avg_queries_eliminated = stats.get('total_queries_eliminated', 0) / max(stats.get('total_aggregations', 1), 1)
    
    if avg_queries_eliminated > 10:
        recommendations.append("Excellent aggregation performance - high N+1 query elimination")
    elif avg_queries_eliminated > 5:
        recommendations.append("Good aggregation performance - moderate query optimization")
    else:
        recommendations.append("Consider more aggressive aggregation for better performance")
    
    avg_time = stats.get('average_execution_time', 0)
    if avg_time > 1000:  # > 1 second
        recommendations.append("Aggregation queries taking longer than expected - consider optimization")
    elif avg_time < 100:  # < 100ms
        recommendations.append("Excellent aggregation response times")
    
    return recommendations

@api_router.get("/users", response_model=List[User])
async def list_users(
    request: Request, 
    current_user: User = Depends(get_current_user),
    tenant_db = Depends(get_tenant_database),
    pagination: Dict = Depends(get_pagination_params),
    metrics: RequestMetrics = Depends(get_request_metrics)
):
    """
    Lista usuários no escopo do ator
    🚀 SUB-FASE 2.3 - Enhanced with Dependency Injection and automatic tenant filtering
    """
    try:
        # 🚀 NEW: Use tenant-aware database with automatic filtering
        logger.debug(f"📋 Listing users with pagination: page={pagination['page']}, limit={pagination['limit']}")
        
        # Build scope filter (existing business logic)
        base_filter = {}
        
        # Apply role-based scope filtering
        if current_user.role == UserRole.ADMIN:
            # Admin sees only their clients (admin_vendor_id = admin.id)
            base_filter["admin_vendor_id"] = current_user.id
        elif current_user.role == UserRole.USER:
            # Users can only see themselves
            base_filter["id"] = current_user.id
        # SUPER_ADMIN sees all users in the tenant (no additional filter)
        
        # 🚀 NEW: Use tenant database with automatic tenant filtering
        users = await tenant_db.find(
            "users", 
            base_filter,
            skip=pagination["skip"],
            limit=pagination["limit"]
        )
        
        # Record metrics
        metrics.record_db_query()
        
        logger.debug(f"📋 Found {len(users)} users for {current_user.role} user {current_user.email}")
        
        return [User(**user) for user in users]
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        # 🔄 FALLBACK: Use original implementation if dependency injection fails
        logger.warning("Falling back to original user listing implementation")
        
        q = build_scope_filter(current_user, {})
        cursor = db.users.find(q).limit(200)
        users = await cursor.to_list(length=200)
        return [User(**user) for user in users]

class UserCreate(BaseModel):
    email: str
    role: str | None = None  # será ignorado para USER (definimos pelo fluxo)
    admin_vendor_id: str | None = None  # opcional; para ADMIN, manter None

@api_router.post("/users", response_model=User)
async def create_user(body: UserCreate, current_user: User = Depends(get_current_user)):
    """
    Criação básica respeitando escopo:
      - SUPER_ADMIN: pode criar em qualquer tenant (ajuste se desejar).
      - ADMIN: cria USERS no próprio tenant e os vincula como seus clientes (admin_vendor_id = admin.id).
      - USER: proibido.
    Obs.: fluxo de convite pode substituir este endpoint futuramente.
    """
    if current_user.role == UserRole.USER:
        raise HTTPException(status_code=403, detail="Sem permissão")

    doc = {
        "id": str(uuid.uuid4()),
        "email": body.email.lower().strip(),
        "name": body.email.split("@")[0].title(),  # Nome baseado no email
        "tenant_id": current_user.tenant_id if current_user.role != UserRole.SUPER_ADMIN else getattr(current_user, "tenant_id", None),
        "role": "user" if current_user.role == UserRole.ADMIN else (body.role or "user"),
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    if current_user.role == UserRole.ADMIN:
        doc["admin_vendor_id"] = current_user.id

    # Índice único (tenant_id, email) previne duplicatas
    try:
        res = await db.users.insert_one(doc)
        created = await db.users.find_one({"_id": res.inserted_id})
        if created:
            created.pop("_id", None)  # Remove ObjectId
            return User(**created)
        else:
            raise HTTPException(status_code=500, detail="Falha ao criar usuário")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao criar usuário: {e}")

# ------------------------ USERS by :id ------------------------
@api_router.get("/users/{user_id}", response_model=User)
async def get_user_by_id(user_id: str, current_user: User = Depends(get_current_user)):
    doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="User não encontrado")
    if not enforce_object_scope(doc, current_user):
        raise HTTPException(status_code=403, detail="Fora do escopo")
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return User(**doc)

class UserUpdate(BaseModel):
    email: str | None = None

@api_router.put("/users/{user_id}", response_model=User)
async def update_user_by_id(user_id: str, body: UserUpdate, current_user: User = Depends(get_current_user)):
    doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="User não encontrado")
    if not enforce_object_scope(doc, current_user):
        raise HTTPException(status_code=403, detail="Fora do escopo")

    updates = {}
    if body.email is not None:
        updates["email"] = body.email.lower().strip()
    if not updates:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        return User(**doc)

    await db.users.update_one({"_id": doc["_id"]}, {"$set": updates})
    updated = await db.users.find_one({"_id": doc["_id"]})
    updated["id"] = str(updated["_id"])
    updated.pop("_id", None)
    return User(**updated)

@api_router.delete("/users/{user_id}", status_code=204)
async def delete_user_by_id(user_id: str, current_user: User = Depends(get_current_user)):
    doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="User não encontrado")
    if not enforce_object_scope(doc, current_user):
        raise HTTPException(status_code=403, detail="Fora do escopo")
    await db.users.delete_one({"_id": doc["_id"]})
    return Response(status_code=204)

@api_router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str, 
    role_data: dict,
    current_user: User = Depends(get_current_admin_user),
    tenant_id: str = Depends(require_tenant)
):
    """Update user role with tenant isolation"""
    role = role_data.get("role")
    
    # Super admin can update any user, regular admin only in their tenant
    if current_user.role == "super_admin":
        query_filter = {"id": user_id}
    else:
        query_filter = add_tenant_filter({"id": user_id}, tenant_id)
    
    result = await db.users.update_one(
        query_filter,
        {"$set": {"role": role}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User role updated successfully"}

# Equipment Management Models
class EquipmentBrandBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class EquipmentBrandCreate(EquipmentBrandBase):
    pass

class EquipmentBrand(EquipmentBrandBase, BaseEntity):
    pass

class EquipmentModelBase(BaseModel):
    name: str
    brand_id: str
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = {}
    is_active: bool = True

class EquipmentModelCreate(EquipmentModelBase):
    pass

class EquipmentModel(EquipmentModelBase, BaseEntity):
    pass

# Equipment Management Routes
@api_router.get("/equipment-brands", response_model=List[EquipmentBrand])
async def get_equipment_brands(current_user: User = Depends(get_current_user)):
    # CRÍTICO: Filtrar marcas por tenant
    brands_filter = add_tenant_filter({"is_active": True}, current_user.tenant_id)
    brands = await db.equipment_brands.find(brands_filter).to_list(1000)
    return [EquipmentBrand(**brand) for brand in brands]

@api_router.post("/equipment-brands", response_model=EquipmentBrand)
async def create_equipment_brand(
    brand_data: EquipmentBrandCreate,
    current_user: User = Depends(get_current_admin_user)
):
    # Check if brand name already exists
    # CRÍTICO: Verificar duplicatas apenas no tenant atual
    brand_filter = add_tenant_filter({"name": brand_data.name}, current_user.tenant_id)
    existing_brand = await db.equipment_brands.find_one(brand_filter)
    if existing_brand:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Marca já cadastrada"
        )
    
    brand_dict = brand_data.dict()
    brand_dict["created_by"] = current_user.id
    
    brand = EquipmentBrand(**brand_dict)
    # CRÍTICO: Inserir com tenant_id
    brand_dict_with_tenant = add_tenant_to_document(brand.dict(), current_user.tenant_id)
    await db.equipment_brands.insert_one(brand_dict_with_tenant)
    
    return brand

@api_router.get("/equipment-models", response_model=List[EquipmentModel])
async def get_equipment_models(brand_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"is_active": True}
    if brand_id:
        query["brand_id"] = brand_id
    
    # CRÍTICO: Filtrar modelos por tenant
    models_filter = add_tenant_filter(query, current_user.tenant_id)
    models = await db.equipment_models.find(models_filter).to_list(1000)
    return [EquipmentModel(**model) for model in models]

@api_router.post("/equipment-models", response_model=EquipmentModel)
async def create_equipment_model(
    model_data: EquipmentModelCreate,
    current_user: User = Depends(get_current_admin_user)
):
    # Check if brand exists
    # CRÍTICO: Verificar marca apenas no tenant atual
    brand_filter = add_tenant_filter({"id": model_data.brand_id}, current_user.tenant_id)
    brand = await db.equipment_brands.find_one(brand_filter)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Marca não encontrada"
        )
    
    # Check if model name already exists for this brand
    # CRÍTICO: Verificar modelo duplicado apenas no tenant atual
    model_filter = add_tenant_filter({
        "name": model_data.name,
        "brand_id": model_data.brand_id
    }, current_user.tenant_id)
    existing_model = await db.equipment_models.find_one(model_filter)
    if existing_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Modelo já cadastrado para esta marca"
        )
    
    model_dict = model_data.dict()
    model_dict["created_by"] = current_user.id
    
    model = EquipmentModel(**model_dict)
    # CRÍTICO: Inserir com tenant_id
    model_dict_with_tenant = add_tenant_to_document(model.dict(), current_user.tenant_id)
    await db.equipment_models.insert_one(model_dict_with_tenant)
    
    return model

# Pessoa Física Routes
@api_router.post("/clientes-pf", response_model=PessoaFisica)
async def create_pessoa_fisica(
    client_data: PessoaFisicaCreate,
    current_user: User = Depends(get_current_admin_user)
):
    # Check if CPF already exists in same tenant
    query_filter = add_tenant_filter({"cpf": client_data.cpf})
    existing_client = await db.clientes_pf.find_one(query_filter)
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado no sistema"
        )
    
    client_dict = client_data.dict()
    client_dict["created_by"] = current_user.id
    
    # Usar helper de tenant para adicionar tenant_id
    # CRÍTICO: Especificar tenant_id do usuário atual
    client_dict = add_tenant_to_document(client_dict, current_user.tenant_id)
    
    # Criar cliente com tenant_id
    client = PessoaFisica(**client_dict)
    await db.clientes_pf.insert_one(client_dict)
    
    return client

@api_router.get("/clientes-pf", response_model=List[PessoaFisica])
async def get_pessoas_fisicas(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant)
):
    """Get all PF clients with tenant isolation"""
    try:
        # Admin can see all active, User can see all active in their tenant
        base_filter = {"status": {"$ne": ClientStatus.INACTIVE}}
        query_filter = enforce_super_admin_or_tenant_filter(base_filter, current_user, tenant_id)
        
        if current_user.role == "super_admin":
            clients = await db.clientes_pf.find(query_filter).to_list(1000)
        else:
            clients = await db.clientes_pf.find(query_filter).to_list(1000)
        
        # Converter e limpar dados
        result = []
        for client in clients:
            # Remove MongoDB ObjectId
            client.pop("_id", None)
            
            # Garantir campos obrigatórios
            if not client.get("id"):
                continue
            
            # Normalizar client_type
            client_type = client.get("client_type", "pf")
            if client_type.upper() == "PF":
                client["client_type"] = "pf"
            elif client_type.upper() == "PJ":
                client["client_type"] = "pj"
            else:
                client["client_type"] = "pf"  # padrão
                
            # Para usuários não-admin, aplicar mascaramento básico de CPF
            if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                cpf = client.get("cpf", "")
                if len(cpf) >= 11:
                    client["cpf"] = cpf[:3] + "***" + cpf[-2:]
            
            try:
                result.append(PessoaFisica(**client))
            except Exception as e:
                logger.warning(f"Skipping invalid client PF {client.get('id')}: {e}")
                continue
        
        return result
    except Exception as e:
        logger.error(f"Error fetching pessoas físicas: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching pessoas físicas: {str(e)}")

@api_router.get("/clientes-pf/{client_id}", response_model=PessoaFisica)
async def get_pessoa_fisica(client_id: str, current_user: User = Depends(get_current_user)):
    query_filter = add_tenant_filter({"id": client_id})
    client_doc = await db.clientes_pf.find_one(query_filter)
    if not client_doc:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Aplicar mascaramento baseado no role do usuário
    license_reference = generate_license_reference(client_doc)
    masked_client = apply_data_masking(client_doc, current_user.role, license_reference)
    
    return PessoaFisica(**masked_client)

@api_router.put("/clientes-pf/{client_id}", response_model=PessoaFisica)
async def update_pessoa_fisica(
    client_id: str,
    client_update: PessoaFisicaUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    # Aplicar filtro de tenant
    query_filter = add_tenant_filter({"id": client_id})
    
    update_data = {k: v for k, v in client_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = current_user.id
    
    # CORREÇÃO: Converter datetime.date para datetime.datetime para compatibilidade MongoDB
    import datetime as dt
    for key, value in update_data.items():
        if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
            update_data[key] = dt.datetime.combine(value, dt.datetime.min.time())
    
    result = await db.clientes_pf.update_one(
        query_filter,
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    updated_client = await db.clientes_pf.find_one(query_filter)
    return PessoaFisica(**updated_client)

@api_router.delete("/clientes-pf/{client_id}")
async def delete_pessoa_fisica(
    client_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.clientes_pf.update_one(
        {"id": client_id},
        {"$set": {"status": ClientStatus.INACTIVE, "updated_at": datetime.utcnow(), "updated_by": current_user.id}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    return {"message": "Cliente inativado com sucesso"}

# Pessoa Jurídica Routes
@api_router.post("/clientes-pj", response_model=PessoaJuridica)
async def create_pessoa_juridica(
    client_data: PessoaJuridicaCreate,
    current_user: User = Depends(get_current_admin_user)
):
    # Check if CNPJ already exists in same tenant (use normalized format)
    cnpj_normalized = client_data.cnpj_normalizado if hasattr(client_data, 'cnpj_normalizado') else client_data.cnpj
    query_filter = add_tenant_filter({"cnpj_normalizado": cnpj_normalized})
    existing_client = await db.clientes_pj.find_one(query_filter)
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CNPJ já cadastrado no sistema"
        )
    
    client_dict = client_data.dict()
    client_dict["created_by"] = current_user.id
    
    # Usar helper de tenant para adicionar tenant_id
    # CRÍTICO: Especificar tenant_id do usuário atual
    client_dict = add_tenant_to_document(client_dict, current_user.tenant_id)
    
    # Criar cliente com tenant_id
    client = PessoaJuridica(**client_dict)
    await db.clientes_pj.insert_one(client_dict)
    
    return client

# Company/Organization Management Routes (for Registry Module)
class CompanyBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(CompanyBase):
    pass

class Company(CompanyBase, BaseEntity):
    pass

@api_router.get("/companies", response_model=List[Company])
async def get_companies(current_user: User = Depends(get_current_user)):
    # CRÍTICO: Filtrar empresas por tenant
    companies_filter = add_tenant_filter({"is_active": True}, current_user.tenant_id)
    companies = await db.companies.find(companies_filter).to_list(1000)
    return [Company(**company) for company in companies]

@api_router.post("/companies", response_model=Company)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_admin_user)
):
    # CRÍTICO: Verificar empresa existente apenas no tenant atual
    company_filter = add_tenant_filter({"name": company_data.name}, current_user.tenant_id)
    existing_company = await db.companies.find_one(company_filter)
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empresa já cadastrada"
        )
    
    company_dict = company_data.dict()
    company_dict["created_by"] = current_user.id
    
    company = Company(**company_dict)
    # CRÍTICO: Inserir empresa com tenant_id
    company_dict_with_tenant = add_tenant_to_document(company.dict(), current_user.tenant_id)
    await db.companies.insert_one(company_dict_with_tenant)
    
    return company

@api_router.put("/companies/{company_id}", response_model=Company)
async def update_company(
    company_id: str,
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    company_dict = company_data.dict()
    company_dict["updated_at"] = datetime.utcnow()
    
    result = await db.companies.update_one(
        {"id": company_id}, 
        {"$set": company_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    company_doc = await db.companies.find_one({"id": company_id})
    return Company(**company_doc)

@api_router.delete("/companies/{company_id}")
async def delete_company(company_id: str, current_user: User = Depends(get_current_admin_user)):
    await db.companies.update_one(
        {"id": company_id}, 
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    return {"message": "Empresa removida com sucesso"}

# License Plans Management Routes  
class LicensePlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = 0.0
    duration_days: int = 30
    max_users: int = 1
    features: List[str] = []
    is_active: bool = True

class LicensePlanCreate(LicensePlanBase):
    pass

class LicensePlanUpdate(LicensePlanBase):
    pass

class LicensePlan(LicensePlanBase, BaseEntity):
    pass

@api_router.get("/license-plans", response_model=List[LicensePlan])
async def get_license_plans(current_user: User = Depends(get_current_user)):
    """
    Get license plans
    🚀 SUB-FASE 2.2 - Enhanced with Redis caching (1 hour TTL)
    """
    try:
        # 🚀 NEW: Try to get from cache first
        from redis_cache_system import get_cached_license_plans
        
        tenant_id = get_current_tenant_id()
        cached_plans = await get_cached_license_plans(tenant_id)
        
        if cached_plans:
            logger.debug("💳 License plans served from Redis cache")
            return [LicensePlan(**plan) for plan in cached_plans if plan.get("is_active", True)]
        
        # 🔄 FALLBACK: Get from database if cache miss
        logger.debug("💳 License plans fetched from database (cache miss)")
        
        query_filter = add_tenant_filter({"is_active": True})
        plans = await db.license_plans.find(query_filter).to_list(1000)
        
        return [LicensePlan(**plan) for plan in plans]
        
    except Exception as e:
        logger.error(f"Error fetching license plans: {str(e)}")
        # Fallback to direct database query
        query_filter = add_tenant_filter({"is_active": True})
        plans = await db.license_plans.find(query_filter).to_list(1000)
        return [LicensePlan(**plan) for plan in plans]

@api_router.post("/license-plans", response_model=LicensePlan)
async def create_license_plan(
    plan_data: LicensePlanCreate,
    current_user: User = Depends(get_current_admin_user)
):
    # CRÍTICO: Verificar plano existente apenas no tenant atual
    plan_filter = add_tenant_filter({"name": plan_data.name}, current_user.tenant_id)
    existing_plan = await db.license_plans.find_one(plan_filter)
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plano já cadastrado"
        )
    
    plan_dict = plan_data.dict()
    plan_dict["created_by"] = current_user.id
    
    plan = LicensePlan(**plan_dict)
    # CRÍTICO: Inserir plano com tenant_id
    plan_dict_with_tenant = add_tenant_to_document(plan.dict(), current_user.tenant_id)
    await db.license_plans.insert_one(plan_dict_with_tenant)
    
    return plan

@api_router.put("/license-plans/{plan_id}", response_model=LicensePlan)
async def update_license_plan(
    plan_id: str,
    plan_data: LicensePlanUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    plan_dict = plan_data.dict()
    plan_dict["updated_at"] = datetime.utcnow()
    
    result = await db.license_plans.update_one(
        {"id": plan_id}, 
        {"$set": plan_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plano não encontrado"
        )
    
    query_filter = add_tenant_filter({"id": plan_id})
    plan_doc = await db.license_plans.find_one(query_filter)
    return LicensePlan(**plan_doc)

@api_router.delete("/license-plans/{plan_id}")
async def delete_license_plan(plan_id: str, current_user: User = Depends(get_current_admin_user)):
    await db.license_plans.update_one(
        {"id": plan_id}, 
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    return {"message": "Plano removido com sucesso"}

# RBAC Endpoints - Sistema de Controle de Acesso
@api_router.get("/rbac/permissions", response_model=List[Permission])
async def get_permissions(current_user: User = Depends(require_permission("rbac.read"))):
    # CRÍTICO: Para permissions, usar filtro global ou por tenant (assumindo global por enquanto)
    permissions_filter = add_tenant_filter({}, "system")  # Permissions são globais no sistema
    permissions = await db.permissions.find(permissions_filter).to_list(1000)
    return [Permission(**perm) for perm in permissions]

@api_router.post("/rbac/permissions", response_model=Permission)
async def create_permission(permission_data: Permission, current_user: User = Depends(require_permission("rbac.manage"))):
    permission = Permission(**permission_data.dict())
    # CRÍTICO: Inserir permission com tenant system (global)
    permission_dict_with_tenant = add_tenant_to_document(permission.dict(), "system")
    await db.permissions.insert_one(permission_dict_with_tenant)
    return permission

@api_router.get("/rbac/roles", response_model=List[Role])  
async def get_roles(current_user: User = Depends(require_permission("rbac.read"))):
    # CRÍTICO: Para roles, usar filtro de tenant (podem ser por tenant ou sistema)
    roles_filter = add_tenant_filter({}, current_user.tenant_id)
    roles = await db.roles.find(roles_filter).to_list(1000)
    return [Role(**role) for role in roles]

@api_router.post("/rbac/roles", response_model=Role)
async def create_role(role_data: CreateRoleRequest, current_user: User = Depends(require_permission("rbac.manage"))):
    try:
        # Verificar duplicatas ANTES de criar
        duplicate_check = await check_role_duplicates(role_data.name)
        
        if duplicate_check.get("has_duplicates"):
            existing = duplicate_check["existing_role"]
            
            log_advanced_error(
                ErrorLevel.WARNING,
                ErrorCategory.DUPLICATE_DATA,
                f"Tentativa bloqueada de criar role duplicado: {role_data.name}",
                user_email=current_user.email,
                details={"existing_role_id": existing["id"], "is_system": existing["is_system"]}
            )
            
            error_msg = f"Já existe um papel com o nome '{role_data.name}'"
            if existing["is_system"]:
                error_msg += " (papel do sistema). Escolha um nome diferente."
            else:
                error_msg += f". ID existente: {existing['id']}"
                
            raise HTTPException(
                status_code=400,
                detail={
                    "message": error_msg,
                    "type": "DUPLICATE_ROLE",
                    "existing_role": existing,
                    "suggestions": [
                        f"{role_data.name} v2",
                        f"{role_data.name} Custom",
                        f"{role_data.name} {datetime.now().strftime('%Y%m%d')}"
                    ]
                }
            )
        
        # Continuar com criação normal se não houver duplicatas
        role_dict = {
            "id": str(uuid.uuid4()),
            "tenant_id": current_user.tenant_id,
            "name": role_data.name,
            "description": role_data.description,
            "permissions": role_data.permissions,
            "is_system": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # 🚨 CRÍTICO: Garantir tenant_id no documento antes de inserir
        role_dict_with_tenant = add_tenant_to_document(role_dict, current_user.tenant_id)
        result = await db.roles.insert_one(role_dict_with_tenant)
        
        log_advanced_error(
            ErrorLevel.INFO,
            ErrorCategory.SYSTEM,
            f"Role criado com sucesso: {role_data.name}",
            user_email=current_user.email,
            details={"role_id": role_dict["id"], "permissions_count": len(role_data.permissions)}
        )
        
        return role_dict
        
    except HTTPException:
        raise
    except Exception as e:
        log_advanced_error(
            ErrorLevel.ERROR,
            ErrorCategory.DATABASE,
            f"Erro ao criar role: {role_data.name}",
            user_email=current_user.email,
            exception=e
        )
        raise HTTPException(status_code=500, detail="Erro interno ao criar papel")

@api_router.put("/rbac/roles/{role_id}", response_model=Role)
async def update_role(role_id: str, role_data: UpdateRoleRequest, current_user: User = Depends(require_permission("rbac.manage"))):
    update_data = {k: v for k, v in role_data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # 🚨 CRÍTICO: Filtrar role por tenant para evitar modificação cross-tenant
    role_filter = add_tenant_filter({"id": role_id}, current_user.tenant_id)
    await db.roles.update_one(role_filter, {"$set": update_data})
    
    role_doc = await db.roles.find_one(role_filter)
    if not role_doc:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return Role(**role_doc)

@api_router.delete("/rbac/roles/{role_id}")
async def delete_role(role_id: str, current_user: User = Depends(require_permission("rbac.manage"))):
    # 🚨 CRÍTICO: Verificar role apenas no tenant atual
    role_filter = add_tenant_filter({"id": role_id}, current_user.tenant_id)
    role_doc = await db.roles.find_one(role_filter)
    if not role_doc:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role_doc.get('is_system', False):
        raise HTTPException(status_code=400, detail="Cannot delete system role")
    
    # 🚨 CRÍTICO: Deletar apenas no tenant atual
    await db.roles.delete_one(role_filter)
    
    # 🚨 CRÍTICO: Remover role apenas de usuários do tenant atual
    users_filter = add_tenant_filter({"rbac.roles": role_id}, current_user.tenant_id)
    await db.users.update_many(
        users_filter,
        {"$pull": {"rbac.roles": role_id}}
    )
    
    return {"message": "Role deleted successfully"}

@api_router.post("/rbac/assign-roles")
async def assign_roles(request: AssignRoleRequest, current_user: User = Depends(require_permission("users.manage"))):
    # Verificar se usuário existe (com filtro de tenant)
    query_filter = add_tenant_filter({"id": request.user_id}, current_user.tenant_id)
    user_doc = await db.users.find_one(query_filter)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 🚨 CRÍTICO: Verificar se roles existem APENAS no tenant atual
    roles_filter = add_tenant_filter({"id": {"$in": request.role_ids}}, current_user.tenant_id)
    existing_roles = await db.roles.find(roles_filter).to_list(1000)
    if len(existing_roles) != len(request.role_ids):
        raise HTTPException(status_code=400, detail="One or more roles not found")
    
    # 🚨 CRÍTICO: Atualizar usuário com filtro de tenant
    user_update_filter = add_tenant_filter({"id": request.user_id}, current_user.tenant_id)
    await db.users.update_one(
        user_update_filter,
        {
            "$set": {
                "rbac.roles": request.role_ids,
                "rbac.last_permission_update": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Roles assigned successfully"}

@api_router.post("/rbac/assign-permissions")
async def assign_direct_permissions(request: AssignPermissionRequest, current_user: User = Depends(require_permission("users.manage"))):
    # 🚨 CRÍTICO: Verificar usuário apenas no tenant atual
    query_filter = add_tenant_filter({"id": request.user_id}, current_user.tenant_id)
    user_doc = await db.users.find_one(query_filter)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 🚨 CRÍTICO: Verificar permissões no contexto adequado (sistema ou tenant)
    permissions_filter = add_tenant_filter({"id": {"$in": request.permission_ids}}, "system")
    existing_permissions = await db.permissions.find(permissions_filter).to_list(1000)
    if len(existing_permissions) != len(request.permission_ids):
        raise HTTPException(status_code=400, detail="One or more permissions not found")
    
    # 🚨 CRÍTICO: Atualizar usuário com filtro de tenant
    user_update_filter = add_tenant_filter({"id": request.user_id}, current_user.tenant_id)
    await db.users.update_one(
        user_update_filter,
        {"id": request.user_id},
        {
            "$set": {
                "rbac.direct_permissions": request.permission_ids,
                "rbac.last_permission_update": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Direct permissions assigned successfully"}

# ======================================
# TENANT MANAGEMENT ENDPOINTS - Multi-Tenancy SaaS
# ======================================

@api_router.get("/tenants", response_model=List[Tenant])
async def get_tenants(current_user: User = Depends(get_current_user)):
    """Lista todos os tenants - apenas super admins podem ver todos"""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas super administradores podem listar tenants"
        )
    
    tenants = await db.tenants.find().to_list(1000)
    return [Tenant(**tenant) for tenant in tenants]

@api_router.get("/tenants/{tenant_id}", response_model=Tenant)
async def get_tenant(tenant_id: str, current_user: User = Depends(get_current_user)):
    """Busca um tenant específico"""
    # Super admin pode ver qualquer tenant, usuário normal só o próprio
    if current_user.role != "super_admin" and get_current_tenant_id() != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado ao tenant solicitado"
        )
    
    tenant_doc = await db.tenants.find_one({"id": tenant_id})
    if not tenant_doc:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    return Tenant(**tenant_doc)

@api_router.post("/tenants", response_model=Tenant)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(get_current_user)
):
    """Cria um novo tenant - apenas super admins"""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas super administradores podem criar tenants"
        )
    
    # Verificar se subdomain já existe
    existing_tenant = await db.tenants.find_one({"subdomain": tenant_data.subdomain})
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subdomínio '{tenant_data.subdomain}' já está em uso"
        )
    
    # Verificar se email de contato já existe
    existing_email = await db.tenants.find_one({"contact_email": tenant_data.contact_email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email de contato '{tenant_data.contact_email}' já está em uso"
        )
    
    # Aplicar configurações do plano
    tenant_dict = tenant_data.dict()
    tenant_dict = apply_plan_limits(tenant_dict, tenant_data.plan)
    tenant_dict["created_by"] = current_user.id
    
    # Criar tenant
    tenant = Tenant(**tenant_dict)
    await db.tenants.insert_one(tenant.dict())
    
    # Criar usuário administrador do tenant
    admin_user_dict = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant.id,
        "name": tenant_data.admin_name,
        "email": tenant_data.admin_email,
        "role": "admin",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "password_hash": get_password_hash(tenant_data.admin_password)
    }
    
    # 🚨 CRÍTICO: Usar add_tenant_to_document para consistência
    admin_user_with_tenant = add_tenant_to_document(admin_user_dict, tenant.id)
    await db.users.insert_one(admin_user_with_tenant)
    
    log_advanced_error(
        ErrorLevel.INFO,
        ErrorCategory.SYSTEM,
        f"Novo tenant criado: {tenant.name} ({tenant.subdomain})",
        user_email=current_user.email,
        details={"tenant_id": tenant.id, "admin_email": tenant_data.admin_email, "plan": tenant.plan}
    )
    
    return tenant

@api_router.put("/tenants/{tenant_id}", response_model=Tenant)
async def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    current_user: User = Depends(get_current_user)
):
    """Atualiza um tenant"""
    # Super admin pode editar qualquer tenant, admin pode editar apenas o próprio
    if current_user.role != "super_admin":
        if current_user.role != "admin" or get_current_tenant_id() != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para editar este tenant"
            )
    
    # Buscar tenant existente
    tenant_doc = await db.tenants.find_one({"id": tenant_id})
    if not tenant_doc:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    # Preparar dados de atualização
    update_data = {k: v for k, v in tenant_update.dict().items() if v is not None}
    
    # Se mudou o plano, aplicar novos limites
    if "plan" in update_data:
        update_data = apply_plan_limits(update_data, update_data["plan"])
    
    update_data["updated_at"] = datetime.utcnow()
    update_data["last_modified_by"] = current_user.id
    
    # Atualizar tenant
    result = await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    # Buscar tenant atualizado
    updated_tenant = await db.tenants.find_one({"id": tenant_id})
    
    log_advanced_error(
        ErrorLevel.INFO,
        ErrorCategory.SYSTEM,
        f"Tenant atualizado: {updated_tenant['name']}",
        user_email=current_user.email,
        details={"tenant_id": tenant_id, "changes": list(update_data.keys())}
    )
    
    return Tenant(**updated_tenant)

@api_router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    reason: str,
    current_user: User = Depends(get_current_user)
):
    """Suspende um tenant - apenas super admins"""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas super administradores podem suspender tenants"
        )
    
    result = await db.tenants.update_one(
        {"id": tenant_id},
        {
            "$set": {
                "status": TenantStatus.SUSPENDED,
                "updated_at": datetime.utcnow(),
                "last_modified_by": current_user.id
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    log_advanced_error(
        ErrorLevel.WARNING,
        ErrorCategory.SYSTEM,
        f"Tenant suspenso: {tenant_id}",
        user_email=current_user.email,
        details={"tenant_id": tenant_id, "reason": reason}
    )
    
    return {"message": f"Tenant suspenso com sucesso. Motivo: {reason}"}

@api_router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user)
):
    """Reativa um tenant suspenso - apenas super admins"""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas super administradores podem reativar tenants"
        )
    
    result = await db.tenants.update_one(
        {"id": tenant_id},
        {
            "$set": {
                "status": TenantStatus.ACTIVE,
                "updated_at": datetime.utcnow(),
                "last_modified_by": current_user.id
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    log_advanced_error(
        ErrorLevel.INFO,
        ErrorCategory.SYSTEM,
        f"Tenant reativado: {tenant_id}",
        user_email=current_user.email,
        details={"tenant_id": tenant_id}
    )
    
    return {"message": "Tenant reativado com sucesso"}

@api_router.get("/tenants/{tenant_id}/stats")
async def get_tenant_stats(
    tenant_id: str,
    current_user: User = Depends(get_current_user)
):
    """Busca estatísticas de uso de um tenant"""
    # Super admin pode ver qualquer tenant, admin pode ver apenas o próprio
    if current_user.role != "super_admin":
        if current_user.role != "admin" or get_current_tenant_id() != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para ver estatísticas deste tenant"
            )
    
    # Buscar tenant
    tenant_doc = await db.tenants.find_one({"id": tenant_id})
    if not tenant_doc:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    
    # Calcular estatísticas
    tenant_filter = {"tenant_id": tenant_id}
    
    stats = {
        "tenant_info": {
            "id": tenant_id,
            "name": tenant_doc["name"],
            "plan": tenant_doc["plan"],
            "status": tenant_doc["status"],
            "created_at": tenant_doc["created_at"]
        },
        "usage": {
            "current_users": await db.users.count_documents(tenant_filter),
            "current_licenses": await db.licenses.count_documents(tenant_filter),
            "current_clients_pf": await db.clientes_pf.count_documents(tenant_filter),
            "current_clients_pj": await db.clientes_pj.count_documents(tenant_filter),
            "categories": await db.categories.count_documents(tenant_filter),
            "products": await db.products.count_documents(tenant_filter)
        },
        "limits": {
            "max_users": tenant_doc.get("max_users", 0),
            "max_licenses": tenant_doc.get("max_licenses", 0),
            "max_clients": tenant_doc.get("max_clients", 0)
        },
        "features": tenant_doc.get("features", {}),
        "compliance": {}
    }
    
    # Calcular compliance com limites
    usage = stats["usage"]
    limits = stats["limits"]
    
    stats["compliance"] = {
        "users_ok": usage["current_users"] <= limits["max_users"] if limits["max_users"] > 0 else True,
        "licenses_ok": usage["current_licenses"] <= limits["max_licenses"] if limits["max_licenses"] > 0 else True,
        "clients_ok": (usage["current_clients_pf"] + usage["current_clients_pj"]) <= limits["max_clients"] if limits["max_clients"] > 0 else True
    }
    
    return stats

@api_router.get("/my-tenant", response_model=Tenant)
async def get_my_tenant(current_user: User = Depends(get_current_user)):
    """Retorna informações do tenant do usuário atual"""
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Tenant não encontrado no contexto")
    
    tenant_doc = await db.tenants.find_one({"id": tenant_id})
    if not tenant_doc:
        # Se não existe tenant, criar um padrão para migração
        default_tenant = {
            "id": "default",
            "name": "AutoTech Services - Sistema Principal",
            "subdomain": "autotech",
            "contact_email": "admin@autotech.com",
            "status": TenantStatus.ACTIVE,
            "plan": TenantPlan.ENTERPRISE,
            "max_users": -1,  # Ilimitado
            "max_licenses": -1,  # Ilimitado
            "max_clients": -1,  # Ilimitado
            "features": get_plan_config(TenantPlan.ENTERPRISE)["features"],
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        await db.tenants.insert_one(default_tenant)
        tenant_doc = default_tenant
    
    return Tenant(**tenant_doc)

# ================================
# HELPER FUNCTIONS FOR SALES DASHBOARD
# ================================

async def get_expiring_licenses():
    """
    Busca licenças que estão expirando ou já expiraram
    """
    try:
        # Buscar licenças com data de expiração próxima (próximos 90 dias)
        future_date = datetime.utcnow() + timedelta(days=90)
        
        query_filter = add_tenant_filter({
            "$or": [
                {"expires_at": {"$lte": future_date}},  # Expirando em 90 dias
                {"expires_at": {"$lte": datetime.utcnow()}}  # Já expiraram
            ]
        })
        
        licenses = await db.licenses.find(query_filter).to_list(1000)
        return licenses
        
    except Exception as e:
        logger.error(f"Error fetching expiring licenses: {e}")
        return []

async def create_expiration_alert(license_doc):
    """
    Cria um alerta de expiração baseado nos dados da licença
    """
    try:
        expires_at = license_doc.get('expires_at')
        if not expires_at:
            return None
            
        # Calcular dias para expirar
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        days_to_expire = (expires_at - datetime.utcnow()).days
        
        # Buscar dados do cliente
        client_name = "Cliente não identificado"
        client_phone = None
        client_id = None
        client_type = None
        
        # Tentar buscar cliente PF
        if license_doc.get('client_pf_id'):
            query_filter_pf = add_tenant_filter({"id": license_doc['client_pf_id']})
            client_pf = await db.clientes_pf.find_one(query_filter_pf)
            if client_pf:
                client_name = client_pf.get('nome_completo', client_name)
                client_phone = client_pf.get('telefone_principal') or client_pf.get('whatsapp')
                client_id = client_pf.get('id')
                client_type = "pf"
        
        # Tentar buscar cliente PJ
        elif license_doc.get('client_pj_id'):
            query_filter_pj = add_tenant_filter({"id": license_doc['client_pj_id']})
            client_pj = await db.clientes_pj.find_one(query_filter_pj)
            if client_pj:
                client_name = client_pj.get('razao_social', client_name)
                client_phone = client_pj.get('telefone_principal') or client_pj.get('whatsapp')
                client_id = client_pj.get('id')
                client_type = "pj"
        
        # Se não encontrar cliente, criar dados padrão
        if not client_id:
            client_id = "unknown"
            client_type = "pf"
        
        # Determinar prioridade, status e tipo de alerta
        priority = get_alert_priority(days_to_expire)
        
        # Determinar tipo de alerta baseado nos dias para expirar
        if days_to_expire < 0:
            alert_type = "EXPIRED"
            status = "pending"  # Licença expirada precisa de ação
        elif days_to_expire <= 1:
            alert_type = "T-1"
            status = "pending"
        elif days_to_expire <= 7:
            alert_type = "T-7"
            status = "pending"
        elif days_to_expire <= 30:
            alert_type = "T-30"
            status = "pending"
        else:
            alert_type = "T-30"
            status = "pending"
        
        # Calcular valor de oportunidade de renovação
        renewal_value = license_doc.get('license_value', 0) or license_doc.get('price', 0) or random.uniform(500, 5000)
        
        alert = ExpirationAlert(
            id=str(uuid.uuid4()),
            client_id=client_id,
            client_type=client_type,
            client_name=client_name,
            license_id=license_doc['id'],
            license_name=license_doc.get('name', 'Licença'),
            expires_at=expires_at,
            days_to_expire=days_to_expire,
            alert_type=alert_type,
            status=status,
            priority=priority,
            contact_phone=client_phone,
            contact_whatsapp=client_phone,  # Usar mesmo telefone para WhatsApp por enquanto
            current_plan_value=renewal_value,
            renewal_opportunity_value=renewal_value,
            contact_attempts=0
        )
        
        return alert
        
    except Exception as e:
        logger.error(f"Error creating expiration alert: {e}")
        return None

async def calculate_sales_metrics(alerts, start_date, end_date):
    """
    Calcula métricas de vendas baseadas nos alertas
    """
    try:
        total_expiring = len(alerts)
        high_priority = len([a for a in alerts if a.priority == "high"])
        total_opportunity_value = sum(a.renewal_opportunity_value or 0 for a in alerts)
        
        # Métricas simuladas para o MVP
        metrics = SalesMetrics(
            total_expiring_licenses=total_expiring,
            licenses_expiring_30_days=len([a for a in alerts if 7 < a.days_to_expire <= 30]),
            licenses_expiring_7_days=len([a for a in alerts if 1 < a.days_to_expire <= 7]),
            licenses_expiring_1_day=len([a for a in alerts if a.days_to_expire <= 1 and a.days_to_expire >= 0]),
            expired_licenses=len([a for a in alerts if a.days_to_expire < 0]),
            contacted_leads=random.randint(10, 50),  # Simulado
            renewed_licenses=random.randint(5, 25),  # Simulado
            lost_opportunities=random.randint(2, 10),  # Simulado
            conversion_rate=random.uniform(15, 35),  # Simulado
            potential_revenue=total_opportunity_value,
            confirmed_revenue=random.uniform(5000, 25000),  # Simulado
            lost_revenue=random.uniform(1000, 8000),  # Simulado
            whatsapp_contacts=random.randint(20, 60),  # Simulado
            phone_contacts=random.randint(10, 30),  # Simulado
            email_contacts=random.randint(30, 80),  # Simulado
            sales_by_person={
                "João Silva": {"contacts": 25, "conversions": 12, "revenue": 8500.00},
                "Maria Santos": {"contacts": 20, "conversions": 8, "revenue": 6200.00}
            },
            period_start=start_date,
            period_end=end_date
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating sales metrics: {e}")
        return SalesMetrics(
            total_expiring_licenses=0,
            licenses_expiring_30_days=0,
            licenses_expiring_7_days=0,
            licenses_expiring_1_day=0,
            expired_licenses=0,
            contacted_leads=0,
            renewed_licenses=0,
            lost_opportunities=0,
            conversion_rate=0,
            potential_revenue=0,
            confirmed_revenue=0,
            lost_revenue=0,
            whatsapp_contacts=0,
            phone_contacts=0,
            email_contacts=0,
            sales_by_person={},
            period_start=start_date,
            period_end=end_date
        )

async def get_recent_sales_activities():
    """
    Busca atividades recentes de vendas (simulado para MVP)
    """
    try:
        # Para o MVP, retornar atividades simuladas
        activities = [
            {
                "id": str(uuid.uuid4()),
                "type": "whatsapp_sent",
                "description": "Mensagem de renovação enviada para João Silva",
                "timestamp": datetime.utcnow() - timedelta(minutes=30),
                "user": "Vendedor 1"
            },
            {
                "id": str(uuid.uuid4()),
                "type": "renewal_closed",
                "description": "Renovação fechada - Empresa ABC Ltda",
                "timestamp": datetime.utcnow() - timedelta(hours=2),
                "user": "Vendedor 2"
            },
            {
                "id": str(uuid.uuid4()),
                "type": "follow_up",
                "description": "Follow-up realizado com Maria Santos",
                "timestamp": datetime.utcnow() - timedelta(hours=4),
                "user": "Vendedor 1"
            }
        ]
        
        return activities
        
    except Exception as e:
        logger.error(f"Error fetching recent activities: {e}")
        return []

async def get_alert_data(alert_id: str):
    """
    Busca dados do cliente e licença baseado no ID do alerta
    Para o MVP, simular dados baseados no alert_id
    """
    try:
        # Para o MVP, simular dados baseados no alert_id
        # Em produção, buscar dados reais do banco
        
        # Simular dados do cliente
        client_data = {
            "id": f"client_{alert_id[:8]}",
            "nome_completo": f"Cliente {alert_id[:8]}",
            "razao_social": f"Empresa {alert_id[:8]} Ltda",
            "whatsapp": "+5511999999999",
            "celular": "+5511888888888",
            "email_principal": f"cliente{alert_id[:8]}@email.com"
        }
        
        # Simular dados da licença
        license_data = {
            "id": f"license_{alert_id[:8]}",
            "name": f"Licença {alert_id[:8]}",
            "expires_at": datetime.utcnow() + timedelta(days=random.randint(-30, 30)),
            "price": random.uniform(500, 5000)
        }
        
        return client_data, license_data
        
    except Exception as e:
        logger.error(f"Error fetching alert data: {e}")
        return None, None

@api_router.get("/rbac/users/{user_id}/permissions")
async def get_user_permissions_endpoint(user_id: str, current_user: User = Depends(require_permission("users.read"))):
    query_filter = add_tenant_filter({"id": user_id})
    user_doc = await db.users.find_one(query_filter)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_permissions = await get_user_permissions(user_doc['email'])
    
    # Buscar detalhes das permissões
    permission_details = []
    if user_permissions:
        permissions = await db.permissions.find({"name": {"$in": user_permissions}}).to_list(1000)
        permission_details = [Permission(**perm) for perm in permissions]
    
    # Buscar roles do usuário
    rbac_info = user_doc.get('rbac', {})
    role_ids = rbac_info.get('roles', [])
    user_roles = []
    if role_ids:
        # 🚨 CRÍTICO: Filtrar roles apenas do tenant do usuário
        user_tenant_id = user_doc.get("tenant_id", "default")
        roles_filter = add_tenant_filter({"id": {"$in": role_ids}}, user_tenant_id)
        roles = await db.roles.find(roles_filter).to_list(1000)
        user_roles = [Role(**role) for role in roles]
    
    return {
        "user_id": user_id,
        "permissions": permission_details,
        "roles": user_roles,
        "has_permissions": len(user_permissions) > 0
    }

@api_router.get("/rbac/users", response_model=List[dict])
async def get_all_users_rbac(current_user: User = Depends(require_permission("users.read"))):
    # Aplicar filtro de tenant
    query_filter = add_tenant_filter({})
    users = await db.users.find(query_filter).to_list(1000)
    
    result = []
    for user in users:
        rbac_info = user.get('rbac', {})
        role_ids = rbac_info.get('roles', [])
        
        # Buscar nomes dos roles
        user_roles = []
        if role_ids:
            # 🚨 CRÍTICO: Filtrar roles apenas do tenant do usuário
            user_tenant_id = user.get("tenant_id", "default")
            roles_filter = add_tenant_filter({"id": {"$in": role_ids}}, user_tenant_id)
            roles = await db.roles.find(roles_filter).to_list(1000)
            user_roles = [{"id": role["id"], "name": role["name"]} for role in roles]
        
        result.append({
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user.get("role", "user"),  # Role legado
            "rbac_roles": user_roles,
            "is_active": rbac_info.get('is_active', True),
            "last_login": user.get("last_login"),
            "created_at": user.get("created_at")
        })
    
    return result

# Debug endpoint para testar permissões do usuário
# Endpoints de Verificação de Duplicatas e Monitoramento Avançado

@api_router.get("/system/check-duplicates/user")
async def check_user_duplicate_endpoint(
    email: str, 
    name: str = None,
    exclude_id: str = None,
    current_user: User = Depends(require_permission("rbac.read"))
):
    """Endpoint para verificar duplicatas de usuários antes da criação"""
    try:
        result = await check_user_duplicates(email, name, exclude_id)
        
        log_advanced_error(
            ErrorLevel.INFO,
            ErrorCategory.VALIDATION,
            f"Verificação de duplicata de usuário solicitada: {email}",
            user_email=current_user.email,
            details={"has_duplicates": result.get("has_duplicates", False)}
        )
        
        return result
    except Exception as e:
        log_advanced_error(
            ErrorLevel.ERROR,
            ErrorCategory.SYSTEM,
            "Erro ao verificar duplicatas de usuário via API",
            user_email=current_user.email,
            exception=e
        )
        raise HTTPException(status_code=500, detail="Erro na verificação de duplicatas")

@api_router.get("/system/check-duplicates/role")
async def check_role_duplicate_endpoint(
    name: str,
    exclude_id: str = None, 
    current_user: User = Depends(require_permission("rbac.read"))
):
    """Endpoint para verificar duplicatas de roles antes da criação"""
    try:
        result = await check_role_duplicates(name, exclude_id)
        
        log_advanced_error(
            ErrorLevel.INFO,
            ErrorCategory.VALIDATION,
            f"Verificação de duplicata de role solicitada: {name}",
            user_email=current_user.email,
            details={"has_duplicates": result.get("has_duplicates", False)}
        )
        
        return result
    except Exception as e:
        log_advanced_error(
            ErrorLevel.ERROR,
            ErrorCategory.SYSTEM,
            "Erro ao verificar duplicatas de role via API",
            user_email=current_user.email,
            exception=e
        )
        raise HTTPException(status_code=500, detail="Erro na verificação de duplicatas")

@api_router.get("/system/logs/advanced")
async def get_advanced_logs(
    level: str = None,
    category: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    current_user: User = Depends(require_permission("system.monitor"))
):
    """Endpoint para recuperar logs avançados com filtros"""
    try:
        # Ler logs do arquivo de manutenção
        logs = []
        
        # Filtros baseados nos parâmetros
        level_filter = level.upper() if level else None
        category_filter = category.upper() if category else None
        
        # Simulação de leitura de logs (implementar leitura real do arquivo)
        # Por agora, retornar logs mockados estruturados
        mock_logs = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "category": "SYSTEM",
                "message": "Sistema funcionando normalmente",
                "user_email": "system",
                "details": {"status": "healthy"}
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "WARNING", 
                "category": "DUPLICATE_DATA",
                "message": "Tentativa de duplicação detectada e bloqueada",
                "user_email": current_user.email,
                "details": {"blocked_action": "role_creation"}
            }
        ]
        
        # Aplicar filtros
        filtered_logs = mock_logs
        if level_filter:
            filtered_logs = [log for log in filtered_logs if log["level"] == level_filter]
        if category_filter:
            filtered_logs = [log for log in filtered_logs if log["category"] == category_filter]
            
        return {
            "logs": filtered_logs[:limit],
            "total": len(filtered_logs),
            "filters_applied": {
                "level": level_filter,
                "category": category_filter,
                "limit": limit
            }
        }
        
    except Exception as e:
        log_advanced_error(
            ErrorLevel.ERROR,
            ErrorCategory.SYSTEM,
            "Erro ao recuperar logs avançados",
            user_email=current_user.email,
            exception=e
        )
        raise HTTPException(status_code=500, detail="Erro ao carregar logs avançados")

@api_router.get("/system/health-check")
async def advanced_health_check(current_user: User = Depends(require_permission("system.monitor"))):
    """Health check avançado com métricas do sistema"""
    try:
        # Verificar status dos componentes principais
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "components": {
                "database": {"status": "healthy", "response_time_ms": 0},
                "rbac_system": {"status": "healthy", "roles_count": 0, "permissions_count": 0},
                "authentication": {"status": "healthy", "active_sessions": 0},
                "duplicate_prevention": {"status": "active", "rules_active": True}
            },
            "metrics": {
                "total_users": 0,
                "total_roles": 0, 
                "total_permissions": 0,
                "duplicate_blocks_today": 0
            },
            "alerts": []
        }
        
        # Testar conexão com banco
        try:
            start_time = datetime.utcnow()
            roles_count = await db.roles.count_documents({"tenant_id": current_user.tenant_id})
            users_count = await db.users.count_documents({"tenant_id": current_user.tenant_id})
            permissions_count = await db.permissions.count_documents({"tenant_id": current_user.tenant_id})
            end_time = datetime.utcnow()
            
            health_status["components"]["database"]["response_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
            health_status["components"]["rbac_system"]["roles_count"] = roles_count
            health_status["components"]["rbac_system"]["permissions_count"] = permissions_count
            health_status["metrics"]["total_users"] = users_count
            health_status["metrics"]["total_roles"] = roles_count
            health_status["metrics"]["total_permissions"] = permissions_count
            
        except Exception as db_error:
            health_status["components"]["database"]["status"] = "unhealthy"
            health_status["overall_status"] = "degraded"
            health_status["alerts"].append(f"Database connection issue: {str(db_error)}")
        
        # Log do health check
        log_advanced_error(
            ErrorLevel.INFO,
            ErrorCategory.SYSTEM,
            f"Health check executado - Status: {health_status['overall_status']}",
            user_email=current_user.email,
            details=health_status["metrics"]
        )
        
        return health_status
        
    except Exception as e:
        log_advanced_error(
            ErrorLevel.CRITICAL,
            ErrorCategory.SYSTEM,
            "Falha crítica no health check do sistema",
            user_email=current_user.email,
            exception=e
        )
        raise HTTPException(status_code=500, detail="Falha no health check do sistema")

# ================================
# DASHBOARD DE VENDAS - ENDPOINTS
# ================================

@api_router.get("/sales-dashboard/summary", response_model=SalesDashboardSummary)
async def get_sales_dashboard_summary(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Endpoint principal do Dashboard de Vendas
    Retorna resumo executivo com métricas e alertas prioritários
    """
    try:
        # Período de análise (últimos 90 dias)
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=90)
        
        # Buscar licenças que estão expirando ou já expiraram
        expiring_licenses = await get_expiring_licenses()
        
        # Gerar alertas de expiração
        alerts = []
        for license_doc in expiring_licenses:
            alert = await create_expiration_alert(license_doc)
            if alert:
                alerts.append(alert)
        
        # Calcular métricas
        metrics = await calculate_sales_metrics(alerts, start_date, end_date)
        
        # Ordenar alertas por prioridade
        priority_alerts = sorted(
            [a for a in alerts if a.priority == "high"],
            key=lambda x: x.days_to_expire
        )[:10]  # Top 10 alertas críticos
        
        # Atividades recentes (simulado por enquanto)
        recent_activities = await get_recent_sales_activities()
        
        # Top oportunidades por valor
        top_opportunities = sorted(
            [
                {
                    "client_name": a.client_name,
                    "license_name": a.license_name,
                    "potential_value": a.renewal_opportunity_value or 0,
                    "days_to_expire": a.days_to_expire,
                    "status": a.status
                }
                for a in alerts 
                if a.renewal_opportunity_value
            ],
            key=lambda x: x["potential_value"],
            reverse=True
        )[:5]
        
        summary = SalesDashboardSummary(
            metrics=metrics,
            priority_alerts=priority_alerts,
            recent_activities=recent_activities,
            top_opportunities=top_opportunities
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating sales dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating dashboard: {str(e)}")

@api_router.get("/sales-dashboard/expiring-licenses", response_model=List[ExpirationAlert])
async def get_expiring_licenses_alerts(
    days_ahead: int = 30,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Lista licenças expirando com alertas de vendas
    """
    try:
        # Buscar licenças expirando nos próximos X dias
        future_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        # Query para buscar licenças expirando
        # CRÍTICO: Usar tenant_id do usuário atual para isolamento
        query_filter = add_tenant_filter({
            "$or": [
                {"expires_at": {"$lte": future_date}},  # Expirando em X dias
                {"expires_at": {"$lte": datetime.utcnow()}}  # Já expiraram
            ]
        }, current_user.tenant_id)
        
        licenses = await db.licenses.find(query_filter).to_list(1000)
        
        # Converter para alertas
        alerts = []
        for license_doc in licenses:
            alert = await create_expiration_alert(license_doc)
            if alert:
                # Filtros opcionais
                if status and alert.status != status:
                    continue
                if priority and alert.priority != priority:
                    continue
                alerts.append(alert)
        
        # Ordenar por urgência (dias para expirar)
        alerts.sort(key=lambda x: x.days_to_expire)
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error fetching expiring licenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/sales-dashboard/send-whatsapp/{alert_id}")
async def send_whatsapp_renewal_message(
    alert_id: str,
    custom_message: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Envia mensagem de WhatsApp para renovação de licença
    """
    try:
        # Para este MVP, vamos simular o envio baseado nos dados do alerta
        # Em produção, buscar o alerta real do banco
        
        # Simular busca de dados do cliente e licença
        client_data, license_data = await get_alert_data(alert_id)
        
        if not client_data or not license_data:
            raise HTTPException(status_code=404, detail="Alerta não encontrado")
        
        # Determinar tipo de alerta
        expires_at = license_data.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        days_to_expire = (expires_at - datetime.utcnow()).days if expires_at else 0
        alert_type = get_alert_type(days_to_expire)
        
        # Enviar mensagem WhatsApp
        whatsapp_message = await send_renewal_whatsapp_message(
            client_data=client_data,
            license_data=license_data,
            alert_type=alert_type,
            salesperson=current_user.name
        )
        
        # Registrar contato
        contact_record = SalesContact(
            alert_id=alert_id,
            contact_method="whatsapp",
            contacted_by=current_user.id,
            notes=f"Mensagem de renovação enviada via WhatsApp - Tipo: {alert_type}",
            outcome="answered" if whatsapp_message.get("status") == "sent" else "no_answer"
        )
        
        # Log da atividade
        maintenance_logger.log("whatsapp_renewal_sent", {
            "alert_id": alert_id,
            "client_id": client_data.get('id'),
            "status": whatsapp_message.get("status", "unknown"),
            "sent_by": current_user.id,
            "alert_type": alert_type
        })
        
        return {
            "message": "Mensagem WhatsApp enviada com sucesso",
            "whatsapp_status": whatsapp_message.get("status", "unknown"),
            "alert_type": alert_type,
            "phone_number": whatsapp_message.get("phone_number", ""),
            "message_id": whatsapp_message.get("id", "")
        }
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp renewal message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/sales-dashboard/bulk-whatsapp")
async def send_bulk_whatsapp_messages(
    alert_ids: List[str],
    message_template: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Envia mensagens WhatsApp em lote para múltiplos alertas
    """
    try:
        results = []
        
        for alert_id in alert_ids:
            try:
                # Buscar dados do alerta
                client_data, license_data = await get_alert_data(alert_id)
                
                if client_data and license_data:
                    # Determinar tipo de alerta
                    expires_at = license_data.get('expires_at')
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    
                    days_to_expire = (expires_at - datetime.utcnow()).days if expires_at else 0
                    alert_type = get_alert_type(days_to_expire)
                    
                    # Enviar mensagem
                    whatsapp_message = await send_renewal_whatsapp_message(
                        client_data=client_data,
                        license_data=license_data,
                        alert_type=alert_type,
                        salesperson=current_user.name
                    )
                    
                    results.append({
                        "alert_id": alert_id,
                        "status": "sent" if whatsapp_message.get("status") == "sent" else "failed",
                        "client_name": client_data.get('nome_completo') or client_data.get('razao_social'),
                        "phone": whatsapp_message.get("phone_number", ""),
                        "message_id": whatsapp_message.get("id", "")
                    })
                    
                else:
                    results.append({
                        "alert_id": alert_id,
                        "status": "failed",
                        "error": "Dados não encontrados"
                    })
                    
            except Exception as e:
                results.append({
                    "alert_id": alert_id,
                    "status": "failed",
                    "error": str(e)
                })
                
            # Delay entre mensagens para evitar spam
            await asyncio.sleep(1)
        
        # Estatísticas do envio
        sent_count = len([r for r in results if r["status"] == "sent"])
        failed_count = len(results) - sent_count
        
        maintenance_logger.log("bulk_whatsapp_campaign", {
            "total_messages": len(results),
            "sent": sent_count,
            "failed": failed_count,
            "sent_by": current_user.id
        })
        
        return {
            "message": f"Campanha concluída: {sent_count} enviadas, {failed_count} falharam",
            "total": len(results),
            "sent": sent_count,
            "failed": failed_count,
            "details": results
        }
        
    except Exception as e:
        logger.error(f"Error sending bulk WhatsApp messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/sales-dashboard/analytics", response_model=Dict[str, Any])
async def get_sales_analytics(
    period_days: int = 30,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Analytics avançadas do dashboard de vendas
    """
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=period_days)
        
        # Métricas por canal (simulado por enquanto - em produção buscar do banco)
        channel_metrics = {
            "whatsapp": {
                "contacts": 45,
                "responses": 32,
                "conversions": 18,
                "response_rate": 71.1,
                "conversion_rate": 40.0
            },
            "phone": {
                "contacts": 23,
                "responses": 19,
                "conversions": 12,
                "response_rate": 82.6,
                "conversion_rate": 52.2
            },
            "email": {
                "contacts": 67,
                "responses": 23,
                "conversions": 8,
                "response_rate": 34.3,
                "conversion_rate": 11.9
            }
        }
        
        # Métricas por vendedor (simulado)
        salesperson_metrics = {
            "João Silva": {"contacts": 45, "conversions": 23, "revenue": 12500.00},
            "Maria Santos": {"contacts": 38, "conversions": 19, "revenue": 9800.00},
            "Carlos Oliveira": {"contacts": 52, "conversions": 16, "revenue": 8900.00}
        }
        
        # Métricas temporais (simulado)
        daily_metrics = []
        for i in range(period_days):
            date = start_date + timedelta(days=i)
            daily_metrics.append({
                "date": date.isoformat(),
                "contacts": random.randint(0, 15),
                "renewals": random.randint(0, 8),
                "revenue": random.uniform(0, 3000)
            })
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period_days
            },
            "channel_metrics": channel_metrics,
            "salesperson_metrics": salesperson_metrics,
            "daily_metrics": daily_metrics,
            "summary": {
                "total_contacts": sum(ch["contacts"] for ch in channel_metrics.values()),
                "total_responses": sum(ch["responses"] for ch in channel_metrics.values()),
                "total_conversions": sum(ch["conversions"] for ch in channel_metrics.values()),
                "total_revenue": sum(sp["revenue"] for sp in salesperson_metrics.values()),
                "avg_response_rate": sum(ch["response_rate"] for ch in channel_metrics.values()) / len(channel_metrics),
                "avg_conversion_rate": sum(ch["conversion_rate"] for ch in channel_metrics.values()) / len(channel_metrics)
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating sales analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Tenant Management Routes
@api_router.post("/tenants", response_model=Tenant)
async def create_tenant(tenant_data: TenantCreate, current_user: User = Depends(get_current_user)):
    """
    Criar novo tenant (disponível apenas para super admins)
    """
    # Verificar se o usuário é super admin
    if not is_super_admin():
        user_permissions = await get_user_permissions(current_user.email)
        if not check_permission(user_permissions, "tenants.create"):
            raise HTTPException(status_code=403, detail="Permission required: tenants.create")
    
    try:
        # Verificar se subdomain já existe
        existing = await db.tenants.find_one({"subdomain": tenant_data.subdomain})
        if existing:
            raise HTTPException(status_code=400, detail="Subdomain already exists")
        
        # Aplicar configurações do plano
        tenant_dict = tenant_data.dict()
        tenant_dict = apply_plan_limits(tenant_dict, tenant_data.plan)
        
        # Criar tenant
        tenant = Tenant(**tenant_dict)
        tenant_doc = tenant.dict()
        
        result = await db.tenants.insert_one(tenant_doc)
        
        # Criar usuário administrador inicial para o tenant
        admin_user_data = {
            "id": str(uuid.uuid4()),
            "name": tenant_data.admin_name,
            "email": tenant_data.admin_email,
            "password_hash": pwd_context.hash(tenant_data.admin_password),
            "role": "admin",
            "tenant_id": tenant.id,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "rbac": {
                "roles": [],  # Será configurado na inicialização RBAC
                "is_active": True,
                "last_permission_update": datetime.utcnow()
            }
        }
        
        # CRÍTICO: Garantir tenant_id no documento admin
        admin_user_with_tenant = add_tenant_to_document(admin_user_data, tenant.id)
        await db.users.insert_one(admin_user_with_tenant)
        
        return tenant
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating tenant: {str(e)}")

@api_router.get("/tenants", response_model=List[Tenant])
async def list_tenants(current_user: User = Depends(get_current_user)):
    """
    Listar todos os tenants (disponível apenas para super admins)
    """
    if not is_super_admin():
        user_permissions = await get_user_permissions(current_user.email)
        if not check_permission(user_permissions, "tenants.read"):
            raise HTTPException(status_code=403, detail="Permission required: tenants.read")
    
    try:
        tenants = await db.tenants.find().to_list(1000)
        return [Tenant(**tenant) for tenant in tenants]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing tenants: {str(e)}")

@api_router.get("/tenants/{tenant_id}", response_model=Tenant)
async def get_tenant(tenant_id: str, current_user: User = Depends(get_current_user)):
    """
    Obter detalhes de um tenant específico
    """
    # Super admin pode ver qualquer tenant, admin só pode ver seu próprio
    if not is_super_admin() and get_current_tenant_id() != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
    
    try:
        tenant = await db.tenants.find_one({"id": tenant_id})
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return Tenant(**tenant)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tenant: {str(e)}")

@api_router.put("/tenants/{tenant_id}", response_model=Tenant)
async def update_tenant(
    tenant_id: str, 
    tenant_update: TenantUpdate, 
    current_user: User = Depends(get_current_user)
):
    """
    Atualizar um tenant
    """
    # Super admin pode atualizar qualquer tenant, admin só pode seu próprio
    if not is_super_admin() and get_current_tenant_id() != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
    
    try:
        # Buscar tenant atual
        tenant = await db.tenants.find_one({"id": tenant_id})
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Aplicar updates
        update_data = tenant_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        update_data["last_modified_by"] = current_user.id
        
        # Se mudou o plano, aplicar novos limites
        if "plan" in update_data:
            new_plan = update_data["plan"]
            update_data = apply_plan_limits(update_data, TenantPlan(new_plan))
        
        await db.tenants.update_one(
            {"id": tenant_id}, 
            {"$set": update_data}
        )
        
        # Buscar tenant atualizado
        updated_tenant = await db.tenants.find_one({"id": tenant_id})
        return Tenant(**updated_tenant)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating tenant: {str(e)}")

@api_router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, current_user: User = Depends(get_current_user)):
    """
    Excluir um tenant (apenas super admins)
    CUIDADO: Esta operação é irreversível e remove todos os dados do tenant
    """
    if not is_super_admin():
        user_permissions = await get_user_permissions(current_user.email)
        if not check_permission(user_permissions, "tenants.delete"):
            raise HTTPException(status_code=403, detail="Permission required: tenants.delete")
    
    try:
        # Verificar se tenant existe
        tenant = await db.tenants.find_one({"id": tenant_id})
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Remover todos os dados do tenant de todas as coleções
        collections_to_clean = [
            "users", "categories", "products", "licenses", 
            "clients_pf", "clients_pj", "roles", "permissions"
        ]
        
        for collection_name in collections_to_clean:
            collection = getattr(db, collection_name)
            await collection.delete_many({"tenant_id": tenant_id})
        
        # Remover o tenant
        await db.tenants.delete_one({"id": tenant_id})
        
        return {"message": "Tenant and all associated data deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting tenant: {str(e)}")

# Tenant Context Routes
@api_router.get("/tenant/current", response_model=Tenant)
async def get_current_tenant_info(current_user: User = Depends(get_current_user)):
    """
    Obter informações do tenant atual
    """
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context available")
    
    try:
        tenant = await db.tenants.find_one({"id": tenant_id})
        if not tenant:
            raise HTTPException(status_code=404, detail="Current tenant not found")
        
        return Tenant(**tenant)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving current tenant: {str(e)}")

@api_router.get("/tenant/stats")
async def get_tenant_stats(current_user: User = Depends(get_current_user)):
    """
    Obter estatísticas de uso do tenant atual
    """
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context available")
    
    try:
        # Contar recursos do tenant
        users_count = await db.users.count_documents({"tenant_id": tenant_id, "is_active": True})
        licenses_count = await db.licenses.count_documents({"tenant_id": tenant_id})
        clients_pf_count = await db.clients_pf.count_documents({"tenant_id": tenant_id})
        clients_pj_count = await db.clients_pj.count_documents({"tenant_id": tenant_id})
        total_clients = clients_pf_count + clients_pj_count
        
        # Buscar tenant para obter limites
        tenant = await db.tenants.find_one({"id": tenant_id})
        
        stats = {
            "tenant_id": tenant_id,
            "usage": {
                "users": {
                    "current": users_count,
                    "limit": tenant.get("max_users", 0) if tenant else 0,
                    "percentage": (users_count / tenant.get("max_users", 1) * 100) if tenant else 0
                },
                "licenses": {
                    "current": licenses_count,
                    "limit": tenant.get("max_licenses", 0) if tenant else 0,
                    "percentage": (licenses_count / tenant.get("max_licenses", 1) * 100) if tenant and tenant.get("max_licenses", 0) > 0 else 0
                },
                "clients": {
                    "current": total_clients,
                    "limit": tenant.get("max_clients", 0) if tenant else 0,
                    "percentage": (total_clients / tenant.get("max_clients", 1) * 100) if tenant else 0
                }
            },
            "plan": tenant.get("plan") if tenant else "free",
            "features": tenant.get("features", {}) if tenant else {}
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tenant stats: {str(e)}")

# Notification System Routes
@api_router.post("/notifications", response_model=Notification)
async def create_notification(
    notification_data: CreateNotificationRequest, 
    current_user: User = Depends(get_current_user)
):
    """
    Criar uma nova notificação
    """
    try:
        tenant_id = current_user.tenant_id
        
        # Criar notificação
        notification_dict = notification_data.dict()
        notification_dict["tenant_id"] = tenant_id
        
        notification = Notification(**notification_dict)
        # CRÍTICO: Garantir tenant_id no documento antes de inserir
        notification_dict_with_tenant = add_tenant_to_document(notification.dict(), tenant_id)
        await db.notifications.insert_one(notification_dict_with_tenant)
        
        # Adicionar à fila se não agendada para o futuro
        if not notification.scheduled_for or notification.scheduled_for <= datetime.utcnow():
            queue_item = NotificationQueue(
                tenant_id=tenant_id,
                notification_id=notification.id,
                priority=1 if notification.priority == NotificationPriority.URGENT else 2
            )
            # CRÍTICO: Garantir tenant_id no documento da fila
            queue_dict_with_tenant = add_tenant_to_document(queue_item.dict(), tenant_id)
            await db.notification_queue.insert_one(queue_dict_with_tenant)
        
        return notification
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating notification: {str(e)}")

@api_router.get("/notifications", response_model=List[Notification])
async def list_notifications(
    status: Optional[NotificationStatus] = None,
    type: Optional[NotificationType] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    Listar notificações do tenant atual
    """
    try:
        query_filter = add_tenant_filter({}, current_user.tenant_id)
        
        if status:
            query_filter["status"] = status
        if type:
            query_filter["type"] = type
        
        notifications = await db.notifications.find(query_filter).sort("created_at", -1).limit(limit).to_list(limit)
        return [Notification(**notif) for notif in notifications]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing notifications: {str(e)}")

@api_router.get("/notifications/config", response_model=NotificationConfig)
async def get_notification_config(current_user: User = Depends(get_current_user)):
    """
    Obter configurações de notificação do tenant atual
    """
    try:
        tenant_id = current_user.tenant_id
        
        config = await db.notification_configs.find_one({"tenant_id": tenant_id})
        
        if not config:
            # Criar configuração padrão
            default_config = NotificationConfig(tenant_id=tenant_id)
            await db.notification_configs.insert_one(default_config.dict())
            return default_config
        
        return NotificationConfig(**config)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving notification config: {str(e)}")

@api_router.put("/notifications/config", response_model=NotificationConfig)
async def update_notification_config(
    config_update: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Atualizar configurações de notificação do tenant
    """
    try:
        tenant_id = current_user.tenant_id
        
        # Verificar permissão (apenas admins podem alterar configurações)
        if current_user.role not in ["admin", "super_admin"]:
            user_permissions = await get_user_permissions(current_user.email)
            if not check_permission(user_permissions, "notifications.manage"):
                raise HTTPException(status_code=403, detail="Permission required: notifications.manage")
        
        config_update["tenant_id"] = tenant_id
        config_update["updated_at"] = datetime.utcnow()
        
        # Upsert configuração
        await db.notification_configs.update_one(
            {"tenant_id": tenant_id},
            {"$set": config_update},
            upsert=True
        )
        
        # Buscar configuração atualizada
        updated_config = await db.notification_configs.find_one({"tenant_id": tenant_id})
        return NotificationConfig(**updated_config)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating notification config: {str(e)}")

@api_router.get("/notifications/stats", response_model=NotificationStats)
async def get_notification_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Obter estatísticas de notificações do tenant atual
    """
    try:
        tenant_id = current_user.tenant_id
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)
        
        # Query base com filtro de tenant e período
        base_filter = {
            "tenant_id": tenant_id,
            "created_at": {"$gte": period_start, "$lte": period_end}
        }
        
        # Agregações para estatísticas
        pipeline = [
            {"$match": base_filter},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "sent": {"$sum": {"$cond": [{"$eq": ["$status", "sent"]}, 1, 0]}},
                "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}},
                "pending": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}},
                "expiring_30": {"$sum": {"$cond": [{"$eq": ["$type", "license_expiring_30"]}, 1, 0]}},
                "expiring_7": {"$sum": {"$cond": [{"$eq": ["$type", "license_expiring_7"]}, 1, 0]}},
                "expiring_1": {"$sum": {"$cond": [{"$eq": ["$type", "license_expiring_1"]}, 1, 0]}},
                "expired": {"$sum": {"$cond": [{"$eq": ["$type", "license_expired"]}, 1, 0]}},
                "email_sent": {"$sum": {"$cond": [{"$eq": ["$channel", "email"]}, 1, 0]}},
                "in_app_sent": {"$sum": {"$cond": [{"$eq": ["$channel", "in_app"]}, 1, 0]}}
            }}
        ]
        
        result = await db.notifications.aggregate(pipeline).to_list(1)
        
        if not result:
            # Nenhuma notificação no período
            stats_data = {
                "tenant_id": tenant_id,
                "period_start": period_start,
                "period_end": period_end
            }
        else:
            data = result[0]
            total = data.get("total", 0)
            sent = data.get("sent", 0)
            
            stats_data = {
                "tenant_id": tenant_id,
                "period_start": period_start,
                "period_end": period_end,
                "total_notifications": total,
                "sent_successfully": sent,
                "failed": data.get("failed", 0),
                "pending": data.get("pending", 0),
                "license_expiring_30": data.get("expiring_30", 0),
                "license_expiring_7": data.get("expiring_7", 0),
                "license_expiring_1": data.get("expiring_1", 0),
                "license_expired": data.get("expired", 0),
                "email_sent": data.get("email_sent", 0),
                "in_app_sent": data.get("in_app_sent", 0),
                "success_rate": (sent / total * 100) if total > 0 else 0.0
            }
        
        return NotificationStats(**stats_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving notification stats: {str(e)}")

@api_router.get("/notifications/{notification_id}", response_model=Notification)
async def get_notification(
    notification_id: str, 
    current_user: User = Depends(get_current_user)
):
    """
    Obter detalhes de uma notificação específica
    """
    try:
        query_filter = add_tenant_filter({"id": notification_id}, current_user.tenant_id)
        notification = await db.notifications.find_one(query_filter)
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return Notification(**notification)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving notification: {str(e)}")

@api_router.put("/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Marcar notificação como lida (para notificações in-app)
    """
    try:
        query_filter = add_tenant_filter({"id": notification_id}, current_user.tenant_id)
        
        # Atualizar status
        update_result = await db.notifications.update_one(
            query_filter,
            {
                "$set": {
                    "status": NotificationStatus.READ,
                    "read_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if update_result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Log da ação
        log_entry = NotificationLog(
            tenant_id=current_user.tenant_id,
            notification_id=notification_id,
            action="marked_read",
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.READ,
            event_data={"user_id": current_user.id}
        )
        await db.notification_logs.insert_one(log_entry.dict())
        
        return {"message": "Notification marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notification as read: {str(e)}")

# Maintenance and Logging Routes
@api_router.get("/maintenance/logs")
async def get_maintenance_logs(
    lines: int = 100,
    current_user: User = Depends(get_current_admin_user)
):
    """Get the latest maintenance logs"""
    try:
        log_file = "/app/maintenance_log.txt"
        if not os.path.exists(log_file):
            return {"logs": [], "message": "No logs found"}
            
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            
        # Get the last 'lines' entries
        recent_logs = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in recent_logs],
            "total_lines": len(all_lines),
            "showing": len(recent_logs)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao ler logs: {str(e)}"
        )

@api_router.post("/maintenance/clear-logs")
async def clear_maintenance_logs(current_user: User = Depends(get_current_admin_user)):
    """Clear maintenance logs"""
    try:
        log_file = "/app/maintenance_log.txt"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("")
        return {"message": "Logs limpos com sucesso"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao limpar logs: {str(e)}"
        )

@api_router.get("/clientes-pj", response_model=List[PessoaJuridica])
async def get_pessoas_juridicas(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(require_tenant)
):
    try:
        # Super Admin vê todos os clientes independente do status
        if current_user.role == UserRole.SUPER_ADMIN:
            query_filter = {}  # Super admin sees all globally
        else:
            # Outros usuários veem apenas clientes ativos em seu tenant
            query_filter = add_tenant_filter({"status": {"$ne": "inactive"}}, tenant_id)
        
        if current_user.role == UserRole.ADMIN or current_user.role == UserRole.SUPER_ADMIN:
            clients = await db.clientes_pj.find(query_filter).to_list(1000)
        else:
            clients = await db.clientes_pj.find(query_filter).to_list(1000)
        
        # Converter e limpar dados
        result = []
        for client in clients:
            # Remove MongoDB ObjectId
            client.pop("_id", None)
            
            # Garantir campos obrigatórios
            if not client.get("id"):
                continue
            
            # Normalizar client_type
            client_type = client.get("client_type", "pj")
            if client_type.upper() == "PF":
                client["client_type"] = "pf"
            elif client_type.upper() == "PJ":
                client["client_type"] = "pj"
            else:
                client["client_type"] = "pj"  # padrão
            
            # Normalizar regime_tributario
            regime = client.get("regime_tributario", "") or ""
            if "simples" in regime.lower():
                client["regime_tributario"] = "simples"
            elif "presumido" in regime.lower():
                client["regime_tributario"] = "lucro_presumido"
            elif "real" in regime.lower():
                client["regime_tributario"] = "lucro_real"
            elif "mei" in regime.lower():
                client["regime_tributario"] = "mei"
            else:
                client["regime_tributario"] = "simples"  # padrão
                
            # Para usuários não-admin, aplicar mascaramento básico de CNPJ
            if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                cnpj = client.get("cnpj", "")
                if len(cnpj) >= 14:
                    client["cnpj"] = cnpj[:2] + "***" + cnpj[-2:]
            
            try:
                result.append(PessoaJuridica(**client))
            except Exception as e:
                logger.warning(f"Skipping invalid client PJ {client.get('id')}: {e}")
                continue
        
        return result
    except Exception as e:
        logger.error(f"Error fetching pessoas jurídicas: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching pessoas jurídicas: {str(e)}")

@api_router.get("/clientes-pj/{client_id}", response_model=PessoaJuridica)
async def get_pessoa_juridica(client_id: str, current_user: User = Depends(get_current_user)):
    query_filter = add_tenant_filter({"id": client_id})
    client_doc = await db.clientes_pj.find_one(query_filter)
    if not client_doc:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Aplicar mascaramento baseado no role do usuário
    license_reference = generate_license_reference(client_doc)
    masked_client = apply_data_masking(client_doc, current_user.role, license_reference)
    
    return PessoaJuridica(**masked_client)

@api_router.put("/clientes-pj/{client_id}", response_model=PessoaJuridica)
async def update_pessoa_juridica(
    client_id: str,
    client_update: PessoaJuridicaUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    # Aplicar filtro de tenant
    query_filter = add_tenant_filter({"id": client_id})
    
    update_data = {k: v for k, v in client_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = current_user.id
    
    # CORREÇÃO: Converter datetime.date para datetime.datetime para compatibilidade MongoDB
    import datetime as dt
    for key, value in update_data.items():
        if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
            update_data[key] = dt.datetime.combine(value, dt.datetime.min.time())
    
    result = await db.clientes_pj.update_one(
        query_filter,
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    updated_client = await db.clientes_pj.find_one(query_filter)
    return PessoaJuridica(**updated_client)

@api_router.delete("/clientes-pj/{client_id}")
async def delete_pessoa_juridica(
    client_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.clientes_pj.update_one(
        {"id": client_id},
        {"$set": {"status": ClientStatus.INACTIVE, "updated_at": datetime.utcnow(), "updated_by": current_user.id}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    return {"message": "Cliente inativado com sucesso"}

# Category Management Routes (keeping existing)
@api_router.post("/categories", response_model=Category)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_admin_user)
):
    # Criar dict da categoria e adicionar tenant_id automaticamente
    category_dict = category_data.dict()
    
    # Usar helper de tenant para adicionar tenant_id
    # CRÍTICO: Especificar tenant_id do usuário atual
    category_dict = add_tenant_to_document(category_dict, current_user.tenant_id)
    
    # Criar categoria com tenant_id
    category = Category(**category_dict)
    
    await db.categories.insert_one(category_dict)
    return category

@api_router.get("/categories", response_model=List[Category])
async def get_categories(
    current_user: User = Depends(get_current_user),
    tenant_db = Depends(get_tenant_database),
    pagination: Dict = Depends(get_pagination_params),
    metrics: RequestMetrics = Depends(get_request_metrics)
):
    """
    Get categories
    🚀 SUB-FASE 2.3 - Enhanced with Dependency Injection and Redis caching (1 hour TTL)
    """
    try:
        # 🚀 NEW: Try to get from cache first
        from redis_cache_system import get_cached_categories
        
        # Get tenant_id from TenantAwareDB for consistency
        tenant_id = tenant_db.tenant_id
        cached_categories = await get_cached_categories(tenant_id)
        
        if cached_categories:
            logger.debug("📁 Categories served from Redis cache")
            metrics.record_cache_hit()
            # Apply pagination to cached results
            start_idx = pagination["skip"]
            end_idx = start_idx + pagination["limit"]
            paginated_categories = cached_categories[start_idx:end_idx]
            return [Category(**category) for category in paginated_categories if category.get("is_active", True)]
        
        # 🔄 FALLBACK: Get from database if cache miss
        logger.debug("📁 Categories fetched from database (cache miss)")
        metrics.record_cache_miss()
        
        # 🚀 NEW: Use tenant-aware database with automatic filtering and pagination
        categories = await tenant_db.find(
            "categories", 
            {"is_active": True},
            skip=pagination["skip"],
            limit=pagination["limit"]
        )
        
        # Record database query
        metrics.record_db_query()
        
        logger.debug(f"📁 Found {len(categories)} categories with pagination (skip={pagination['skip']}, limit={pagination['limit']})")
        
        return [Category(**category) for category in categories]
        
    except Exception as e:
        logger.error(f"Error fetching categories with dependency injection: {str(e)}")
        # 🔄 FALLBACK: Use original implementation if dependency injection fails
        logger.warning("Falling back to original categories implementation")
        
        query_filter = add_tenant_filter({"is_active": True})
        categories = await db.categories.find(query_filter).to_list(1000)
        return [Category(**category) for category in categories]

@api_router.get("/categories/{category_id}", response_model=Category)
async def get_category(category_id: str, current_user: User = Depends(get_current_user)):
    query_filter = add_tenant_filter({"id": category_id})
    category_doc = await db.categories.find_one(query_filter)
    if not category_doc:
        raise HTTPException(status_code=404, detail="Category not found")
    return Category(**category_doc)

@api_router.put("/categories/{category_id}", response_model=Category)
async def update_category(
    category_id: str,
    category_update: CategoryUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    update_data = {k: v for k, v in category_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.categories.update_one(
        add_tenant_filter({"id": category_id}),
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    query_filter = add_tenant_filter({"id": category_id})
    updated_category = await db.categories.find_one(query_filter)
    return Category(**updated_category)

@api_router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.categories.update_one(
        {"id": category_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"message": "Category deleted successfully"}

# Product and License Plan routes (keeping existing with minor updates)
@api_router.post("/products", response_model=Product)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_admin_user)
):
    try:
        maintenance_logger.info("products", "create_product_start", {
            "user_id": current_user.id,
            "user_email": current_user.email,
            "product_data": product_data.dict()
        })
        
        # Check if product with same name already exists in same tenant
        query_filter = add_tenant_filter({"name": product_data.name})
        existing_product = await db.products.find_one(query_filter)
        if existing_product:
            maintenance_logger.error("products", "create_product_duplicate", {
                "product_name": product_data.name,
                "existing_id": existing_product.get("id")
            }, "Product with same name already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Produto com o mesmo nome já existe"
            )
        
        # Create product
        product_dict = product_data.dict()
        product_dict["created_by"] = current_user.id
        
        # Usar helper de tenant para adicionar tenant_id
        product_dict = add_tenant_to_document(product_dict)
        
        # Criar produto com tenant_id
        product = Product(**product_dict)
        
        maintenance_logger.debug("products", "create_product_before_insert", {
            "product_id": product.id,
            "product_name": product.name,
            "complete_product": product.dict()
        })
        
        # Insert into database
        result = await db.products.insert_one(product_dict)
        
        maintenance_logger.info("products", "create_product_success", {
            "product_id": product.id,
            "product_name": product.name,
            "insert_result": str(result.inserted_id) if result else "None"
        })
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        maintenance_logger.error("products", "create_product_exception", {
            "product_data": product_data.dict() if product_data else "None",
            "user_id": current_user.id if current_user else "None"
        }, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )

@api_router.get("/products", response_model=List[Product])
async def get_products(
    current_user: User = Depends(get_current_user),
    tenant_db = Depends(get_tenant_database),
    pagination: Dict = Depends(get_pagination_params),
    metrics: RequestMetrics = Depends(get_request_metrics)
):
    """
    Get products
    🚀 SUB-FASE 2.3 - Enhanced with Dependency Injection and automatic tenant filtering
    """
    try:
        maintenance_logger.debug("products", "get_products_start", {
            "user_id": current_user.id,
            "user_email": current_user.email,
            "tenant_id": tenant_db.tenant_id,
            "pagination": pagination
        })
        
        # 🚀 NEW: Use tenant-aware database with automatic filtering and pagination
        products = await tenant_db.find(
            "products", 
            {"is_active": True},
            skip=pagination["skip"],
            limit=pagination["limit"]
        )
        
        # Record database query and metrics
        metrics.record_db_query()
        
        maintenance_logger.info("products", "get_products_success", {
            "count": len(products),
            "user_id": current_user.id,
            "tenant_id": tenant_db.tenant_id,
            "pagination": pagination
        })
        
        logger.debug(f"📦 Found {len(products)} products with pagination (skip={pagination['skip']}, limit={pagination['limit']})")
        
        return [Product(**product) for product in products]
        
    except Exception as e:
        maintenance_logger.error("products", "get_products_exception", {
            "user_id": current_user.id if current_user else "None",
            "error": str(e)
        }, str(e))
        
        # 🔄 FALLBACK: Use original implementation if dependency injection fails
        logger.warning("Falling back to original products implementation")
        
        try:
            query_filter = add_tenant_filter({"is_active": True})
            products = await db.products.find(query_filter).to_list(1000)
            return [Product(**product) for product in products]
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {str(fallback_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao buscar produtos: {str(e)}"
            )

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str, current_user: User = Depends(get_current_user)):
    query_filter = add_tenant_filter({"id": product_id})
    product_doc = await db.products.find_one(query_filter)
    if not product_doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product_doc)

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    update_data = {k: v for k, v in product_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    query_filter = add_tenant_filter({"id": product_id})
    updated_product = await db.products.find_one(query_filter)
    return Product(**updated_product)

@api_router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.products.update_one(
        {"id": product_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully"}

# License Plan routes (keeping existing structure)
@api_router.post("/license-plans", response_model=LicensePlan)
async def create_license_plan(
    plan_data: LicensePlanCreate,
    current_user: User = Depends(get_current_admin_user)
):
    plan = LicensePlan(**plan_data.dict())
    await db.license_plans.insert_one(plan.dict())
    return plan

@api_router.get("/license-plans", response_model=List[LicensePlan])
async def get_license_plans(current_user: User = Depends(get_current_user)):
    query_filter = add_tenant_filter({"is_active": True})
    plans = await db.license_plans.find(query_filter).to_list(1000)
    return [LicensePlan(**plan) for plan in plans]

@api_router.get("/license-plans/{plan_id}", response_model=LicensePlan)
async def get_license_plan(plan_id: str, current_user: User = Depends(get_current_user)):
    query_filter = add_tenant_filter({"id": plan_id})
    plan_doc = await db.license_plans.find_one(query_filter)
    if not plan_doc:
        raise HTTPException(status_code=404, detail="License plan not found")
    return LicensePlan(**plan_doc)

@api_router.put("/license-plans/{plan_id}", response_model=LicensePlan)
async def update_license_plan(
    plan_id: str,
    plan_update: LicensePlanUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    update_data = {k: v for k, v in plan_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.license_plans.update_one(
        add_tenant_filter({"id": plan_id}),
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="License plan not found")
    
    query_filter = add_tenant_filter({"id": plan_id})
    updated_plan = await db.license_plans.find_one(query_filter)
    return LicensePlan(**updated_plan)

@api_router.delete("/license-plans/{plan_id}")
async def delete_license_plan(
    plan_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.license_plans.update_one(
        {"id": plan_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="License plan not found")
    
    return {"message": "License plan deleted successfully"}

# Enhanced License Management Routes (updated for new client system)
@api_router.post("/licenses", response_model=License)
async def create_license(
    license_data: LicenseCreate,
    current_user: User = Depends(get_current_admin_user),
    tenant_id: str = Depends(require_tenant)
):
    """Create license with tenant isolation"""
    license_dict = license_data.dict()
    license_dict["created_by"] = current_user.id
    
    # CRÍTICO: Adicionar tenant_id à nova licença  
    license_dict = add_tenant_to_document(license_dict, tenant_id)
    
    license = License(**license_dict)
    await db.licenses.insert_one(license.dict())
    
    return license

@api_router.get("/licenses", response_model=List[License])
async def get_licenses(
    request: Request,
    current_user: User = Depends(get_current_user),
    tenant_db = Depends(get_tenant_database),
    pagination: Dict = Depends(get_pagination_params),
    metrics: RequestMetrics = Depends(get_request_metrics)
):
    """
    Get licenses with pagination and scope filtering
    🚀 SUB-FASE 2.3 - Enhanced with Dependency Injection and automatic tenant filtering
    """
    try:
        # 🚀 NEW: Use enhanced pagination from dependency injection
        logger.debug(f"📄 Listing licenses with pagination: page={pagination['page']}, limit={pagination['limit']}")
        
        # Build scope filter (existing business logic)
        base_filter = {}
        
        # Apply role-based scope filtering
        if current_user.role == UserRole.ADMIN:
            # Admin sees licenses for their clients
            base_filter["admin_vendor_id"] = current_user.id
        elif current_user.role == UserRole.USER:
            # Users see only their own licenses
            base_filter["user_id"] = current_user.id
        # SUPER_ADMIN sees all licenses in the tenant
        
        # 🚀 NEW: Use tenant database with automatic tenant filtering
        licenses = await tenant_db.find(
            "licenses",
            base_filter,
            skip=pagination["skip"],
            limit=pagination["limit"]
        )
        
        # Record metrics
        metrics.record_db_query()
        
        # Clean up licenses data and handle missing required fields
        valid_licenses = []
        for license_data in licenses:
            # Remove MongoDB ObjectId
            if "_id" in license_data:
                license_data.pop("_id")
            
            # Ensure required fields have default values
            if "license_type" not in license_data:
                license_data["license_type"] = "standard"
            if "status" not in license_data:
                license_data["status"] = "active"
            if "client_id" not in license_data:
                license_data["client_id"] = ""
            if "plan_id" not in license_data:
                license_data["plan_id"] = ""
            
            try:
                valid_license = License(**license_data)
                valid_licenses.append(valid_license)
            except Exception as validation_error:
                logger.warning(f"Skipping invalid license {license_data.get('id', 'unknown')}: {validation_error}")
                continue
        
        logger.debug(f"📄 Found {len(valid_licenses)} valid licenses for {current_user.role} user {current_user.email}")
        
        return valid_licenses
        
    except Exception as e:
        logger.error(f"Error listing licenses: {str(e)}")
        # 🔄 FALLBACK: Use original implementation if dependency injection fails
        logger.warning("Falling back to original license listing implementation")
        
        # Original pagination logic
        try:
            page = int(request.query_params.get("page", "1"))
            size = int(request.query_params.get("size", "50"))
        except ValueError:
            page, size = 1, 50
        page = max(1, page)
        size = min(200, max(1, size))

        # Escopo centralizado (RBAC+ABAC)
        query_filter = build_scope_filter(current_user, {})

        cursor = db.licenses.find(query_filter).skip((page - 1) * size).limit(size)
        licenses = await cursor.to_list(length=size)
        
        # Clean up licenses data and handle missing required fields
        valid_licenses = []
        for license_data in licenses:
            # Remove MongoDB ObjectId
            license_data.pop("_id", None)
            
            # Ensure required fields exist
            if "name" not in license_data or not license_data["name"]:
                license_data["name"] = f"License {license_data.get('id', 'Unknown')}"
            
            if "created_by" not in license_data or not license_data["created_by"]:
                license_data["created_by"] = "system"
            
            # Convert datetime objects to ISO strings
            for field in ["created_at", "updated_at", "expires_at"]:
                if field in license_data and isinstance(license_data[field], datetime):
                    license_data[field] = license_data[field].isoformat()
            
            valid_licenses.append(License(**license_data))
        
        return valid_licenses
    except Exception as e:
        logger.error(f"Error fetching licenses: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching licenses: {str(e)}")

# ------------------------ LICENSES by :id ------------------------
@api_router.get("/licenses/{license_id}", response_model=License)
async def get_license_by_id(license_id: str, current_user: User = Depends(get_current_user)):
    doc = await db.licenses.find_one({"_id": ObjectId(license_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Licença não encontrada")
    if not enforce_object_scope(doc, current_user):
        raise HTTPException(status_code=403, detail="Fora do escopo")
    
    # Remove MongoDB ObjectId
    doc.pop("_id", None)
    doc["id"] = doc.get("id", str(ObjectId()))
    
    # Ensure required fields exist
    if "name" not in doc or not doc["name"]:
        doc["name"] = f"License {doc.get('id', 'Unknown')}"
    
    if "created_by" not in doc or not doc["created_by"]:
        doc["created_by"] = "system"
    
    # Convert datetime objects to ISO strings
    for field in ["created_at", "updated_at", "expires_at"]:
        if field in doc and isinstance(doc[field], datetime):
            doc[field] = doc[field].isoformat()
    
    return License(**doc)

class LicenseUpdate(BaseModel):
    serial: str | None = None
    assigned_user_id: str | None = None

@api_router.put("/licenses/{license_id}", response_model=License)
async def update_license_by_id(license_id: str, body: LicenseUpdate, current_user: User = Depends(get_current_user)):
    doc = await db.licenses.find_one({"_id": ObjectId(license_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Licença não encontrada")
    if not enforce_object_scope(doc, current_user):
        raise HTTPException(status_code=403, detail="Fora do escopo")

    updates = {}
    if body.serial is not None:
        updates["serial"] = body.serial.strip()
    if body.assigned_user_id is not None:
        updates["assigned_user_id"] = body.assigned_user_id
    if not updates:
        doc.pop("_id", None)
        doc["id"] = doc.get("id", str(ObjectId()))
        return License(**doc)

    await db.licenses.update_one({"_id": doc["_id"]}, {"$set": updates})
    updated = await db.licenses.find_one({"_id": doc["_id"]})
    updated.pop("_id", None)
    updated["id"] = updated.get("id", str(ObjectId()))
    
    # Ensure required fields exist
    if "name" not in updated or not updated["name"]:
        updated["name"] = f"License {updated.get('id', 'Unknown')}"
    
    return License(**updated)

@api_router.delete("/licenses/{license_id}", status_code=204)
async def delete_license_by_id(license_id: str, current_user: User = Depends(get_current_user)):
    doc = await db.licenses.find_one({"_id": ObjectId(license_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Licença não encontrada")
    if not enforce_object_scope(doc, current_user):
        raise HTTPException(status_code=403, detail="Fora do escopo")
    await db.licenses.delete_one({"_id": doc["_id"]})
    return Response(status_code=204)

# ------------------------ SEARCH endpoints with safe filters ------------------------
@api_router.get("/search/users", response_model=List[User])
async def search_users(request: Request, current_user: User = Depends(get_current_user)):
    """
    Busca usuários com filtros seguros via query params.
    Exemplo: /search/users?email=test&role=USER
    """
    client_filter = dict(request.query_params)
    page = int(client_filter.pop("page", "1"))
    size = min(200, int(client_filter.pop("size", "50")))
    
    # Campos permitidos para filtro (whitelist)
    safe_filter = whitelist_filter(client_filter, ["email", "role", "is_active"])
    user_scope = build_scope_filter(current_user, {})
    final_filter = merge_with_scope(user_scope, safe_filter)
    
    cursor = db.users.find(final_filter).skip((page - 1) * size).limit(size)
    users = await cursor.to_list(length=size)
    
    result = []
    for user in users:
        user.pop("_id", None)
        result.append(User(**user))
    return result

@api_router.get("/search/licenses", response_model=List[License])
async def search_licenses(request: Request, current_user: User = Depends(get_current_user)):
    """
    Busca licenças com filtros seguros via query params.
    Exemplo: /search/licenses?status=active&serial=123
    """
    client_filter = dict(request.query_params)
    page = int(client_filter.pop("page", "1"))
    size = min(200, int(client_filter.pop("size", "50")))
    
    # Campos permitidos para filtro (whitelist)
    safe_filter = whitelist_filter(client_filter, ["status", "serial", "assigned_user_id"])
    user_scope = build_scope_filter(current_user, {})
    final_filter = merge_with_scope(user_scope, safe_filter)
    
    cursor = db.licenses.find(final_filter).skip((page - 1) * size).limit(size)
    licenses = await cursor.to_list(length=size)
    
    valid_licenses = []
    for license_data in licenses:
        try:
            # Remove MongoDB ObjectId
            license_data.pop("_id", None)
            
            # Ensure required fields exist
            if "name" not in license_data or not license_data["name"]:
                license_data["name"] = f"License {license_data.get('id', 'Unknown')}"
            
            if "created_by" not in license_data or not license_data["created_by"]:
                license_data["created_by"] = "system"
            
            # Convert datetime objects to ISO strings
            for field in ["created_at", "updated_at", "expires_at"]:
                if field in license_data and isinstance(license_data[field], datetime):
                    license_data[field] = license_data[field].isoformat()
            
            valid_licenses.append(License(**license_data))
        except Exception as e:
            logger.error(f"Error processing license {license_data.get('id')}: {e}")
            continue
    
    return valid_licenses

# ------------------------ CONVITES ------------------------
class InviteCreate(BaseModel):
    email: str
    ttl_seconds: int | None = None

@api_router.post("/admin/invitations")
async def create_invitation(body: InviteCreate, current_user: User = Depends(get_current_user)):
    """
    Admin cria um convite para um e-mail específico dentro do seu tenant.
    O user aceito será criado como USER, vinculado a este Admin (admin_vendor_id).
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Sem permissão")

    # Super admin pode especificar tenant no futuro; por ora usamos o tenant do ator
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ausente no contexto")

    email = body.email.lower().strip()
    tok = generate_invite_token(email=email, tenant_id=tenant_id, admin_vendor_id=current_user.id, ttl_seconds=body.ttl_seconds)
    th = token_hash(tok)

    # Persistir convite para permitir revogação/single-use
    inv = {
        "token_hash": th,
        "email": email,
        "tenant_id": tenant_id,
        "admin_vendor_id": current_user.id,
        "created_at": int(time.time()),
        "used_at": None,
        "revoked": False,
    }
    try:
        await db.invitations.insert_one(inv)
    except Exception as e:
        # Duplicidade de token_hash é improvável, mas trate qualquer falha
        raise HTTPException(status_code=400, detail=f"Erro ao registrar convite: {e}")

    # Monta link (frontend deve ter rota /accept-invite?token=...)
    frontend_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    invite_link = f"{frontend_url}/accept-invite?token={tok}"

    # Envio de e-mail (stub)
    try:
        send_invitation_email(to_email=email, invite_link=invite_link, inviter_name=getattr(current_user, "email", "Admin"))
    except Exception as e:
        print(f"[invite] falha ao enviar e-mail: {e}")

    return {"ok": True, "invite_link": invite_link}

class AcceptInvitePayload(BaseModel):
    token: str
    password: str | None = None  # se desejar criar já com senha

@api_router.post("/auth/accept-invite")
async def accept_invite(body: AcceptInvitePayload):
    """
    Aceita um convite e cria/ativa o USER vinculado ao admin vendedor.
    Não exige autenticação prévia: valida o token de convite.
    """
    try:
        payload = verify_invite(body.token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    th = token_hash(body.token)
    inv = await db.invitations.find_one({"token_hash": th})
    if not inv or inv.get("revoked"):
        raise HTTPException(status_code=400, detail="Convite inválido ou revogado")
    if inv.get("used_at"):
        raise HTTPException(status_code=400, detail="Convite já utilizado")

    email = payload["email"]
    tenant_id = payload["tenant_id"]
    admin_vendor_id = payload["admin_vendor_id"]

    # Cria usuário (ou garante vínculo se já existir no tenant)
    existing = await db.users.find_one({"tenant_id": tenant_id, "email": email})
    if existing:
        # Se já existe, apenas garante vínculo (não eleva papel)
        update = {"admin_vendor_id": admin_vendor_id}
        await db.users.update_one({"_id": existing["_id"]}, {"$set": update})
        user_id = existing["_id"]
    else:
        doc = {
            "id": str(uuid.uuid4()),
            "email": email,
            "name": email.split("@")[0].title(),
            "tenant_id": tenant_id,
            "role": "user",
            "admin_vendor_id": admin_vendor_id,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        if body.password:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
            doc["password_hash"] = pwd_context.hash(body.password)
        
        res = await db.users.insert_one(doc)
        user_id = res.inserted_id

    # Marca convite como usado (single-use)
    await db.invitations.update_one({"_id": inv["_id"]}, {"$set": {"used_at": int(time.time())}})

    created = await db.users.find_one({"_id": user_id})
    if created:
        created.pop("_id", None)
        created.pop("password_hash", None)  # Não retornar hash de senha
        return {"ok": True, "user": created}
    else:
        raise HTTPException(status_code=500, detail="Erro ao criar usuário")

class RevokeInvitePayload(BaseModel):
    token: str

@api_router.post("/admin/invitations/revoke")
async def revoke_invitation(body: RevokeInvitePayload, current_user: User = Depends(get_current_user)):
    """
    Revoga um convite ainda não utilizado. Admin só revoga convites criados por ele.
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Sem permissão")

    th = token_hash(body.token)
    inv = await db.invitations.find_one({"token_hash": th})
    if not inv:
        raise HTTPException(status_code=404, detail="Convite não encontrado")

    # Admin só pode revogar convites dele no próprio tenant
    if current_user.role == UserRole.ADMIN:
        if inv.get("tenant_id") != current_user.tenant_id or inv.get("admin_vendor_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Fora do escopo")

    if inv.get("used_at"):
        raise HTTPException(status_code=400, detail="Convite já utilizado")

    await db.invitations.update_one({"_id": inv["_id"]}, {"$set": {"revoked": True}})
    return {"ok": True}

@api_router.get("/admin/invitations")
async def list_invitations(current_user: User = Depends(get_current_user)):
    """
    Lista convites criados pelo admin atual.
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Sem permissão")

    # Admin vê apenas seus convites no próprio tenant
    query = {}
    if current_user.role == UserRole.ADMIN:
        query = {"tenant_id": current_user.tenant_id, "admin_vendor_id": current_user.id}

    invites = await db.invitations.find(query).sort("created_at", -1).limit(100).to_list(100)
    
    result = []
    for invite in invites:
        invite.pop("_id", None)
        invite.pop("token_hash", None)  # Não expor hash do token
        result.append(invite)
    
    return result

# Enhanced Dashboard Stats
@api_router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_admin_user),
    tenant_id: str = Depends(require_tenant)
):
    """Get statistics with proper tenant isolation"""
    # Super admin can see global stats, regular admin sees tenant stats
    if current_user.role == "super_admin":
        # Global stats for super admin
        total_licenses = await db.licenses.count_documents({})
        active_licenses = await db.licenses.count_documents({"status": LicenseStatus.ACTIVE})
        total_users = await db.users.count_documents({})
        expired_licenses = await db.licenses.count_documents({"status": LicenseStatus.EXPIRED})
        total_categories = await db.categories.count_documents({"is_active": True})
        total_products = await db.products.count_documents({"is_active": True})
        total_clientes_pf = await db.clientes_pf.count_documents({"status": {"$ne": ClientStatus.INACTIVE}})
        total_clientes_pj = await db.clientes_pj.count_documents({"status": {"$ne": ClientStatus.INACTIVE}})
    else:
        # Tenant-specific stats for regular admin
        total_licenses = await db.licenses.count_documents(add_tenant_filter({}, tenant_id))
        active_licenses = await db.licenses.count_documents(add_tenant_filter({"status": LicenseStatus.ACTIVE}, tenant_id))
        total_users = await db.users.count_documents(add_tenant_filter({}, tenant_id))
        expired_licenses = await db.licenses.count_documents(add_tenant_filter({"status": LicenseStatus.EXPIRED}, tenant_id))
        total_categories = await db.categories.count_documents(add_tenant_filter({"is_active": True}, tenant_id))
        total_products = await db.products.count_documents(add_tenant_filter({"is_active": True}, tenant_id))
        total_clientes_pf = await db.clientes_pf.count_documents(add_tenant_filter({"status": {"$ne": ClientStatus.INACTIVE}}, tenant_id))
        total_clientes_pj = await db.clientes_pj.count_documents(add_tenant_filter({"status": {"$ne": ClientStatus.INACTIVE}}, tenant_id))
    
    return {
        "total_licenses": total_licenses,
        "active_licenses": active_licenses,
        "total_users": total_users,
        "expired_licenses": expired_licenses,
        "total_categories": total_categories,
        "total_products": total_products,
        "total_clientes_pf": total_clientes_pf,
        "total_clientes_pj": total_clientes_pj,
        "total_clients": total_clientes_pf + total_clientes_pj
    }

# Demo credentials and health check (keeping existing)
# Temporally endpoint to migrate demo user to separate tenant
@api_router.post("/admin/migrate-demo-user")
async def migrate_demo_user(current_user: User = Depends(get_current_admin_user)):
    """Migra usuário demo para tenant separado (uso temporário)"""
    try:
        demo_user_tenant_id = "demo-user-tenant"
        
        # Create demo user tenant if not exists
        demo_tenant_exists = await db.tenants.find_one({"id": demo_user_tenant_id})
        if not demo_tenant_exists:
            demo_tenant_data = {
                "id": demo_user_tenant_id,
                "name": "Demo User Company",
                "subdomain": "demo-user",
                "contact_email": "user@demo.com",
                "status": "active",
                "plan": "free",
                "max_users": 5,
                "max_licenses": 10,
                "max_clients": 5,
                "features": {
                    "api_access": False,
                    "webhooks": False,
                    "advanced_reports": False,
                    "white_label": False,
                    "priority_support": False,
                    "audit_logs": False,
                    "sso": False
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.tenants.insert_one(demo_tenant_data)
            logger.info("Demo user tenant created during migration")
        
        # Update user tenant_id
        result = await db.users.update_one(
            {"email": "user@demo.com"},
            {"$set": {"tenant_id": demo_user_tenant_id}}
        )
        
        return {
            "status": "success",
            "message": "Demo user migrated to separate tenant",
            "tenant_id": demo_user_tenant_id,
            "users_updated": result.modified_count
        }
    except Exception as e:
        logger.error(f"Failed to migrate demo user: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Migration failed: {str(e)}"
        )

# OBSERVABILITY & HEALTH CHECK ENDPOINTS
@api_router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.3.1",
        "service": "License Management System"
    }

# Also provide root-level health check (without /api prefix)  
@app.get("/health")
async def root_health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow(), "version": "1.3.1", "service": "License Management System"}

@api_router.get("/health/detailed")
async def detailed_health_check(current_user: User = Depends(get_current_admin_user)):
    """Detailed health check with system metrics (admin only)"""
    try:
        # Get comprehensive health metrics
        system_health = metrics_collector.get_system_health()
        database_health = await get_database_health()
        tenant_health = await get_tenant_health()
        security_health = get_security_health()
        
        overall_status = "healthy"
        if (system_health.get("status") != "healthy" or 
            database_health.get("status") != "healthy" or
            tenant_health.get("status") != "healthy" or
            security_health.get("status") != "healthy"):
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "system": system_health,
                "database": database_health,
                "tenants": tenant_health,
                "security": security_health
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@api_router.get("/metrics")
async def get_metrics(current_user: User = Depends(get_current_admin_user)):
    """Get system metrics for monitoring (admin only)"""
    return metrics_collector.get_system_health()

@api_router.get("/metrics/tenant/{tenant_id}")
async def get_tenant_metrics(
    tenant_id: str, 
    current_user: User = Depends(get_current_admin_user)
):
    """Get metrics for specific tenant (admin only)"""
    if tenant_id not in metrics_collector.tenant_metrics:
        raise HTTPException(status_code=404, detail="Tenant metrics not found")
    
    return {
        "tenant_id": tenant_id,
        "metrics": metrics_collector.tenant_metrics[tenant_id],
        "timestamp": datetime.utcnow().isoformat()
    }

@api_router.get("/demo-credentials")
async def demo_credentials():
    # NÃO exponha em produção
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {
        "admin": {
            "email": "admin@demo.com",
            "password": "admin123"
        },
        "user": {
            "email": "user@demo.com", 
            "password": "user123"
        }
    }

@api_router.get("/")
async def root():
    return {"message": "Enhanced License Management System API", "status": "running", "version": "2.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# WhatsApp Integration Endpoints - Direct implementation to avoid circular imports
import httpx

# WhatsApp Service Configuration
WHATSAPP_SERVICE_URL = os.getenv("WHATSAPP_SERVICE_URL", "http://localhost:3001")
WHATSAPP_REQUEST_TIMEOUT = 30.0

# WhatsApp Models
class WhatsAppSendRequest(BaseModel):
    phone_number: str
    message: str
    message_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class WhatsAppBulkSendRequest(BaseModel):
    messages: List[Dict[str, str]]

class WhatsAppStatus(BaseModel):
    connected: bool
    status: str
    user: Optional[Dict[str, Any]] = None
    uptime: Optional[int] = None
    last_activity: Optional[datetime] = None

class WhatsAppQRResponse(BaseModel):
    qr: Optional[str] = None
    status: str

class WhatsAppSendResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    phone_number: str
    error: Optional[str] = None
    timestamp: datetime

# WhatsApp Service Helper Functions
async def call_whatsapp_service(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Helper function to call WhatsApp Node.js service"""
    try:
        async with httpx.AsyncClient(timeout=WHATSAPP_REQUEST_TIMEOUT) as client:
            url = f"{WHATSAPP_SERVICE_URL}/{endpoint}"
            
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", "WhatsApp service error")
                # 🔧 FIX: Ensure error is properly serializable string
                if isinstance(error_message, dict):
                    error_message = str(error_message.get("message", error_message))
                raise HTTPException(status_code=response.status_code, detail=str(error_message))
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="WhatsApp service timeout")
    except Exception as e:
        logger.error(f"Error calling WhatsApp service: {e}")
        raise HTTPException(status_code=503, detail="WhatsApp service unavailable")

# WhatsApp API Endpoints
@api_router.get("/whatsapp/health")
async def whatsapp_health_check():
    """Health check do serviço WhatsApp"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{WHATSAPP_SERVICE_URL}/health")
            is_healthy = response.status_code == 200
            
            return {
                "service": "WhatsApp Integration",
                "healthy": is_healthy,
                "service_url": WHATSAPP_SERVICE_URL,
                "timestamp": datetime.utcnow().isoformat()
            }
    except:
        return {
            "service": "WhatsApp Integration",
            "healthy": False,
            "service_url": WHATSAPP_SERVICE_URL,
            "timestamp": datetime.utcnow().isoformat()
        }

@api_router.get("/whatsapp/status")
async def get_whatsapp_status(current_user: User = Depends(get_current_user)):
    """Obtém status da conexão WhatsApp"""
    data = await call_whatsapp_service("status")
    
    # Log da consulta
    maintenance_logger.log("whatsapp_status_check", {
        "user_id": current_user.id,
        "connected": data.get("connected", False),
        "status": data.get("status", "unknown")
    })
    
    return WhatsAppStatus(**data)

@api_router.get("/whatsapp/qr")
async def get_whatsapp_qr(current_user: User = Depends(get_current_admin_user)):
    """Obtém QR code para conectar WhatsApp (Admin only)"""
    data = await call_whatsapp_service("qr")
    
    # Log da consulta
    maintenance_logger.log("whatsapp_qr_request", {
        "user_id": current_user.id,
        "has_qr": bool(data.get("qr")),
        "status": data.get("status", "unknown")
    })
    
    return WhatsAppQRResponse(**data)

@api_router.post("/whatsapp/send")
async def send_whatsapp_message(
    request: WhatsAppSendRequest,
    current_user: User = Depends(get_current_user)
):
    """Envia mensagem WhatsApp individual"""
    
    # Log da tentativa
    maintenance_logger.log("whatsapp_send_attempt", {
        "user_id": current_user.id,
        "phone_number": request.phone_number,
        "message_length": len(request.message),
        "has_context": bool(request.context)
    })
    
    try:
        payload = {
            "phone_number": request.phone_number,
            "message": request.message,
            "message_id": request.message_id,
            "context": request.context or {}
        }
        
        data = await call_whatsapp_service("send", "POST", payload)
        
        result = WhatsAppSendResponse(
            success=data.get("success", False),
            message_id=data.get("message_id"),
            phone_number=request.phone_number,
            error=data.get("error"),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        result = WhatsAppSendResponse(
            success=False,
            phone_number=request.phone_number,
            error=str(e),
            timestamp=datetime.utcnow()
        )
    
    # Log do resultado
    maintenance_logger.log("whatsapp_send_result", {
        "user_id": current_user.id,
        "phone_number": request.phone_number,
        "success": result.success,
        "error": result.error,
        "message_id": result.message_id
    })
    
    return result

@api_router.post("/whatsapp/send-bulk")
async def send_bulk_whatsapp(
    request: WhatsAppBulkSendRequest,
    current_user: User = Depends(get_current_user)
):
    """Envia mensagens WhatsApp em lote"""
    
    # Log da tentativa
    maintenance_logger.log("whatsapp_bulk_send_attempt", {
        "user_id": current_user.id,
        "message_count": len(request.messages),
        "phone_numbers": [msg.get("phone_number") for msg in request.messages]
    })
    
    try:
        payload = {"messages": request.messages}
        result = await call_whatsapp_service("send-bulk", "POST", payload)
    except Exception as e:
        result = {
            "total": len(request.messages),
            "sent": 0,
            "failed": len(request.messages),
            "error": getattr(e, 'detail', str(e))  # 🔧 FIX: Proper HTTPException error extraction
        }
    
    # Log do resultado
    maintenance_logger.log("whatsapp_bulk_send_result", {
        "user_id": current_user.id,
        "total": result.get("total", 0),
        "sent": result.get("sent", 0),
        "failed": result.get("failed", 0)
    })
    
    return result

@api_router.post("/whatsapp/restart")
async def restart_whatsapp_connection(current_user: User = Depends(get_current_admin_user)):
    """Reinicia conexão WhatsApp (Admin only)"""
    
    try:
        await call_whatsapp_service("restart", "POST")
        success = True
        message = "WhatsApp connection restart initiated"
    except Exception as e:
        success = False
        message = f"Failed to restart WhatsApp connection: {str(e)}"
    
    # Log da operação
    maintenance_logger.log("whatsapp_restart", {
        "user_id": current_user.id,
        "success": success
    })
    
    if success:
        return {"message": message}
    else:
        raise HTTPException(status_code=500, detail=message)

# Helper function for sales dashboard integration - Updated to use direct service call
async def send_renewal_whatsapp_message(client_data: Dict, license_data: Dict, alert_type: str, salesperson: str = None):
    """
    Função helper para enviar mensagens de renovação via WhatsApp
    Integração com o sistema de vendas
    """
    # Buscar número de telefone do cliente
    phone_number = None
    for field in ['whatsapp', 'celular', 'telefone']:
        if client_data.get(field):
            phone_number = client_data[field]
            break
    
    if not phone_number:
        raise ValueError("Cliente não possui número de WhatsApp/telefone cadastrado")
    
    # Gerar mensagem usando template
    client_name = client_data.get('nome_completo') or client_data.get('razao_social', 'Cliente')
    license_name = license_data.get('name', 'sua licença')
    
    expires_at = license_data.get('expires_at')
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    
    days_to_expire = (expires_at - datetime.utcnow()).days if expires_at else 0
    
    # Template de mensagem baseado no tipo de alerta
    if alert_type == "T-30":
        message = f"""Olá {client_name}! 👋

Esperamos que esteja tudo bem! 

Queremos lembrá-lo que sua licença do {license_name} vence em {days_to_expire} dias.

Para garantir a continuidade dos seus serviços sem interrupções, que tal renovarmos hoje mesmo?

✅ Sem interrupção de serviços
✅ Preço especial para renovação antecipada  
✅ Suporte técnico garantido

Posso ajudar com a renovação agora mesmo!

{salesperson or "Equipe de Vendas"}
Sua Empresa de Licenças"""
    elif alert_type == "T-7":
        message = f"""🚨 URGENTE - {client_name}!

Sua licença do {license_name} vence em apenas {days_to_expire} dias!

⚠️ ATENÇÃO: Após o vencimento, seus sistemas podem parar de funcionar.

OFERTA ESPECIAL para renovação imediata:
💰 15% de desconto
🎁 +30 dias grátis de suporte

👆 Responda AGORA para garantir seu desconto!

{salesperson or "Equipe de Vendas"} - Sua Empresa"""
    elif alert_type == "T-1":
        message = f"""🔴 CRÍTICO - {client_name}!

SUA LICENÇA VENCE HOJE!

{license_name} expira em menos de 24h.

🚨 SEUS SISTEMAS VÃO PARAR DE FUNCIONAR!

LIGUE AGORA: (11) 9999-9999

Posso renovar em 5 minutos via PIX!

NÃO PERCA TEMPO - RESPONDA AGORA!

{salesperson or "Equipe de Vendas"} - SUPORTE EMERGENCIAL"""
    elif alert_type == "EXPIRED":
        days_expired = abs(days_to_expire)
        message = f"""❌ {client_name}, sua licença VENCEU!

O {license_name} expirou há {days_expired} dias.

CONSEQUÊNCIAS ATUAIS:
🚫 Sistemas bloqueados
🚫 Suporte suspenso

REATIVE AGORA com desconto especial:
💰 20% OFF para reativação
🔄 Reativação imediata

LIGUE URGENTE: (11) 9999-9999

{salesperson or "Equipe de Vendas"} - REATIVAÇÃO"""
    else:
        message = f"Olá {client_name}! Sua licença {license_name} precisa de atenção. Entre em contato conosco: (11) 9999-9999"
    
    # Enviar mensagem via WhatsApp service
    try:
        payload = {
            "phone_number": phone_number,
            "message": message,
            "message_id": f"renewal_{client_data.get('id')}_{alert_type}",
            "context": {
                "client_id": client_data.get('id'),
                "license_id": license_data.get('id'),
                "alert_type": alert_type,
                "salesperson": salesperson
            }
        }
        
        data = await call_whatsapp_service("send", "POST", payload)
        
        return {
            "success": data.get("success", False),
            "message_id": data.get("message_id"),
            "phone_number": phone_number,
            "error": data.get("error"),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        return {
            "success": False,
            "phone_number": phone_number,
            "error": getattr(e, 'detail', str(e)),  # 🔧 FIX: Proper HTTPException error extraction
            "timestamp": datetime.utcnow()
        }

# Include routers
app.include_router(api_router)
# app.include_router(whatsapp_router)  # Real WhatsApp integration - Commented out to avoid circular import

# Add structured logging middlewares (simplified integration)
@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    """Simple structured logging middleware"""
    import time
    import uuid
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Start timing
    start_time = time.time()
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log request with structured logger
        structured_logger.info(
            EventCategory.SYSTEM,
            "request_completed",
            f"{request.method} {request.url.path} - {response.status_code}",
            details={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "query_params": dict(request.query_params),
                "user_agent": request.headers.get('user-agent', 'unknown')[:100]
            }
        )
        
        # Log slow requests
        if duration_ms > 1000:
            structured_logger.warning(
                EventCategory.SYSTEM,
                "slow_request",
                f"Slow request: {duration_ms:.2f}ms",
                details={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "duration_ms": duration_ms
                }
            )
        
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        # Log error
        structured_logger.error(
            EventCategory.SYSTEM,
            "request_error", 
            f"{request.method} {request.url.path} - Error",
            error=e,
            details={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "duration_ms": round(duration_ms, 2)
            }
        )
        raise

# 🚀 PHASE 1 SECURITY IMPROVEMENTS - Add new middlewares
# Order is critical: Error handling → Tenant validation → Existing middlewares

# 1. Global error handling (catch all errors)
app.add_middleware(ErrorHandlingMiddleware)

# 2. Tenant validation (security-first)
app.add_middleware(TenantValidationMiddleware, db=db)

# Add structured logging middlewares
app.add_middleware(ErrorLoggingMiddleware)
app.add_middleware(PerformanceMonitoringMiddleware) 
app.add_middleware(StructuredLoggingMiddleware)

# ---------- CORS (origens explícitas; nunca '*' com credentials) ----------
# Use settings from new configuration system
CORS_ORIGINS = settings.cors_origins
ALLOW_CREDENTIALS = settings.allow_credentials
ALLOWED_HEADERS = ["Content-Type", "Authorization", "Accept", "X-Tenant-ID"]
EXPOSE_HEADERS = ["X-Tenant-ID"]

# Enhanced CORS validation using settings
if ALLOW_CREDENTIALS and "*" in CORS_ORIGINS:
    raise RuntimeError("CORS_ORIGINS cannot contain '*' when allow_credentials=True")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=ALLOWED_HEADERS,
    expose_headers=EXPOSE_HEADERS,
)

# Middlewares de observabilidade, rate limit e tenant context
# app.add_middleware(ObservabilityMiddleware)  # Disabled due to __call__ signature conflict
app.add_middleware(RateLimitMiddleware)
# NOTE: TenantContextMiddleware now works with TenantValidationMiddleware
app.add_middleware(TenantContextMiddleware)
app.add_middleware(ResponseTenantHeaderMiddleware)

# Debug middleware to log all requests
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    return response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def initialize_rbac_system():
    """Initialize RBAC system with default permissions and roles"""
    try:
        # Verificar se sistema RBAC já foi inicializado
        existing_permissions = await db.permissions.count_documents({})
        if existing_permissions > 0:
            logger.info("RBAC system already initialized")
            return
        
        logger.info("Initializing RBAC system...")
        
        # Criar permissões padrão
        default_permissions = [
            {"name": "users.read", "description": "Visualizar usuários", "resource": "users", "action": "read"},
            {"name": "users.create", "description": "Criar usuários", "resource": "users", "action": "create"},
            {"name": "users.update", "description": "Editar usuários", "resource": "users", "action": "update"},
            {"name": "users.delete", "description": "Excluir usuários", "resource": "users", "action": "delete"},
            {"name": "users.manage", "description": "Gerenciar usuários (todas ações)", "resource": "users", "action": "manage"},
            
            {"name": "licenses.read", "description": "Visualizar licenças", "resource": "licenses", "action": "read"},
            {"name": "licenses.create", "description": "Criar licenças", "resource": "licenses", "action": "create"},
            {"name": "licenses.update", "description": "Editar licenças", "resource": "licenses", "action": "update"},
            {"name": "licenses.delete", "description": "Excluir licenças", "resource": "licenses", "action": "delete"},
            {"name": "licenses.manage", "description": "Gerenciar licenças (todas ações)", "resource": "licenses", "action": "manage"},
            
            {"name": "clients.read", "description": "Visualizar clientes", "resource": "clients", "action": "read"},
            {"name": "clients.create", "description": "Criar clientes", "resource": "clients", "action": "create"},
            {"name": "clients.update", "description": "Editar clientes", "resource": "clients", "action": "update"},
            {"name": "clients.delete", "description": "Excluir clientes", "resource": "clients", "action": "delete"},
            {"name": "clients.manage", "description": "Gerenciar clientes (todas ações)", "resource": "clients", "action": "manage"},
            
            {"name": "reports.read", "description": "Visualizar relatórios", "resource": "reports", "action": "read"},
            {"name": "reports.create", "description": "Criar relatórios", "resource": "reports", "action": "create"},
            {"name": "reports.export", "description": "Exportar relatórios", "resource": "reports", "action": "export"},
            
            {"name": "rbac.read", "description": "Visualizar sistema RBAC", "resource": "rbac", "action": "read"},
            {"name": "rbac.manage", "description": "Gerenciar sistema RBAC", "resource": "rbac", "action": "manage"},
            
            {"name": "maintenance.read", "description": "Visualizar manutenção", "resource": "maintenance", "action": "read"},
            {"name": "maintenance.manage", "description": "Gerenciar manutenção", "resource": "maintenance", "action": "manage"},
            
            {"name": "*", "description": "Super Admin - Todas as permissões", "resource": "*", "action": "*"}
        ]
        
        # Inserir permissões
        permissions_to_insert = []
        for perm_data in default_permissions:
            permission = Permission(**perm_data)
            permissions_to_insert.append(permission.dict())
        
        await db.permissions.insert_many(permissions_to_insert)
        logger.info(f"Created {len(permissions_to_insert)} default permissions")
        
        # Buscar IDs das permissões criadas
        all_permissions = await db.permissions.find().to_list(1000)
        permission_map = {p["name"]: p["id"] for p in all_permissions}
        
        # Criar roles padrão
        default_roles = [
            {
                "name": "Super Admin",
                "description": "Acesso completo ao sistema",
                "permissions": [permission_map["*"]],
                "is_system": True
            },
            {
                "name": "Admin",
                "description": "Administrador com acesso a usuários e licenças",
                "permissions": [
                    permission_map["users.manage"],
                    permission_map["licenses.manage"],
                    permission_map["clients.manage"],
                    permission_map["reports.read"],
                    permission_map["maintenance.read"]
                ],
                "is_system": True
            },
            {
                "name": "Manager", 
                "description": "Gerente com acesso a licenças e relatórios",
                "permissions": [
                    permission_map["licenses.manage"],
                    permission_map["clients.read"],
                    permission_map["clients.create"],
                    permission_map["clients.update"],
                    permission_map["reports.read"],
                    permission_map["reports.export"]
                ],
                "is_system": False
            },
            {
                "name": "Sales",
                "description": "Vendedor com acesso a clientes e criação de licenças",
                "permissions": [
                    permission_map["clients.manage"],
                    permission_map["licenses.create"],
                    permission_map["licenses.read"],
                    permission_map["reports.read"]
                ],
                "is_system": False
            },
            {
                "name": "Viewer",
                "description": "Usuário com acesso apenas para visualização",
                "permissions": [
                    permission_map["licenses.read"],
                    permission_map["clients.read"],
                    permission_map["users.read"]
                ],
                "is_system": False
            }
        ]
        
        # Inserir roles
        roles_to_insert = []
        for role_data in default_roles:
            role = Role(**role_data)
            roles_to_insert.append(role.dict())
        
        await db.roles.insert_many(roles_to_insert)
        logger.info(f"Created {len(roles_to_insert)} default roles")
        
        # Atribuir Super Admin role ao usuário admin existente
        admin_user = await db.users.find_one({"email": "admin@demo.com"})
        if admin_user:
            super_admin_role = next(r for r in roles_to_insert if r["name"] == "Super Admin")
            await db.users.update_one(
                {"email": "admin@demo.com"},
                {
                    "$set": {
                        "rbac.roles": [super_admin_role["id"]],
                        "rbac.is_active": True,
                        "rbac.last_permission_update": datetime.utcnow()
                    }
                }
            )
            logger.info("Assigned Super Admin role to admin@demo.com")
        
        logger.info("RBAC system initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize RBAC system: {e}")

async def initialize_default_tenant():
    """
    Inicializar tenant padrão para dados existentes
    """
    logger.info("Checking default tenant...")
    
    # Verificar se tenant padrão já existe
    default_tenant = await db.tenants.find_one({"id": "default"})
    
    if not default_tenant:
        # Criar tenant padrão
        tenant_data = {
            "id": "default",
            "name": "Sistema Padrão",
            "subdomain": "default",
            "contact_email": "admin@sistema.com",
            "status": TenantStatus.ACTIVE,
            "plan": TenantPlan.ENTERPRISE,
            "max_users": -1,  # Ilimitado
            "max_licenses": -1,  # Ilimitado
            "max_clients": -1,  # Ilimitado
            "features": {
                "api_access": True,
                "webhooks": True,
                "advanced_reports": True,
                "white_label": True,
                "priority_support": True,
                "audit_logs": True,
                "sso": True
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "current_users": 0,
            "current_licenses": 0,
            "current_clients": 0
        }
        
        await db.tenants.insert_one(tenant_data)
        logger.info("Default tenant created")
        
        # Migrar dados existentes para o tenant padrão
        collections_to_migrate = [
            "users", "categories", "products", "licenses", 
            "clients_pf", "clients_pj", "roles", "permissions"
        ]
        
        for collection_name in collections_to_migrate:
            collection = getattr(db, collection_name)
            
            # Adicionar tenant_id aos documentos que não têm
            result = await collection.update_many(
                {"tenant_id": {"$exists": False}},
                {"$set": {"tenant_id": "default"}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Migrated {result.modified_count} documents in {collection_name} to default tenant")
        
    else:
        logger.info("Default tenant already exists")

async def ensure_critical_indexes():
    """
    Ensure critical database indexes are created for optimal performance
    🚀 SUB-FASE 2.1 - Enhanced with comprehensive performance optimization
    """
    try:
        logger.info("🚀 SUB-FASE 2.1 - Starting comprehensive database optimization...")
        
        # 🚀 NEW: Use advanced database optimizer
        from database_optimization import optimize_database_performance
        success = await optimize_database_performance(db)
        
        if success:
            logger.info("✅ SUB-FASE 2.1 - Advanced database optimization completed successfully!")
        else:
            logger.warning("⚠️ Advanced optimization failed, falling back to minimal optimizer...")
            
            # Fallback to existing minimal optimizer
            from minimal_optimizer import MinimalOptimizer
            optimizer = MinimalOptimizer()
            await optimizer.connect()
            
            # Check if optimization is needed (simple check for existing indexes)
            collections = await optimizer.db.list_collection_names() 
            if "licenses" in collections:
                indexes = await optimizer.db.licenses.list_indexes().to_list(None)
                has_tenant_index = any(idx.get("name") == "tenant_expires_idx" for idx in indexes)
                
                if not has_tenant_index:
                    logger.info("Creating essential database indexes...")
                    await optimizer.create_essential_indexes()
                    logger.info("✅ Critical database indexes created successfully")
                else:
                    logger.info("✅ Critical database indexes already exist")
            
            await optimizer.close()
        
    except Exception as e:
        logger.error(f"❌ Database optimization failed: {e}")
        # Don't raise the exception to prevent startup failure 
        # Indexes are important but not critical for basic functionality

async def ensure_indexes():
    """Garantir índices únicos de tenant_id + campo principal e índices compostos para hierarquias"""
    try:
        # users: único por tenant/email e consulta por admin_vendor_id
        existing = await db.users.index_information()
        if "uniq_tenant_email" not in existing:
            await db.users.create_index(
                [("tenant_id", 1), ("email", 1)],
                unique=True,
                name="uniq_tenant_email",
            )
        if "idx_users_tenant_admin_vendor" not in existing:
            await db.users.create_index(
                [("tenant_id", 1), ("admin_vendor_id", 1)],
                name="idx_users_tenant_admin_vendor",
            )

        # licenses: único por tenant/serial e consultas por seller/assigned
        existing = await db.licenses.index_information()
        if "uniq_tenant_serial" not in existing:
            await db.licenses.create_index(
                [("tenant_id", 1), ("serial", 1)],
                unique=True,
                name="uniq_tenant_serial",
            )
        if "idx_licenses_tenant_seller" not in existing:
            await db.licenses.create_index([("tenant_id", 1), ("seller_admin_id", 1)], name="idx_licenses_tenant_seller")
        if "idx_licenses_tenant_assigned" not in existing:
            await db.licenses.create_index([("tenant_id", 1), ("assigned_user_id", 1)], name="idx_licenses_tenant_assigned")

        # Índices básicos para outras coleções
        await db.categories.create_index([("tenant_id", 1), ("id", 1)], unique=True)
        await db.products.create_index([("tenant_id", 1), ("id", 1)], unique=True)
        await db.clientes_pf.create_index([("tenant_id", 1), ("cpf", 1)], unique=True)
        await db.clientes_pj.create_index([("tenant_id", 1), ("cnpj", 1)], unique=True)
        await db.roles.create_index([("tenant_id", 1), ("id", 1)], unique=True)
        await db.permissions.create_index([("tenant_id", 1), ("id", 1)], unique=True)

        # Índices de convites
        existing = await db.invitations.index_information()
        if "uniq_invite_token_hash" not in existing:
            await db.invitations.create_index(
                [("token_hash", 1)],
                unique=True,
                name="uniq_invite_token_hash",
            )
        if "idx_invite_email" not in existing:
            await db.invitations.create_index([("email", 1), ("tenant_id", 1)], name="idx_invite_email")
        if "idx_invite_admin" not in existing:
            await db.invitations.create_index([("tenant_id", 1), ("admin_vendor_id", 1)], name="idx_invite_admin")
        
        print("✅ Índices únicos e compostos criados com sucesso (incluindo convites)")
    except Exception as e:
        # Logue o erro de índice, mas não derrube a app
        print(f"[indexes] erro ao criar índices: {e}")

@app.on_event("startup")
async def startup_db_client():
    logger.info("Starting up License Management System...")
    
    # Garantir índices críticos
    await ensure_indexes()
    
    # Initialize default tenant first
    await initialize_default_tenant()
    maintenance_logger.info("system", "multi_tenancy_initialized", {
        "default_tenant_created": True,
        "data_migration_completed": True,
        "tenant_isolation_active": True,
        "collections_migrated": ["users", "categories", "products", "licenses", "clients_pf", "clients_pj", "roles", "permissions"]
    })
    
    # Create critical database indexes (idempotent)
    await ensure_critical_indexes()
    
    # Security: Only create demo users if explicitly enabled
    if os.getenv("SEED_DEMO", "false").lower() == "true":
        logger.info("SEED_DEMO=true: Creating demo users")
        
        # Create demo admin user with default tenant
        admin_exists = await db.users.find_one({"email": "admin@demo.com"})
        if not admin_exists:
            admin_user = User(
                email="admin@demo.com",
                name="Demo Admin",
                role=UserRole.ADMIN,
                tenant_id="default"
            )
            admin_dict = admin_user.dict()
            admin_dict["password_hash"] = get_password_hash("admin123")
            await db.users.insert_one(admin_dict)
            logger.info("Demo admin user created")
        
        user_exists = await db.users.find_one({"email": "user@demo.com"})
        if not user_exists:
            # Create separate tenant for demo user
            demo_user_tenant_id = "demo-user-tenant"
            demo_tenant_exists = await db.tenants.find_one({"id": demo_user_tenant_id})
            
            if not demo_tenant_exists:
                # Create demo user tenant
                demo_tenant_data = {
                    "id": demo_user_tenant_id,
                    "name": "Demo User Company",
                    "subdomain": "demo-user",
                    "contact_email": "user@demo.com",
                    "status": "active",
                    "plan": "free",
                    "max_users": 5,
                    "max_licenses": 10,
                    "max_clients": 5,
                    "features": {
                        "api_access": False,
                        "webhooks": False,
                        "advanced_reports": False,
                        "white_label": False,
                        "priority_support": False,
                        "audit_logs": False,
                        "sso": False
                    },
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                await db.tenants.insert_one(demo_tenant_data)
                logger.info("Demo user tenant created")
            
            demo_user = User(
                email="user@demo.com",
                name="Demo User",
                role=UserRole.USER,
                tenant_id=demo_user_tenant_id  # Separate tenant!
            )
            user_dict = demo_user.dict()
            user_dict["password_hash"] = get_password_hash("user123")
            await db.users.insert_one(user_dict)
            logger.info("Demo regular user created in separate tenant")
            
        # Create some demo categories
        categories_exist = await db.categories.count_documents({"tenant_id": "default"}) > 0
        if not categories_exist:
            demo_categories = [
                {"name": "Software", "description": "Licenças de software", "color": "#3B82F6", "icon": "code", "tenant_id": "default"},
                {"name": "Office", "description": "Ferramentas de escritório", "color": "#10B981", "icon": "briefcase", "tenant_id": "default"},
                {"name": "Design", "description": "Ferramentas de design", "color": "#8B5CF6", "icon": "palette", "tenant_id": "default"},
                {"name": "Segurança", "description": "Ferramentas de segurança", "color": "#EF4444", "icon": "shield", "tenant_id": "default"}
            ]
            for cat_data in demo_categories:
                category = Category(**cat_data)
                await db.categories.insert_one(category.dict())
            logger.info("Demo categories created")
    else:
        logger.info("SEED_DEMO=false: Skipping demo user creation for security")
    
    # Initialize RBAC system
    await initialize_rbac_system()
    
    # Optimize database indexes (run only once or when needed)
    try:
        from minimal_optimizer import MinimalOptimizer
        optimizer = MinimalOptimizer()
        await optimizer.connect()
        
        # Check if optimization is needed (simple check for existing indexes)
        collections = await optimizer.db.list_collection_names() 
        if "licenses" in collections:
            indexes = await optimizer.db.licenses.list_indexes().to_list(None)
            has_tenant_index = any(idx.get("name") == "tenant_expires_idx" for idx in indexes)
            
            if not has_tenant_index:
                logger.info("🗄️ Running database optimization...")
                await optimizer.create_essential_indexes()
                logger.info("✅ Database optimization completed")
            else:
                logger.info("✅ Database already optimized")
        
        await optimizer.close()
        
    except Exception as e:
        logger.warning(f"Database optimization skipped: {e}")
    
    # Start robust scheduler system  
    await start_robust_scheduler()
    maintenance_logger.info("scheduler", "robust_scheduler_started", {
        "status": "operational", 
        "scheduler_type": "apscheduler",
        "persistence": "mongodb",
        "features": ["license_expiry_detection", "multi_channel_alerts", "tenant_isolation", "auto_recovery", "cron_scheduling"]
    })
    logger.info("Notification jobs started")

    await initialize_rbac_system()

@app.on_event("shutdown")
async def shutdown_db_client():
    # Stop robust scheduler
    await stop_robust_scheduler()
    logger.info("Robust scheduler stopped")
    
    client.close()