# Multi-Tenancy System for License Management
# Implementação de isolamento de dados por tenant (cliente SaaS)

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import re

class TenantStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"  
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"

class TenantPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class TenantBase(BaseModel):
    name: str = Field(..., description="Nome da organização/empresa")
    subdomain: str = Field(..., description="Subdomínio único (ex: empresa.licensemanager.com)")
    contact_email: str = Field(..., description="Email de contato principal")
    status: TenantStatus = TenantStatus.TRIAL
    plan: TenantPlan = TenantPlan.FREE
    
    # Configurações
    max_users: int = Field(default=5, description="Limite máximo de usuários")
    max_licenses: int = Field(default=100, description="Limite máximo de licenças")
    max_clients: int = Field(default=50, description="Limite máximo de clientes")
    
    # Customização (White-label)
    custom_logo_url: Optional[str] = None
    primary_color: str = Field(default="#3B82F6", description="Cor primária da interface")
    company_name: Optional[str] = None
    
    # Configurações avançadas
    timezone: str = Field(default="America/Sao_Paulo")
    locale: str = Field(default="pt_BR")
    currency: str = Field(default="BRL")
    
    # Recursos habilitados por plano
    features: Dict[str, bool] = Field(default_factory=lambda: {
        "api_access": False,
        "webhooks": False,
        "advanced_reports": False,
        "white_label": False,
        "priority_support": False,
        "audit_logs": False,
        "sso": False
    })
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        if not v:
            raise ValueError('Subdomain is required')
        
        # Apenas letras, números e hífens, sem espaços
        if not re.match(r'^[a-z0-9-]+$', v.lower()):
            raise ValueError('Subdomain must contain only lowercase letters, numbers and hyphens')
        
        # Não pode começar ou terminar com hífen
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('Subdomain cannot start or end with hyphen')
            
        # Tamanho mínimo e máximo
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Subdomain must be between 3 and 50 characters')
            
        return v.lower()

class TenantCreate(TenantBase):
    # Dados do administrador inicial
    admin_name: str = Field(..., description="Nome do administrador inicial")
    admin_email: str = Field(..., description="Email do administrador inicial")
    admin_password: str = Field(..., min_length=8, description="Senha do administrador inicial")

class Tenant(TenantBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    # Métricas de uso (para billing)
    current_users: int = 0
    current_licenses: int = 0
    current_clients: int = 0
    
    # Billing info
    subscription_started_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None
    last_payment_at: Optional[datetime] = None
    
    # Auditoria
    created_by: Optional[str] = None  # ID do usuário que criou
    last_modified_by: Optional[str] = None

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None
    status: Optional[TenantStatus] = None
    plan: Optional[TenantPlan] = None
    max_users: Optional[int] = None
    max_licenses: Optional[int] = None  
    max_clients: Optional[int] = None
    custom_logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    company_name: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    currency: Optional[str] = None
    features: Optional[Dict[str, bool]] = None

# Context para tenant atual na request
class TenantContext:
    def __init__(self):
        self.current_tenant_id: Optional[str] = None
        self.current_tenant: Optional[Tenant] = None
        self.is_super_admin: bool = False
        
    def set_tenant(self, tenant_id: str, tenant: Optional[Tenant] = None, is_super_admin: bool = False):
        self.current_tenant_id = tenant_id
        self.current_tenant = tenant
        self.is_super_admin = is_super_admin
        
    def clear(self):
        self.current_tenant_id = None
        self.current_tenant = None
        self.is_super_admin = False

# Instância global do contexto (será gerenciada pelo middleware)
tenant_context = TenantContext()

# Mixin para adicionar tenant_id aos models
class TenantMixin(BaseModel):
    tenant_id: str = Field(..., description="ID do tenant proprietário dos dados")
    
    def dict(self, **kwargs):
        # Sempre incluir tenant_id no dict
        result = super().dict(**kwargs)
        if hasattr(self, 'tenant_id'):
            result['tenant_id'] = self.tenant_id
        return result

# Utilitários para tenant
def get_current_tenant_id() -> Optional[str]:
    """Retorna o ID do tenant atual do contexto"""
    return tenant_context.current_tenant_id

def get_current_tenant() -> Optional[Tenant]:
    """Retorna o tenant atual do contexto"""
    return tenant_context.current_tenant

def is_super_admin() -> bool:
    """Verifica se o usuário atual é super admin (cross-tenant)"""
    return tenant_context.is_super_admin

def require_tenant() -> str:
    """Retorna tenant_id obrigatório ou lança exceção"""
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise ValueError("Tenant context is required but not set")
    return tenant_id

def add_tenant_filter(query_filter: dict) -> dict:
    """Adiciona filtro de tenant a uma query MongoDB"""
    if is_super_admin():
        return query_filter  # Super admin vê tudo
        
    tenant_id = get_current_tenant_id()
    if tenant_id:
        query_filter["tenant_id"] = tenant_id
    return query_filter

def add_tenant_to_document(document: dict) -> dict:
    """Adiciona tenant_id a um documento antes de inserir no MongoDB"""
    if is_super_admin() and "tenant_id" in document:
        return document  # Super admin pode especificar tenant
        
    tenant_id = require_tenant()
    document["tenant_id"] = tenant_id
    return document

# Configurações default por plano
PLAN_CONFIGS = {
    TenantPlan.FREE: {
        "max_users": 2,
        "max_licenses": 50,
        "max_clients": 25,
        "features": {
            "api_access": False,
            "webhooks": False,
            "advanced_reports": False,
            "white_label": False,
            "priority_support": False,
            "audit_logs": False,
            "sso": False
        }
    },
    TenantPlan.BASIC: {
        "max_users": 5,
        "max_licenses": 200,
        "max_clients": 100,
        "features": {
            "api_access": True,
            "webhooks": False,
            "advanced_reports": True,
            "white_label": False,
            "priority_support": False,
            "audit_logs": True,
            "sso": False
        }
    },
    TenantPlan.PROFESSIONAL: {
        "max_users": 20,
        "max_licenses": 1000,
        "max_clients": 500,
        "features": {
            "api_access": True,
            "webhooks": True,
            "advanced_reports": True,
            "white_label": True,
            "priority_support": True,
            "audit_logs": True,
            "sso": False
        }
    },
    TenantPlan.ENTERPRISE: {
        "max_users": 100,
        "max_licenses": -1,  # Ilimitado
        "max_clients": -1,   # Ilimitado
        "features": {
            "api_access": True,
            "webhooks": True,
            "advanced_reports": True,
            "white_label": True,
            "priority_support": True,
            "audit_logs": True,
            "sso": True
        }
    }
}

def get_plan_config(plan: TenantPlan) -> dict:
    """Retorna configuração padrão para um plano"""
    return PLAN_CONFIGS.get(plan, PLAN_CONFIGS[TenantPlan.FREE])

def apply_plan_limits(tenant_data: dict, plan: TenantPlan) -> dict:
    """Aplica limites do plano aos dados do tenant"""
    config = get_plan_config(plan)
    tenant_data.update({
        "max_users": config["max_users"],
        "max_licenses": config["max_licenses"], 
        "max_clients": config["max_clients"],
        "features": config["features"]
    })
    return tenant_data