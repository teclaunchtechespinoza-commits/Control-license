#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_test import LicenseManagementAPITester

def main():
    """Run the critical user registration test"""
    tester = LicenseManagementAPITester()
    
    print("🚀 TESTE CRÍTICO DO SISTEMA DE REGISTRO DE USUÁRIOS")
    print("="*80)
    print("PROBLEMA REPORTADO: 'Registration failed' com dados específicos")
    print("- Nome: Edson")
    print("- Email: espinozatecnico@gmail.com")
    print("- Senha: qualquer senha de teste")
    print("="*80)
    
    # Run the critical registration test
    exit_code = tester.run_critical_user_registration_test()
    
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)