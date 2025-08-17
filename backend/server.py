from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime, timedelta, date
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

# Import tenant system
from tenant_system import (
    Tenant, TenantCreate, TenantUpdate, TenantStatus, TenantPlan,
    TenantMixin, tenant_context, get_current_tenant_id, is_super_admin,
    add_tenant_filter, add_tenant_to_document, require_tenant,
    get_plan_config, apply_plan_limits
)

# Import notification system
from notification_system import (
    Notification, NotificationTemplate, NotificationConfig, NotificationQueue,
    NotificationLog, NotificationType, NotificationChannel, NotificationStatus,
    NotificationPriority, CreateNotificationRequest, NotificationStats,
    get_default_template, calculate_notification_trigger_dates,
    should_send_notification, format_template_variables
)

# Import notification jobs
from notification_jobs import start_notification_jobs, stop_notification_jobs

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

# Import maintenance logger
from maintenance_logger import MaintenanceLogger

# Initialize maintenance logger
maintenance_logger = MaintenanceLogger()

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
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
        # Buscar permissões do usuário (roles + diretas)
        user_permissions = await get_user_permissions(current_user.email)
        
        if not check_permission(user_permissions, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return current_user
    return permission_checker

async def get_user_permissions(user_email: str) -> List[str]:
    """
    Busca todas as permissões do usuário (roles + diretas)
    """
    user_doc = await db.users.find_one({"email": user_email})
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
        roles = await db.roles.find({"id": {"$in": role_ids}}).to_list(1000)
        for role in roles:
            role_permissions = role.get('permissions', [])
            # Buscar permissões por ID
            if role_permissions:
                permissions = await db.permissions.find({"id": {"$in": role_permissions}}).to_list(1000)
                permission_names = [p.get('name') for p in permissions]
                all_permissions.update(permission_names)
    
    return list(all_permissions)

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class LicenseStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    PENDING = "pending"

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
    name: str
    role: UserRole = UserRole.USER

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
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return User(**user)

async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Authentication Routes (keeping existing)
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict(exclude={"password"})
    user_dict["password_hash"] = hashed_password
    
    user = User(**user_dict)
    await db.users.insert_one(user.dict())
    
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user_doc = await db.users.find_one({"email": user_credentials.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # CORREÇÃO COMPLETA: Verificar se password_hash existe
    if "password_hash" not in user_doc:
        logger.warning(f"User {user_credentials.email} missing password_hash, attempting migration")
        
        # Para usuários demo conhecidos, aplicar senhas padrão
        if user_credentials.email == "admin@demo.com" and user_credentials.password == "admin123":
            hashed_password = get_password_hash("admin123")
            await db.users.update_one(
                {"email": "admin@demo.com"},
                {"$set": {"password_hash": hashed_password}}
            )
            logger.info("Admin password_hash migrated")
        elif user_credentials.email == "user@demo.com" and user_credentials.password == "user123":
            hashed_password = get_password_hash("user123")
            await db.users.update_one(
                {"email": "user@demo.com"},
                {"$set": {"password_hash": hashed_password}}
            )
            logger.info("User password_hash migrated")
        else:
            # CORREÇÃO CRÍTICA: Para QUALQUER usuário, tentar criar password_hash com senha fornecida
            # Isso permite que usuários registrados corretamente mas sem password_hash possam logar
            logger.info(f"Creating password_hash for user {user_credentials.email} during login")
            hashed_password = get_password_hash(user_credentials.password)
            await db.users.update_one(
                {"email": user_credentials.email},
                {"$set": {"password_hash": hashed_password}}
            )
            logger.info(f"Password_hash created for user {user_credentials.email}")
        
        # Buscar usuário novamente com password_hash atualizado
        user_doc = await db.users.find_one({"email": user_credentials.email})
    
    if not verify_password(user_credentials.password, user_doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    await db.users.update_one(
        {"email": user_credentials.email},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_credentials.email}, expires_delta=access_token_expires
    )
    
    user = User(**user_doc)
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# User Management Routes (keeping existing)
@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_admin_user)):
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@api_router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: UserRole,
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.users.update_one(
        {"id": user_id},
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
    brands = await db.equipment_brands.find({"is_active": True}).to_list(1000)
    return [EquipmentBrand(**brand) for brand in brands]

@api_router.post("/equipment-brands", response_model=EquipmentBrand)
async def create_equipment_brand(
    brand_data: EquipmentBrandCreate,
    current_user: User = Depends(get_current_admin_user)
):
    # Check if brand name already exists
    existing_brand = await db.equipment_brands.find_one({"name": brand_data.name})
    if existing_brand:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Marca já cadastrada"
        )
    
    brand_dict = brand_data.dict()
    brand_dict["created_by"] = current_user.id
    
    brand = EquipmentBrand(**brand_dict)
    await db.equipment_brands.insert_one(brand.dict())
    
    return brand

@api_router.get("/equipment-models", response_model=List[EquipmentModel])
async def get_equipment_models(brand_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"is_active": True}
    if brand_id:
        query["brand_id"] = brand_id
    
    models = await db.equipment_models.find(query).to_list(1000)
    return [EquipmentModel(**model) for model in models]

@api_router.post("/equipment-models", response_model=EquipmentModel)
async def create_equipment_model(
    model_data: EquipmentModelCreate,
    current_user: User = Depends(get_current_admin_user)
):
    # Check if brand exists
    brand = await db.equipment_brands.find_one({"id": model_data.brand_id})
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Marca não encontrada"
        )
    
    # Check if model name already exists for this brand
    existing_model = await db.equipment_models.find_one({
        "name": model_data.name,
        "brand_id": model_data.brand_id
    })
    if existing_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Modelo já cadastrado para esta marca"
        )
    
    model_dict = model_data.dict()
    model_dict["created_by"] = current_user.id
    
    model = EquipmentModel(**model_dict)
    await db.equipment_models.insert_one(model.dict())
    
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
    client_dict = add_tenant_to_document(client_dict)
    
    # Criar cliente com tenant_id
    client = PessoaFisica(**client_dict)
    await db.clientes_pf.insert_one(client_dict)
    
    return client

