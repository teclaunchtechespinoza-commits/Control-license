#!/usr/bin/env python3
"""
Script de migração: Adicionar tenant_id às licenças existentes
PROBLEMA: Licenças antigas não têm tenant_id, causando erro 403 'Fora do escopo'
SOLUÇÃO: Adicionar tenant_id='default' a todas as licenças sem tenant_id
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

async def migrate_licenses():
    """Adiciona tenant_id às licenças que não têm"""
    # Conectar ao MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.license_db
    
    print("🔍 Verificando licenças sem tenant_id...")
    
    # Contar licenças sem tenant_id
    licenses_without_tenant = await db.licenses.count_documents({
        "$or": [
            {"tenant_id": {"$exists": False}},
            {"tenant_id": None}
        ]
    })
    
    print(f"📊 Encontradas {licenses_without_tenant} licenças sem tenant_id")
    
    if licenses_without_tenant == 0:
        print("✅ Todas as licenças já têm tenant_id")
        return
    
    # Atualizar licenças sem tenant_id
    result = await db.licenses.update_many(
        {
            "$or": [
                {"tenant_id": {"$exists": False}},
                {"tenant_id": None}
            ]
        },
        {
            "$set": {
                "tenant_id": "default",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    print(f"✅ Atualizadas {result.modified_count} licenças com tenant_id='default'")
    
    # Verificar resultado
    remaining = await db.licenses.count_documents({
        "$or": [
            {"tenant_id": {"$exists": False}},
            {"tenant_id": None}
        ]
    })
    
    if remaining == 0:
        print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    else:
        print(f"⚠️ Ainda restam {remaining} licenças sem tenant_id")
    
    # Mostrar estatísticas
    total_licenses = await db.licenses.count_documents({})
    licenses_with_default = await db.licenses.count_documents({"tenant_id": "default"})
    
    print(f"\n📊 ESTATÍSTICAS FINAIS:")
    print(f"   Total de licenças: {total_licenses}")
    print(f"   Licenças com tenant_id='default': {licenses_with_default}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_licenses())
