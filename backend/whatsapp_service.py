"""
WhatsApp Service Integration for FastAPI
Conecta com o serviço Node.js para funcionalidades WhatsApp
"""

import httpx
import asyncio
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import os

# Import from server.py instead of separate modules
from server import get_current_user, User, maintenance_logger, db, add_tenant_filter

# Redis para idempotência e rate limiting
try:
    import redis.asyncio as redis
    redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
except ImportError:
    redis_client = None
    logger.warning("Redis não disponível - idempotência e rate limiting desabilitados")

logger = logging.getLogger(__name__)

# Configuration
WHATSAPP_SERVICE_URL = os.getenv("WHATSAPP_SERVICE_URL", "http://localhost:3001")
WHATSAPP_REQUEST_TIMEOUT = 30.0

# Pydantic Models
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

class WhatsAppWebhookData(BaseModel):
    event: str
    data: Dict[str, Any]
    timestamp: str

# Router
whatsapp_router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# Constantes para categorização de erros
ERROR_TYPES = {
    "LICENSE_EXPIRED": "Licença expirada - renovação necessária",
    "RATE_LIMIT": "Limite de envio excedido - tente novamente mais tarde", 
    "DUPLICATE": "Mensagem duplicada ignorada",
    "PHONE_INVALID": "Número de telefone inválido",
    "SERVICE_ERROR": "Erro no serviço WhatsApp",
    "CLIENT_NOT_FOUND": "Cliente não encontrado",
    "TIMEOUT": "Timeout na comunicação com WhatsApp"
}

