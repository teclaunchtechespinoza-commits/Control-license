#!/usr/bin/env python3
"""
Structured Logger System - Enterprise Logging with Correlation
Sistema de logs estruturados com correlação de tenant_id, request_id e auditoria completa
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextvars import ContextVar
from enum import Enum
import traceback

# Context variables for request tracking
current_tenant_id: ContextVar[Optional[str]] = ContextVar('current_tenant_id', default=None)
current_request_id: ContextVar[Optional[str]] = ContextVar('current_request_id', default=None)
current_user_id: ContextVar[Optional[str]] = ContextVar('current_user_id', default=None)
current_user_email: ContextVar[Optional[str]] = ContextVar('current_user_email', default=None)

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    AUDIT = "AUDIT"

class EventCategory(str, Enum):
    # Authentication & Authorization
    AUTH = "auth"
    RBAC = "rbac"
    
    # Data Operations
    DATA_CREATE = "data_create"
    DATA_READ = "data_read"
    DATA_UPDATE = "data_update" 
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    
    # System Events
    SYSTEM = "system"
    SCHEDULER = "scheduler"
    HEALTH = "health"
    
    # Business Logic
    LICENSE = "license"
    CLIENT = "client"
    NOTIFICATION = "notification"
    BILLING = "billing"
    
    # Security Events
    SECURITY = "security"
    COMPLIANCE = "compliance"
    AUDIT = "audit"

class SensitiveDataMasker:
    """Mask sensitive data in logs for LGPD compliance"""
    
    SENSITIVE_FIELDS = {
        'password', 'cpf', 'cnpj', 'email', 'phone', 'credit_card', 
        'bank_account', 'social_security', 'access_token', 'refresh_token',
        'api_key', 'secret', 'private_key'
    }
    
    @classmethod
    def mask_sensitive_data(cls, data: Any) -> Any:
        """Recursively mask sensitive data in dictionaries and lists"""
        if isinstance(data, dict):
            return {
                key: cls._mask_value(key, value) for key, value in data.items()
            }
        elif isinstance(data, list):
            return [cls.mask_sensitive_data(item) for item in data]
        else:
            return data
    
    @classmethod
    def _mask_value(cls, key: str, value: Any) -> Any:
        """Mask individual field values"""
        if key.lower() in cls.SENSITIVE_FIELDS or 'password' in key.lower():
            if isinstance(value, str) and len(value) > 0:
                if len(value) <= 3:
                    return "***"
                elif len(value) <= 8:
                    return f"{value[0]}***{value[-1]}" 
                else:
                    return f"{value[:2]}***{value[-2:]}"
            return "***"
        elif isinstance(value, dict):
            return cls.mask_sensitive_data(value)
        elif isinstance(value, list):
            return cls.mask_sensitive_data(value)
        else:
            return value

class StructuredLogger:
    """
    Enterprise structured logging system with:
    - JSON format for all logs
    - Request correlation with tenant_id and request_id
    - Audit trail for sensitive operations
    - LGPD compliant data masking
    - Performance metrics
    - Security event tracking
    """
    
    def __init__(self, name: str = "structured_logger"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Configure JSON formatter
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup file and console handlers with JSON formatting"""
        
        # File handler for structured logs
        file_handler = logging.FileHandler('/app/structured_logs.json')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(JSONFormatter())
        
        # Audit handler for sensitive operations
        audit_handler = logging.FileHandler('/app/audit_logs.json')
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(JSONFormatter())
        audit_handler.addFilter(AuditFilter())
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(audit_handler)
    
    def _build_log_record(
        self, 
        level: LogLevel,
        category: EventCategory, 
        action: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        sensitive: bool = False,
        audit_required: bool = False
    ) -> Dict[str, Any]:
        """Build structured log record with all metadata"""
        
        # Generate unique event ID for tracking
        event_id = str(uuid.uuid4())
        
        # Build base record
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": event_id,
            "level": level.value,
            "category": category.value,
            "action": action,
            "message": message,
            
            # Request correlation
            "tenant_id": current_tenant_id.get(),
            "request_id": current_request_id.get(),
            "user_id": current_user_id.get(),
            "user_email": current_user_email.get(),
            
            # System metadata
            "service": "license_management",
            "version": "1.3.0",
            "environment": os.getenv("ENVIRONMENT", "production")
        }
        
        # Add details with sensitive data masking
        if details:
            if sensitive:
                record["details"] = SensitiveDataMasker.mask_sensitive_data(details)
                record["data_masked"] = True
            else:
                record["details"] = details
        
        # Add error information
        if error:
            record["error"] = {
                "type": error.__class__.__name__,
                "message": str(error),
                "traceback": traceback.format_exc() if level == LogLevel.ERROR else None
            }
        
        # Mark for audit if required
        if audit_required:
            record["audit_required"] = True
            record["audit_category"] = "sensitive_operation"
        
        return record
    
    def debug(
        self,
        category: EventCategory,
        action: str, 
        message: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log debug information"""
        record = self._build_log_record(
            LogLevel.DEBUG, category, action, message, details, **kwargs
        )
        self.logger.debug(json.dumps(record, ensure_ascii=False))
    
    def info(
        self,
        category: EventCategory,
        action: str,
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log informational events"""
        record = self._build_log_record(
            LogLevel.INFO, category, action, message, details, **kwargs
        )
        self.logger.info(json.dumps(record, ensure_ascii=False))
    
    def warning(
        self,
        category: EventCategory,
        action: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log warning events"""
        record = self._build_log_record(
            LogLevel.WARNING, category, action, message, details, **kwargs
        )
        self.logger.warning(json.dumps(record, ensure_ascii=False))
    
    def error(
        self,
        category: EventCategory,
        action: str,
        message: str,
        error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log error events"""
        record = self._build_log_record(
            LogLevel.ERROR, category, action, message, details, error, **kwargs
        )
        self.logger.error(json.dumps(record, ensure_ascii=False))
    
    def critical(
        self,
        category: EventCategory,
        action: str,
        message: str,
        error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log critical events"""
        record = self._build_log_record(
            LogLevel.CRITICAL, category, action, message, details, error, **kwargs
        )
        self.logger.critical(json.dumps(record, ensure_ascii=False))
    
    def audit(
        self,
        action: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        sensitive: bool = True,
        **kwargs
    ):
        """Log audit events for sensitive operations"""
        record = self._build_log_record(
            LogLevel.AUDIT, EventCategory.AUDIT, action, message, 
            details, sensitive=sensitive, audit_required=True, **kwargs
        )
        self.logger.info(json.dumps(record, ensure_ascii=False))

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        # If the record message is already JSON, return as-is
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, ValueError):
            # If not JSON, create structured record
            log_record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            if record.exc_info:
                log_record["exception"] = self.formatException(record.exc_info)
            
            return json.dumps(log_record, ensure_ascii=False)

class AuditFilter(logging.Filter):
    """Filter to capture only audit-required logs"""
    
    def filter(self, record):
        try:
            message = record.getMessage()
            log_data = json.loads(message)
            return log_data.get("audit_required", False)
        except:
            return False

# Context managers for correlation tracking
class RequestContext:
    """Context manager for request-level correlation"""
    
    def __init__(self, tenant_id: str = None, user_id: str = None, user_email: str = None):
        self.tenant_id = tenant_id
        self.user_id = user_id  
        self.user_email = user_email
        self.request_id = str(uuid.uuid4())
        
        # Store previous values for restoration
        self.prev_tenant_id = None
        self.prev_user_id = None
        self.prev_user_email = None
        self.prev_request_id = None
    
    def __enter__(self):
        self.prev_tenant_id = current_tenant_id.get()
        self.prev_user_id = current_user_id.get()
        self.prev_user_email = current_user_email.get()
        self.prev_request_id = current_request_id.get()
        
        current_tenant_id.set(self.tenant_id)
        current_user_id.set(self.user_id)
        current_user_email.set(self.user_email)
        current_request_id.set(self.request_id)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        current_tenant_id.set(self.prev_tenant_id)
        current_user_id.set(self.prev_user_id)
        current_user_email.set(self.prev_user_email)
        current_request_id.set(self.prev_request_id)

# Pre-configured loggers for different components
auth_logger = StructuredLogger("auth_logger")
data_logger = StructuredLogger("data_logger") 
system_logger = StructuredLogger("system_logger")
audit_logger = StructuredLogger("audit_logger")
security_logger = StructuredLogger("security_logger")

# Global logger instance
structured_logger = StructuredLogger("global_logger")

# Convenience functions for common logging patterns
def log_user_login(user_email: str, tenant_id: str, success: bool, details: Dict[str, Any] = None):
    """Log user authentication attempts"""
    with RequestContext(tenant_id=tenant_id, user_email=user_email):
        if success:
            auth_logger.info(
                EventCategory.AUTH,
                "user_login_success",
                f"User {user_email} successfully logged in",
                details=details or {},
                audit_required=True
            )
        else:
            auth_logger.warning(
                EventCategory.AUTH, 
                "user_login_failed",
                f"Failed login attempt for {user_email}",
                details=details or {},
                sensitive=True,
                audit_required=True
            )

def log_data_access(
    action: str, 
    resource: str,
    tenant_id: str,
    user_id: str,
    user_email: str,
    details: Dict[str, Any] = None,
    sensitive: bool = False
):
    """Log data access operations"""
    with RequestContext(tenant_id=tenant_id, user_id=user_id, user_email=user_email):
        data_logger.info(
            EventCategory.DATA_READ if action == "read" else EventCategory.DATA_UPDATE,
            f"data_{action}",
            f"User accessed {resource}",
            details=details or {},
            sensitive=sensitive,
            audit_required=True
        )

def log_data_export(
    resource: str,
    export_format: str,
    tenant_id: str, 
    user_id: str,
    user_email: str,
    record_count: int = None
):
    """Log data export operations (high security priority)"""
    with RequestContext(tenant_id=tenant_id, user_id=user_id, user_email=user_email):
        audit_logger.audit(
            "data_export",
            f"User exported {resource} data in {export_format} format", 
            details={
                "resource": resource,
                "export_format": export_format,
                "record_count": record_count,
                "exported_at": datetime.utcnow().isoformat()
            }
        )

def log_permission_change(
    target_user: str,
    action: str,
    permissions: List[str],
    tenant_id: str,
    admin_user_id: str,
    admin_email: str
):
    """Log RBAC permission changes"""
    with RequestContext(tenant_id=tenant_id, user_id=admin_user_id, user_email=admin_email):
        security_logger.audit(
            "permission_change",
            f"Permissions {action} for user {target_user}",
            details={
                "target_user": target_user,
                "action": action,
                "permissions": permissions,
                "admin_user": admin_email
            }
        )

def log_system_error(
    component: str,
    error: Exception,
    details: Dict[str, Any] = None
):
    """Log system errors with full context"""
    system_logger.error(
        EventCategory.SYSTEM,
        "system_error",
        f"Error in {component}: {str(error)}",
        error=error,
        details=details or {}
    )

def log_performance_metric(
    operation: str,
    duration_ms: float,
    tenant_id: str = None,
    details: Dict[str, Any] = None
):
    """Log performance metrics"""
    with RequestContext(tenant_id=tenant_id):
        system_logger.info(
            EventCategory.SYSTEM,
            "performance_metric",
            f"Operation {operation} completed in {duration_ms:.2f}ms",
            details={
                "operation": operation,
                "duration_ms": duration_ms,
                **(details or {})
            }
        )

# FastAPI middleware integration
async def set_request_context(tenant_id: str, user_id: str = None, user_email: str = None):
    """Set request context for correlation (used in middleware)"""
    current_tenant_id.set(tenant_id)
    current_user_id.set(user_id) 
    current_user_email.set(user_email)
    current_request_id.set(str(uuid.uuid4()))

# CLI for log analysis
if __name__ == "__main__":
    # Example usage
    logger = StructuredLogger("test_logger")
    
    # Test different log levels
    logger.info(
        EventCategory.SYSTEM,
        "test_log",
        "Testing structured logger",
        details={"test": True, "environment": "development"}
    )
    
    # Test audit logging
    logger.audit(
        "test_audit",
        "Testing audit functionality", 
        details={"sensitive_data": "will be masked"}
    )
    
    # Test error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        logger.error(
            EventCategory.SYSTEM,
            "test_error",
            "Testing error logging",
            error=e,
            details={"test_context": "error handling"}
        )
    


# ==========================================
# EXTENSÃO v1.4.0: Mascaramento de Secrets
# Adicionado: 2026-02-13
# ==========================================
import re

class SecretMaskingFilter(logging.Filter):
    """
    Filtro que mascara secrets em logs automaticamente
    Integração transparente com structured_logger existente
    """
    
    SENSITIVE_PATTERNS = [
        (r'mongodb://[^:]+:[^@]+@[^/\s"\']*', 'mongodb://***:***@***'),
        (r'Bearer\s+[a-zA-Z0-9_\-\.]+', 'Bearer ***MASKED***'),
        (r'\b(sk-[a-zA-Z0-9]{20,})', '***MASKED***'),
        (r'\b(pk-[a-zA-Z0-9]{20,})', '***MASKED***'),
        (r'(api[_-]?key["\']?\s*[:=]\s*["\']?)[a-zA-Z0-9\-_]{16,}', r'\1***MASKED***'),
        (r'("password"\s*:\s*")[^"]*', r'\1***MASKED***'),
        (r'("secret"\s*:\s*")[^"]*', r'\1***MASKED***'),
        (r'("token"\s*:\s*")[^"]*', r'\1***MASKED***'),
        (r'(postgresql://[^:]+:)[^@]+(@)', r'\1***MASKED***\2'),
        (r'(mysql://[^:]+:)[^@]+(@)', r'\1***MASKED***\2'),
    ]
    
    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = self._mask_sensitive_data(record.msg)
        
        if record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(self._mask_sensitive_data(arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)
        
        if hasattr(record, 'extra_fields') and isinstance(record.extra_fields, dict):
            record.extra_fields = self._mask_dict(record.extra_fields)
        
        if record.exc_info and record.exc_text:
            record.exc_text = self._mask_sensitive_data(record.exc_text)
        
        return True
    
    def _mask_sensitive_data(self, text):
        if not isinstance(text, str):
            return text
        masked = text
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            masked = re.sub(pattern, replacement, masked, flags=re.IGNORECASE)
        return masked
    
    def _mask_dict(self, data):
        if not isinstance(data, dict):
            return self._mask_sensitive_data(str(data))
        
        masked = {}
        sensitive_keys = {'password', 'secret', 'token', 'key', 'auth', 'credential', 
                         'api_key', 'apikey', 'access_token', 'refresh_token'}
        
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                masked[key] = '***MASKED***'
            elif isinstance(value, dict):
                masked[key] = self._mask_dict(value)
            elif isinstance(value, list):
                masked[key] = [self._mask_dict(item) if isinstance(item, dict) 
                              else self._mask_sensitive_data(str(item)) for item in value]
            elif isinstance(value, str):
                masked[key] = self._mask_sensitive_data(value)
            else:
                masked[key] = value
        return masked


def add_secret_masking():
    """Adiciona filtro de máscara ao logger existente"""
    logger = logging.getLogger("license_manager")
    
    for handler in logger.handlers:
        for f in handler.filters:
            if isinstance(f, SecretMaskingFilter):
                return
    
    mask_filter = SecretMaskingFilter()
    for handler in logger.handlers:
        handler.addFilter(mask_filter)
    
    logger.debug("Secret masking filter activated")


# Auto-executa ao importar o módulo
add_secret_masking()