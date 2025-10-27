#!/usr/bin/env python3
"""Adicionar 10 licenças com status 'active' para teste"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timedelta, timezone
import uuid

async def add_active_licenses():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client.license_db
    
    print("🔧 Adicionando 10 licenças com status 'active'...")
    
    # Pegar admin
    admin = await db.users.find_one({"email": "admin@demo.com"})
    if not admin:
        print("❌ Admin não encontrado")
        return
    
    admin_id = admin.get('id')
    now = datetime.now(timezone.utc)
    
    # Criar 10 licenças ativas
    for i in range(1, 11):
        license_data = {
            "id": str(uuid.uuid4()),
            "name": f"Licença Ativa {i}",
            "description": f"Licença de teste #{i} com status ACTIVE",
            "license_key": f"LIC-ACTIVE-{uuid.uuid4().hex[:16].upper()}",
            "status": "active",  # STATUS ATIVO
            "max_users": 10 + i,
            "expires_at": now + timedelta(days=365),  # Expira em 1 ano
            "features": ["feature1", "feature2"],
            "tenant_id": "default",
            "created_by": admin_id,
            "created_at": now,
            "updated_at": now
        }
        await db.licenses.insert_one(license_data)
        print(f"✅ Criada: {license_data['name']}")
    
    # Estatísticas
    total = await db.licenses.count_documents({"tenant_id": "default"})
    active = await db.licenses.count_documents({"tenant_id": "default", "status": "active"})
    
    print(f"\n📊 Total: {total} licenças")
    print(f"📊 Ativas: {active} licenças")
    print("🎉 CONCLUÍDO!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_active_licenses())
