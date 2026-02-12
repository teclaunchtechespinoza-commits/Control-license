#!/usr/bin/env python3
"""
Gerador de Secrets Seguros - License Manager v1.4.0
Uso: python scripts/setup_secrets.py
"""
import secrets
import string


def generate_secret(length=48):
    """Gera secret criptograficamente seguro"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main():
    print("🔐 Gerador de Secrets - License Manager v1.4.0\n")
    
    secrets_needed = {
        "JWT_SECRET_KEY": 48,
        "JWT_REFRESH_SECRET_KEY": 48,
        "SECRET_KEY": 48,
        "INITIAL_SUPERADMIN_PASSWORD": 24,
    }
    
    print("Copie estes valores para seu arquivo .env:\n")
    print("="*60)
    
    for name, length in secrets_needed.items():
        value = generate_secret(length)
        print(f"{name}={value}")
    
    print("="*60)
    print("\n⚠️  IMPORTANTE:")
    print("   1. Copie para .env imediatamente")
    print("   2. Nunca compartilhe estes valores")
    print("   3. Faça backup seguro do .env")


if __name__ == "__main__":
    main()