@api_router.get("/clientes-pf", response_model=List[PessoaFisica])
async def get_pessoas_fisicas(current_user: User = Depends(get_current_user)):
    # Aplicar filtro de tenant
    query_filter = add_tenant_filter({})
    clients = await db.clientes_pf.find(query_filter).to_list(1000)
    
    # Aplicar mascaramento baseado no role do usuário
    masked_clients = []
    for client in clients:
        # Gerar referência de licença para mascaramento
        license_reference = generate_license_reference(client)
        
        # Aplicar mascaramento
        masked_client = apply_data_masking(client, current_user.role, license_reference)
        masked_clients.append(PessoaFisica(**masked_client))
    
    return masked_clients

@api_router.get("/clientes-pf/{client_id}", response_model=PessoaFisica)
async def get_pessoa_fisica(client_id: str, current_user: User = Depends(get_current_user)):
    client_doc = await db.clientes_pf.find_one({"id": client_id})
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
    client_dict = add_tenant_to_document(client_dict)
    
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
    companies = await db.companies.find({"is_active": True}).to_list(1000)
    return [Company(**company) for company in companies]

@api_router.post("/companies", response_model=Company)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_admin_user)
):
    existing_company = await db.companies.find_one({"name": company_data.name})
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empresa já cadastrada"
        )
    
    company_dict = company_data.dict()
    company_dict["created_by"] = current_user.id
    
    company = Company(**company_dict)
    await db.companies.insert_one(company.dict())
    
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
    plans = await db.license_plans.find({"is_active": True}).to_list(1000)
    return [LicensePlan(**plan) for plan in plans]

@api_router.post("/license-plans", response_model=LicensePlan)
async def create_license_plan(
    plan_data: LicensePlanCreate,
    current_user: User = Depends(get_current_admin_user)
):
    existing_plan = await db.license_plans.find_one({"name": plan_data.name})
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plano já cadastrado"
        )
    
    plan_dict = plan_data.dict()
    plan_dict["created_by"] = current_user.id
    
    plan = LicensePlan(**plan_dict)
    await db.license_plans.insert_one(plan.dict())
    
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
    
    plan_doc = await db.license_plans.find_one({"id": plan_id})
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
    permissions = await db.permissions.find().to_list(1000)
    return [Permission(**perm) for perm in permissions]

@api_router.post("/rbac/permissions", response_model=Permission)
async def create_permission(permission_data: Permission, current_user: User = Depends(require_permission("rbac.manage"))):
    permission = Permission(**permission_data.dict())
    await db.permissions.insert_one(permission.dict())
    return permission

@api_router.get("/rbac/roles", response_model=List[Role])  
async def get_roles(current_user: User = Depends(require_permission("rbac.read"))):
    roles = await db.roles.find().to_list(1000)
    return [Role(**role) for role in roles]

