#!/usr/bin/env python3
"""
Robust Job Scheduler - APScheduler Implementation
Sistema robusto de agendamento de jobs com persistência MongoDB e recovery automático
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from motor.motor_asyncio import AsyncIOMotorClient
import os
import traceback
from functools import wraps
import pytz

# APScheduler imports
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler import events

from notification_system import (
    Notification, NotificationConfig, NotificationQueue, NotificationLog,
    NotificationType, NotificationChannel, NotificationStatus,
    should_send_notification, format_template_variables,
    get_default_template, calculate_notification_trigger_dates
)

# Tenant system imports
from tenant_system import add_tenant_filter, add_tenant_to_document

# Import maintenance logger
import sys
sys.path.insert(0, '/app')
from maintenance_logger import MaintenanceLogger

# Initialize maintenance logger
maintenance_logger = MaintenanceLogger()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobustJobScheduler:
    """
    Enterprise-grade job scheduler with:
    - Persistent job storage in MongoDB
    - Automatic recovery after restart
    - Comprehensive error handling
    - Job monitoring and metrics
    - Tenant-aware job isolation
    """
    
    def __init__(self, mongo_url: str, db_name: str):
        self.mongo_url = mongo_url
        self.db_name = db_name
        self.scheduler = None
        self.db = None
        self.client = None
        self.is_running = False
        
        # Job statistics
        self.job_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "last_execution": None,
            "uptime_start": datetime.utcnow()
        }
        
        # Configure timezone (unified to match backend)
        tz_name = os.getenv('TZ', 'America/Recife')
        self.timezone = pytz.timezone(tz_name)
    
    async def initialize(self):
        """Initialize scheduler with MongoDB persistence"""
        try:
            # Connect to MongoDB
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
            
            # Test connection
            await self.client.admin.command('ismaster')
            logger.info(f"✅ Connected to MongoDB: {self.db_name}")
            
            # Configure APScheduler
            jobstores = {
                'default': MongoDBJobStore(host=self.mongo_url, database=self.db_name)
            }
            
            executors = {
                'default': AsyncIOExecutor()
            }
            
            job_defaults = {
                'coalesce': True,  # Combine multiple pending executions
                'max_instances': 1,  # Prevent concurrent executions
                'misfire_grace_time': 300  # 5 minute grace period for missed jobs
            }
            
            # Create scheduler
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone=self.timezone
            )
            
            # Add event listeners for monitoring
            self.scheduler.add_listener(self._job_success_listener, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
            self.scheduler.add_listener(self._job_missed_listener, EVENT_JOB_MISSED)
            
            logger.info("✅ APScheduler configured with MongoDB persistence")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize scheduler: {e}")
            raise
    
    async def start(self):
        """Start the scheduler"""
        try:
            if not self.scheduler:
                await self.initialize()
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            
            # Schedule core jobs
            await self._schedule_core_jobs()
            
            # Log startup
            maintenance_logger.info("scheduler", "startup", {
                "status": "started",
                "timezone": str(self.timezone),
                "persistence": "mongodb",
                "features": ["auto_recovery", "job_monitoring", "tenant_isolation"]
            })
            
            logger.info("🚀 Robust scheduler started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}")
            raise
    
    async def stop(self):
        """Stop the scheduler gracefully"""
        try:
            if self.scheduler and self.is_running:
                self.scheduler.shutdown(wait=True)
                self.is_running = False
                
                if self.client:
                    self.client.close()
                
                maintenance_logger.info("scheduler", "shutdown", {
                    "status": "stopped",
                    "uptime_minutes": (datetime.utcnow() - self.job_stats["uptime_start"]).total_seconds() / 60,
                    "total_executions": self.job_stats["total_executions"]
                })
                
                logger.info("✅ Scheduler stopped gracefully")
        
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
    
    async def _schedule_core_jobs(self):
        """Schedule core system jobs"""
        try:
            # 1. License expiry check - Every hour at minute 0
            self.scheduler.add_job(
                func=check_expiring_licenses_job,
                args=[self.mongo_url, self.db_name],
                trigger='cron',
                minute=0,  # Every hour at :00
                id='license_expiry_check',
                name='License Expiry Checker',
                replace_existing=True,
                max_instances=1
            )
            
            # 2. Notification queue processor - Every 2 minutes  
            self.scheduler.add_job(
                func=process_notification_queue_job,
                args=[self.mongo_url, self.db_name],
                trigger='interval',
                minutes=2,
                id='notification_queue_processor', 
                name='Notification Queue Processor',
                replace_existing=True,
                max_instances=1
            )
            
            # 3. Daily cleanup job - Every day at 2 AM
            self.scheduler.add_job(
                func=daily_cleanup_job,
                args=[self.mongo_url, self.db_name],
                trigger='cron',
                hour=2,
                minute=0,
                id='daily_cleanup',
                name='Daily Cleanup Job',
                replace_existing=True,
                max_instances=1
            )
            
            # 4. System health check - Every 15 minutes
            self.scheduler.add_job(
                func=system_health_check_job,
                args=[self.mongo_url, self.db_name],
                trigger='interval',
                minutes=15,
                id='health_check',
                name='System Health Monitor',
                replace_existing=True,
                max_instances=1
            )
            
            # List scheduled jobs
            jobs = self.scheduler.get_jobs()
            logger.info(f"📅 Scheduled {len(jobs)} core jobs:")
            for job in jobs:
                logger.info(f"  ✅ {job.name} - Next run: {job.next_run_time}")
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule core jobs: {e}")
            raise
    
    def _job_wrapper(self, func: Callable):
        """Decorator to wrap job functions with error handling and metrics"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            job_name = func.__name__
            start_time = datetime.utcnow()
            
            try:
                # Execute job
                result = await func(*args, **kwargs)
                
                # Update success metrics
                self.job_stats["successful_executions"] += 1
                self.job_stats["total_executions"] += 1
                self.job_stats["last_execution"] = start_time
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                maintenance_logger.info("jobs", f"{job_name}_success", {
                    "job_name": job_name,
                    "duration_seconds": duration,
                    "result": str(result)[:500] if result else None
                })
                
                return result
                
            except Exception as e:
                # Update error metrics
                self.job_stats["failed_executions"] += 1
                self.job_stats["total_executions"] += 1
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                error_trace = traceback.format_exc()
                
                maintenance_logger.error("jobs", f"{job_name}_error", {
                    "job_name": job_name,
                    "error": str(e),
                    "duration_seconds": duration,
                    "traceback": error_trace
                }, str(e))
                
                logger.error(f"❌ Job {job_name} failed: {e}")
                raise
        
        return wrapper
    
    async def _check_expiring_licenses(self):
        """Check for expiring licenses and create notifications"""
        try:
            logger.info("🔍 Starting license expiry check...")
            
            # Check windows: 30 days, 7 days, 1 day
            check_windows = [30, 7, 1]
            total_notifications = 0
            
            for days in check_windows:
                # Calculate target date
                target_date = datetime.utcnow() + timedelta(days=days)
                start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)
                
                # Find expiring licenses
                # CRÍTICO: Adicionar filtro de tenant para licenças
                license_filter = add_tenant_filter({
                    "expires_at": {
                        "$gte": start_of_day,
                        "$lt": end_of_day
                    },
                    "status": {"$in": ["active", "pending"]}
                }, "default")  # Default tenant - precisa ser configurável
                expiring_licenses = await self.db.licenses.find(license_filter).to_list(1000)
                
                # Create notifications for each license
                for license_data in expiring_licenses:
                    try:
                        await self._create_expiry_notification(license_data, days)
                        total_notifications += 1
                    except Exception as e:
                        logger.error(f"Failed to create notification for license {license_data.get('id')}: {e}")
                
                if expiring_licenses:
                    maintenance_logger.info("notifications", "licenses_detected", {
                        "expiring_in_days": days,
                        "licenses_count": len(expiring_licenses),
                        "notification_type": f"NotificationType.LICENSE_EXPIRING_{days}",
                        "target_date": target_date.strftime("%Y-%m-%d")
                    })
            
            logger.info(f"✅ License expiry check completed - {total_notifications} notifications created")
            return {"notifications_created": total_notifications}
            
        except Exception as e:
            logger.error(f"❌ License expiry check failed: {e}")
            raise
    
    async def _create_expiry_notification(self, license_data: Dict, days_to_expire: int):
        """Create expiry notification for a specific license"""
        try:
            # Determine notification type
            if days_to_expire == 30:
                notification_type = NotificationType.LICENSE_EXPIRING_30
            elif days_to_expire == 7:
                notification_type = NotificationType.LICENSE_EXPIRING_7
            elif days_to_expire == 1:
                notification_type = NotificationType.LICENSE_EXPIRING_1
            else:
                notification_type = NotificationType.LICENSE_EXPIRING_7  # Default
            
            # Check if notification already exists
            # CRÍTICO: Adicionar filtro de tenant para busca de notificação
            tenant_id = license_data.get("tenant_id", "default")
            existing_filter = add_tenant_filter({
                "license_id": license_data.get("id"),
                "type": notification_type,
                "target_date": license_data.get("expires_at")
            }, tenant_id)
            existing = await self.db.notifications.find_one(existing_filter)
            
            if existing:
                return  # Skip if already created
            
            # Get notification config
            config = await self.db.notification_config.find_one({
                "tenant_id": license_data.get("tenant_id", "default")
            })
            
            if not config or not config.get("enabled", True):
                return  # Skip if notifications disabled for tenant
            
            # Create notification
            notification = Notification(
                id=f"expiry_{license_data.get('id')}_{days_to_expire}_{datetime.utcnow().strftime('%Y%m%d')}",
                tenant_id=license_data.get("tenant_id", "default"),
                type=notification_type,
                license_id=license_data.get("id"),
                user_id=license_data.get("assigned_user_id"),
                title=f"License expiring in {days_to_expire} days",
                message=f"License '{license_data.get('name')}' expires on {license_data.get('expires_at', '').strftime('%Y-%m-%d') if license_data.get('expires_at') else 'N/A'}",
                channels=[NotificationChannel.EMAIL, NotificationChannel.WHATSAPP],
                priority=1 if days_to_expire == 1 else (2 if days_to_expire == 7 else 3),
                target_date=license_data.get("expires_at"),
                metadata={
                    "license_name": license_data.get("name"),
                    "days_to_expire": days_to_expire,
                    "client_name": license_data.get("client_name"),
                    "auto_generated": True
                },
                created_at=datetime.utcnow()
            )
            
            # Insert notification
            # CRÍTICO: Garantir tenant_id no documento antes de inserir
            notification_dict = add_tenant_to_document(notification.dict(), tenant_id)
            await self.db.notifications.insert_one(notification_dict)
            
            # Add to notification queue for processing
            queue_item = NotificationQueue(
                id=f"queue_{notification.id}",
                tenant_id=notification.tenant_id,
                notification_id=notification.id,
                priority=notification.priority,
                process_after=datetime.utcnow() + timedelta(minutes=1),
                created_at=datetime.utcnow()
            )
            
            # CRÍTICO: Garantir tenant_id no documento da fila antes de inserir
            queue_dict = add_tenant_to_document(queue_item.dict(), tenant_id)
            await self.db.notification_queue.insert_one(queue_dict)
            
        except Exception as e:
            logger.error(f"Failed to create expiry notification: {e}")
            raise
    
    async def _process_notification_queue(self):
        """Process pending notifications in queue"""
        try:
            logger.info("📧 Processing notification queue...")
            
            # Get pending notifications
            # CRÍTICO: Para processamento global, usar tenant padrão por enquanto
            # TODO: Melhorar para processar todos os tenants
            queue_filter = add_tenant_filter({
                "is_processing": False,
                "process_after": {"$lte": datetime.utcnow()}
            }, "default")
            queue_items = await self.db.notification_queue.find(queue_filter).sort("priority", 1).limit(10).to_list(10)
            
            processed = 0
            
            for queue_item in queue_items:
                try:
                    # Mark as processing
                    # CRÍTICO: Adicionar filtro de tenant para update
                    queue_tenant_id = queue_item.get("tenant_id", "default")
                    queue_update_filter = add_tenant_filter({"_id": queue_item["_id"]}, queue_tenant_id)
                    await self.db.notification_queue.update_one(
                        queue_update_filter,
                        {"$set": {"is_processing": True, "worker_id": "apscheduler"}}
                    )
                    
                    # Get notification details
                    # CRÍTICO: Adicionar filtro de tenant para busca de notificação
                    notification_filter = add_tenant_filter({
                        "id": queue_item["notification_id"]
                    }, queue_tenant_id)
                    notification = await self.db.notifications.find_one(notification_filter)
                    
                    if notification:
                        # Simulate notification sending (replace with actual implementation)
                        await self._send_notification(notification)
                        
                        # Remove from queue
                        # CRÍTICO: Adicionar filtro de tenant para delete
                        delete_filter = add_tenant_filter({"_id": queue_item["_id"]}, queue_tenant_id)
                        await self.db.notification_queue.delete_one(delete_filter)
                        processed += 1
                    else:
                        # Notification not found, remove from queue
                        # CRÍTICO: Adicionar filtro de tenant para delete
                        delete_filter = add_tenant_filter({"_id": queue_item["_id"]}, queue_tenant_id)
                        await self.db.notification_queue.delete_one(delete_filter)
                
                except Exception as e:
                    logger.error(f"Failed to process queue item: {e}")
                    # Reset processing flag
                    await self.db.notification_queue.update_one(
                        {"_id": queue_item["_id"]},
                        {"$set": {"is_processing": False, "worker_id": None}}
                    )
            
            if processed > 0:
                logger.info(f"✅ Processed {processed} notifications")
                
            return {"notifications_processed": processed}
            
        except Exception as e:
            logger.error(f"❌ Notification queue processing failed: {e}")
            raise
    
    async def _send_notification(self, notification: Dict):
        """Send notification via configured channels"""
        try:
            # Update notification status to sending
            await self.db.notifications.update_one(
                {"id": notification["id"]},
                {"$set": {"status": NotificationStatus.SENDING, "sent_at": datetime.utcnow()}}
            )
            
            # Simulate sending (replace with actual email/WhatsApp integration)
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Update to sent
            await self.db.notifications.update_one(
                {"id": notification["id"]},
                {"$set": {"status": NotificationStatus.SENT}}
            )
            
            # Log notification sent
            log_entry = NotificationLog(
                id=f"log_{notification['id']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                tenant_id=notification["tenant_id"],
                notification_id=notification["id"],
                channel=NotificationChannel.EMAIL,  # Example
                status=NotificationStatus.SENT,
                sent_at=datetime.utcnow(),
                metadata={"simulated": True}
            )
            
            await self.db.notification_logs.insert_one(log_entry.dict())
            
        except Exception as e:
            # Update to failed
            await self.db.notifications.update_one(
                {"id": notification["id"]},
                {"$set": {"status": NotificationStatus.FAILED, "error_message": str(e)}}
            )
            raise
    
    async def _daily_cleanup(self):
        """Daily cleanup of old logs and processed notifications"""
        try:
            logger.info("🧹 Starting daily cleanup...")
            
            # Cleanup old notification logs (older than 90 days)
            cleanup_date = datetime.utcnow() - timedelta(days=90)
            
            deleted_logs = await self.db.notification_logs.delete_many({
                "created_at": {"$lt": cleanup_date}
            })
            
            # Cleanup old processed notifications (older than 30 days)
            notification_cleanup_date = datetime.utcnow() - timedelta(days=30)
            
            deleted_notifications = await self.db.notifications.delete_many({
                "status": {"$in": [NotificationStatus.SENT, NotificationStatus.FAILED]},
                "created_at": {"$lt": notification_cleanup_date}
            })
            
            cleanup_stats = {
                "logs_deleted": deleted_logs.deleted_count,
                "notifications_deleted": deleted_notifications.deleted_count,
                "cleanup_date": cleanup_date.isoformat()
            }
            
            maintenance_logger.info("cleanup", "daily_cleanup_completed", cleanup_stats)
            logger.info(f"✅ Daily cleanup completed: {cleanup_stats}")
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"❌ Daily cleanup failed: {e}")
            raise
    
    async def _system_health_check(self):
        """Monitor system health and performance"""
        try:
            health_stats = {}
            
            # Check database connection
            start_time = datetime.utcnow()
            await self.client.admin.command('ismaster')
            db_response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            health_stats["database_response_ms"] = db_response_time
            health_stats["database_status"] = "healthy" if db_response_time < 100 else "slow"
            
            # Check notification queue size
            queue_size = await self.db.notification_queue.count_documents({})
            health_stats["notification_queue_size"] = queue_size
            health_stats["queue_status"] = "healthy" if queue_size < 1000 else "high"
            
            # Check recent errors
            recent_errors = await self.db.notification_logs.count_documents({
                "status": NotificationStatus.FAILED,
                "created_at": {"$gte": datetime.utcnow() - timedelta(hours=1)}
            })
            
            health_stats["recent_errors"] = recent_errors
            health_stats["error_status"] = "healthy" if recent_errors < 10 else "high"
            
            # Overall health
            health_stats["overall_status"] = "healthy" if all(
                status in ["healthy"] for status in [
                    health_stats["database_status"],
                    health_stats["queue_status"], 
                    health_stats["error_status"]
                ]
            ) else "degraded"
            
            maintenance_logger.info("health", "system_health_check", health_stats)
            
            return health_stats
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            raise
    
    async def _update_job_statistics(self):
        """Update job execution statistics"""
        try:
            # Calculate uptime
            uptime_seconds = (datetime.utcnow() - self.job_stats["uptime_start"]).total_seconds()
            
            stats = {
                **self.job_stats,
                "uptime_hours": round(uptime_seconds / 3600, 2),
                "success_rate": round(
                    (self.job_stats["successful_executions"] / max(self.job_stats["total_executions"], 1)) * 100, 2
                ),
                "scheduler_status": "running" if self.is_running else "stopped"
            }
            
            # Store in database
            await self.db.scheduler_stats.replace_one(
                {"type": "current_stats"},
                {"type": "current_stats", "updated_at": datetime.utcnow(), **stats},
                upsert=True
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Statistics update failed: {e}")
            raise
    
    def _job_success_listener(self, event):
        """Handle successful job execution"""
        logger.info(f"✅ Job {event.job_id} completed successfully")
    
    def _job_error_listener(self, event):
        """Handle job execution errors"""
        logger.error(f"❌ Job {event.job_id} failed: {event.exception}")
        
        maintenance_logger.error("jobs", "job_execution_error", {
            "job_id": event.job_id,
            "exception": str(event.exception),
            "traceback": event.traceback
        }, str(event.exception))
    
    def _job_missed_listener(self, event):
        """Handle missed job executions"""
        logger.warning(f"⚠️ Job {event.job_id} missed execution")
        
        maintenance_logger.warning("jobs", "job_missed_execution", {
            "job_id": event.job_id,
            "scheduled_run_time": event.scheduled_run_time.isoformat() if event.scheduled_run_time else None
        })
    
    async def get_job_status(self) -> Dict:
        """Get current job scheduler status"""
        try:
            jobs = self.scheduler.get_jobs() if self.scheduler else []
            
            job_info = []
            for job in jobs:
                job_info.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
            
            return {
                "scheduler_running": self.is_running,
                "total_jobs": len(jobs),
                "jobs": job_info,
                "statistics": self.job_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return {"error": str(e)}

# Standalone job functions for APScheduler (don't reference self)
async def check_expiring_licenses_job(mongo_url: str, db_name: str):
    """Standalone function for license expiry check job"""
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        logger.info("🔍 Starting license expiry check...")
        
        # Check windows: 30 days, 7 days, 1 day
        check_windows = [30, 7, 1]
        total_notifications = 0
        
        for days in check_windows:
            # Calculate target date
            target_date = datetime.utcnow() + timedelta(days=days)
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            # Find expiring licenses
            expiring_licenses = await db.licenses.find({
                "expires_at": {
                    "$gte": start_of_day,
                    "$lt": end_of_day
                },
                "status": {"$in": ["active", "pending"]}
            }).to_list(1000)
            
            # Create notifications for each license
            for license_data in expiring_licenses:
                try:
                    await _create_expiry_notification_standalone(db, license_data, days)
                    total_notifications += 1
                except Exception as e:
                    logger.error(f"Failed to create notification for license {license_data.get('id')}: {e}")
            
            if expiring_licenses:
                maintenance_logger.info("notifications", "licenses_detected", {
                    "expiring_in_days": days,
                    "licenses_count": len(expiring_licenses),
                    "notification_type": f"NotificationType.LICENSE_EXPIRING_{days}",
                    "target_date": target_date.strftime("%Y-%m-%d")
                })
        
        logger.info(f"✅ License expiry check completed - {total_notifications} notifications created")
        client.close()
        return {"notifications_created": total_notifications}
        
    except Exception as e:
        logger.error(f"❌ License expiry check failed: {e}")
        if 'client' in locals():
            client.close()
        raise

async def process_notification_queue_job(mongo_url: str, db_name: str):
    """Standalone function for notification queue processing job"""
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        logger.info("📧 Processing notification queue...")
        
        # Get pending notifications
        queue_items = await db.notification_queue.find({
            "is_processing": False,
            "process_after": {"$lte": datetime.utcnow()}
        }).sort("priority", 1).limit(10).to_list(10)
        
        processed = 0
        
        for queue_item in queue_items:
            try:
                # Mark as processing
                await db.notification_queue.update_one(
                    {"_id": queue_item["_id"]},
                    {"$set": {"is_processing": True, "worker_id": "apscheduler"}}
                )
                
                # Get notification details
                notification = await db.notifications.find_one({
                    "id": queue_item["notification_id"]
                })
                
                if notification:
                    # Simulate notification sending
                    await _send_notification_standalone(db, notification)
                    
                    # Remove from queue
                    await db.notification_queue.delete_one({"_id": queue_item["_id"]})
                    processed += 1
                else:
                    # Notification not found, remove from queue
                    await db.notification_queue.delete_one({"_id": queue_item["_id"]})
            
            except Exception as e:
                logger.error(f"Failed to process queue item: {e}")
                # Reset processing flag
                await db.notification_queue.update_one(
                    {"_id": queue_item["_id"]},
                    {"$set": {"is_processing": False, "worker_id": None}}
                )
        
        if processed > 0:
            logger.info(f"✅ Processed {processed} notifications")
            
        client.close()
        return {"notifications_processed": processed}
        
    except Exception as e:
        logger.error(f"❌ Notification queue processing failed: {e}")
        if 'client' in locals():
            client.close()
        raise

async def daily_cleanup_job(mongo_url: str, db_name: str):
    """Standalone function for daily cleanup job"""
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        logger.info("🧹 Starting daily cleanup...")
        
        # Cleanup old notification logs (older than 90 days)
        cleanup_date = datetime.utcnow() - timedelta(days=90)
        
        deleted_logs = await db.notification_logs.delete_many({
            "created_at": {"$lt": cleanup_date}
        })
        
        # Cleanup old processed notifications (older than 30 days)
        notification_cleanup_date = datetime.utcnow() - timedelta(days=30)
        
        deleted_notifications = await db.notifications.delete_many({
            "status": {"$in": [NotificationStatus.SENT, NotificationStatus.FAILED]},
            "created_at": {"$lt": notification_cleanup_date}
        })
        
        cleanup_stats = {
            "logs_deleted": deleted_logs.deleted_count,
            "notifications_deleted": deleted_notifications.deleted_count,
            "cleanup_date": cleanup_date.isoformat()
        }
        
        maintenance_logger.info("cleanup", "daily_cleanup_completed", cleanup_stats)
        logger.info(f"✅ Daily cleanup completed: {cleanup_stats}")
        
        client.close()
        return cleanup_stats
        
    except Exception as e:
        logger.error(f"❌ Daily cleanup failed: {e}")
        if 'client' in locals():
            client.close()
        raise

async def system_health_check_job(mongo_url: str, db_name: str):
    """Standalone function for system health check job"""
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        health_stats = {}
        
        # Check database connection
        start_time = datetime.utcnow()
        await client.admin.command('ismaster')
        db_response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        health_stats["database_response_ms"] = db_response_time
        health_stats["database_status"] = "healthy" if db_response_time < 100 else "slow"
        
        # Check notification queue size
        queue_size = await db.notification_queue.count_documents({})
        health_stats["notification_queue_size"] = queue_size
        health_stats["queue_status"] = "healthy" if queue_size < 1000 else "high"
        
        # Check recent errors
        recent_errors = await db.notification_logs.count_documents({
            "status": NotificationStatus.FAILED,
            "created_at": {"$gte": datetime.utcnow() - timedelta(hours=1)}
        })
        
        health_stats["recent_errors"] = recent_errors
        health_stats["error_status"] = "healthy" if recent_errors < 10 else "high"
        
        # Overall health
        health_stats["overall_status"] = "healthy" if all(
            status in ["healthy"] for status in [
                health_stats["database_status"],
                health_stats["queue_status"], 
                health_stats["error_status"]
            ]
        ) else "degraded"
        
        maintenance_logger.info("health", "system_health_check", health_stats)
        
        client.close()
        return health_stats
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        if 'client' in locals():
            client.close()
        raise

# Helper functions for standalone jobs
async def _create_expiry_notification_standalone(db, license_data: Dict, days_to_expire: int):
    """Create expiry notification for a specific license (standalone version)"""
    try:
        # Determine notification type
        if days_to_expire == 30:
            notification_type = NotificationType.LICENSE_EXPIRING_30
        elif days_to_expire == 7:
            notification_type = NotificationType.LICENSE_EXPIRING_7
        elif days_to_expire == 1:
            notification_type = NotificationType.LICENSE_EXPIRING_1
        else:
            notification_type = NotificationType.LICENSE_EXPIRING_7  # Default
        
        # Check if notification already exists
        existing = await db.notifications.find_one({
            "license_id": license_data.get("id"),
            "type": notification_type,
            "target_date": license_data.get("expires_at")
        })
        
        if existing:
            return  # Skip if already created
        
        # Get notification config
        config = await db.notification_config.find_one({
            "tenant_id": license_data.get("tenant_id", "default")
        })
        
        if not config or not config.get("enabled", True):
            return  # Skip if notifications disabled for tenant
        
        # Create notification
        notification = Notification(
            id=f"expiry_{license_data.get('id')}_{days_to_expire}_{datetime.utcnow().strftime('%Y%m%d')}",
            tenant_id=license_data.get("tenant_id", "default"),
            type=notification_type,
            license_id=license_data.get("id"),
            user_id=license_data.get("assigned_user_id"),
            title=f"License expiring in {days_to_expire} days",
            message=f"License '{license_data.get('name')}' expires on {license_data.get('expires_at', '').strftime('%Y-%m-%d') if license_data.get('expires_at') else 'N/A'}",
            channels=[NotificationChannel.EMAIL, NotificationChannel.WHATSAPP],
            priority=1 if days_to_expire == 1 else (2 if days_to_expire == 7 else 3),
            target_date=license_data.get("expires_at"),
            metadata={
                "license_name": license_data.get("name"),
                "days_to_expire": days_to_expire,
                "client_name": license_data.get("client_name"),
                "auto_generated": True
            },
            created_at=datetime.utcnow()
        )
        
        # Insert notification
        await db.notifications.insert_one(notification.dict())
        
        # Add to notification queue for processing
        queue_item = NotificationQueue(
            id=f"queue_{notification.id}",
            tenant_id=notification.tenant_id,
            notification_id=notification.id,
            priority=notification.priority,
            process_after=datetime.utcnow() + timedelta(minutes=1),
            created_at=datetime.utcnow()
        )
        
        await db.notification_queue.insert_one(queue_item.dict())
        
    except Exception as e:
        logger.error(f"Failed to create expiry notification: {e}")
        raise

async def _send_notification_standalone(db, notification: Dict):
    """Send notification via configured channels (standalone version)"""
    try:
        # Update notification status to sending
        await db.notifications.update_one(
            {"id": notification["id"]},
            {"$set": {"status": NotificationStatus.SENDING, "sent_at": datetime.utcnow()}}
        )
        
        # Simulate sending (replace with actual email/WhatsApp integration)
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Update to sent
        await db.notifications.update_one(
            {"id": notification["id"]},
            {"$set": {"status": NotificationStatus.SENT}}
        )
        
        # Log notification sent
        log_entry = NotificationLog(
            id=f"log_{notification['id']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            tenant_id=notification["tenant_id"],
            notification_id=notification["id"],
            channel=NotificationChannel.EMAIL,  # Example
            status=NotificationStatus.SENT,
            sent_at=datetime.utcnow(),
            metadata={"simulated": True}
        )
        
        await db.notification_logs.insert_one(log_entry.dict())
        
    except Exception as e:
        # Update to failed
        await db.notifications.update_one(
            {"id": notification["id"]},
            {"$set": {"status": NotificationStatus.FAILED, "error_message": str(e)}}
        )
        raise

# Global scheduler instance
_scheduler_instance = None

async def get_scheduler() -> RobustJobScheduler:
    """Get global scheduler instance"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv('/app/backend/.env')
        
        mongo_url = os.environ['MONGO_URL']
        db_name = os.environ['DB_NAME']
        
        _scheduler_instance = RobustJobScheduler(mongo_url, db_name)
    
    return _scheduler_instance

# Main functions for integration
async def start_robust_scheduler():
    """Start the robust scheduler system"""
    try:
        scheduler = await get_scheduler()
        await scheduler.start()
        logger.info("🚀 Robust scheduler started")
        return scheduler
        
    except Exception as e:
        logger.error(f"❌ Failed to start robust scheduler: {e}")
        raise

async def stop_robust_scheduler():
    """Stop the robust scheduler system"""
    try:
        global _scheduler_instance
        
        if _scheduler_instance:
            await _scheduler_instance.stop()
            _scheduler_instance = None
            logger.info("✅ Robust scheduler stopped")
        
    except Exception as e:
        logger.error(f"❌ Failed to stop robust scheduler: {e}")
        raise

# CLI usage for testing
if __name__ == "__main__":
    async def main():
        scheduler = await get_scheduler()
        await scheduler.start()
        
        try:
            # Keep running
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await scheduler.stop()
    
    asyncio.run(main())