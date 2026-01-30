# Sistema de Controle de Licenças - PRD

## Resumo do Projeto
Sistema SaaS multi-tenant para gerenciamento de licenças de software, com controle de acesso baseado em papéis (RBAC), sistema de tickets, auditoria e notificações.

## Usuários-Alvo
- **Super Admin**: Gerencia todos os tenants e usuários
- **Admin**: Gerencia usuários e licenças do seu tenant
- **User**: Visualiza suas licenças e abre tickets de suporte

## Credenciais de Teste
- Super Admin: `superadmin@autotech.com` / `admin123`
- Admin: `admin@demo.com` / `admin123`
- User: `user@demo.com` / `user123`

---

## Funcionalidades Implementadas

### Core
- [x] Sistema multi-tenant com isolamento de dados
- [x] RBAC (Role-Based Access Control)
- [x] Autenticação JWT com refresh tokens
- [x] Dashboard administrativo unificado
- [x] Dashboard simplificado para usuários

### Autenticação & Segurança
- [x] Login unificado (email OU código de acesso)
- [x] Detecção automática do tipo de login
- [x] Rate limiting
- [x] Password visibility toggle (ícone de olho)
- [x] Recuperação de Senha via Código
- [x] Sistema de Aprovação de Registros

### UI/UX Melhorias
- [x] Login Unificado - Uma única aba para email e código
- [x] Abas com cores diferenciadas - Azul (Entrar) / Verde (Registrar)
- [x] Detecção inteligente - Mostra "📧 Email" ou "🔑 Código"
- [x] Link "Esqueci senha" aparece só quando é email

### Gestão de Licenças
- [x] CRUD completo de licenças
- [x] Status: active, expired, suspended, pending, cancelled
- [x] Associação com clientes PF/PJ
- [x] Notificações de expiração
- [x] **Módulo de Importação de Dados (30/01/2026)** ✨

### Módulo de Importação (NOVO)
- [x] Upload de arquivos CSV/Excel
- [x] Pré-visualização antes de importar
- [x] Detecção automática de conflitos (Serial duplicado)
- [x] Mapeamento flexível de colunas
- [x] Histórico de importações
- [x] Relatório detalhado de importação

**Campos suportados:**
- Manufacturer → Fabricante
- Model → Modelo
- Serial → Número de série (chave única)
- Added → Data de ativação

### Sistema de Tickets
- [x] Criação de tickets por usuários
- [x] Aprovação/Rejeição por admins

### Auditoria & Logs
- [x] Activity logs estruturados
- [x] Rastreamento de ações por usuário

---

## Arquitetura

### Backend
- FastAPI + Motor (MongoDB async)
- Pydantic para validação
- JWT HttpOnly cookies para autenticação

### Frontend
- React 18
- Tailwind CSS
- Shadcn/UI components
- Sonner para toasts

### Database
- MongoDB
- Collections: `tenants`, `users`, `licenses`, `tickets`, `activity_logs`, `password_recovery`

---

## Changelog Recente

### 30/01/2026 - Módulo de Importação de Dados
- **Implementado**: Sistema completo de importação CSV/Excel
  - Endpoints: `/api/import/preview`, `/api/import/execute`, `/api/import/history`, `/api/import/conflicts`
  - Interface drag-and-drop para upload
  - Pré-visualização de dados antes de importar
  - Detecção de conflitos por Serial
  - Opção de atualizar registros existentes
  - Relatório de importação com estatísticas
  - Histórico de lotes de importação
  
- **Campos da Licença expandidos**:
  - `serial_number` - Número de série único
  - `manufacturer` - Fabricante
  - `model` - Modelo do equipamento
  - `activation_date` - Data de ativação
  - `import_source` - Origem da importação
  - `import_batch_id` - ID do lote

### 26/01/2026 - Sistema de Aprovação de Registros
- Fluxo completo de aprovação de registros
- Login unificado com detecção automática

---

## Próximas Tarefas (Backlog)

### P1 - Importação Avançada
- [ ] Suporte a Excel (.xlsx) com múltiplas abas
- [ ] Agendamento de importação automática
- [ ] Mapeamento customizável de colunas

### P2 - Documentação
- [ ] Manual do usuário no Help Center
- [ ] Manual do administrador
- [ ] Changelog técnico visível

### P3 - Funcionalidades Futuras
- [ ] Notificação por email quando registro for aprovado
- [ ] Renovação self-service de licenças
- [ ] Histórico de pagamentos
- [ ] Modularização do server.py

---

## API Endpoints de Importação

```
POST /api/import/preview     - Pré-visualiza dados do arquivo
POST /api/import/execute     - Executa importação
GET  /api/import/history     - Histórico de importações
GET  /api/import/conflicts   - Lista conflitos pendentes
```

---

## Notas Técnicas

### Email Service (MOCKED)
O serviço de email está stub. Para produção, integrar com SendGrid/AWS SES.

### Importação de Dados
- Serial é usado como chave única para detecção de duplicados
- Suporta múltiplos formatos de data
- Gera nome automático: `{Manufacturer} - {Model}` ou `Licença {Serial[:8]}`
