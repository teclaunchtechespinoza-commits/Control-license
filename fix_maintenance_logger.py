#!/usr/bin/env python3
"""
Script to fix maintenance logger imports and usage in server.py
"""

import re

def fix_maintenance_logger():
    # Read the file
    with open('/app/backend/server.py', 'r') as f:
        content = f.read()
    
    # Replace the import section
    old_import = """# Import maintenance logger
import sys
sys.path.append('/app')
from maintenance_logger import logger as maint_logger"""
    
    new_import = """# Import maintenance logger
from maintenance_logger import MaintenanceLogger

# Initialize maintenance logger
maintenance_logger = MaintenanceLogger()"""
    
    content = content.replace(old_import, new_import)
    
    # Replace all occurrences of maint_logger with maintenance_logger
    content = content.replace('maint_logger', 'maintenance_logger')
    
    # Write the file back
    with open('/app/backend/server.py', 'w') as f:
        f.write(content)
    
    print("Successfully updated maintenance logger imports and usage!")

if __name__ == "__main__":
    fix_maintenance_logger()