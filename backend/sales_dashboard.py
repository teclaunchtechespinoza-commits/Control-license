"""
Dashboard de Vendas - Módulo de análise de vendas e licenças com WhatsApp
Transforma alertas técnicos em ferramenta de vendas imediata
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timedelta, date
from enum import Enum
import uuid

# Modelos para Dashboard de Vendas

class ExpirationAlert(BaseModel):
    """Alerta de expiração de licença para vendas"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str  # ID do cliente (PF ou PJ)
    client_type: Literal["pf", "pj"]  # Tipo do cliente
    client_name: str  # Nome do cliente
    license_id: str  # ID da licença
    license_name: str  # Nome da licença
    expires_at: datetime  # Data de expiração
    days_to_expire: int  # Dias restantes
    alert_type: Literal["T-30", "T-7", "T-1", "EXPIRED"]  # Tipo do alerta
    status: Literal["pending", "contacted", "renewed", "lost"] = "pending"  # Status da oportunidade
    priority: Literal["high", "medium", "low"] = "medium"  # Prioridade
    
    # Dados do cliente para vendas
    contact_phone: Optional[str] = None
    contact_whatsapp: Optional[str] = None
    contact_email: Optional[str] = None
    contact_preference: Optional[str] = None
    
    # Histórico de contatos
    last_contact_date: Optional[datetime] = None
    last_contact_method: Optional[str] = None  # "whatsapp", "phone", "email"
    contact_attempts: int = 0
    
    # Dados de vendas
    current_plan_value: Optional[float] = None
    renewal_opportunity_value: Optional[float] = None
    assigned_salesperson: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SalesMetrics(BaseModel):
    """Métricas de vendas do dashboard"""
    # Contadores principais
    total_expiring_licenses: int = 0
    licenses_expiring_30_days: int = 0
    licenses_expiring_7_days: int = 0
    licenses_expiring_1_day: int = 0
    expired_licenses: int = 0
    
    # Taxa de conversão
    contacted_leads: int = 0
    renewed_licenses: int = 0
    lost_opportunities: int = 0
    conversion_rate: float = 0.0  # Percentual de renovação
    
    # Valores financeiros
    potential_revenue: float = 0.0  # Receita potencial de renovações
    confirmed_revenue: float = 0.0  # Receita confirmada (renovado)
    lost_revenue: float = 0.0  # Receita perdida
    
    # Por canal
    whatsapp_contacts: int = 0
    phone_contacts: int = 0
    email_contacts: int = 0
    
    # Por vendedor
    sales_by_person: Dict[str, Dict[str, Any]] = {}
    
    # Período de análise
    period_start: date
    period_end: date

class SalesDashboardSummary(BaseModel):
    """Resumo executivo do dashboard de vendas"""
    metrics: SalesMetrics
    priority_alerts: List[ExpirationAlert]  # Top alertas por prioridade
    recent_activities: List[Dict[str, Any]]  # Atividades recentes
    top_opportunities: List[Dict[str, Any]]  # Maiores oportunidades por valor

class WhatsAppMessageTemplate(BaseModel):
    """Template de mensagem WhatsApp para diferentes cenários"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Nome do template
    scenario: Literal["T-30", "T-7", "T-1", "EXPIRED", "FOLLOW_UP"]  # Cenário de uso
    message_template: str  # Template da mensagem com variáveis
    variables: List[str] = []  # Variáveis disponíveis
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class WhatsAppCampaign(BaseModel):
    """Campanha de WhatsApp para renovação de licenças"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Nome da campanha
    template_id: str  # ID do template usado
    target_alerts: List[str] = []  # IDs dos alertas alvo
    scheduled_date: datetime  # Data agendada para envio
    status: Literal["scheduled", "running", "completed", "cancelled"] = "scheduled"
    
    # Resultados
    messages_sent: int = 0
    messages_delivered: int = 0
    messages_read: int = 0
    responses_received: int = 0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # ID do usuário que criou

