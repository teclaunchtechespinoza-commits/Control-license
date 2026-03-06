"""
Certificate Generation System - License Manager v1.4.0
Sistema de geração de certificados digitais com QR Code e validação online
"""
import os
import io
import uuid
import hashlib
import base64
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from PIL import Image

# Pydantic models
from pydantic import BaseModel, Field
from enum import Enum


class CertificateStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class CertificateCredentials(BaseModel):
    """Credenciais geradas para o certificado"""
    login: str
    password: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CertificateBase(BaseModel):
    """Modelo base do certificado"""
    license_id: str
    tenant_id: str
    
    # Número único do certificado
    certificate_number: str
    verification_code: str  # Código curto para URL
    
    # Dados do cliente (snapshot)
    client_name: str
    client_document: Optional[str] = None  # CPF/CNPJ
    
    # Dados do produto
    product_name: str
    serial_number: str
    region: str = "América do Norte"
    
    # Datas
    activation_date: datetime
    expiration_date: datetime
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Emissor
    issued_by_id: str
    issued_by_name: str
    issued_by_email: str
    
    # Credenciais
    credentials: Optional[CertificateCredentials] = None
    
    # Segurança
    hash: str  # SHA256 para validação
    qr_code_data: Optional[str] = None  # Base64 do QR Code
    
    # Status
    status: CertificateStatus = CertificateStatus.ACTIVE
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None
    
    # Configurações
    public_access: bool = True
    
    # Métricas
    download_count: int = 0
    view_count: int = 0


class Certificate(CertificateBase):
    """Certificado completo com ID"""
    id: str = Field(default_factory=lambda: f"cert_{uuid.uuid4().hex[:12]}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CertificateGenerator:
    """Gerador de certificados digitais"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    def generate_certificate_number(self) -> str:
        """Gera número único do certificado: CERT-YYYY-NNNNNN"""
        year = datetime.now().year
        unique_id = uuid.uuid4().hex[:6].upper()
        return f"CERT-{year}-{unique_id}"
    
    def generate_verification_code(self) -> str:
        """Gera código curto para URL (12 caracteres)"""
        return uuid.uuid4().hex[:12]
    
    def generate_hash(self, data: Dict[str, Any]) -> str:
        """Gera hash SHA256 para validação do certificado"""
        # Concatena dados críticos
        hash_input = f"{data['certificate_number']}:{data['serial_number']}:{data['client_name']}:{data['expiration_date']}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def generate_credentials(self, client_name: str, serial_number: str) -> CertificateCredentials:
        """Gera credenciais únicas para o certificado"""
        # Login: sgw + primeiras letras do nome + números do serial
        name_parts = client_name.lower().split()
        login_base = ''.join([p[:3] for p in name_parts[:2]])
        serial_suffix = ''.join(filter(str.isdigit, serial_number))[-4:]
        login = f"sgw{login_base}{serial_suffix}"
        
        # Senha: @Produto + Ano + Random
        year = datetime.now().year
        random_suffix = uuid.uuid4().hex[:4].upper()
        password = f"@Lic{year}{random_suffix}"
        
        return CertificateCredentials(
            login=login,
            password=password
        )
    
    def generate_qr_code(self, verification_code: str) -> str:
        """Gera QR Code em base64"""
        # URL de validação
        validation_url = f"{self.base_url}/certificado/{verification_code}"
        
        # Criar QR Code estilizado
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(validation_url)
        qr.make(fit=True)
        
        # Criar imagem com módulos arredondados
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer()
        )
        
        # Converter para base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def create_certificate(
        self,
        license_data: Dict[str, Any],
        issuer_data: Dict[str, Any],
        tenant_id: str
    ) -> Certificate:
        """Cria um novo certificado completo"""
        
        # Gerar identificadores
        certificate_number = self.generate_certificate_number()
        verification_code = self.generate_verification_code()
        
        # Preparar dados do cliente
        client_name = license_data.get('client_name') or license_data.get('name', 'Cliente')
        serial_number = license_data.get('serial_number') or license_data.get('license_key', '')
        product_name = license_data.get('product_name') or license_data.get('manufacturer', 'Produto')
        if license_data.get('model'):
            product_name = f"{product_name} {license_data['model']}"
        
        # Datas
        activation_date = license_data.get('activation_date') or datetime.now(timezone.utc)
        expiration_date = license_data.get('expires_at') or license_data.get('expiration_date')
        
        if isinstance(activation_date, str):
            activation_date = datetime.fromisoformat(activation_date.replace('Z', '+00:00'))
        if isinstance(expiration_date, str):
            expiration_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
        
        # Se não houver data de expiração, usar validade padrão de 365 dias
        if not expiration_date:
            validity_days = license_data.get('validity_days', 365)
            expiration_date = activation_date + timedelta(days=validity_days)
        
        # Gerar credenciais
        credentials = self.generate_credentials(client_name, serial_number)
        
        # Dados para hash
        hash_data = {
            'certificate_number': certificate_number,
            'serial_number': serial_number,
            'client_name': client_name,
            'expiration_date': str(expiration_date)
        }
        cert_hash = self.generate_hash(hash_data)
        
        # Gerar QR Code
        qr_code_data = self.generate_qr_code(verification_code)
        
        # Criar certificado
        certificate = Certificate(
            license_id=license_data.get('id', ''),
            tenant_id=tenant_id,
            certificate_number=certificate_number,
            verification_code=verification_code,
            client_name=client_name,
            client_document=license_data.get('client_document'),
            product_name=product_name,
            serial_number=serial_number,
            region=license_data.get('region', 'América do Norte'),
            activation_date=activation_date,
            expiration_date=expiration_date,
            issued_by_id=issuer_data.get('id', ''),
            issued_by_name=issuer_data.get('name', ''),
            issued_by_email=issuer_data.get('email', ''),
            credentials=credentials,
            hash=cert_hash,
            qr_code_data=qr_code_data
        )
        
        return certificate
    
    def get_certificate_status(self, certificate: Certificate) -> CertificateStatus:
        """Retorna o status atual do certificado"""
        if certificate.status == CertificateStatus.REVOKED:
            return CertificateStatus.REVOKED
        
        now = datetime.now(timezone.utc)
        exp_date = certificate.expiration_date
        
        # Normalizar timezone
        if exp_date.tzinfo is None:
            exp_date = exp_date.replace(tzinfo=timezone.utc)
        
        if exp_date < now:
            return CertificateStatus.EXPIRED
        
        return CertificateStatus.ACTIVE
    
    def get_days_remaining(self, certificate: Certificate) -> int:
        """Retorna dias restantes até expiração"""
        now = datetime.now(timezone.utc)
        exp_date = certificate.expiration_date
        
        if exp_date.tzinfo is None:
            exp_date = exp_date.replace(tzinfo=timezone.utc)
        
        delta = exp_date - now
        return delta.days


# Instância global (será configurada no startup)
certificate_generator: Optional[CertificateGenerator] = None


def get_certificate_generator() -> CertificateGenerator:
    """Retorna instância do gerador de certificados"""
    global certificate_generator
    if certificate_generator is None:
        base_url = os.environ.get('FRONTEND_BASE_URL', 'http://localhost:3000')
        certificate_generator = CertificateGenerator(base_url)
    return certificate_generator
