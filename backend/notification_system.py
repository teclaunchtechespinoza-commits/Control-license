# Sistema de Notificações para Alertas de Vencimento/Renovação
# Reduzir churn e aumentar receita através de alertas inteligentes

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json

class NotificationType(str, Enum):
    LICENSE_EXPIRING_30 = "license_expiring_30"    # 30 dias antes
    LICENSE_EXPIRING_7 = "license_expiring_7"     # 7 dias antes  
    LICENSE_EXPIRING_1 = "license_expiring_1"     # 1 dia antes
    LICENSE_EXPIRED = "license_expired"            # Já expirou
    RENEWAL_REMINDER = "renewal_reminder"          # Lembrete de renovação
    CUSTOM = "custom"                              # Notificação personalizada

class NotificationChannel(str, Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    SMS = "sms"        # Futuro
    WEBHOOK = "webhook" # Futuro

class NotificationStatus(str, Enum):
    PENDING = "pending"      # Aguardando envio
    SENT = "sent"           # Enviado com sucesso  
    FAILED = "failed"       # Falha no envio
    READ = "read"           # Lido pelo usuário (in-app)
    CLICKED = "clicked"     # Clicado pelo usuário
    CANCELLED = "cancelled" # Cancelado

class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="ID do tenant")
    name: str = Field(..., description="Nome do template")
    type: NotificationType = Field(..., description="Tipo de notificação")
    
    # Templates por canal
    email_subject: Optional[str] = None
    email_template: Optional[str] = None  # HTML template
    in_app_title: Optional[str] = None
    in_app_message: Optional[str] = None
    sms_template: Optional[str] = None
    
    # Configurações
    is_active: bool = True
    priority: NotificationPriority = NotificationPriority.NORMAL
    
    # Variáveis disponíveis no template
    available_variables: List[str] = Field(default_factory=lambda: [
        "{customer_name}", "{license_name}", "{expires_at}", 
        "{days_until_expiry}", "{renewal_url}", "{support_email}"
    ])
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

class NotificationConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="ID do tenant")
    
    # Configurações globais por tenant
    enabled: bool = True
    
    # Configurações por tipo
    license_expiring_30_enabled: bool = True
    license_expiring_7_enabled: bool = True
    license_expiring_1_enabled: bool = True
    license_expired_enabled: bool = True
    renewal_reminder_enabled: bool = True
    
    # Canais habilitados
    email_enabled: bool = True
    in_app_enabled: bool = True
    sms_enabled: bool = False
    webhook_enabled: bool = False
    
    # Configurações de envio
    max_notifications_per_day: int = Field(default=100, description="Limite de notificações por dia")
    retry_failed_after_hours: int = Field(default=4, description="Tentar novamente após X horas")
    max_retries: int = Field(default=3, description="Máximo de tentativas")
    
    # Horários de envio (formato HH:MM)
    send_time_start: str = Field(default="08:00", description="Início do horário de envio")
    send_time_end: str = Field(default="18:00", description="Fim do horário de envio")
    timezone: str = Field(default="America/Sao_Paulo")
    
    # Configurações de opt-out
    allow_opt_out: bool = True
    opt_out_url_template: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="ID do tenant")
    
    # Tipo e canal
    type: NotificationType = Field(..., description="Tipo de notificação")
    channel: NotificationChannel = Field(..., description="Canal de envio")
    priority: NotificationPriority = NotificationPriority.NORMAL
    
    # Destinatário
    recipient_email: Optional[str] = None
    recipient_user_id: Optional[str] = None
    recipient_name: Optional[str] = None
    
    # Conteúdo
    subject: Optional[str] = None
    title: Optional[str] = None
    message: str = Field(..., description="Conteúdo da notificação")
    html_content: Optional[str] = None
    
    # Contexto (dados da licença, cliente, etc.)
    context_data: Dict[str, Any] = Field(default_factory=dict)
    license_id: Optional[str] = None
    client_id: Optional[str] = None
    
    # Status e tracking
    status: NotificationStatus = NotificationStatus.PENDING
    scheduled_for: Optional[datetime] = None  # Quando enviar
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    
    # Tentativas e erros
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    
    # Metadados
    template_id: Optional[str] = None
    external_id: Optional[str] = None  # ID do serviço externo (SendGrid, etc.)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationQueue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="ID do tenant")
    
    notification_id: str = Field(..., description="ID da notificação")
    priority: int = Field(default=1, description="Prioridade na fila (menor = maior prioridade)")
    
    # Agendamento
    process_after: datetime = Field(default_factory=datetime.utcnow)
    
    # Status na fila
    is_processing: bool = False
    processed_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="ID do tenant")
    
    notification_id: str = Field(..., description="ID da notificação")
    action: str = Field(..., description="Ação executada (sent, failed, read, etc.)")
    
    # Detalhes
    channel: NotificationChannel
    status: NotificationStatus
    
    # Dados do evento
    event_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    
    # Tracking
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Classes para requests/responses da API
class CreateNotificationRequest(BaseModel):
    type: NotificationType
    channel: NotificationChannel
    recipient_email: Optional[str] = None
    recipient_user_id: Optional[str] = None
    subject: Optional[str] = None
    message: str
    license_id: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    priority: NotificationPriority = NotificationPriority.NORMAL

