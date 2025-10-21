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
    
    # Print basic summary
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    print(f"Total de testes executados: {tester.tests_run}")
    print(f"Testes aprovados: {tester.tests_passed}")
    print(f"Testes falharam: {tester.tests_run - tester.tests_passed}")
    
    if tester.tests_run > 0:
        success_rate = (tester.tests_passed / tester.tests_run) * 100
        print(f"Taxa de sucesso: {success_rate:.1f}%")
    
    # Exit with appropriate code
    if success:
        print("\n✅ Teste concluído com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Teste falhou!")
        sys.exit(1)