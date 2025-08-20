#!/usr/bin/env python3

import sys
from backend_test import LicenseManagementAPITester

def main():
    """Run the critical RBAC and maintenance module validation test"""
    tester = LicenseManagementAPITester()
    return tester.run_critical_rbac_maintenance_validation()

if __name__ == "__main__":
    sys.exit(main())