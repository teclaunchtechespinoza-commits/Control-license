#!/usr/bin/env python3
"""
Tenant Isolation Validator - Verifica se todas as consultas MongoDB 
incluem filtro de tenant para garantir isolamento de dados
"""

import re
import sys
from pathlib import Path

# Padrões que indicam consultas MongoDB sem filtro de tenant
DANGEROUS_PATTERNS = [
    # find_one sem add_tenant_filter
    r'db\.\w+\.find_one\(\s*\{\s*"(?!tenant_id)[^}]*\}\s*\)(?![^}]*add_tenant_filter)',
    
    # find sem add_tenant_filter
    r'db\.\w+\.find\(\s*\{\s*"(?!tenant_id)[^}]*\}\s*\)(?![^}]*add_tenant_filter)',
    
    # update_one/update_many sem filtro
    r'db\.\w+\.update_(?:one|many)\(\s*\{\s*"(?!tenant_id)[^}]*\}',
    
    # delete_one/delete_many sem filtro
    r'db\.\w+\.delete_(?:one|many)\(\s*\{\s*"(?!tenant_id)[^}]*\}',
]

# Exceções permitidas (consultas que podem ser globais)
ALLOWED_EXCEPTIONS = [
    # Login pode ser global
    r'db\.users\.find_one\(\s*\{\s*"email"',
    
    # Tenants collection (global por natureza)
    r'db\.tenants\.', 
    
    # Sistema/startup queries
    r'# Sistema|# Startup|# Demo',
    
    # Auth/JWT queries
    r'# Auth|# JWT|get_current_user|startup_event',
]

def validate_tenant_isolation(file_path: Path) -> dict:
    """Valida isolamento de tenant em um arquivo Python"""
    results = {
        'file': str(file_path),
        'violations': [],
        'total_queries': 0,
        'safe_queries': 0
    }
    
    try:
        content = file_path.read_text()
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Ignorar comentários
            if line.strip().startswith('#'):
                continue
                
            # Verificar se é uma consulta MongoDB
            if 'db.' in line and ('find' in line or 'update' in line or 'delete' in line):
                results['total_queries'] += 1
                
                # Verificar se é uma exceção permitida
                is_exception = any(re.search(pattern, line) for pattern in ALLOWED_EXCEPTIONS)
                if is_exception:
                    results['safe_queries'] += 1
                    continue
                
                # Verificar padrões perigosos
                for pattern in DANGEROUS_PATTERNS:
                    if re.search(pattern, line):
                        results['violations'].append({
                            'line': line_num,
                            'code': line.strip(),
                            'issue': 'Missing tenant filter in MongoDB query'
                        })
                        break
                else:
                    # Se não encontrou violação, é segura
                    results['safe_queries'] += 1
                    
    except Exception as e:
        results['error'] = str(e)
    
    return results

def main():
    """Executa validação no backend"""
    backend_path = Path("/app/backend/server.py")
    
    if not backend_path.exists():
        print("❌ Arquivo backend/server.py não encontrado")
        sys.exit(1)
    
    print("🔍 Validando isolamento de tenant...")
    results = validate_tenant_isolation(backend_path)
    
    print(f"\n📊 Relatório de Validação:")
    print(f"├── Arquivo: {results['file']}")
    print(f"├── Total de consultas: {results['total_queries']}")
    print(f"├── Consultas seguras: {results['safe_queries']}")
    print(f"└── Violações encontradas: {len(results['violations'])}")
    
    if results['violations']:
        print(f"\n🚨 VIOLAÇÕES CRÍTICAS DE ISOLAMENTO:")
        for i, violation in enumerate(results['violations'], 1):
            print(f"\n{i}. Linha {violation['line']}:")
            print(f"   Código: {violation['code']}")
            print(f"   Problema: {violation['issue']}")
    
    # Calcular score de segurança
    if results['total_queries'] > 0:
        safety_score = (results['safe_queries'] / results['total_queries']) * 100
        print(f"\n🎯 Score de Segurança: {safety_score:.1f}%")
        
        if safety_score >= 95:
            print("✅ EXCELENTE: Sistema altamente seguro")
            sys.exit(0)
        elif safety_score >= 85:
            print("⚠️ BOM: Algumas melhorias necessárias")
            sys.exit(0)  
        else:
            print("🚨 CRÍTICO: Muitas violações de segurança")
            sys.exit(1)
    else:
        print("❓ Nenhuma consulta MongoDB encontrada")

if __name__ == "__main__":
    main()