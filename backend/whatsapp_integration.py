"""
WhatsApp Integration Module - Sistema simplificado de integração WhatsApp
Baseado no playbook Baileys mas adaptado para uso FastAPI puro
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import httpx
import uuid
import re
import logging

logger = logging.getLogger(__name__)

# Models para WhatsApp Integration

class WhatsAppMessage(BaseModel):
    """Modelo para mensagem WhatsApp"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phone_number: str  # Número do destinatário
    message: str  # Conteúdo da mensagem
    message_type: Literal["text", "template"] = "text"
    template_id: Optional[str] = None  # ID do template usado
    
    # Status tracking
    status: Literal["pending", "sent", "delivered", "read", "failed"] = "pending"
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Context
    campaign_id: Optional[str] = None
    alert_id: Optional[str] = None  # ID do alerta de renovação
    client_id: Optional[str] = None
    sent_by: Optional[str] = None  # ID do usuário que enviou
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WhatsAppContact(BaseModel):
    """Contato WhatsApp"""
    phone_number: str
    name: Optional[str] = None
    client_id: Optional[str] = None
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    is_active: bool = True

class WhatsAppSession(BaseModel):
    """Sessão WhatsApp (para futura implementação com Baileys)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["disconnected", "connecting", "connected", "error"] = "disconnected"
    qr_code: Optional[str] = None
    phone_number: Optional[str] = None
    last_connected: Optional[datetime] = None
    error_message: Optional[str] = None

class WhatsAppStats(BaseModel):
    """Estatísticas de WhatsApp"""
    total_messages_sent: int = 0
    messages_delivered: int = 0
    messages_read: int = 0
    messages_failed: int = 0
    delivery_rate: float = 0.0  # Taxa de entrega
    read_rate: float = 0.0  # Taxa de leitura
    active_contacts: int = 0
    last_message_sent: Optional[datetime] = None

# Service Classes

class WhatsAppService:
    """
    Serviço principal de WhatsApp
    NOTA: Por enquanto simula envio - implementação completa com Baileys será feita posteriormente
    """
    
    def __init__(self):
        self.session = WhatsAppSession()
        self.WHATSAPP_SERVICE_URL = "http://localhost:3001"  # Futuro serviço Node.js
    
    async def get_session_status(self) -> WhatsAppSession:
        """Retorna status da sessão WhatsApp"""
        return self.session
    
    async def send_message(self, phone_number: str, message: str, context: Optional[Dict] = None) -> WhatsAppMessage:
        """
        Envia mensagem WhatsApp
        Por enquanto simula o envio - implementação real virá com Node.js service
        """
        # Validar número de telefone
        phone_number = self.format_phone_number(phone_number)
        
        # Criar registro da mensagem
        whatsapp_message = WhatsAppMessage(
            phone_number=phone_number,
            message=message,
            status="pending"
        )
        
        if context:
            whatsapp_message.alert_id = context.get("alert_id")
            whatsapp_message.client_id = context.get("client_id")
            whatsapp_message.campaign_id = context.get("campaign_id")
            whatsapp_message.sent_by = context.get("sent_by")
        
        try:
            # Por enquanto, simular envio bem-sucedido
            # TODO: Implementar integração real com serviço Node.js/Baileys
            success = await self._simulate_message_send(whatsapp_message)
            
            if success:
                whatsapp_message.status = "sent"
                whatsapp_message.sent_at = datetime.utcnow()
                logger.info(f"WhatsApp message sent to {phone_number} (SIMULATED)")
            else:
                whatsapp_message.status = "failed"
                whatsapp_message.error_message = "Service unavailable - simulated failure"
                logger.error(f"Failed to send WhatsApp message to {phone_number}")
                
        except Exception as e:
            whatsapp_message.status = "failed"
            whatsapp_message.error_message = str(e)
            logger.error(f"Error sending WhatsApp message: {e}")
        
        return whatsapp_message
    
    async def send_bulk_messages(self, messages_data: List[Dict]) -> List[WhatsAppMessage]:
        """Envia múltiplas mensagens em lote"""
        results = []
        
        for data in messages_data:
            phone_number = data.get("phone_number")
            message = data.get("message")
            context = data.get("context", {})
            
            if phone_number and message:
                result = await self.send_message(phone_number, message, context)
                results.append(result)
                
                # Pequeno delay para evitar spam
                await asyncio.sleep(0.5)
        
        return results
    
    async def get_message_status(self, message_id: str) -> Optional[str]:
        """Verifica status de uma mensagem específica"""
        # TODO: Implementar verificação real de status
        return "delivered"
    
    def format_phone_number(self, phone: str) -> str:
        """Formatar número de telefone para WhatsApp"""
        # Remover caracteres não numéricos
        phone = re.sub(r'[^0-9]', '', phone)
        
        # Adicionar código do país se não tiver
        if len(phone) == 11 and phone.startswith('11'):  # Brasil
            phone = '55' + phone
        elif len(phone) == 10:  # Número sem 9 adicional
            phone = '5511' + phone
        elif not phone.startswith('55'):
            phone = '55' + phone
            
        return phone
    
    async def _simulate_message_send(self, message: WhatsAppMessage) -> bool:
        """
        Simula envio de mensagem
        Remove esta função quando implementar integração real
        """
        import asyncio
        import random
        
        # Simular delay de envio
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Simular 95% de taxa de sucesso
        return random.random() < 0.95
    
    async def try_real_service_connection(self) -> bool:
        """
        Tenta conectar com serviço real de WhatsApp (Node.js)
        Retorna True se conectou, False se está usando simulação
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.WHATSAPP_SERVICE_URL}/status", timeout=2.0)
                if response.status_code == 200:
                    data = response.json()
                    self.session.status = "connected" if data.get("connected") else "disconnected"
                    return data.get("connected", False)
        except:
            pass
        
        # Se não conseguir conectar, manter em modo simulação
        self.session.status = "disconnected"
        return False

