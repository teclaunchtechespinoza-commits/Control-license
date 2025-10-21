#!/usr/bin/env python3
"""
Test script specifically for license endpoint inconsistencies
"""
import sys
import os
sys.path.append('/app')

from backend_test import LicenseManagementAPITester

if __name__ == "__main__":
    tester = LicenseManagementAPITester()
    
    # Run only the critical license inconsistencies test
    print("🚀 EXECUTANDO TESTE CRÍTICO DE INCONSISTÊNCIAS DE LICENÇAS")
    print("="*80)
    
    success = tester.test_license_endpoints_critical_inconsistencies()
    
    # Print summary
    tester.print_summary()
    
    # Exit with appropriate code
    if success:
        print("\n✅ Teste concluído com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Teste falhou!")
        sys.exit(1)