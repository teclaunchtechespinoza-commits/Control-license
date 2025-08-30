# Jobs em Background para Sistema de Notificações
# Processamento automatizado de alertas de vencimento/renovação

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import os

from notification_system import (
    Notification, NotificationConfig, NotificationQueue, NotificationLog,
    NotificationType, NotificationChannel, NotificationStatus,
    should_send_notification, format_template_variables,
    get_default_template, calculate_notification_trigger_dates
)

# Import maintenance logger from parent directory
import sys
sys.path.insert(0, '/app')
from maintenance_logger import MaintenanceLogger

# Import tenant security functions  
sys.path.insert(0, '/app/backend')
from deps import add_tenant_filter, add_tenant_to_document

# Initialize maintenance logger
maintenance_logger = MaintenanceLogger()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationJobProcessor:
    """
    Processador de jobs de notificação com isolamento de tenant
    CRÍTICO: Deve processar apenas notificações do tenant correto
    """
    def __init__(self, db_client, tenant_id: str = None):
        self.tenant_id = tenant_id or "default"  # Tenant context for notifications
        self.db = db_client
        self.is_running = False
        self.worker_id = f"worker-{self.tenant_id}-{datetime.utcnow().strftime('%H%M%S')}"
    
    async def start_processing(self):
        """Iniciar processamento de jobs em background"""
        self.is_running = True
        logger.info(f"Starting notification job processor: {self.worker_id}")
        
        # Loop principal de processamento
        while self.is_running:
            try:
                # Processar fila de notificações
                await self.process_notification_queue()
                
                # Verificar licenças próximas do vencimento (a cada hora)
                current_minute = datetime.utcnow().minute
                if current_minute == 0:  # A cada hora cheia
                    await self.check_expiring_licenses()
                
                # Aguardar antes do próximo ciclo
                await asyncio.sleep(60)  # Verificar a cada minuto
                
            except Exception as e:
                logger.error(f"Error in notification job processor: {e}")
                await asyncio.sleep(300)  # Aguardar 5 minutos se houver erro
    
    async def stop_processing(self):
        """Parar processamento"""
        self.is_running = False
        logger.info(f"Stopping notification job processor: {self.worker_id}")
    
    async def process_notification_queue(self):
        """Processar fila de notificações pendentes"""
        try:
            # Buscar notificações pendentes na fila
            queue_items = await self.db.notification_queue.find({
                "is_processing": False,
                "process_after": {"$lte": datetime.utcnow()}
            }).sort("priority", 1).limit(10).to_list(10)
            
            for queue_item in queue_items:
                try:
                    # Marcar como processando
                    await self.db.notification_queue.update_one(
                        {"_id": queue_item["_id"]},
                        {
                            "$set": {
                                "is_processing": True,
                                "worker_id": self.worker_id
                            }
                        }
                    )
                    
                    # Processar notificação
                    success = await self.process_single_notification(queue_item["notification_id"])
                    
                    if success:
                        # Remover da fila se processado com sucesso
                        await self.db.notification_queue.delete_one({"_id": queue_item["_id"]})
                    else:
                        # Remarcar para retry
                        retry_after = datetime.utcnow() + timedelta(hours=1)
                        await self.db.notification_queue.update_one(
                            {"_id": queue_item["_id"]},
                            {
                                "$set": {
                                    "is_processing": False,
                                    "process_after": retry_after,
                                    "worker_id": None
                                }
                            }
                        )
                
                except Exception as e:
                    logger.error(f"Error processing queue item {queue_item.get('id')}: {e}")
                    # Desmarcar processamento em caso de erro
                    await self.db.notification_queue.update_one(
                        {"_id": queue_item["_id"]},
                        {
                            "$set": {
                                "is_processing": False,
                                "worker_id": None
                            }
                        }
                    )
        
        except Exception as e:
            logger.error(f"Error processing notification queue: {e}")
    
    async def process_single_notification(self, notification_id: str) -> bool:
        """Processar uma única notificação"""
        try:
            # Buscar notificação
            notification_doc = await self.db.notifications.find_one({"id": notification_id})
            if not notification_doc:
                logger.warning(f"Notification {notification_id} not found")
                return True  # Remover da fila pois não existe
            
            notification = Notification(**notification_doc)
            
            # Verificar se já foi enviada
            if notification.status != NotificationStatus.PENDING:
                return True  # Já processada
            
            # Verificar configurações do tenant
            config = await self.get_tenant_notification_config(notification.tenant_id)
            if not config or not config.enabled:
                logger.info(f"Notifications disabled for tenant {notification.tenant_id}")
                return True  # Pular se desabilitado
            
            # Verificar limites diários
            if not await self.check_daily_limits(notification.tenant_id, config):
                logger.warning(f"Daily notification limit reached for tenant {notification.tenant_id}")
                # Reagendar para amanhã
                tomorrow = datetime.utcnow() + timedelta(days=1)
                await self.db.notification_queue.insert_one({
                    "tenant_id": notification.tenant_id,
                    "notification_id": notification_id,
                    "priority": 2,
                    "process_after": tomorrow
                })
                return True
            
            # Enviar notificação
            success = await self.send_notification(notification)
            
            # Atualizar status
            if success:
                await self.db.notifications.update_one(
                    {"id": notification_id},
                    {
                        "$set": {
                            "status": NotificationStatus.SENT,
                            "sent_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                # Log de sucesso
                log_entry = NotificationLog(
                    tenant_id=notification.tenant_id,
                    notification_id=notification_id,
                    action="sent",
                    channel=notification.channel,
                    status=NotificationStatus.SENT,
                    event_data={"worker_id": self.worker_id}
                )
                await self.db.notification_logs.insert_one(log_entry.dict())
                
                logger.info(f"Notification {notification_id} sent successfully")
                return True
                
            else:
                # Incrementar tentativas
                attempts = notification.attempts + 1
                
                if attempts >= notification.max_attempts:
                    # Máximo de tentativas atingido
                    await self.db.notifications.update_one(
                        {"id": notification_id},
                        {
                            "$set": {
                                "status": NotificationStatus.FAILED,
                                "attempts": attempts,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    
                    # Log de falha final
                    log_entry = NotificationLog(
                        tenant_id=notification.tenant_id,
                        notification_id=notification_id,
                        action="failed_final",
                        channel=notification.channel,
                        status=NotificationStatus.FAILED,
                        event_data={"attempts": attempts, "worker_id": self.worker_id}
                    )
                    await self.db.notification_logs.insert_one(log_entry.dict())
                    
                    logger.error(f"Notification {notification_id} failed after {attempts} attempts")
                    return True  # Remover da fila
                else:
                    # Atualizar tentativas
                    await self.db.notifications.update_one(
                        {"id": notification_id},
                        {
                            "$set": {
                                "attempts": attempts,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    
                    logger.warning(f"Notification {notification_id} failed, attempt {attempts}")
                    return False  # Manter na fila para retry
        
        except Exception as e:
            logger.error(f"Error processing notification {notification_id}: {e}")
            return False
    
    async def send_notification(self, notification: Notification) -> bool:
        """Enviar notificação (implementação mock para MVP)"""
        try:
            if notification.channel == NotificationChannel.EMAIL:
                # Mock de envio de email
                logger.info(f"[MOCK EMAIL] To: {notification.recipient_email}")
                logger.info(f"[MOCK EMAIL] Subject: {notification.subject}")
                logger.info(f"[MOCK EMAIL] Content: {notification.message[:100]}...")
                
                # Simular possível falha (5% de chance)
                import random
                if random.random() < 0.05:
                    return False
                
                return True
                
            elif notification.channel == NotificationChannel.IN_APP:
                # Para notificações in-app, apenas marcar como enviada
                logger.info(f"[IN-APP] Notification queued for user: {notification.recipient_user_id}")
                return True
                
            else:
                logger.warning(f"Unsupported notification channel: {notification.channel}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    async def check_expiring_licenses(self):
        """Verificar licenças próximas do vencimento e criar notificações"""
        try:
            maintenance_logger.info("notifications", "expiry_check_started", {
                "worker_id": self.worker_id,
                "check_windows": [30, 7, 1],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            now = datetime.utcnow()
            total_notifications_created = 0
            
            # Definir janelas de verificação
            check_dates = {
                30: NotificationType.LICENSE_EXPIRING_30,
                7: NotificationType.LICENSE_EXPIRING_7,
                1: NotificationType.LICENSE_EXPIRING_1
            }
            
            for days, notification_type in check_dates.items():
                target_date = now + timedelta(days=days)
                date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = date_start + timedelta(days=1)
                
                # Buscar licenças que vencem na data alvo
                licenses = await self.db.licenses.find({
                    "expires_at": {
                        "$gte": date_start,
                        "$lt": date_end
                    },
                    "status": {"$in": ["active", "pending"]}  # Apenas licenças ativas
                }).to_list(1000)
                
                logger.info(f"Found {len(licenses)} licenses expiring in {days} days")
                
                if len(licenses) > 0:
                    maintenance_logger.info("notifications", "licenses_detected", {
                        "expiring_in_days": days,
                        "licenses_count": len(licenses),
                        "notification_type": str(notification_type),
                        "target_date": target_date.strftime("%Y-%m-%d")
                    })
                
                for license_doc in licenses:
                    try:
                        await self.create_expiry_notification(license_doc, notification_type)
                        total_notifications_created += 1
                    except Exception as e:
                        logger.error(f"Error creating notification for license {license_doc.get('id')}: {e}")
                        maintenance_logger.error("notifications", "create_notification_failed", {
                            "license_id": license_doc.get('id'),
                            "notification_type": str(notification_type)
                        }, str(e))
            
            # Verificar licenças já expiradas (últimos 7 dias)
            expired_start = now - timedelta(days=7)
            expired_licenses = await self.db.licenses.find({
                "expires_at": {
                    "$gte": expired_start,
                    "$lt": now
                },
                "status": {"$ne": "expired"}  # Não notificar se já marcada como expirada
            }).to_list(1000)
            
            logger.info(f"Found {len(expired_licenses)} recently expired licenses")
            
            if len(expired_licenses) > 0:
                maintenance_logger.info("notifications", "expired_licenses_detected", {
                    "expired_licenses_count": len(expired_licenses),
                    "check_period": "last_7_days"
                })
            
            for license_doc in expired_licenses:
                try:
                    await self.create_expiry_notification(license_doc, NotificationType.LICENSE_EXPIRED)
                    total_notifications_created += 1
                    
                    # Marcar licença como expirada
                    await self.db.licenses.update_one(
                        {"id": license_doc["id"]},
                        {"$set": {"status": "expired"}}
                    )
                except Exception as e:
                    logger.error(f"Error processing expired license {license_doc.get('id')}: {e}")
                    maintenance_logger.error("notifications", "process_expired_failed", {
                        "license_id": license_doc.get('id')
                    }, str(e))
            
            maintenance_logger.info("notifications", "expiry_check_completed", {
                "worker_id": self.worker_id,
                "total_notifications_created": total_notifications_created,
                "processing_duration": "completed",
                "status": "success"
            })
        
        except Exception as e:
            logger.error(f"Error checking expiring licenses: {e}")
            maintenance_logger.error("notifications", "expiry_check_failed", {
                "worker_id": self.worker_id
            }, str(e))
    
    async def create_expiry_notification(self, license_doc: dict, notification_type: NotificationType):
        """Criar notificação de vencimento para uma licença"""
        try:
            license_id = license_doc["id"]
            tenant_id = license_doc.get("tenant_id", "default")
            
            # Verificar se já existe notificação deste tipo para esta licença
            existing = await self.db.notifications.find_one({
                "license_id": license_id,
                "type": notification_type,
                "tenant_id": tenant_id
            })
            
            if existing:
                logger.debug(f"Notification of type {notification_type} already exists for license {license_id}")
                return
            
            # Obter configurações do tenant
            config = await self.get_tenant_notification_config(tenant_id)
            if not config or not config.enabled:
                return
            
            # Verificar se este tipo de notificação está habilitado
            if not self.is_notification_type_enabled(config, notification_type):
                return
            
            # Buscar dados do cliente
            client_info = await self.get_license_client_info(license_doc)
            if not client_info:
                logger.warning(f"No client info found for license {license_id}")
                return
            
            # Obter template padrão
            template_data = get_default_template(notification_type)
            
            # Preparar contexto para template
            expires_at = license_doc.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            
            days_until_expiry = (expires_at - datetime.utcnow()).days if expires_at else 0
            
            context = {
                "customer_name": client_info.get("name", "Cliente"),
                "license_name": license_doc.get("name", "Licença"),
                "expires_at": expires_at.strftime("%d/%m/%Y") if expires_at else "N/A",
                "days_until_expiry": max(0, days_until_expiry),
                "renewal_url": f"https://app.exemplo.com/renovar/{license_id}",
                "support_email": "suporte@exemplo.com"
            }
            
            # Criar notificações para canais habilitados
            channels = []
            if config.email_enabled and client_info.get("email"):
                channels.append(NotificationChannel.EMAIL)
            if config.in_app_enabled:
                channels.append(NotificationChannel.IN_APP)
            
            for channel in channels:
                # Preparar conteúdo baseado no canal
                if channel == NotificationChannel.EMAIL:
                    subject = format_template_variables(template_data.get("email_subject", ""), context)
                    message = format_template_variables(template_data.get("email_template", ""), context)
                    html_content = message
                    recipient_email = client_info.get("email")
                    recipient_user_id = None
                    
                elif channel == NotificationChannel.IN_APP:
                    subject = format_template_variables(template_data.get("in_app_title", ""), context)
                    message = format_template_variables(template_data.get("in_app_message", ""), context)
                    html_content = None
                    recipient_email = None
                    recipient_user_id = license_doc.get("assigned_user_id")
                
                # Criar notificação
                notification = Notification(
                    tenant_id=tenant_id,
                    type=notification_type,
                    channel=channel,
                    priority=self.get_notification_priority(notification_type),
                    recipient_email=recipient_email,
                    recipient_user_id=recipient_user_id,
                    recipient_name=client_info.get("name"),
                    subject=subject,
                    message=message,
                    html_content=html_content,
                    context_data=context,
                    license_id=license_id,
                    client_id=client_info.get("id")
                )
                
                # Inserir no banco
                await self.db.notifications.insert_one(notification.dict())
                
                # Adicionar à fila
                queue_item = NotificationQueue(
                    tenant_id=tenant_id,
                    notification_id=notification.id,
                    priority=1 if notification.priority == "urgent" else 2
                )
                await self.db.notification_queue.insert_one(queue_item.dict())
                
                logger.info(f"Created {channel} notification for license {license_id} ({notification_type})")
        
        except Exception as e:
            logger.error(f"Error creating expiry notification: {e}")
    
    async def get_tenant_notification_config(self, tenant_id: str) -> Optional[NotificationConfig]:
        """Obter configuração de notificações do tenant"""
        try:
            config_doc = await self.db.notification_configs.find_one({"tenant_id": tenant_id})
            if config_doc:
                return NotificationConfig(**config_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting notification config for tenant {tenant_id}: {e}")
            return None
    
    async def get_license_client_info(self, license_doc: dict) -> Optional[dict]:
        """Obter informações do cliente da licença"""
        try:
            # Verificar cliente PF
            if license_doc.get("client_pf_id"):
                client = await self.db.clientes_pf.find_one({"id": license_doc["client_pf_id"]})
                if client:
                    return {
                        "id": client["id"],
                        "name": client.get("nome_completo", "Cliente"),
                        "email": client.get("email_principal")
                    }
            
            # Verificar cliente PJ
            if license_doc.get("client_pj_id"):
                client = await self.db.clientes_pj.find_one({"id": license_doc["client_pj_id"]})
                if client:
                    return {
                        "id": client["id"],
                        "name": client.get("razao_social", "Empresa"),
                        "email": client.get("email_principal")
                    }
            
            # Se não encontrar cliente específico, buscar pelo usuário atribuído
            if license_doc.get("assigned_user_id"):
                user = await self.db.users.find_one({"id": license_doc["assigned_user_id"]})
                if user:
                    return {
                        "id": user["id"],
                        "name": user.get("name", "Usuário"),
                        "email": user.get("email")
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error getting client info: {e}")
            return None
    
    def is_notification_type_enabled(self, config: NotificationConfig, notification_type: NotificationType) -> bool:
        """Verificar se um tipo de notificação está habilitado"""
        mapping = {
            NotificationType.LICENSE_EXPIRING_30: config.license_expiring_30_enabled,
            NotificationType.LICENSE_EXPIRING_7: config.license_expiring_7_enabled,
            NotificationType.LICENSE_EXPIRING_1: config.license_expiring_1_enabled,
            NotificationType.LICENSE_EXPIRED: config.license_expired_enabled,
            NotificationType.RENEWAL_REMINDER: config.renewal_reminder_enabled
        }
        return mapping.get(notification_type, True)
    
    def get_notification_priority(self, notification_type: NotificationType) -> str:
        """Determinar prioridade baseada no tipo de notificação"""
        if notification_type == NotificationType.LICENSE_EXPIRING_1:
            return "urgent"
        elif notification_type == NotificationType.LICENSE_EXPIRED:
            return "high"
        elif notification_type == NotificationType.LICENSE_EXPIRING_7:
            return "high"
        else:
            return "normal"
    
    async def check_daily_limits(self, tenant_id: str, config: NotificationConfig) -> bool:
        """Verificar se ainda pode enviar notificações (limite diário)"""
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            sent_today = await self.db.notifications.count_documents({
                "tenant_id": tenant_id,
                "status": NotificationStatus.SENT,
                "sent_at": {"$gte": today_start, "$lt": today_end}
            })
            
            return sent_today < config.max_notifications_per_day
        except Exception as e:
            logger.error(f"Error checking daily limits: {e}")
            return True  # Em caso de erro, permitir envio

# Função para inicializar o processador de jobs
notification_processor = None

async def start_notification_jobs(db_client):
    """Inicializar jobs de notificação"""
    global notification_processor
    
    if notification_processor is None:
        notification_processor = NotificationJobProcessor(db_client)
        # Iniciar em background task
        asyncio.create_task(notification_processor.start_processing())
        logger.info("Notification job processor started")

async def stop_notification_jobs():
    """Parar jobs de notificação"""
    global notification_processor
    
    if notification_processor:
        await notification_processor.stop_processing()
        notification_processor = None
        logger.info("Notification job processor stopped")