#!/usr/bin/env python3
"""
Auditoria de Segurança - License Manager v1.4.0
Uso: python scripts/security_audit.py
Retorna: 0 (OK) ou 1 (problemas encontrados)
"""
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Tuple


class SecurityAuditor:
    """Auditoria de segurança para arquitetura Emergent (server.py)"""
    
    CRITICAL_PATTERNS: List[Tuple[str, str]] = [
        (r'=\s*["\']mongodb://[^:]+:[^@]+@', "MongoDB URL hardcoded"),
        (r'=\s*["\']sk-[a-zA-Z0-9]{20,}', "API Key (sk-*) hardcoded"),
        (r'=\s*["\']pk-[a-zA-Z0-9]{20,}', "API Key (pk-*) hardcoded"),
        (r'password\s*=\s*["\'][^"\']{8,}["\']', "Password hardcoded"),
        (r'secret[_\w]*\s*=\s*["\'][^"\']{8,}["\']', "Secret hardcoded"),
        (r'token\s*=\s*["\'][^"\']{20,}["\']', "Token hardcoded"),
        (r'print\s*\([^)]*(password|secret|mongodb://)', "Print de dados sensíveis"),
    ]
    
    WARNING_PATTERNS: List[Tuple[str, str]] = [
        (r'allow_origins\s*=\s*\[["\']?\*["\']?\]', "CORS permite '*'"),
        (r'debug\s*=\s*True', "Debug=True hardcoded"),
        (r'#.*TODO.*(?:security|secret|password)', "TODO relacionado a segurança"),
    ]
    
    def __init__(self):
        self.root = Path(__file__).parent.parent.resolve()
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def scan_server_py(self) -> None:
        """Escaneia server.py (arquivo principal)"""
        server_file = self.root / "server.py"
        
        if not server_file.exists():
            self.issues.append("server.py não encontrado no diretório raiz")
            return
        
        content = server_file.read_text()
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, desc in self.CRITICAL_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    snippet = line.strip()[:60]
                    self.issues.append(f"server.py:{line_num} - {desc}\n    {snippet}")
                    break
            
            for pattern, desc in self.WARNING_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    self.warnings.append(f"server.py:{line_num} - {desc}")
        
        if 'os.environ' in content or 'os.getenv' in content:
            self.info.append("✅ Usa variáveis de ambiente (os.environ/os.getenv)")
        else:
            self.warnings.append("Não detectado uso de variáveis de ambiente")
        
        if 'SecretMaskingFilter' in content or 'add_secret_masking' in content:
            self.info.append("✅ Filtro de mascaramento detectado")
        
        print(f"✅ server.py auditado ({len(lines)} linhas)")
    
    def check_env_security(self) -> None:
        """Verifica proteção do .env"""
        gitignore = self.root / ".gitignore"
        env_file = self.root / ".env"
        env_example = self.root / ".env.example"
        
        # Também verifica gitignore na raiz do projeto
        root_gitignore = self.root.parent / ".gitignore"
        
        gitignore_content = ""
        if gitignore.exists():
            gitignore_content = gitignore.read_text()
        if root_gitignore.exists():
            gitignore_content += root_gitignore.read_text()
        
        if '.env' in gitignore_content:
            self.info.append("✅ .env está no .gitignore")
        else:
            self.issues.append("❌ .env NÃO está no .gitignore")
        
        if env_file.exists():
            try:
                result = subprocess.run(
                    ["git", "-C", str(self.root), "ls-files", ".env"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.stdout.strip():
                    self.issues.append("🚨 CRÍTICO: .env está tracked pelo Git!\n    Execute: git rm --cached .env && git commit -m 'Remove .env do tracking'")
                else:
                    self.info.append("✅ .env não está no Git")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.warnings.append("⚠️  Não foi possível verificar status do .env no Git")
        
        if env_example.exists():
            self.info.append("✅ .env.example existe")
        else:
            self.warnings.append("⚠️  .env.example não encontrado (recomendado)")
        
        if env_file.exists():
            content = env_file.read_text()
            placeholders = ['change_me', 'your_', 'xxx', '123456']
            if any(p in content.lower() for p in placeholders):
                self.warnings.append("⚠️  .env contém valores padrão/placeholder")
    
    def check_existing_security_modules(self) -> None:
        """Verifica módulos de segurança existentes"""
        modules = {
            'rate_limiting.py': 'Rate Limiting',
            'security_headers.py': 'Security Headers',
            'structured_logger.py': 'Structured Logging',
            'logging_middleware.py': 'Logging Middleware',
        }
        
        for filename, description in modules.items():
            filepath = self.root / filename
            if filepath.exists():
                size = filepath.stat().st_size
                self.info.append(f"✅ {description}: {filename} ({size/1024:.1f}KB)")
            else:
                self.warnings.append(f"⚠️  {description} não encontrado: {filename}")
    
    def generate_report(self) -> bool:
        """Gera relatório e retorna status"""
        print("\n" + "="*70)
        print("🔒 RELATÓRIO DE AUDITORIA DE SEGURANÇA")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Diretório: {self.root}")
        print("="*70)
        
        if self.info:
            print("\n📋 Componentes detectados:")
            for item in self.info:
                print(f"   {item}")
        
        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} AVISOS (não críticos):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.issues:
            print(f"\n🚨 {len(self.issues)} PROBLEMAS CRÍTICOS:")
            for i, issue in enumerate(self.issues, 1):
                print(f"\n   {i}. {issue}")
            
            print("\n" + "="*70)
            print("📋 AÇÕES CORRETIVAS:")
            print("   1. Mover secrets hardcoded para variáveis de ambiente")
            print("   2. Usar: os.environ.get('NOME_VAR') no código")
            print("   3. Adicionar .env ao .gitignore se necessário")
            print("   4. Executar: git rm --cached .env (se no Git)")
            print("="*70)
            return False
        
        print("\n" + "="*70)
        print("✅ AUDITORIA APROVADA")
        print("   Nenhum problema crítico de segurança detectado")
        print("="*70)
        return True


def main() -> int:
    """Entry point"""
    print("🔍 Iniciando auditoria de segurança...\n")
    
    auditor = SecurityAuditor()
    auditor.scan_server_py()
    auditor.check_env_security()
    auditor.check_existing_security_modules()
    
    success = auditor.generate_report()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
