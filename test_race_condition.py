#!/usr/bin/env python3
"""
Test script for license creation and listing race condition fix
"""

import sys
import os
sys.path.append('/app')

from backend_test import LicenseManagementAPITester

def main():
    """Run the specific race condition test"""
    print("🚀 TESTE FINAL - CORREÇÃO DE RACE CONDITION")
    print("="*60)
    
    tester = LicenseManagementAPITester()
    
    # Run the specific test
    success = tester.test_license_creation_and_listing_race_condition_fix()
    
    # Print final results
    print("\n" + "="*60)
    print("RESULTADO FINAL")
    print("="*60)
    
    if success:
        print("🎉 TESTE APROVADO - Race condition foi RESOLVIDA!")
        return 0
    else:
        print("❌ TESTE FALHOU - Race condition ainda existe!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)