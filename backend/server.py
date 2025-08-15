from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, Dict, Any, Literal
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

# Import maintenance logger
import sys
sys.path.append('/app')
from maintenance_logger import logger as maint_logger

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

# Create API router
api_router = APIRouter(prefix="/api")

# Enums
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

# Base Models
class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
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
    # Check if CPF already exists
    existing_client = await db.clientes_pf.find_one({"cpf": client_data.cpf})
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado no sistema"
        )
    
    client_dict = client_data.dict()
    client_dict["created_by"] = current_user.id
    
    client = PessoaFisica(**client_dict)
    await db.clientes_pf.insert_one(client.dict())
    
    return client

@api_router.get("/clientes-pf", response_model=List[PessoaFisica])
async def get_pessoas_fisicas(current_user: User = Depends(get_current_user)):
    clients = await db.clientes_pf.find().to_list(1000)
    return [PessoaFisica(**client) for client in clients]

@api_router.get("/clientes-pf/{client_id}", response_model=PessoaFisica)
async def get_pessoa_fisica(client_id: str, current_user: User = Depends(get_current_user)):
    client_doc = await db.clientes_pf.find_one({"id": client_id})
    if not client_doc:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return PessoaFisica(**client_doc)

@api_router.put("/clientes-pf/{client_id}", response_model=PessoaFisica)
async def update_pessoa_fisica(
    client_id: str,
    client_update: PessoaFisicaUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    update_data = {k: v for k, v in client_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = current_user.id
    
    result = await db.clientes_pf.update_one(
        {"id": client_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    updated_client = await db.clientes_pf.find_one({"id": client_id})
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
    # Check if CNPJ already exists (use normalized format)
    cnpj_normalized = client_data.cnpj_normalizado if hasattr(client_data, 'cnpj_normalizado') else client_data.cnpj
    existing_client = await db.clientes_pj.find_one({"cnpj_normalizado": cnpj_normalized})
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CNPJ já cadastrado no sistema"
        )
    
    client_dict = client_data.dict()
    client_dict["created_by"] = current_user.id
    
    client = PessoaJuridica(**client_dict)
    await db.clientes_pj.insert_one(client.dict())
    
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
    clients = await db.clientes_pj.find().to_list(1000)
    return [PessoaJuridica(**client) for client in clients]

@api_router.get("/clientes-pj/{client_id}", response_model=PessoaJuridica)
async def get_pessoa_juridica(client_id: str, current_user: User = Depends(get_current_user)):
    client_doc = await db.clientes_pj.find_one({"id": client_id})
    if not client_doc:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return PessoaJuridica(**client_doc)

@api_router.put("/clientes-pj/{client_id}", response_model=PessoaJuridica)
async def update_pessoa_juridica(
    client_id: str,
    client_update: PessoaJuridicaUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    update_data = {k: v for k, v in client_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = current_user.id
    
    result = await db.clientes_pj.update_one(
        {"id": client_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    updated_client = await db.clientes_pj.find_one({"id": client_id})
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
    category = Category(**category_data.dict())
    await db.categories.insert_one(category.dict())
    return category

@api_router.get("/categories", response_model=List[Category])
async def get_categories(current_user: User = Depends(get_current_user)):
    categories = await db.categories.find({"is_active": True}).to_list(1000)
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
        maint_logger.info("products", "create_product_start", {
            "user_id": current_user.id,
            "user_email": current_user.email,
            "product_data": product_data.dict()
        })
        
        # Check if product with same name already exists
        existing_product = await db.products.find_one({"name": product_data.name})
        if existing_product:
            maint_logger.error("products", "create_product_duplicate", {
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
        product = Product(**product_dict)
        
        maint_logger.debug("products", "create_product_before_insert", {
            "product_id": product.id,
            "product_name": product.name,
            "complete_product": product.dict()
        })
        
        # Insert into database
        result = await db.products.insert_one(product.dict())
        
        maint_logger.info("products", "create_product_success", {
            "product_id": product.id,
            "product_name": product.name,
            "insert_result": str(result.inserted_id) if result else "None"
        })
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        maint_logger.error("products", "create_product_exception", {
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
        maint_logger.debug("products", "get_products_start", {
            "user_id": current_user.id,
            "user_email": current_user.email
        })
        
        products = await db.products.find({"is_active": True}).to_list(1000)
        
        maint_logger.info("products", "get_products_success", {
            "count": len(products),
            "user_id": current_user.id
        })
        
        return [Product(**product) for product in products]
        
    except Exception as e:
        maint_logger.error("products", "get_products_exception", {
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

@app.on_event("startup")
async def startup_db_client():
    # Create demo users on startup if they don't exist
    admin_exists = await db.users.find_one({"email": "admin@demo.com"})
    if not admin_exists:
        admin_user = User(
            email="admin@demo.com",
            name="Demo Admin",
            role=UserRole.ADMIN
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
            role=UserRole.USER
        )
        user_dict = demo_user.dict()
        user_dict["password_hash"] = get_password_hash("user123")
        await db.users.insert_one(user_dict)
        logger.info("Demo regular user created")
        
    # Create some demo categories
    categories_exist = await db.categories.count_documents({}) > 0
    if not categories_exist:
        demo_categories = [
            {"name": "Software", "description": "Licenças de software", "color": "#3B82F6", "icon": "code"},
            {"name": "Office", "description": "Ferramentas de escritório", "color": "#10B981", "icon": "briefcase"},
            {"name": "Design", "description": "Ferramentas de design", "color": "#8B5CF6", "icon": "palette"},
            {"name": "Segurança", "description": "Ferramentas de segurança", "color": "#EF4444", "icon": "shield"}
        ]
        for cat_data in demo_categories:
            category = Category(**cat_data)
            await db.categories.insert_one(category.dict())
        logger.info("Demo categories created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()