class WhatsAppService:
    """Service class para integração com Node.js WhatsApp service"""
    
    def __init__(self):
        self.service_url = WHATSAPP_SERVICE_URL
        self.client = None
    
    async def get_client(self) -> httpx.AsyncClient:
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(timeout=WHATSAPP_REQUEST_TIMEOUT)
        return self.client
    
    async def check_service_health(self) -> bool:
        """Verifica se o serviço WhatsApp está funcionando"""
        try:
            client = await self.get_client()
            response = await client.get(f"{self.service_url}/health")
            return response.status_code == 200
        except:
            return False
    
    async def get_status(self) -> WhatsAppStatus:
        """Obtém status da conexão WhatsApp"""
        try:
            client = await self.get_client()
            response = await client.get(f"{self.service_url}/status")
            
            if response.status_code == 200:
                data = response.json()
                return WhatsAppStatus(**data)
            else:
                raise HTTPException(status_code=response.status_code, detail="WhatsApp service error")
                
        except httpx.TimeoutException:
            raise HTTPException(status_code=503, detail="WhatsApp service timeout")
        except Exception as e:
            logger.error(f"Error getting WhatsApp status: {e}")
            raise HTTPException(status_code=503, detail="WhatsApp service unavailable")
    
    async def get_qr_code(self) -> WhatsAppQRResponse:
        """Obtém QR code para conexão"""
        try:
            client = await self.get_client()
            response = await client.get(f"{self.service_url}/qr")
            
            if response.status_code == 200:
                data = response.json()
                return WhatsAppQRResponse(**data)
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to get QR code")
                
        except httpx.TimeoutException:
            raise HTTPException(status_code=503, detail="WhatsApp service timeout")
        except Exception as e:
            logger.error(f"Error getting QR code: {e}")
            raise HTTPException(status_code=503, detail="WhatsApp service unavailable")
    
    async def send_message(self, phone_number: str, message: str, message_id: str = None, context: Dict = None) -> WhatsAppSendResponse:
        """Envia mensagem WhatsApp"""
        try:
            client = await self.get_client()
            payload = {
                "phone_number": phone_number,
                "message": message,
                "message_id": message_id,
                "context": context or {}
            }
            
            response = await client.post(f"{self.service_url}/send", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return WhatsAppSendResponse(
                    success=data.get("success", False),
                    message_id=data.get("message_id"),
                    phone_number=phone_number,
                    error=data.get("error"),
                    timestamp=datetime.utcnow()
                )
            else:
                error_data = response.json() if response.content else {}
                return WhatsAppSendResponse(
                    success=False,
                    phone_number=phone_number,
                    error=error_data.get("error", "Unknown error"),
                    timestamp=datetime.utcnow()
                )
                
        except httpx.TimeoutException:
            return WhatsAppSendResponse(
                success=False,
                phone_number=phone_number,
                error="WhatsApp service timeout",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return WhatsAppSendResponse(
                success=False,
                phone_number=phone_number,
                error=str(e),
                timestamp=datetime.utcnow()
            )
    
    async def send_bulk_messages(self, messages: List[Dict], tenant_id: str = "default") -> Dict[str, Any]:
        """Envia mensagens em lote com idempotência, rate limiting e validação de licenças"""
        results = {"total": len(messages), "sent": 0, "failed": 0, "errors": []}

        for msg in messages:
            phone_number = msg.get("phone_number")
            message_text = msg.get("message")
            message_id = msg.get("message_id") or f"bulk_{uuid.uuid4()}"
            client_id = msg.get("client_id")

            try:
                # 1. Validar se cliente existe e tem licença válida
                if client_id:
                    license_valid = await self._check_license_validity(client_id, tenant_id)
                    if not license_valid:
                        results["failed"] += 1
                        results["errors"].append({
                            "phone_number": phone_number,
                            "message_id": message_id,
                            "error": ERROR_TYPES["LICENSE_EXPIRED"],
                            "error_type": "LICENSE_EXPIRED"
                        })
                        continue

                # 2. Verificar idempotência
                if redis_client and not await self._check_idempotency(message_id):
                    results["failed"] += 1
                    results["errors"].append({
                        "phone_number": phone_number,
                        "message_id": message_id,
                        "error": ERROR_TYPES["DUPLICATE"],
                        "error_type": "DUPLICATE"
                    })
                    continue

                # 3. Verificar rate limit por tenant
                if redis_client and not await self._check_rate_limit(tenant_id):
                    results["failed"] += 1
                    results["errors"].append({
                        "phone_number": phone_number,
                        "message_id": message_id,
                        "error": ERROR_TYPES["RATE_LIMIT"],
                        "error_type": "RATE_LIMIT"
                    })
                    continue

                # 4. Tentar enviar mensagem
                client = await self.get_client()
                payload = {
                    "phone_number": phone_number,
                    "message": message_text,
                    "message_id": message_id,
                    "context": msg.get("context", {}),
                    "tenant_id": tenant_id
                }
                
                response = await client.post(f"{self.service_url}/send", json=payload)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success", False):
                        results["sent"] += 1
                        # Marcar como enviada no Redis para idempotência
                        if redis_client:
                            await self._mark_as_sent(message_id)
                    else:
                        results["failed"] += 1
                        results["errors"].append({
                            "phone_number": phone_number,
                            "message_id": message_id,
                            "error": data.get("error", "Falha desconhecida"),
                            "error_type": "SERVICE_ERROR"
                        })
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "phone_number": phone_number,
                        "message_id": message_id,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "error_type": "SERVICE_ERROR"
                    })

            except httpx.TimeoutException:
                results["failed"] += 1
                results["errors"].append({
                    "phone_number": phone_number,
                    "message_id": message_id,
                    "error": ERROR_TYPES["TIMEOUT"],
                    "error_type": "TIMEOUT"
                })
            except Exception as e:
                logger.error(f"Erro no envio em lote para {phone_number}: {e}")
                results["failed"] += 1
                results["errors"].append({
                    "phone_number": phone_number,
                    "message_id": message_id,
                    "error": str(e),
                    "error_type": "SERVICE_ERROR"
                })

        return results

    async def _check_license_validity(self, client_id: str, tenant_id: str) -> bool:
        """Verifica se cliente tem licença válida (não expirada)"""
        try:
            # Verificar licenças para cliente PF
            query_filter_pf = add_tenant_filter({
                "client_pf_id": client_id,
                "expires_at": {"$gte": datetime.now(timezone.utc)}
            }, tenant_id)
            
            license_pf = await db.licenses.find_one(query_filter_pf)
            if license_pf:
                return True
            
            # Verificar licenças para cliente PJ
            query_filter_pj = add_tenant_filter({
                "client_pj_id": client_id,
                "expires_at": {"$gte": datetime.now(timezone.utc)}
            }, tenant_id)
            
            license_pj = await db.licenses.find_one(query_filter_pj)
            return license_pj is not None
            
        except Exception as e:
            logger.error(f"Erro ao verificar validade da licença para cliente {client_id}: {e}")
            return False
    
    async def _check_idempotency(self, message_id: str) -> bool:
        """Verifica se mensagem já foi processada (idempotência)"""
        try:
            key = f"whatsapp:sent:{message_id}"
            exists = await redis_client.exists(key)
            return not exists  # True se não existe (pode processar)
        except Exception as e:
            logger.error(f"Erro ao verificar idempotência para {message_id}: {e}")
            return True  # Em caso de erro, permite o envio
    
    async def _mark_as_sent(self, message_id: str) -> None:
        """Marca mensagem como enviada para idempotência"""
        try:
            key = f"whatsapp:sent:{message_id}"
            await redis_client.setex(key, 3600, "1")  # TTL de 1 hora
        except Exception as e:
            logger.error(f"Erro ao marcar mensagem {message_id} como enviada: {e}")
    
    async def _check_rate_limit(self, tenant_id: str) -> bool:
        """Verifica rate limit por tenant (30 mensagens/minuto)"""
        try:
            key = f"whatsapp:rate_limit:{tenant_id}"
            current = await redis_client.get(key)
            
            if current is None:
                # Primeira mensagem no minuto
                await redis_client.setex(key, 60, "1")  # TTL de 1 minuto
                return True
            elif int(current) < 30:  # Limite de 30 msgs/minuto
                await redis_client.incr(key)
                return True
            else:
                return False  # Rate limit excedido
                
        except Exception as e:
            logger.error(f"Erro ao verificar rate limit para tenant {tenant_id}: {e}")
            return True  # Em caso de erro, permite o envio
    
    async def restart_connection(self) -> bool:
        """Reinicia conexão WhatsApp"""
        try:
            client = await self.get_client()
            response = await client.post(f"{self.service_url}/restart")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error restarting WhatsApp connection: {e}")
            return False

