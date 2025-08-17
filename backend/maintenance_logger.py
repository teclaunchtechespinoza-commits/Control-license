"""
Maintenance Logger - Sistema de logging para manutenção e debugging
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class MaintenanceLogger:
    """
    Sistema de logging para manutenção e debugging
    """
    
    def __init__(self):
        self.logger = logging.getLogger("maintenance")
        self.logger.setLevel(logging.DEBUG)
        
        # Create console handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log(self, event_type: str, details: Optional[Dict[str, Any]] = None, level: LogLevel = LogLevel.INFO):
        """
        Log an event with details
        """
        try:
            log_entry = {
                "timestamp": datetime.utcnow(),
                "event_type": event_type,
                "details": details or {}
            }
            
            # Use DateTimeEncoder for JSON serialization
            message = json.dumps(log_entry, cls=DateTimeEncoder, ensure_ascii=False)
            
            # Log based on level
            if level == LogLevel.DEBUG:
                self.logger.debug(message)
            elif level == LogLevel.INFO:
                self.logger.info(message)
            elif level == LogLevel.WARNING:
                self.logger.warning(message)
            elif level == LogLevel.ERROR:
                self.logger.error(message)
            elif level == LogLevel.CRITICAL:
                self.logger.critical(message)
                
        except Exception as e:
            # Fallback logging if JSON serialization fails
            self.logger.error(f"Maintenance logging error: {e}")
            self.logger.info(f"Event: {event_type}, Details: {str(details)}")
    
    def debug(self, event_type: str, details: Optional[Dict[str, Any]] = None):
        """Log debug event"""
        self.log(event_type, details, LogLevel.DEBUG)
    
    def info(self, event_type: str, details: Optional[Dict[str, Any]] = None):
        """Log info event"""
        self.log(event_type, details, LogLevel.INFO)
    
    def warning(self, event_type: str, details: Optional[Dict[str, Any]] = None):
        """Log warning event"""
        self.log(event_type, details, LogLevel.WARNING)
    
    def error(self, event_type: str, details: Optional[Dict[str, Any]] = None):
        """Log error event"""
        self.log(event_type, details, LogLevel.ERROR)
    
    def critical(self, event_type: str, details: Optional[Dict[str, Any]] = None):
        """Log critical event"""
        self.log(event_type, details, LogLevel.CRITICAL)