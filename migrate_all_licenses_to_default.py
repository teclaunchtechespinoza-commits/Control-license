#!/usr/bin/env python3
"""
Migração URGENTE: Atualizar TODAS as licenças para tenant_id='default'
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def migrate():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client.license_db
    
    print("🔧 MIGRAÇÃO URGENTE: Atualizando tenant_id para todas as licenças")
    
    # Atualizar TODAS as licenças para tenant_id='default'
    result = await db.licenses.update_many(
        {},  # Todas as licenças
        {"$set": {"tenant_id": "default"}}
    )
    
    print(f"✅ {result.modified_count} licenças atualizadas")
    
    # Atualizar TODOS os usuários para tenant_id='default'
    result2 = await db.users.update_many(
        {},
        {"$set": {"tenant_id": "default"}}
    )
    
    print(f"✅ {result2.modified_count} usuários atualizados")
    
    # Atualizar TODOS os clientes para tenant_id='default'
    result3 = await db.clientes_pf.update_many(
        {},
        {"$set": {"tenant_id": "default"}}
    )
    result4 = await db.clientes_pj.update_many(
        {},
        {"$set": {"tenant_id": "default"}}
    )
    
    print(f"✅ {result3.modified_count} clientes PF atualizados")
    print(f"✅ {result4.modified_count} clientes PJ atualizados")
    
    # Estatísticas
    total = await db.licenses.count_documents({})
    with_default = await db.licenses.count_documents({"tenant_id": "default"})
    
    print(f"\n📊 Total: {total}, com tenant_id=default: {with_default}")
    print("🎉 MIGRAÇÃO CONCLUÍDA!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate())
