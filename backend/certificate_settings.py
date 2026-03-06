"""
Certificate Settings System - License Manager v1.5.0
Sistema de configurações de certificados por tenant
Permite personalizar logo, termos e screenshots do procedimento
"""
import os
import uuid
import base64
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ProcedureStep(BaseModel):
    """Passo do procedimento com screenshot opcional"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    order: int
    title: str
    description: str
    screenshot_base64: Optional[str] = None  # Imagem em base64
    screenshot_filename: Optional[str] = None


class CertificateTerms(BaseModel):
    """Termos de compromisso editáveis"""
    introduction: str = "Este termo estabelece as condições de uso da licença de acesso ao sistema."
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None


class CertificateSettings(BaseModel):
    """Configurações de certificado por tenant"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    
    # Logo customizado
    logo_base64: Optional[str] = None
    logo_filename: Optional[str] = None
    logo_width: int = 150  # Largura em pixels
    company_name: str = "LICENSE MANAGER"
    company_subtitle: Optional[str] = None
    
    # Cores do tema
    primary_color: str = "#22c55e"  # Verde
    secondary_color: str = "#3b82f6"  # Azul
    background_color: str = "#0a0a0a"  # Preto
    
    # Termos de compromisso
    terms: CertificateTerms = Field(default_factory=CertificateTerms)
    
    # Procedimento (screenshots editáveis)
    procedure_title: str = "PROCEDIMENTO DE ATIVAÇÃO"
    procedure_subtitle: str = "Siga os passos abaixo para ativar seu acesso"
    prerequisites: List[str] = Field(default_factory=lambda: [
        "Equipamento compatível com número de série válido",
        "Conexão com a internet estável",
        "Credenciais de acesso (fornecidas neste certificado)"
    ])
    procedure_steps: List[ProcedureStep] = Field(default_factory=list)
    
    # Informações importantes (página 2)
    important_info: List[str] = Field(default_factory=lambda: [
        "Mantenha este certificado em seus arquivos, ele pode ser solicitado para comprovar a ativação.",
        "Consulte nossa documentação ou suporte técnico em caso de dúvidas.",
        "O acesso é de uso exclusivo e intransferível.",
        "Mantenha seu equipamento atualizado para melhor funcionamento."
    ])
    
    # Metadados
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    

def get_default_terms() -> CertificateTerms:
    """Retorna termos padrão em português"""
    return CertificateTerms(
        introduction="Este termo estabelece as condições de uso da licença de acesso ao sistema.",
        sections=[
            {
                "number": 1,
                "title": "O que você está contratando",
                "content": "Este serviço oferece acesso temporário ao sistema através de uma licença vinculada ao seu equipamento. A licença é válida pelo período especificado no certificado.",
                "items": [
                    "Fornecer acesso estável e seguro ao sistema",
                    "Suporte técnico durante o período de validade",
                    "Atualizações de segurança quando necessário"
                ]
            },
            {
                "number": 2,
                "title": "Sobre o uso da licença",
                "content": "A licença está vinculada ao número de série do seu equipamento. Não é permitida a transferência para outros equipamentos sem autorização prévia.",
                "items": []
            },
            {
                "number": 3,
                "title": "Como funciona a ativação",
                "content": "A ativação é realizada pelo cliente com suporte da equipe técnica quando necessário. As credenciais fornecidas neste certificado são de uso pessoal e intransferível.",
                "items": []
            },
            {
                "number": 4,
                "title": "O que está incluso",
                "content": "",
                "items": [
                    "✓ Licença de acesso pelo período contratado",
                    "✓ Credenciais únicas de acesso",
                    "✓ Certificado digital com validação online",
                    "✓ Suporte técnico por e-mail"
                ]
            },
            {
                "number": 5,
                "title": "Garantias e Reembolsos",
                "content": "Em caso de problemas técnicos comprovadamente causados pelo sistema, a equipe técnica trabalhará para resolver a situação. Reembolsos são avaliados caso a caso, conforme política vigente.",
                "items": []
            },
            {
                "number": 6,
                "title": "Compromisso",
                "content": "Nosso compromisso é oferecer suporte e soluções justas, sempre dentro dos limites técnicos e contratuais do serviço.",
                "items": []
            }
        ]
    )


def get_default_procedure_steps() -> List[ProcedureStep]:
    """Retorna passos padrão do procedimento"""
    return [
        ProcedureStep(
            order=1,
            title="Conectar equipamento",
            description="Conecte seu equipamento ao veículo pela porta de diagnóstico e ligue a ignição.",
            screenshot_base64=None
        ),
        ProcedureStep(
            order=2,
            title="Selecionar diagnóstico",
            description="Na tela inicial, selecione a opção 'Diagnóstico' para iniciar.",
            screenshot_base64=None
        ),
        ProcedureStep(
            order=3,
            title="Aguardar detecção",
            description="Aguarde o equipamento detectar o veículo automaticamente.",
            screenshot_base64=None
        ),
        ProcedureStep(
            order=4,
            title="Selecionar região",
            description="Quando solicitado, selecione a região conforme especificado no certificado.",
            screenshot_base64=None
        ),
        ProcedureStep(
            order=5,
            title="Inserir credenciais",
            description="Digite o LOGIN e SENHA fornecidos neste certificado. Marque 'Lembrar-me' para facilitar acessos futuros.",
            screenshot_base64=None
        ),
        ProcedureStep(
            order=6,
            title="Confirmação",
            description="Aguarde a mensagem de confirmação de desbloqueio. Clique OK para continuar com o diagnóstico completo.",
            screenshot_base64=None
        )
    ]


def create_default_settings(tenant_id: str, company_name: str = "LICENSE MANAGER") -> CertificateSettings:
    """Cria configurações padrão para um tenant"""
    return CertificateSettings(
        tenant_id=tenant_id,
        company_name=company_name,
        terms=get_default_terms(),
        procedure_steps=get_default_procedure_steps()
    )
