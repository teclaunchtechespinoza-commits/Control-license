#!/usr/bin/env python3
"""
CRITICAL SECURITY TOOL: MongoDB Tenant Filter Validator
Scans for MongoDB operations without proper tenant isolation

Usage: python tools/check_tenant_filters.py backend/
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Pattern to find MongoDB operations
MONGO_OPERATION_PATTERN = re.compile(
    r'db\.([a-zA-Z_][a-zA-Z0-9_]*)\.'
    r'(find|find_one|update_one|update_many|delete_one|delete_many|'
    r'insert_one|insert_many|aggregate|count_documents|replace_one)\s*\('
)

# Patterns that indicate proper tenant scoping
TENANT_SAFE_PATTERNS = [
    r'add_tenant_filter',
    r'get_tenant_safe_filter', 
    r'enforce_super_admin_or_tenant_filter',
    r'tenant_id.*in.*query',
    r'filter.*tenant_id',
    r'"tenant_id"',
    r"'tenant_id'",
]

# Allowed exceptions (operations that can be global)
GLOBAL_OPERATION_EXCEPTIONS = [
    # System operations
    r'db\.tenants\.',
    r'db\.system\.',
    r'# System|# Global|# Admin',
    
    # Auth operations (users can be found globally for login)
    r'email.*login|login.*email',
    r'find_one.*email.*password',
    
    # RBAC/System setup
    r'role.*super_admin|super_admin.*role',
    r'initialize|startup|bootstrap',
    
    # Demo/seed operations
    r'demo|seed|example',
]

def scan_file_for_unsafe_operations(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Scan a Python file for MongoDB operations without tenant filters
    Returns list of (line_number, line_content, operation)
    """
    violations = []
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            # Find MongoDB operations
            for match in MONGO_OPERATION_PATTERN.finditer(line):
                collection = match.group(1)
                operation = match.group(2)
                full_operation = f"db.{collection}.{operation}"
                
                # Check if this is a global operation exception
                is_global_exception = any(
                    re.search(pattern, line, re.IGNORECASE) 
                    for pattern in GLOBAL_OPERATION_EXCEPTIONS
                )
                
                if is_global_exception:
                    continue
                
                # Check if operation has proper tenant scoping
                # Look in the current line and surrounding context
                start_line = max(0, line_num - 3)
                end_line = min(len(lines), line_num + 2)
                context = '\n'.join(lines[start_line:end_line])
                
                has_tenant_scoping = any(
                    re.search(pattern, context, re.IGNORECASE)
                    for pattern in TENANT_SAFE_PATTERNS
                )
                
                if not has_tenant_scoping:
                    violations.append((line_num, line.strip(), full_operation))
                    
    except Exception as e:
        print(f"Error scanning {file_path}: {e}", file=sys.stderr)
    
    return violations

def scan_directory(directory: Path) -> dict:
    """Scan all Python files in directory for tenant violations"""
    results = {}
    total_files = 0
    total_violations = 0
    
    for file_path in directory.rglob("*.py"):
        if '__pycache__' in str(file_path):
            continue
            
        total_files += 1
        violations = scan_file_for_unsafe_operations(file_path)
        
        if violations:
            results[str(file_path)] = violations
            total_violations += len(violations)
    
    return {
        'files': results,
        'summary': {
            'total_files_scanned': total_files,
            'files_with_violations': len(results),
            'total_violations': total_violations
        }
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/check_tenant_filters.py <directory>")
        print("Example: python tools/check_tenant_filters.py backend/")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    if not directory.exists():
        print(f"Directory {directory} does not exist")
        sys.exit(1)
    
    print("🔍 CRITICAL SECURITY SCAN: Checking MongoDB tenant isolation...")
    print(f"📁 Scanning directory: {directory}")
    print("-" * 60)
    
    results = scan_directory(directory)
    
    if not results['files']:
        print("✅ SUCCESS: All MongoDB operations appear to be tenant-scoped!")
        print(f"📊 Scanned {results['summary']['total_files_scanned']} files")
        sys.exit(0)
    
    # Print violations
    print("🚨 CRITICAL SECURITY VIOLATIONS FOUND:")
    print(f"📊 Files scanned: {results['summary']['total_files_scanned']}")
    print(f"📊 Files with violations: {results['summary']['files_with_violations']}")
    print(f"📊 Total violations: {results['summary']['total_violations']}")
    print("-" * 60)
    
    for file_path, violations in results['files'].items():
        print(f"\n🔴 {file_path}:")
        for line_num, line_content, operation in violations:
            print(f"  Line {line_num}: {operation}")
            print(f"    Code: {line_content}")
    
    print("\n" + "=" * 60)
    print("🛠️  CRITICAL FIXES REQUIRED:")
    print("1. Add tenant_id to all MongoDB queries using add_tenant_filter()")  
    print("2. Use require_tenant() dependency on all data endpoints")
    print("3. Apply get_tenant_safe_filter() for user-based queries")
    print("4. Review each violation for proper tenant isolation")
    print("\n💡 Example fix:")
    print("  BEFORE: db.licenses.find({'status': 'active'})")
    print("  AFTER:  db.licenses.find(add_tenant_filter({'status': 'active'}, tenant_id))")
    
    sys.exit(1)

if __name__ == "__main__":
    main()