#!/usr/bin/env python3

import sys
import os
sys.path.append('/app')

from backend_test import LicenseManagementAPITester

def main():
    """Run RBAC system testing as requested in review"""
    print("🚀 STARTING RBAC SYSTEM MVP TESTING")
    print("="*60)
    print("🎯 OBJECTIVE: Retest RBAC system after admin permission fix")
    print("📋 FOCUS: Verify admin@demo.com now has Super Admin role with '*' permission")
    print("🔧 VERIFICATION: Confirm admin can access RBAC endpoints without 403 errors")
    print()
    
    tester = LicenseManagementAPITester()
    
    # Run RBAC MVP test
    result = tester.test_rbac_system_mvp()
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())