# Global service instance
whatsapp_service = WhatsAppService()

# API Endpoints
@whatsapp_router.get("/health")
async def whatsapp_health_check():
    """Health check do serviço WhatsApp"""
    is_healthy = await whatsapp_service.check_service_health()
    
    return {
        "service": "WhatsApp Integration",
        "healthy": is_healthy,
        "service_url": WHATSAPP_SERVICE_URL,
        "timestamp": datetime.utcnow().isoformat()
    }

@whatsapp_router.get("/status", response_model=WhatsAppStatus)
async def get_whatsapp_status(current_user: User = Depends(get_current_user)):
    """Obtém status da conexão WhatsApp"""
    status = await whatsapp_service.get_status()
    
    # Log da consulta
    maintenance_logger.log("whatsapp_status_check", {
        "user_id": current_user.id,
        "connected": status.connected,
        "status": status.status
    })
    
    return status

@whatsapp_router.get("/qr", response_model=WhatsAppQRResponse)
async def get_whatsapp_qr(current_user: User = Depends(get_current_user)):
    """Obtém QR code para conectar WhatsApp"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only admin can access QR code")
    
    qr_response = await whatsapp_service.get_qr_code()
    
    # Log da consulta
    maintenance_logger.log("whatsapp_qr_request", {
        "user_id": current_user.id,
        "has_qr": bool(qr_response.qr),
        "status": qr_response.status
    })
    
    return qr_response

@whatsapp_router.post("/send", response_model=WhatsAppSendResponse)
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
    
    result = await whatsapp_service.send_message(
        phone_number=request.phone_number,
        message=request.message,
        message_id=request.message_id,
        context=request.context
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

@whatsapp_router.post("/send-bulk")
async def send_bulk_whatsapp(
    request: WhatsAppBulkSendRequest,
    current_user: User = Depends(get_current_user)
):
    """Envia mensagens WhatsApp em lote com idempotência, rate limiting e validação de licenças"""
    
    # Log da tentativa
    maintenance_logger.log("whatsapp_bulk_send_attempt", {
        "user_id": current_user.id,
        "tenant_id": current_user.tenant_id,
        "message_count": len(request.messages),
        "phone_numbers": [msg.get("phone_number") for msg in request.messages]
    })
    
    # Usar tenant_id do usuário atual
    result = await whatsapp_service.send_bulk_messages(
        request.messages,
        tenant_id=current_user.tenant_id
    )
    
    # Log do resultado detalhado
    maintenance_logger.log("whatsapp_bulk_send_result", {
        "user_id": current_user.id,
        "tenant_id": current_user.tenant_id,
        "total": result.get("total", 0),
        "sent": result.get("sent", 0),
        "failed": result.get("failed", 0),
        "error_types": [error.get("error_type") for error in result.get("errors", [])]
    })
    
    return result

@whatsapp_router.post("/restart")
async def restart_whatsapp_connection(current_user: User = Depends(get_current_user)):
    """Reinicia conexão WhatsApp"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only admin can restart WhatsApp connection")
    
    success = await whatsapp_service.restart_connection()
    
    # Log da operação
    maintenance_logger.log("whatsapp_restart", {
        "user_id": current_user.id,
        "success": success
    })
    
    if success:
        return {"message": "WhatsApp connection restart initiated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to restart WhatsApp connection")

@whatsapp_router.post("/webhook")
async def whatsapp_webhook(webhook_data: WhatsAppWebhookData):
    """Webhook para receber eventos do serviço Node.js"""
    
    # Log do evento
    maintenance_logger.log(f"whatsapp_webhook_{webhook_data.event}", {
        "event": webhook_data.event,
        "data": webhook_data.data,
        "timestamp": webhook_data.timestamp
    })
    
    # Aqui podemos processar diferentes tipos de eventos
    # Por exemplo: message_sent, message_delivered, message_failed, etc.
    
    return {"status": "received"}

# Integration helpers - para usar nos outros módulos
async def send_renewal_whatsapp_message(client_data: Dict, license_data: Dict, alert_type: str, salesperson: str = None):
    """
    Função helper para enviar mensagens de renovação via WhatsApp
    Integração com o sistema de vendas
    """
    from whatsapp_integration import template_service
    
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
    
    message = template_service.create_renewal_message(
        client_name=client_name,
        license_name=license_name,
        days_to_expire=days_to_expire,
        alert_type=alert_type,
        salesperson_name=salesperson or "Equipe de Vendas",
        company_name="Sua Empresa de Licenças",
        support_phone="(11) 9999-9999"
    )
    
    # Enviar mensagem
    result = await whatsapp_service.send_message(
        phone_number=phone_number,
        message=message,
        message_id=f"renewal_{client_data.get('id')}_{alert_type}",
        context={
            "client_id": client_data.get('id'),
            "license_id": license_data.get('id'),
            "alert_type": alert_type,
            "salesperson": salesperson
        }
    )
    
    return result