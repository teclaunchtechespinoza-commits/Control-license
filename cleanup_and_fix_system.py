#!/usr/bin/env python3
"""
SCRIPT DE LIMPEZA E CORREÇÃO COMPLETA DO SISTEMA
- Remove duplicidades
- Remove dados corrompidos
- Valida integridade
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from collections import defaultdict
import os

async def cleanup_system():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.license_management
    
    print("="*80)
    print("🔧 LIMPEZA E CORREÇÃO COMPLETA DO SISTEMA")
    print("="*80)
    
    # 1. REMOVER LICENÇAS DUPLICADAS
    print("\n1️⃣ Removendo licenças duplicadas...")
    licenses = await db.licenses.find({}).to_list(length=None)
    seen_keys = {}
    duplicates_removed = 0
    
    for lic in licenses:
        key = lic.get('license_key')
        if not key:
            # Remover licenças sem chave
            await db.licenses.delete_one({'_id': lic['_id']})
            duplicates_removed += 1
            print(f"   ❌ Removida licença sem chave: {lic.get('name', 'Unknown')}")
            continue
        
        if key in seen_keys:
            # Duplicada - manter a mais recente
            existing = seen_keys[key]
            if lic.get('created_at', '') > existing.get('created_at', ''):
                # Nova é mais recente - remover antiga
                await db.licenses.delete_one({'_id': existing['_id']})
                seen_keys[key] = lic
            else:
                # Antiga é mais recente - remover nova
                await db.licenses.delete_one({'_id': lic['_id']})
            duplicates_removed += 1
            print(f"   ❌ Removida licença duplicada: {key}")
        else:
            seen_keys[key] = lic
    
    print(f"   ✅ {duplicates_removed} licenças duplicadas removidas")
    
    # 2. CORRIGIR LICENÇAS SEM tenant_id
    print("\n2️⃣ Corrigindo licenças sem tenant_id...")
    result = await db.licenses.update_many(
        {"$or": [{"tenant_id": {"$exists": False}}, {"tenant_id": None}]},
        {"$set": {"tenant_id": "default"}}
    )
    print(f"   ✅ {result.modified_count} licenças corrigidas com tenant_id='default'")
    
    # 3. REMOVER USUÁRIOS DUPLICADOS
    print("\n3️⃣ Removendo usuários duplicados...")
    users = await db.users.find({}).to_list(length=None)
    seen_emails = {}
    users_removed = 0
    
    for user in users:
        email = user.get('email')
        if not email:
            # Remover usuários sem email
            await db.users.delete_one({'_id': user['_id']})
            users_removed += 1
            continue
        
        if email in seen_emails:
            # Duplicado - manter o mais recente
            existing = seen_emails[email]
            if user.get('created_at', '') > existing.get('created_at', ''):
                await db.users.delete_one({'_id': existing['_id']})
                seen_emails[email] = user
            else:
                await db.users.delete_one({'_id': user['_id']})
            users_removed += 1
            print(f"   ❌ Removido usuário duplicado: {email}")
        else:
            seen_emails[email] = user
    
    print(f"   ✅ {users_removed} usuários duplicados removidos")
    
    # 4. CORRIGIR USUÁRIOS SEM tenant_id
    print("\n4️⃣ Corrigindo usuários sem tenant_id...")
    result = await db.users.update_many(
        {"$or": [{"tenant_id": {"$exists": False}}, {"tenant_id": None}]},
        {"$set": {"tenant_id": "default"}}
    )
    print(f"   ✅ {result.modified_count} usuários corrigidos")
    
    # 5. REMOVER CONVITES EXPIRADOS/CORROMPIDOS
    print("\n5️⃣ Limpando convites corrompidos...")
    result = await db.invitations.delete_many({
        "$or": [
            {"email": {"$exists": False}},
            {"email": None},
            {"token_hash": {"$exists": False}},
            {"token_hash": None}
        ]
    })
    print(f"   ✅ {result.deleted_count} convites corrompidos removidos")
    
    # 6. ESTATÍSTICAS FINAIS
    print("\n📊 ESTATÍSTICAS FINAIS:")
    stats = {
        'licenças': await db.licenses.count_documents({}),
        'licenças (tenant=default)': await db.licenses.count_documents({'tenant_id': 'default'}),
        'usuários': await db.users.count_documents({}),
        'convites': await db.invitations.count_documents({}),
        'produtos': await db.products.count_documents({}),
        'categorias': await db.categories.count_documents({})
    }
    
    for key, val in stats.items():
        print(f"   {key}: {val}")
    
    print("\n" + "="*80)
    print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
    print("="*80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_system())
