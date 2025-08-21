#!/usr/bin/env python3
"""
🚀 GERADOR MASSIVO DE DADOS DE TESTE - STRESS TEST SYSTEM
Gera mais de 1000 registros de todos os tipos para testar o sistema sob carga
"""

import asyncio
import random
from datetime import datetime, timedelta
from faker import Faker
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import os
from dotenv import load_dotenv
import bcrypt

# Load environment
load_dotenv()

# Setup Faker with Brazilian locale
fake = Faker('pt_BR')

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = "license_management"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]

class MassiveDataGenerator:
    def __init__(self):
        self.created_categories = []
        self.created_products = []
        self.created_users = []
        self.created_clients_pf = []
        self.created_clients_pj = []
        self.created_licenses = []
        self.created_equipment_brands = []
        self.created_equipment_models = []
        
    async def generate_categories(self, count=50):
        """Gerar 50 categorias diversificadas"""
        print(f"🏷️ Gerando {count} categorias...")
        
        category_types = [
            ("Software de Gestão", "Sistema completo de gestão empresarial", "#3B82F6", "briefcase"),
            ("Ferramentas de Design", "Software para criação e design", "#8B5CF6", "palette"),
            ("Segurança Digital", "Soluções de segurança e antivírus", "#EF4444", "shield"),
            ("Desenvolvimento", "IDEs e ferramentas de programação", "#10B981", "code"),
            ("Office & Produtividade", "Suítes de escritório e produtividade", "#F59E0B", "file-text"),
            ("Comunicação", "Ferramentas de comunicação empresarial", "#06B6D4", "message-circle"),
            ("Análise de Dados", "Business Intelligence e Analytics", "#84CC16", "bar-chart"),
            ("CRM & Vendas", "Customer Relationship Management", "#EC4899", "users"),
            ("ERP Empresarial", "Enterprise Resource Planning", "#6366F1", "settings"),
            ("E-commerce", "Plataformas de comércio eletrônico", "#F97316", "shopping-cart"),
            ("Marketing Digital", "Ferramentas de marketing online", "#14B8A6", "trending-up"),
            ("Recursos Humanos", "Gestão de pessoas e RH", "#A855F7", "user-check"),
            ("Financeiro", "Gestão financeira e contábil", "#059669", "dollar-sign"),
            ("Logística", "Gestão de estoque e logística", "#DC2626", "truck"),
            ("Educação", "Plataformas educacionais", "#7C3AED", "book"),
            ("Saúde", "Sistemas para área da saúde", "#0891B2", "heart"),
            ("Jurídico", "Software jurídico e advocacia", "#1F2937", "scale"),
            ("Imobiliário", "Gestão imobiliária", "#92400E", "home"),
            ("Agricultura", "AgTech e gestão rural", "#65A30D", "leaf"),
            ("Indústria 4.0", "Automação industrial", "#4338CA", "cpu"),
        ]
        
        categories = []
        for i in range(count):
            base_category = random.choice(category_types)
            category = {
                "id": str(uuid.uuid4()),
                "name": f"{base_category[0]} {random.choice(['Pro', 'Enterprise', 'Standard', 'Premium', 'Ultimate'])}",
                "description": f"{base_category[1]} - {fake.text(max_nb_chars=100)}",
                "color": base_category[2],
                "icon": base_category[3],
                "created_at": fake.date_time_between(start_date='-2y', end_date='now'),
                "updated_at": fake.date_time_between(start_date='-1y', end_date='now'),
                "is_active": random.choice([True, True, True, False]),  # 75% ativo
                "tenant_id": "default"
            }
            categories.append(category)
            
        await db.categories.insert_many(categories)
        self.created_categories = categories
        print(f"✅ {count} categorias criadas!")

    async def generate_equipment_brands(self, count=20):
        """Gerar 20 marcas de equipamentos"""
        print(f"🏭 Gerando {count} marcas de equipamentos...")
        
        brand_names = [
            "Dell Technologies", "HP Inc.", "Lenovo Group", "Acer Inc.", "ASUS",
            "MSI", "Apple", "Samsung", "LG Electronics", "Sony", "Toshiba",
            "Fujitsu", "NEC", "Panasonic", "Huawei", "Xiaomi", "Microsoft",
            "Google", "Intel", "AMD", "NVIDIA", "Cisco", "IBM", "Oracle"
        ]
        
        brands = []
        for i in range(count):
            brand = {
                "id": str(uuid.uuid4()),
                "name": random.choice(brand_names) + f" {random.choice(['Corp', 'Ltd', 'Inc', 'SA', 'Brasil'])}",
                "created_at": fake.date_time_between(start_date='-3y', end_date='now'),
                "tenant_id": "default"
            }
            brands.append(brand)
            
        await db.equipment_brands.insert_many(brands)
        self.created_equipment_brands = brands
        print(f"✅ {count} marcas de equipamentos criadas!")

    async def generate_equipment_models(self, count=100):
        """Gerar 100 modelos de equipamentos"""
        print(f"💻 Gerando {count} modelos de equipamentos...")
        
        if not self.created_equipment_brands:
            await self.generate_equipment_brands()
        
        model_types = ["Laptop", "Desktop", "Server", "Tablet", "Smartphone", "Monitor", "Printer", "Scanner"]
        model_series = ["Pro", "Elite", "Business", "Gaming", "Workstation", "Ultra", "Max", "Plus"]
        
        models = []
        for i in range(count):
            brand = random.choice(self.created_equipment_brands)
            model = {
                "id": str(uuid.uuid4()),
                "brand_id": brand["id"],
                "name": f"{random.choice(model_types)} {random.choice(model_series)} {random.randint(1000, 9999)}",
                "created_at": fake.date_time_between(start_date='-2y', end_date='now'),
                "tenant_id": "default"
            }
            models.append(model)
            
        await db.equipment_models.insert_many(models)
        self.created_equipment_models = models
        print(f"✅ {count} modelos de equipamentos criados!")

    async def generate_products(self, count=200):
        """Gerar 200 produtos diversificados"""
        print(f"📦 Gerando {count} produtos...")
        
        if not self.created_categories:
            await self.generate_categories()
        
        product_names = [
            "Sistema de Gestão Empresarial", "CRM Avançado", "ERP Completo", "Suite Office",
            "Antivírus Empresarial", "Firewall Pro", "Designer Gráfico", "CAD Professional",
            "Contador Digital", "BI Analytics", "E-commerce Platform", "Marketing Automation",
            "RH Digital", "Logística Inteligente", "Telemedicina", "Educação Online",
            "Jurídico Cloud", "Imobiliária Pro", "AgTech Solutions", "Indústria 4.0"
        ]
        
        versions = ["v1.0", "v2.0", "v3.5", "v4.2", "v5.1", "2024", "2025", "Pro", "Enterprise", "Ultimate"]
        
        products = []
        for i in range(count):
            category = random.choice(self.created_categories)
            base_price = random.uniform(99.99, 9999.99)
            
            product = {
                "id": str(uuid.uuid4()),
                "name": f"{random.choice(product_names)} {random.choice(versions)}",
                "description": fake.text(max_nb_chars=200),
                "version": random.choice(versions),
                "price": round(base_price, 2),
                "currency": "BRL",
                "category_id": category["id"],
                "features": random.sample([
                    "Multi-user", "Cloud Storage", "API Integration", "Mobile App",
                    "Advanced Reports", "Custom Dashboard", "24/7 Support", "SSL Security",
                    "Data Export", "Workflow Automation", "Real-time Sync", "Backup Auto"
                ], k=random.randint(3, 8)),
                "created_at": fake.date_time_between(start_date='-2y', end_date='now'),
                "updated_at": fake.date_time_between(start_date='-1y', end_date='now'),
                "is_active": random.choice([True, True, True, False]),  # 75% ativo
                "tenant_id": "default"
            }
            products.append(product)
            
        await db.products.insert_many(products)
        self.created_products = products
        print(f"✅ {count} produtos criados!")

    async def generate_users(self, count=100):
        """Gerar 100 usuários diversos"""
        print(f"👥 Gerando {count} usuários...")
        
        roles = ["admin", "user", "user", "user", "user"]  # 20% admin, 80% user
        
        users = []
        for i in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{fake.domain_name()}"
            
            # Hash da senha
            password = "user123"
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            user = {
                "id": str(uuid.uuid4()),
                "name": f"{first_name} {last_name}",
                "email": email,
                "password_hash": password_hash,
                "role": random.choice(roles),
                "tenant_id": "default",
                "is_active": random.choice([True, True, True, False]),  # 75% ativo
                "created_at": fake.date_time_between(start_date='-2y', end_date='now'),
                "last_login": fake.date_time_between(start_date='-30d', end_date='now') if random.choice([True, False]) else None
            }
            users.append(user)
            
        await db.users.insert_many(users)
        self.created_users = users
        print(f"✅ {count} usuários criados!")

    async def generate_clients_pf(self, count=300):
        """Gerar 300 clientes Pessoa Física"""
        print(f"🧑 Gerando {count} clientes Pessoa Física...")
        
        status_options = ["active", "inactive", "pending_verification", "blocked"]
        
        clients_pf = []
        for i in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            client = {
                "id": str(uuid.uuid4()),
                "client_type": "PF",
                "nome_completo": f"{first_name} {last_name}",
                "cpf": fake.cpf().replace(".", "").replace("-", ""),
                "rg": fake.rg(),
                "data_nascimento": fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
                "email_principal": f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{fake.domain_name()}",
                "telefone_principal": fake.phone_number(),
                "telefone_secundario": fake.phone_number() if random.choice([True, False]) else None,
                "endereco_principal": {
                    "logradouro": fake.street_name(),
                    "numero": str(random.randint(1, 9999)),
                    "complemento": f"Apto {random.randint(1, 999)}" if random.choice([True, False]) else None,
                    "bairro": fake.neighborhood(),
                    "cidade": fake.city(),
                    "estado": fake.state_abbr(),
                    "cep": fake.postcode().replace("-", ""),
                    "pais": "Brasil"
                },
                "profissao": fake.job(),
                "renda_mensal": round(random.uniform(1500, 25000), 2),
                "estado_civil": random.choice(["solteiro", "casado", "divorciado", "viuvo"]),
                "nacionalidade": "Brasileira",
                "genero": random.choice(["masculino", "feminino", "outro", "prefere_nao_informar"]),
                "status": random.choice(status_options),
                "observacoes": fake.text(max_nb_chars=150) if random.choice([True, False]) else None,
                "created_at": fake.date_time_between(start_date='-2y', end_date='now'),
                "updated_at": fake.date_time_between(start_date='-1y', end_date='now'),
                "tenant_id": "default"
            }
            clients_pf.append(client)
            
        await db.clientes_pf.insert_many(clients_pf)
        self.created_clients_pf = clients_pf
        print(f"✅ {count} clientes PF criados!")

    async def generate_clients_pj(self, count=200):
        """Gerar 200 clientes Pessoa Jurídica"""
        print(f"🏢 Gerando {count} clientes Pessoa Jurídica...")
        
        company_types = ["LTDA", "SA", "EIRELI", "MEI", "EPP"]
        business_areas = [
            "Tecnologia", "Saúde", "Educação", "Varejo", "Indústria", "Serviços",
            "Construção", "Agricultura", "Logística", "Financeiro", "Comunicação"
        ]
        
        clients_pj = []
        for i in range(count):
            company_name = f"{fake.company()} {random.choice(company_types)}"
            
            # Gerar CNPJ válido (formato básico)
            cnpj_base = ''.join([str(random.randint(0, 9)) for _ in range(8)])
            cnpj_filial = '0001'
            cnpj_dv = '00'  # Simplificado
            cnpj = f"{cnpj_base}{cnpj_filial}{cnpj_dv}"
            
            client = {
                "id": str(uuid.uuid4()),
                "client_type": "PJ",
                "razao_social": company_name,
                "nome_fantasia": f"{fake.company()} {random.choice(['Pro', 'Plus', 'Solutions', 'Tech', 'Digital'])}",
                "cnpj": cnpj,
                "inscricao_estadual": f"{random.randint(100000000, 999999999)}",
                "inscricao_municipal": f"{random.randint(1000000, 9999999)}",
                "data_abertura": fake.date_between(start_date='-20y', end_date='-1y').isoformat(),
                "email_principal": f"contato@{fake.domain_name()}",
                "telefone_principal": fake.phone_number(),
                "telefone_comercial": fake.phone_number(),
                "endereco_matriz": {
                    "logradouro": fake.street_name(),
                    "numero": str(random.randint(1, 9999)),
                    "complemento": f"Sala {random.randint(101, 999)}" if random.choice([True, False]) else None,
                    "bairro": fake.neighborhood(),
                    "cidade": fake.city(),
                    "estado": fake.state_abbr(),
                    "cep": fake.postcode().replace("-", ""),
                    "pais": "Brasil"
                },
                "representante_legal": {
                    "nome": fake.name(),
                    "cpf": fake.cpf().replace(".", "").replace("-", ""),
                    "cargo": random.choice(["Diretor", "Gerente", "Administrador", "Sócio"]),
                    "email": f"{fake.first_name().lower()}@{fake.domain_name()}",
                    "telefone": fake.phone_number()
                },
                "area_atuacao": random.choice(business_areas),
                "porte_empresa": random.choice(["MEI", "Microempresa", "Pequeno Porte", "Médio Porte", "Grande Porte"]),
                "faturamento_anual": round(random.uniform(50000, 50000000), 2),
                "numero_funcionarios": random.randint(1, 1000),
                "regime_tributario": random.choice(["Simples Nacional", "Lucro Presumido", "Lucro Real"]),
                "status": random.choice(["active", "inactive", "pending_verification", "blocked"]),
                "observacoes": fake.text(max_nb_chars=200) if random.choice([True, False]) else None,
                "created_at": fake.date_time_between(start_date='-2y', end_date='now'),
                "updated_at": fake.date_time_between(start_date='-1y', end_date='now'),
                "tenant_id": "default"
            }
            clients_pj.append(client)
            
        await db.clientes_pj.insert_many(clients_pj)
        self.created_clients_pj = clients_pj
        print(f"✅ {count} clientes PJ criados!")

    async def generate_licenses(self, count=500):
        """Gerar 500 licenças diversificadas com experiências de receita positiva e negativa"""
        print(f"📜 Gerando {count} licenças diversificadas...")
        
        if not self.created_products:
            await self.generate_products()
        if not self.created_users:
            await self.generate_users()
        if not self.created_clients_pf:
            await self.generate_clients_pf()
        if not self.created_clients_pj:
            await self.generate_clients_pj()
        
        status_options = ["active", "pending", "expired", "suspended", "cancelled"]
        
        licenses = []
        for i in range(count):
            product = random.choice(self.created_products)
            user = random.choice(self.created_users)
            
            # Decidir tipo de cliente (PF ou PJ)
            client_type = random.choice(["PF", "PJ"])
            if client_type == "PF" and self.created_clients_pf:
                client = random.choice(self.created_clients_pf)
                client_pf_id = client["id"]
                client_pj_id = None
            elif client_type == "PJ" and self.created_clients_pj:
                client = random.choice(self.created_clients_pj)
                client_pf_id = None
                client_pj_id = client["id"]
            else:
                client_pf_id = None
                client_pj_id = None
            
            # Datas para simular diferentes cenários
            created_date = fake.date_time_between(start_date='-2y', end_date='now')
            
            # Simular diferentes tipos de experiência (positiva/negativa)
            experience_type = random.choice(["positive", "negative", "neutral"])
            
            if experience_type == "positive":
                # Licenças ativas, renovadas, gerando receita
                status = random.choice(["active", "active", "active", "pending"])
                expires_at = fake.date_time_between(start_date='now', end_date='+2y')
                renewal_count = random.randint(1, 5)
                last_payment = fake.date_time_between(start_date='-30d', end_date='now')
            elif experience_type == "negative":
                # Licenças problema: canceladas, expiradas, em atraso
                status = random.choice(["expired", "cancelled", "suspended"])
                expires_at = fake.date_time_between(start_date='-1y', end_date='-1d')
                renewal_count = 0
                last_payment = fake.date_time_between(start_date='-6m', end_date='-1m')
            else:
                # Licenças neutras
                status = random.choice(status_options)
                expires_at = fake.date_time_between(start_date='-6m', end_date='+1y')
                renewal_count = random.randint(0, 2)
                last_payment = fake.date_time_between(start_date='-3m', end_date='now')
            
            license = {
                "id": str(uuid.uuid4()),
                "name": f"{product['name']} - Licença {random.choice(['Empresarial', 'Individual', 'Educacional', 'Governamental'])}",
                "description": f"Licença para {product['name']} - {fake.text(max_nb_chars=100)}",
                "license_key": f"LIC-{uuid.uuid4().hex[:16].upper()}",
                "status": status,
                "max_users": random.choice([1, 5, 10, 25, 50, 100, 500]),
                "current_activations": random.randint(0, 25),
                "expires_at": expires_at,
                "features": random.sample([
                    "Advanced Analytics", "Premium Support", "Custom Integration", "Mobile Access",
                    "Cloud Backup", "API Access", "Multi-Language", "White Label", "SSO",
                    "Advanced Security", "Custom Reports", "Workflow Automation"
                ], k=random.randint(2, 6)),
                "category_id": product.get("category_id"),
                "client_pf_id": client_pf_id,
                "client_pj_id": client_pj_id,
                "product_id": product["id"],
                "assigned_user_id": user["id"],
                "created_at": created_date,
                "updated_at": fake.date_time_between(start_date=created_date, end_date='now'),
                "created_by": user["id"],
                "issued_date": created_date,
                
                # Campos para análise de receita
                "license_value": round(random.uniform(99.99, 9999.99), 2),
                "payment_frequency": random.choice(["monthly", "quarterly", "annually", "one-time"]),
                "renewal_count": renewal_count,
                "last_payment_date": last_payment,
                "total_revenue": round(random.uniform(99.99, 50000.99), 2),
                "experience_type": experience_type,
                
                "tenant_id": "default"
            }
            licenses.append(license)
            
        await db.licenses.insert_many(licenses)
        self.created_licenses = licenses
        print(f"✅ {count} licenças criadas com experiências diversificadas!")

    async def generate_notifications(self, count=1000):
        """Gerar 1000 notificações do sistema"""
        print(f"🔔 Gerando {count} notificações...")
        
        if not self.created_users:
            await self.generate_users()
        if not self.created_licenses:
            await self.generate_licenses()
        
        notification_types = [
            "license_expiring", "license_expired", "payment_due", "payment_overdue",
            "license_activated", "license_suspended", "system_maintenance", "security_alert",
            "feature_update", "contract_renewal", "support_ticket", "performance_alert"
        ]
        
        channels = ["email", "in_app", "sms", "whatsapp"]
        priorities = ["low", "medium", "high", "urgent"]
        
        notifications = []
        for i in range(count):
            user = random.choice(self.created_users)
            license_ref = random.choice(self.created_licenses) if random.choice([True, False]) else None
            
            notification = {
                "id": str(uuid.uuid4()),
                "type": random.choice(notification_types),
                "title": fake.sentence(nb_words=6),
                "message": fake.text(max_nb_chars=200),
                "channel": random.choice(channels),
                "priority": random.choice(priorities),
                "status": random.choice(["sent", "pending", "failed", "read"]),
                "recipient_id": user["id"],
                "recipient_email": user["email"],
                "license_id": license_ref["id"] if license_ref else None,
                "sent_at": fake.date_time_between(start_date='-6m', end_date='now'),
                "read_at": fake.date_time_between(start_date='-3m', end_date='now') if random.choice([True, False]) else None,
                "metadata": {
                    "source": random.choice(["system", "manual", "automated", "api"]),
                    "campaign_id": str(uuid.uuid4()) if random.choice([True, False]) else None,
                    "retry_count": random.randint(0, 3)
                },
                "created_at": fake.date_time_between(start_date='-6m', end_date='now'),
                "tenant_id": "default"
            }
            notifications.append(notification)
            
        await db.notifications.insert_many(notifications)
        print(f"✅ {count} notificações criadas!")

    async def generate_all_data(self):
        """Gerar todos os tipos de dados em sequência"""
        print("🚀 INICIANDO GERAÇÃO MASSIVA DE DADOS DE TESTE")
        print("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Gerar dados em ordem de dependência
            await self.generate_categories(50)
            await self.generate_equipment_brands(20)
            await self.generate_equipment_models(100)
            await self.generate_products(200)
            await self.generate_users(100)
            await self.generate_clients_pf(300)
            await self.generate_clients_pj(200)
            await self.generate_licenses(500)
            await self.generate_notifications(1000)
            
            end_time = datetime.now()
            total_time = end_time - start_time
            
            print("=" * 60)
            print("🎉 GERAÇÃO DE DADOS CONCLUÍDA COM SUCESSO!")
            print(f"⏱️  Tempo total: {total_time}")
            print("\n📊 RESUMO DOS DADOS GERADOS:")
            print(f"   🏷️  Categorias: 50")
            print(f"   🏭 Marcas de Equipamentos: 20")
            print(f"   💻 Modelos de Equipamentos: 100")
            print(f"   📦 Produtos: 200")
            print(f"   👥 Usuários: 100")
            print(f"   🧑 Clientes PF: 300")
            print(f"   🏢 Clientes PJ: 200")
            print(f"   📜 Licenças: 500")
            print(f"   🔔 Notificações: 1000")
            print(f"   📈 TOTAL DE REGISTROS: 2,470")
            print("\n🎯 TIPOS DE EXPERIÊNCIA NAS LICENÇAS:")
            print("   ✅ Positivas: ~33% (receita crescente, renovações)")
            print("   ❌ Negativas: ~33% (cancelamentos, atrasos)")
            print("   ⚪ Neutras: ~34% (situação normal)")
            print("\n💪 SISTEMA PRONTO PARA STRESS TEST!")
            
        except Exception as e:
            print(f"❌ Erro durante geração: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Função principal"""
    generator = MassiveDataGenerator()
    await generator.generate_all_data()

if __name__ == "__main__":
    asyncio.run(main())