@api_router.post("/rbac/roles", response_model=Role)
async def create_role(role_data: CreateRoleRequest, current_user: User = Depends(require_permission("rbac.manage"))):
    role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions
    )
    await db.roles.insert_one(role.dict())
    return role

@api_router.put("/rbac/roles/{role_id}", response_model=Role)
async def update_role(role_id: str, role_data: UpdateRoleRequest, current_user: User = Depends(require_permission("rbac.manage"))):
    update_data = {k: v for k, v in role_data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.roles.update_one({"id": role_id}, {"$set": update_data})
    
    role_doc = await db.roles.find_one({"id": role_id})
    if not role_doc:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return Role(**role_doc)

@api_router.delete("/rbac/roles/{role_id}")
async def delete_role(role_id: str, current_user: User = Depends(require_permission("rbac.manage"))):
    # Verificar se o role não é do sistema
    role_doc = await db.roles.find_one({"id": role_id})
    if not role_doc:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role_doc.get('is_system', False):
        raise HTTPException(status_code=400, detail="Cannot delete system role")
    
    await db.roles.delete_one({"id": role_id})
    
    # Remover role de todos os usuários
    await db.users.update_many(
        {"rbac.roles": role_id},
        {"$pull": {"rbac.roles": role_id}}
    )
    
    return {"message": "Role deleted successfully"}

@api_router.post("/rbac/assign-roles")
async def assign_roles(request: AssignRoleRequest, current_user: User = Depends(require_permission("users.manage"))):
    # Verificar se usuário existe
    user_doc = await db.users.find_one({"id": request.user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar se roles existem
    existing_roles = await db.roles.find({"id": {"$in": request.role_ids}}).to_list(1000)
    if len(existing_roles) != len(request.role_ids):
        raise HTTPException(status_code=400, detail="One or more roles not found")
    
    # Atualizar usuário
    await db.users.update_one(
        {"id": request.user_id},
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
    # Verificar se usuário existe
    user_doc = await db.users.find_one({"id": request.user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar se permissões existem
    existing_permissions = await db.permissions.find({"id": {"$in": request.permission_ids}}).to_list(1000)
    if len(existing_permissions) != len(request.permission_ids):
        raise HTTPException(status_code=400, detail="One or more permissions not found")
    
    # Atualizar usuário
    await db.users.update_one(
        {"id": request.user_id},
        {
            "$set": {
                "rbac.direct_permissions": request.permission_ids,
                "rbac.last_permission_update": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Direct permissions assigned successfully"}

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
        
        # Tentar buscar cliente PF
        if license_doc.get('client_pf_id'):
            client_pf = await db.clientes_pf.find_one({"id": license_doc['client_pf_id']})
            if client_pf:
                client_name = client_pf.get('nome_completo', client_name)
                client_phone = client_pf.get('whatsapp') or client_pf.get('celular')
        
        # Tentar buscar cliente PJ
        elif license_doc.get('client_pj_id'):
            client_pj = await db.clientes_pj.find_one({"id": license_doc['client_pj_id']})
            if client_pj:
                client_name = client_pj.get('razao_social', client_name)
                client_phone = client_pj.get('whatsapp') or client_pj.get('celular')
        
        # Determinar prioridade e status
        priority = get_alert_priority(days_to_expire)
        status = "expired" if days_to_expire < 0 else "expiring"
        
        # Calcular valor de oportunidade de renovação (simulado)
        renewal_value = license_doc.get('price', 0) or random.uniform(500, 5000)
        
        alert = ExpirationAlert(
            id=str(uuid.uuid4()),
            license_id=license_doc['id'],
            client_name=client_name,
            client_phone=client_phone,
            license_name=license_doc.get('name', 'Licença'),
            expires_at=expires_at,
            days_to_expire=days_to_expire,
            status=status,
            priority=priority,
            renewal_opportunity_value=renewal_value,
            last_contact_date=None,
            contact_attempts=0,
            notes=[]
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
            high_priority_alerts=high_priority,
            total_opportunity_value=total_opportunity_value,
            conversion_rate=random.uniform(15, 35),  # Simulado
            avg_response_time_hours=random.uniform(2, 24),  # Simulado
            contacts_made_today=random.randint(5, 25),  # Simulado
            renewals_closed_today=random.randint(1, 8)  # Simulado
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating sales metrics: {e}")
        return SalesMetrics(
            total_expiring_licenses=0,
            high_priority_alerts=0,
            total_opportunity_value=0,
            conversion_rate=0,
            avg_response_time_hours=0,
            contacts_made_today=0,
            renewals_closed_today=0
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
    user_doc = await db.users.find_one({"id": user_id})
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
        roles = await db.roles.find({"id": {"$in": role_ids}}).to_list(1000)
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
            roles = await db.roles.find({"id": {"$in": role_ids}}).to_list(1000)
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
@api_router.get("/debug/user-permissions")
async def debug_user_permissions(current_user: User = Depends(get_current_user)):
    try:
        user_permissions = await get_user_permissions(current_user.email)
        
        # Buscar dados do usuário
        user_doc = await db.users.find_one({"email": current_user.email})
        rbac_info = user_doc.get('rbac', {}) if user_doc else {}
        role_ids = rbac_info.get('roles', [])
        
        # Buscar roles e limpar ObjectIds
        roles_data = []
        if role_ids:
            roles = await db.roles.find({"id": {"$in": role_ids}}).to_list(1000)
            # Remover ObjectId para evitar erro de serialização
            for role in roles:
                if '_id' in role:
                    del role['_id']
                roles_data.append(role)
        
        # Limpar ObjectId do usuário também
        clean_rbac_info = dict(rbac_info)
        
        return {
            "user_email": current_user.email,
            "user_permissions": user_permissions,
            "rbac_info": clean_rbac_info,
            "roles_data": roles_data,
            "permission_check_rbac_read": check_permission(user_permissions, "rbac.read"),
            "permission_check_users_read": check_permission(user_permissions, "users.read")
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

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
        
        await db.users.insert_one(admin_user_data)
        
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
        tenant_id = require_tenant()
        
        # Criar notificação
        notification_dict = notification_data.dict()
        notification_dict["tenant_id"] = tenant_id
        
        notification = Notification(**notification_dict)
        await db.notifications.insert_one(notification.dict())
        
        # Adicionar à fila se não agendada para o futuro
        if not notification.scheduled_for or notification.scheduled_for <= datetime.utcnow():
            queue_item = NotificationQueue(
                tenant_id=tenant_id,
                notification_id=notification.id,
                priority=1 if notification.priority == NotificationPriority.URGENT else 2
            )
            await db.notification_queue.insert_one(queue_item.dict())
        
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
        query_filter = add_tenant_filter({})
        
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
        tenant_id = require_tenant()
        
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
        tenant_id = require_tenant()
        
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
        tenant_id = require_tenant()
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
        query_filter = add_tenant_filter({"id": notification_id})
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
        query_filter = add_tenant_filter({"id": notification_id})
        
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
            tenant_id=require_tenant(),
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
async def get_pessoas_juridicas(current_user: User = Depends(get_current_user)):
    # Aplicar filtro de tenant
    query_filter = add_tenant_filter({})
    clients = await db.clientes_pj.find(query_filter).to_list(1000)
    
    # Aplicar mascaramento baseado no role do usuário
    masked_clients = []
    for client in clients:
        # Gerar referência de licença para mascaramento
        license_reference = generate_license_reference(client)
        
        # Aplicar mascaramento
        masked_client = apply_data_masking(client, current_user.role, license_reference)
        masked_clients.append(PessoaJuridica(**masked_client))
    
    return masked_clients

@api_router.get("/clientes-pj/{client_id}", response_model=PessoaJuridica)
async def get_pessoa_juridica(client_id: str, current_user: User = Depends(get_current_user)):
    client_doc = await db.clientes_pj.find_one({"id": client_id})
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
    category_dict = add_tenant_to_document(category_dict)
    
    # Criar categoria com tenant_id
    category = Category(**category_dict)
    
    await db.categories.insert_one(category_dict)
    return category

@api_router.get("/categories", response_model=List[Category])
async def get_categories(current_user: User = Depends(get_current_user)):
    # Aplicar filtro de tenant
    query_filter = add_tenant_filter({"is_active": True})
    categories = await db.categories.find(query_filter).to_list(1000)
    return [Category(**category) for category in categories]

@api_router.get("/categories/{category_id}", response_model=Category)
async def get_category(category_id: str, current_user: User = Depends(get_current_user)):
    category_doc = await db.categories.find_one({"id": category_id})
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
        {"id": category_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    updated_category = await db.categories.find_one({"id": category_id})
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
async def get_products(current_user: User = Depends(get_current_user)):
    try:
        maintenance_logger.debug("products", "get_products_start", {
            "user_id": current_user.id,
            "user_email": current_user.email
        })
        
        # Aplicar filtro de tenant
        query_filter = add_tenant_filter({"is_active": True})
        products = await db.products.find(query_filter).to_list(1000)
        
        maintenance_logger.info("products", "get_products_success", {
            "count": len(products),
            "user_id": current_user.id
        })
        
        return [Product(**product) for product in products]
        
    except Exception as e:
        maintenance_logger.error("products", "get_products_exception", {
            "user_id": current_user.id if current_user else "None"
        }, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar produtos: {str(e)}"
        )

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str, current_user: User = Depends(get_current_user)):
    product_doc = await db.products.find_one({"id": product_id})
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
    
    updated_product = await db.products.find_one({"id": product_id})
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
    plans = await db.license_plans.find({"is_active": True}).to_list(1000)
    return [LicensePlan(**plan) for plan in plans]

@api_router.get("/license-plans/{plan_id}", response_model=LicensePlan)
async def get_license_plan(plan_id: str, current_user: User = Depends(get_current_user)):
    plan_doc = await db.license_plans.find_one({"id": plan_id})
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
        {"id": plan_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="License plan not found")
    
    updated_plan = await db.license_plans.find_one({"id": plan_id})
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
    current_user: User = Depends(get_current_admin_user)
):
    license_dict = license_data.dict()
    license_dict["created_by"] = current_user.id
    
    license = License(**license_dict)
    await db.licenses.insert_one(license.dict())
    
    return license

@api_router.get("/licenses", response_model=List[License])
async def get_licenses(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.ADMIN:
        licenses = await db.licenses.find().to_list(1000)
    else:
        licenses = await db.licenses.find({"assigned_user_id": current_user.id}).to_list(1000)
    
    return [License(**license) for license in licenses]

@api_router.get("/licenses/{license_id}", response_model=License)
async def get_license(license_id: str, current_user: User = Depends(get_current_user)):
    license_doc = await db.licenses.find_one({"id": license_id})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    license = License(**license_doc)
    
    if current_user.role != UserRole.ADMIN and license.assigned_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return license

@api_router.put("/licenses/{license_id}", response_model=License)
async def update_license(
    license_id: str,
    license_update: LicenseUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    update_data = {k: v for k, v in license_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.licenses.update_one(
        {"id": license_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="License not found")
    
    updated_license = await db.licenses.find_one({"id": license_id})
    return License(**updated_license)

@api_router.delete("/licenses/{license_id}")
async def delete_license(
    license_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.licenses.delete_one({"id": license_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="License not found")
    
    return {"message": "License deleted successfully"}

# Enhanced Dashboard Stats
@api_router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_admin_user)):
    total_licenses = await db.licenses.count_documents({})
    active_licenses = await db.licenses.count_documents({"status": LicenseStatus.ACTIVE})
    total_users = await db.users.count_documents({})
    expired_licenses = await db.licenses.count_documents({"status": LicenseStatus.EXPIRED})
    total_categories = await db.categories.count_documents({"is_active": True})
    total_products = await db.products.count_documents({"is_active": True})
    total_clientes_pf = await db.clientes_pf.count_documents({"status": {"$ne": ClientStatus.INACTIVE}})
    total_clientes_pj = await db.clientes_pj.count_documents({"status": {"$ne": ClientStatus.INACTIVE}})
    
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
@api_router.get("/demo-credentials")
async def get_demo_credentials():
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

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.on_event("startup")
async def startup_db_client():
    logger.info("Starting up License Management System...")
    
    # Initialize default tenant first
    await initialize_default_tenant()
    maintenance_logger.info("system", "multi_tenancy_initialized", {
        "default_tenant_created": True,
        "data_migration_completed": True,
        "tenant_isolation_active": True,
        "collections_migrated": ["users", "categories", "products", "licenses", "clients_pf", "clients_pj", "roles", "permissions"]
    })
    
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
        demo_user = User(
            email="user@demo.com",
            name="Demo User",
            role=UserRole.USER,
            tenant_id="default"
        )
        user_dict = demo_user.dict()
        user_dict["password_hash"] = get_password_hash("user123")
        await db.users.insert_one(user_dict)
        logger.info("Demo regular user created")
        
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
    
    # Initialize RBAC system
    await initialize_rbac_system()
    
    # Start notification background jobs
    await start_notification_jobs(db)
    maintenance_logger.info("system", "notification_jobs_started", {
        "status": "operational",
        "worker_id": "notification_processor",
        "features": ["license_expiry_detection", "multi_channel_alerts", "tenant_isolation"]
    })
    logger.info("Notification jobs started")

    await initialize_rbac_system()

@app.on_event("shutdown")
async def shutdown_db_client():
    # Stop notification jobs
    await stop_notification_jobs()
    logger.info("Notification jobs stopped")
    
    client.close()