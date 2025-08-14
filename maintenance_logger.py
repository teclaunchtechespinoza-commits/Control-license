import os
import json
import datetime
from typing import Dict, Any, Optional

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return super().default(obj)

class MaintenanceLogger:
    def __init__(self):
        self.log_file = "/app/maintenance_log.txt"
        
    def log(self, level: str, module: str, action: str, details: Dict[str, Any], error: Optional[str] = None):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "module": module,
            "action": action,
            "details": details
        }
        
        if error:
            log_entry["error"] = error
            
        try:
            # Use DateTimeEncoder for the entire log_entry, not just details
            full_entry_json = json.dumps(log_entry, cls=DateTimeEncoder, ensure_ascii=False)
            details_json = json.dumps(details, cls=DateTimeEncoder, ensure_ascii=False)
        except Exception as e:
            details_json = f"{{serialization_error: {str(e)}}}"
            
        log_line = f"[{timestamp}] [{level}] {module} - {action}: {details_json}"
        if error:
            log_line += f" ERROR: {error}"
        log_line += "\n"
        
        # Write to file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass  # Don't let logging errors break the main functionality
            
        # Also print to console
        print(log_line.strip())
    
    def info(self, module: str, action: str, details: Dict[str, Any]):
        self.log("INFO", module, action, details)
        
    def error(self, module: str, action: str, details: Dict[str, Any], error: str):
        self.log("ERROR", module, action, details, error)
        
    def debug(self, module: str, action: str, details: Dict[str, Any]):
        self.log("DEBUG", module, action, details)

# Global logger instance
logger = MaintenanceLogger()