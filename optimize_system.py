#!/usr/bin/env python3
"""
OTIMIZAÇÃO E LIMPEZA DO SISTEMA
- Limpa cache Redis
- Remove dados temporários
- Otimiza índices MongoDB
- Melhora performance
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import redis

async def optimize_system():
    print("="*80)
    print("🚀 OTIMIZAÇÃO E LIMPEZA DO SISTEMA")
    print("="*80)
    
    # 1. LIMPAR CACHE REDIS
    print("\n1️⃣ Limpando cache Redis...")
    try:
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        keys_count = redis_client.dbsize()
        if keys_count > 0:
            redis_client.flushdb()
            print(f"   ✅ {keys_count} chaves removidas do Redis")
        else:
            print("   ✅ Cache Redis já estava limpo")
    except Exception as e:
        print(f"   ⚠️ Redis não disponível ou já limpo: {e}")
    
    # 2. OTIMIZAR ÍNDICES MONGODB
    print("\n2️⃣ Otimizando índices MongoDB...")
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.license_management
    
    # Índices essenciais
    indexes_created = 0
    
    # Users
    try:
        await db.users.create_index([("email", 1)], unique=True)
        await db.users.create_index([("tenant_id", 1)])
        await db.users.create_index([("id", 1)])
        indexes_created += 3
        print("   ✅ Índices de users otimizados")
    except:
        print("   ✅ Índices de users já existem")
    
    # Licenses
    try:
        await db.licenses.create_index([("tenant_id", 1)])
        await db.licenses.create_index([("id", 1)])
        await db.licenses.create_index([("license_key", 1)])
        await db.licenses.create_index([("status", 1)])
        indexes_created += 4
        print("   ✅ Índices de licenses otimizados")
    except:
        print("   ✅ Índices de licenses já existem")
    
    # 3. REMOVER SESSÕES EXPIRADAS
    print("\n3️⃣ Removendo sessões expiradas...")
    from datetime import datetime, timedelta, timezone
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    result = await db.sessions.delete_many({
        "created_at": {"$lt": cutoff_date}
    })
    print(f"   ✅ {result.deleted_count} sessões antigas removidas")
    
    # 4. REMOVER CONVITES EXPIRADOS
    print("\n4️⃣ Removendo convites expirados...")
    result = await db.invitations.delete_many({
        "$and": [
            {"revoked": True},
            {"created_at": {"$lt": cutoff_date}}
        ]
    })
    print(f"   ✅ {result.deleted_count} convites antigos removidos")
    
    # 5. ESTATÍSTICAS FINAIS
    print("\n📊 ESTATÍSTICAS PÓS-OTIMIZAÇÃO:")
    stats = {
        'Usuários': await db.users.count_documents({}),
        'Licenças': await db.licenses.count_documents({}),
        'Sessões ativas': await db.sessions.count_documents({}),
        'Convites ativos': await db.invitations.count_documents({"revoked": False}),
    }
    
    for key, val in stats.items():
        print(f"   {key}: {val}")
    
    print("\n" + "="*80)
    print("✅ OTIMIZAÇÃO CONCLUÍDA!")
    print("="*80)
    print("\n💡 RECOMENDAÇÕES:")
    print("   - Reinicie o backend para aplicar otimizações")
    print("   - Limpe cache do navegador (Ctrl+Shift+Delete)")
    print("   - Sistema deve estar mais rápido e responsivo")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(optimize_system())