class NotificationStats(BaseModel):
    tenant_id: str
    period_start: datetime
    period_end: datetime
    
    # Contadores por status
    total_notifications: int = 0
    sent_successfully: int = 0
    failed: int = 0
    pending: int = 0
    
    # Contadores por tipo
    license_expiring_30: int = 0
    license_expiring_7: int = 0
    license_expiring_1: int = 0
    license_expired: int = 0
    
    # Contadores por canal
    email_sent: int = 0
    in_app_sent: int = 0
    
    # Métricas de engagement
    open_rate: float = 0.0      # Taxa de abertura
    click_rate: float = 0.0     # Taxa de clique
    
    # Eficiência
    avg_processing_time: float = 0.0  # Tempo médio de processamento
    success_rate: float = 0.0         # Taxa de sucesso

# Configurações padrão por tipo de notificação
DEFAULT_TEMPLATES = {
    NotificationType.LICENSE_EXPIRING_30: {
        "name": "Licença vencendo em 30 dias",
        "email_subject": "🔔 Sua licença {license_name} vence em 30 dias",
        "email_template": """
        <h2>Olá {customer_name}!</h2>
        <p>Sua licença <strong>{license_name}</strong> vencerá em <strong>30 dias</strong>.</p>
        <p><strong>Data de vencimento:</strong> {expires_at}</p>
        <p>Para continuar aproveitando nossos serviços, renove sua licença antes do vencimento.</p>
        <a href="{renewal_url}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Renovar Agora</a>
        <p>Precisa de ajuda? Entre em contato: {support_email}</p>
        """,
        "in_app_title": "Licença vencendo em 30 dias",
        "in_app_message": "Sua licença {license_name} vence em {days_until_expiry} dias. Renove agora para continuar usando."
    },
    NotificationType.LICENSE_EXPIRING_7: {
        "name": "Licença vencendo em 7 dias",
        "email_subject": "⚠️ URGENTE: Sua licença {license_name} vence em 7 dias",
        "email_template": """
        <h2>⚠️ ATENÇÃO {customer_name}!</h2>
        <p>Sua licença <strong>{license_name}</strong> vencerá em apenas <strong>7 dias</strong>.</p>
        <p><strong>Data de vencimento:</strong> {expires_at}</p>
        <p>🚨 <strong>Ação necessária:</strong> Renove sua licença para evitar interrupção do serviço.</p>
        <a href="{renewal_url}" style="background: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">RENOVAR AGORA</a>
        <p>Dúvidas? Fale conosco: {support_email}</p>
        """,
        "in_app_title": "⚠️ Licença vence em 7 dias",
        "in_app_message": "URGENTE: Sua licença {license_name} vence em {days_until_expiry} dias!"
    },
    NotificationType.LICENSE_EXPIRING_1: {
        "name": "Licença vencendo amanhã",
        "email_subject": "🚨 ÚLTIMO AVISO: Sua licença {license_name} vence AMANHÃ",
        "email_template": """
        <h2>🚨 ÚLTIMO AVISO {customer_name}!</h2>
        <p>Sua licença <strong>{license_name}</strong> vencerá <strong>AMANHÃ</strong>.</p>
        <p><strong>Data de vencimento:</strong> {expires_at}</p>
        <p>🔥 <strong>ÚLTIMA CHANCE:</strong> Renove agora para não perder o acesso!</p>
        <a href="{renewal_url}" style="background: #dc3545; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 18px;">RENOVAR IMEDIATAMENTE</a>
        <p>Suporte urgente: {support_email}</p>
        """,
        "in_app_title": "🚨 Licença vence AMANHÃ",
        "in_app_message": "ÚLTIMO AVISO: Sua licença {license_name} vence amanhã! Renove agora!"
    },
    NotificationType.LICENSE_EXPIRED: {
        "name": "Licença expirada",
        "email_subject": "❌ Sua licença {license_name} EXPIROU",
        "email_template": """
        <h2>❌ Licença Expirada - {customer_name}</h2>
        <p>Sua licença <strong>{license_name}</strong> expirou em <strong>{expires_at}</strong>.</p>
        <p>💔 Você perdeu o acesso aos nossos serviços, mas ainda pode renovar!</p>
        <p>✅ <strong>Benefícios da renovação:</strong></p>
        <ul>
            <li>Acesso imediato restaurado</li>
            <li>Todos os dados preservados</li>
            <li>Suporte prioritário</li>
        </ul>
        <a href="{renewal_url}" style="background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">RENOVAR E REATIVAR</a>
        <p>Precisa de desconto? Fale conosco: {support_email}</p>
        """,
        "in_app_title": "❌ Licença Expirada",
        "in_app_message": "Sua licença {license_name} expirou. Renove para reativar o acesso."
    }
}

