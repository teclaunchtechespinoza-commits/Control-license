#!/usr/bin/env python3
"""
Script para corrigir e criar licenças expirando para o dashboard de vendas
"""

import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import os
from dotenv import load_dotenv
import random

# Load environment
load_dotenv()

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = "license_management"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]

async def create_expiring_licenses():
    """Criar licenças específicas que estão expirando para testar o sistema"""
    print("🔧 Criando licenças expirando para testar dashboard de vendas...")
    
    # Buscar alguns clientes e usuários existentes
    sample_clients_pf = await db.clientes_pf.find().limit(10).to_list(10)
    sample_clients_pj = await db.clientes_pj.find().limit(10).to_list(10)
    sample_users = await db.users.find().limit(5).to_list(5)
    sample_products = await db.products.find().limit(10).to_list(10)
    
    if not sample_users:
        print("❌ Nenhum usuário encontrado!")
        return
        
    # Criar licenças com diferentes cenários de expiração
    expiring_scenarios = [
        # Licenças já expiraram (alta prioridade)
        {"days_offset": -5, "count": 15, "description": "Expiraram há 5 dias"},
        {"days_offset": -2, "count": 10, "description": "Expiraram há 2 dias"},
        {"days_offset": -1, "count": 8, "description": "Expiraram ontem"},
        
        # Licenças expirando hoje/amanhã (urgente)
        {"days_offset": 0, "count": 12, "description": "Expiram hoje"},
        {"days_offset": 1, "count": 15, "description": "Expiram amanhã"},
        
        # Licenças expirando próximos dias (alta prioridade)
        {"days_offset": 3, "count": 20, "description": "Expiram em 3 dias"},
        {"days_offset": 7, "count": 25, "description": "Expiram em 1 semana"},
        
        # Licenças expirando próximas semanas (média prioridade)
        {"days_offset": 15, "count": 30, "description": "Expiram em 15 dias"},
        {"days_offset": 30, "count": 35, "description": "Expiram em 30 dias"},
    ]
    
    all_licenses = []
    
    for scenario in expiring_scenarios:
        print(f"📅 Criando {scenario['count']} licenças - {scenario['description']}")
        
        for i in range(scenario['count']):
            # Data de expiração
            expires_at = datetime.utcnow() + timedelta(days=scenario['days_offset'])
            
            # Escolher cliente aleatório (PF ou PJ)
            client_pf_id = None
            client_pj_id = None
            client_name = "Cliente Teste"
            
            if sample_clients_pf and random.choice([True, False]):
                client = random.choice(sample_clients_pf)
                client_pf_id = client["id"]
                client_name = client.get("nome_completo", "Cliente PF")
            elif sample_clients_pj:
                client = random.choice(sample_clients_pj)
                client_pj_id = client["id"]
                client_name = client.get("razao_social", "Cliente PJ")
            
            # Escolher usuário e produto
            user = random.choice(sample_users)
            product = random.choice(sample_products) if sample_products else None
            
            # Criar licença
            license_data = {
                "id": str(uuid.uuid4()),
                "name": f"Licença {product['name'] if product else 'Software'} - {client_name[:20]}",
                "description": f"Licença empresarial para {client_name}",
                "license_key": f"EXP-{uuid.uuid4().hex[:12].upper()}",
                "status": "active",  # Ativas mas expirando
                "max_users": random.choice([1, 5, 10, 25, 50]),
                "current_activations": random.randint(1, 10),
                "expires_at": expires_at,
                "features": ["Premium Support", "Cloud Backup", "API Access"],
                "category_id": product.get("category_id") if product else None,
                "client_pf_id": client_pf_id,
                "client_pj_id": client_pj_id,
                "product_id": product["id"] if product else None,
                "assigned_user_id": user["id"],
                "created_at": datetime.utcnow() - timedelta(days=random.randint(30, 365)),
                "updated_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                "created_by": user["id"],
                "issued_date": datetime.utcnow() - timedelta(days=random.randint(30, 365)),
                
                # Campos para receita/oportunidade
                "license_value": round(random.uniform(299.99, 4999.99), 2),
                "payment_frequency": random.choice(["monthly", "quarterly", "annually"]),
                "renewal_count": random.randint(0, 5),
                "last_payment_date": datetime.utcnow() - timedelta(days=random.randint(1, 90)),
                "total_revenue": round(random.uniform(299.99, 25000.99), 2),
                "experience_type": "expiring",  # Marcar como experiência de expiração
                
                "tenant_id": "default"
            }
            
            all_licenses.append(license_data)
    
    # Inserir todas as licenças
    if all_licenses:
        await db.licenses.insert_many(all_licenses)
        print(f"✅ {len(all_licenses)} licenças expirando criadas com sucesso!")
        
        # Criar resumo por cenário
        print("\n📊 RESUMO DAS LICENÇAS CRIADAS:")
        for scenario in expiring_scenarios:
            print(f"   📅 {scenario['description']}: {scenario['count']} licenças")
        
        total_expiring = sum(s['count'] for s in expiring_scenarios)
        print(f"\n🎯 TOTAL DE LICENÇAS EXPIRANDO: {total_expiring}")
        print("💰 OPORTUNIDADES DE RENOVAÇÃO CRIADAS!")
        
    else:
        print("❌ Nenhuma licença criada!")

async def update_existing_licenses_with_expiration():
    """Atualizar algumas licenças existentes para ter datas de expiração próximas"""
    print("🔄 Atualizando licenças existentes com datas de expiração variadas...")
    
    # Buscar licenças ativas
    existing_licenses = await db.licenses.find({"status": "active"}).limit(50).to_list(50)
    
    updated_count = 0
    for license_doc in existing_licenses[:30]:  # Atualizar 30 licenças
        # Definir nova data de expiração (variada)
        days_to_expire = random.choice([
            -3, -1, 0, 1, 2, 5, 7, 10, 15, 20, 30, 45, 60
        ])
        new_expires_at = datetime.utcnow() + timedelta(days=days_to_expire)
        
        # Atualizar licença
        await db.licenses.update_one(
            {"id": license_doc["id"]},
            {
                "$set": {
                    "expires_at": new_expires_at,
                    "license_value": round(random.uniform(199.99, 3999.99), 2),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        updated_count += 1
    
    print(f"✅ {updated_count} licenças existentes atualizadas com novas datas de expiração!")

async def main():
    """Função principal"""
    print("🚀 INICIANDO CORREÇÃO DE LICENÇAS EXPIRANDO")
    print("=" * 60)
    
    try:
        # Criar novas licenças expirando
        await create_expiring_licenses()
        
        # Atualizar licenças existentes
        await update_existing_licenses_with_expiration()
        
        print("\n" + "=" * 60)
        print("🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!")
        print("📈 Dashboard de Vendas agora terá licenças expirando!")
        print("💼 Vendedores terão oportunidades de renovação!")
        
    except Exception as e:
        print(f"❌ Erro durante correção: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())