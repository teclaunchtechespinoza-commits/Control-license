#!/usr/bin/env python3
"""
Criar admin user e licenças de teste diretamente no MongoDB
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_data():
    """Criar admin e licenças de teste"""
    # Conectar ao MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.license_db
    
    print("🔧 Criando dados de teste...")
    
    # 1. Criar admin user se não existir
    admin_exists = await db.users.find_one({"email": "admin@demo.com"})
    if not admin_exists:
        admin_data = {
            "id": str(uuid.uuid4()),
            "email": "admin@demo.com",
            "full_name": "Admin Demo",
            "password_hash": pwd_context.hash("admin123"),
            "role": "admin",
            "is_active": True,
            "tenant_id": "default",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(admin_data)
        print("✅ Admin user criado: admin@demo.com / admin123")
    else:
        print("✅ Admin user já existe")
        # Atualizar tenant_id se necessário
        if admin_exists.get('tenant_id') != 'default':
            await db.users.update_one(
                {"email": "admin@demo.com"},
                {"$set": {"tenant_id": "default"}}
            )
            print("   → Tenant ID atualizado para 'default'")
    
    # 2. Criar tenant default se não existir
    tenant_exists = await db.tenants.find_one({"id": "default"})
    if not tenant_exists:
        tenant_data = {
            "id": "default",
            "name": "Default Tenant",
            "subdomain": "default",
            "contact_email": "admin@demo.com",
            "status": "active",
            "plan": "enterprise",
            "max_users": 1000,
            "max_licenses": 10000,
            "max_clients": 5000,
            "features": {
                "api_access": True,
                "whatsapp_integration": True,
                "advanced_reporting": True,
                "multi_user": True
            },
            "created_at": datetime.now(timezone.utc)
        }
        await db.tenants.insert_one(tenant_data)
        print("✅ Tenant 'default' criado")
    else:
        print("✅ Tenant 'default' já existe")
    
    # 3. Pegar ID do admin
    admin = await db.users.find_one({"email": "admin@demo.com"})
    admin_id = admin.get('id')
    
    # 4. Criar categorias se não existirem
    category_names = ["Software", "Hardware", "Consultoria", "Suporte"]
    category_ids = []
    
    for cat_name in category_names:
        cat_exists = await db.categories.find_one({"name": cat_name, "tenant_id": "default"})
        if not cat_exists:
            cat_data = {
                "id": str(uuid.uuid4()),
                "name": cat_name,
                "description": f"Categoria {cat_name}",
                "is_active": True,
                "tenant_id": "default",
                "created_by": admin_id,
                "created_at": datetime.now(timezone.utc)
            }
            await db.categories.insert_one(cat_data)
            category_ids.append(cat_data["id"])
            print(f"✅ Categoria criada: {cat_name}")
        else:
            category_ids.append(cat_exists.get('id'))
    
    # 5. Criar licenças de teste
    license_count = await db.licenses.count_documents({"tenant_id": "default"})
    
    if license_count < 20:
        print(f"📄 Criando licenças de teste... (existem {license_count})")
        
        for i in range(20):
            now = datetime.now(timezone.utc)
            
            # Variar status das licenças
            if i < 10:
                expires_at = now + timedelta(days=30 + i*10)  # Ativas
            elif i < 15:
                expires_at = now + timedelta(days=5)  # Expirando em breve
            else:
                expires_at = now - timedelta(days=10 + i)  # Expiradas
            
            license_data = {
                "id": str(uuid.uuid4()),
                "name": f"Licença Teste {i+1}",
                "description": f"Licença de teste número {i+1} criada automaticamente",
                "license_key": f"LIC-{uuid.uuid4().hex[:16].upper()}",
                "status": "active",
                "max_users": 10 + (i * 5),
                "expires_at": expires_at,
                "features": ["feature1", "feature2"],
                "category_id": category_ids[i % len(category_ids)],
                "tenant_id": "default",
                "created_by": admin_id,
                "created_at": now,
                "updated_at": now
            }
            await db.licenses.insert_one(license_data)
        
        print(f"✅ 20 licenças criadas com tenant_id='default'")
    else:
        print(f"✅ Já existem {license_count} licenças")
    
    # 6. Estatísticas finais
    total_users = await db.users.count_documents({})
    total_licenses = await db.licenses.count_documents({})
    licenses_default = await db.licenses.count_documents({"tenant_id": "default"})
    
    print("\n" + "="*60)
    print("📊 DADOS DE TESTE CRIADOS COM SUCESSO!")
    print("="*60)
    print(f"👥 Usuários: {total_users}")
    print(f"📄 Licenças: {total_licenses}")
    print(f"📄 Licenças (tenant=default): {licenses_default}")
    print("\n🔑 CREDENCIAIS:")
    print("   Email: admin@demo.com")
    print("   Senha: admin123")
    print("   Tenant ID: default")
    print("="*60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_test_data())