def get_default_template(notification_type: NotificationType) -> dict:
    """Retorna template padrão para um tipo de notificação"""
    return DEFAULT_TEMPLATES.get(notification_type, {})

def calculate_notification_trigger_dates(expires_at: datetime) -> Dict[str, datetime]:
    """Calcula as datas de trigger para notificações de uma licença"""
    return {
        "30_days_before": expires_at - timedelta(days=30),
        "7_days_before": expires_at - timedelta(days=7),
        "1_day_before": expires_at - timedelta(days=1),
        "expiry_date": expires_at
    }

def should_send_notification(expires_at: datetime, notification_type: NotificationType) -> bool:
    """Verifica se deve enviar uma notificação com base na data de vencimento"""
    now = datetime.utcnow()
    days_until_expiry = (expires_at - now).days
    
    if notification_type == NotificationType.LICENSE_EXPIRING_30:
        return days_until_expiry == 30
    elif notification_type == NotificationType.LICENSE_EXPIRING_7:
        return days_until_expiry == 7
    elif notification_type == NotificationType.LICENSE_EXPIRING_1:
        return days_until_expiry == 1
    elif notification_type == NotificationType.LICENSE_EXPIRED:
        return days_until_expiry < 0
        
    return False

def format_template_variables(template: str, context: Dict[str, Any]) -> str:
    """Substitui variáveis no template pelos valores do contexto"""
    formatted = template
    for key, value in context.items():
        placeholder = "{" + key + "}"
        if placeholder in formatted:
            formatted = formatted.replace(placeholder, str(value))
    return formatted