#!/usr/bin/env python3
"""
Test script specifically for SUB-FASE 2.4 - Sistema de Aggregation Queries
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_test import LicenseManagementAPITester

def main():
    """Run SUB-FASE 2.4 aggregation tests"""
    print("🚀 STARTING SUB-FASE 2.4 - SISTEMA DE AGGREGATION QUERIES TESTS")
    print("="*80)
    
    # Initialize tester
    tester = LicenseManagementAPITester()
    
    # Run the aggregation test
    success = tester.test_sub_fase_2_4_aggregation_queries_system()
    
    # Print final summary
    print("\n" + "="*80)
    print("FINAL AGGREGATION TEST RESULTS")
    print("="*80)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"📊 Success rate: {success_rate:.1f}%")
    
    if success and success_rate >= 80:
        print("\n🎉 SUB-FASE 2.4 AGGREGATION TESTS PASSED!")
        print("   The aggregation query system is working correctly.")
        return 0
    else:
        print(f"\n❌ SUB-FASE 2.4 AGGREGATION TESTS FAILED!")
        print(f"   Some issues were found with the aggregation system.")
        return 1

if __name__ == "__main__":
    sys.exit(main())