class WhatsAppTemplateService:
    """Serviço para gerenciamento de templates de mensagem"""
    
    def __init__(self):
        self.templates = {}
    
    def render_template(self, template: str, variables: Dict[str, str]) -> str:
        """Renderiza template com variáveis"""
        message = template
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            message = message.replace(placeholder, str(value))
        
        return message
    
    def create_renewal_message(self, 
                             client_name: str,
                             license_name: str, 
                             days_to_expire: int,
                             alert_type: str,
                             **kwargs) -> str:
        """Cria mensagem de renovação baseada no tipo de alerta"""
        
        base_variables = {
            "client_name": client_name,
            "license_name": license_name,
            "days_to_expire": str(days_to_expire),
            "expiry_date": kwargs.get("expiry_date", "em breve"),
            "company_name": kwargs.get("company_name", "Sua Empresa"),
            "salesperson_name": kwargs.get("salesperson_name", "Equipe de Vendas"),
            "support_phone": kwargs.get("support_phone", "(11) 9999-9999"),
        }
        
        if alert_type == "T-30":
            template = """Olá {client_name}! 👋

Esperamos que esteja tudo bem! 

Queremos lembrá-lo que sua licença do {license_name} vence em {days_to_expire} dias.

Para garantir a continuidade dos seus serviços sem interrupções, que tal renovarmos hoje mesmo?

✅ Sem interrupção de serviços
✅ Preço especial para renovação antecipada  
✅ Suporte técnico garantido

Posso ajudar com a renovação agora mesmo!

{salesperson_name}
{company_name}"""
            
        elif alert_type == "T-7":
            template = """🚨 URGENTE - {client_name}!

Sua licença do {license_name} vence em apenas {days_to_expire} dias!

⚠️ ATENÇÃO: Após o vencimento, seus sistemas podem parar de funcionar.

OFERTA ESPECIAL para renovação imediata:
💰 15% de desconto
🎁 +30 dias grátis de suporte

👆 Responda AGORA para garantir seu desconto!

{salesperson_name} - {company_name}"""
            
        elif alert_type == "T-1":
            template = """🔴 CRÍTICO - {client_name}!

SUA LICENÇA VENCE HOJE!

{license_name} expira em menos de 24h.

🚨 SEUS SISTEMAS VÃO PARAR DE FUNCIONAR!

LIGUE AGORA: {support_phone}

Posso renovar em 5 minutos via PIX!

NÃO PERCA TEMPO - RESPONDA AGORA!

{salesperson_name} - SUPORTE EMERGENCIAL"""
            
        elif alert_type == "EXPIRED":
            days_expired = abs(days_to_expire)
            base_variables["days_expired"] = str(days_expired)
            template = """❌ {client_name}, sua licença VENCEU!

O {license_name} expirou há {days_expired} dias.

CONSEQUÊNCIAS ATUAIS:
🚫 Sistemas bloqueados
🚫 Suporte suspenso

REATIVE AGORA com desconto especial:
💰 20% OFF para reativação
🔄 Reativação imediata

LIGUE URGENTE: {support_phone}

{salesperson_name} - REATIVAÇÃO"""
        
        else:
            template = """Olá {client_name}! Sua licença {license_name} precisa de atenção. Entre em contato conosco: {support_phone}"""
        
        return self.render_template(template, base_variables)

# Global instances
whatsapp_service = WhatsAppService()
template_service = WhatsAppTemplateService()

# Funções auxiliares para uso nos endpoints

async def send_renewal_whatsapp(client_data: Dict, license_data: Dict, alert_type: str, salesperson: str = None) -> WhatsAppMessage:
    """Envia mensagem de renovação via WhatsApp"""
    
    phone = None
    # Tentar diferentes campos de telefone
    for field in ['whatsapp', 'celular', 'telefone']:
        if client_data.get(field):
            phone = client_data[field]
            break
    
    if not phone:
        raise ValueError("Cliente não possui número de WhatsApp/telefone cadastrado")
    
    # Preparar dados para o template
    client_name = client_data.get('nome_completo') or client_data.get('razao_social', 'Cliente')
    license_name = license_data.get('name', 'sua licença')
    
    expires_at = license_data.get('expires_at')
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    
    days_to_expire = (expires_at - datetime.utcnow()).days if expires_at else 0
    
    # Gerar mensagem
    message = template_service.create_renewal_message(
        client_name=client_name,
        license_name=license_name,
        days_to_expire=days_to_expire,
        alert_type=alert_type,
        salesperson_name=salesperson or "Equipe de Vendas",
        company_name="Sua Empresa de Licenças",
        support_phone="(11) 9999-9999"
    )
    
    # Contexto para rastreamento
    context = {
        "client_id": client_data.get('id'),
        "alert_id": f"alert_{uuid.uuid4()}",
        "sent_by": salesperson
    }
    
    # Enviar mensagem
    return await whatsapp_service.send_message(phone, message, context)

import asyncio