class SalesContact(BaseModel):
    """Registro de contato de vendas"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_id: str  # ID do alerta relacionado
    contact_method: Literal["whatsapp", "phone", "email", "in_person"]
    contact_date: datetime = Field(default_factory=datetime.utcnow)
    contacted_by: str  # ID do vendedor
    
    # Detalhes do contato
    notes: Optional[str] = None
    outcome: Literal["no_answer", "answered", "interested", "not_interested", "callback_requested"] = "no_answer"
    next_action: Optional[str] = None
    next_contact_date: Optional[datetime] = None
    
    # Para WhatsApp
    whatsapp_message_id: Optional[str] = None
    message_template_used: Optional[str] = None

# Funções auxiliares para cálculo de métricas

def calculate_days_to_expire(expires_at: datetime) -> int:
    """Calcula dias restantes para expiração"""
    now = datetime.utcnow()
    delta = expires_at - now
    return max(0, delta.days)

def get_alert_type(days_to_expire: int) -> str:
    """Determina o tipo de alerta baseado nos dias restantes"""
    if days_to_expire <= 0:
        return "EXPIRED"
    elif days_to_expire <= 1:
        return "T-1"
    elif days_to_expire <= 7:
        return "T-7"
    elif days_to_expire <= 30:
        return "T-30"
    else:
        return "FUTURE"

def get_alert_priority(alert_type: str, client_value: float = 0) -> str:
    """Determina a prioridade do alerta"""
    if alert_type == "EXPIRED":
        return "high"
    elif alert_type == "T-1":
        return "high"
    elif alert_type == "T-7":
        return "high" if client_value > 1000 else "medium"
    elif alert_type == "T-30":
        return "medium" if client_value > 500 else "low"
    else:
        return "low"

# Templates padrão de mensagens WhatsApp
DEFAULT_WHATSAPP_TEMPLATES = [
    {
        "name": "Renovação 30 dias",
        "scenario": "T-30",
        "message_template": """Olá {client_name}! 👋

Esperamos que esteja tudo bem! 

Queremos lembrá-lo que sua licença do {license_name} vence em {days_to_expire} dias ({expiry_date}).

Para garantir a continuidade dos seus serviços sem interrupções, que tal renovarmos hoje mesmo?

✅ Sem interrupção de serviços
✅ Preço especial para renovação antecipada
✅ Suporte técnico garantido

Posso ajudar com a renovação agora mesmo! 

Responda aqui ou me ligue: {support_phone}

{salesperson_name}
{company_name}""",
        "variables": ["client_name", "license_name", "days_to_expire", "expiry_date", "support_phone", "salesperson_name", "company_name"]
    },
    {
        "name": "Renovação 7 dias - URGENTE",
        "scenario": "T-7",
        "message_template": """🚨 URGENTE - {client_name}! 

Sua licença do {license_name} vence em apenas {days_to_expire} dias!

⚠️ ATENÇÃO: Após o vencimento, seus sistemas podem parar de funcionar.

OFERTA ESPECIAL para renovação imediata:
💰 {discount_percentage}% de desconto
🎁 +30 dias grátis de suporte

👆 Responda AGORA para garantir seu desconto!

Ou me ligue urgente: {support_phone}

{salesperson_name} - {company_name}""",
        "variables": ["client_name", "license_name", "days_to_expire", "discount_percentage", "support_phone", "salesperson_name", "company_name"]
    },
    {
        "name": "Renovação 1 dia - CRÍTICO",
        "scenario": "T-1",
        "message_template": """🔴 CRÍTICO - {client_name}!

SUA LICENÇA VENCE HOJE!

{license_name} expira em menos de 24h.

🚨 SEUS SISTEMAS VÃO PARAR DE FUNCIONAR!

LIGUE AGORA: {emergency_phone}
WhatsApp: {support_whatsapp}

Posso renovar em 5 minutos via:
💳 Cartão de crédito
🏦 PIX instantâneo

NÃO PERCA TEMPO - RESPONDA AGORA!

{salesperson_name} - SUPORTE EMERGENCIAL
{company_name}""",
        "variables": ["client_name", "license_name", "emergency_phone", "support_whatsapp", "salesperson_name", "company_name"]
    },
    {
        "name": "Licença Vencida - REATIVAÇÃO",
        "scenario": "EXPIRED",
        "message_template": """❌ {client_name}, sua licença VENCEU!

O {license_name} expirou há {days_expired} dias.

CONSEQUÊNCIAS ATUAIS:
🚫 Sistemas bloqueados
🚫 Suporte suspenso  
🚫 Atualizações paradas

REATIVE AGORA com desconto especial:
💰 {reactivation_discount}% OFF
🔄 Reativação imediata
✅ Suporte prioritário

LIGUE URGENTE: {emergency_phone}

{salesperson_name} - REATIVAÇÃO
{company_name}""",
        "variables": ["client_name", "license_name", "days_expired", "reactivation_discount", "emergency_phone", "salesperson_name", "company_name"]
    }
]