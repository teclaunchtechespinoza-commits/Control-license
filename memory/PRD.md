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
- [x] Login por email/senha (Admin)
- [x] Login por serial/senha (Usuário)
- [x] Rate limiting
- [x] Password visibility toggle (ícone de olho)
- [x] **Recuperação de Senha via Código (25/01/2026)**
  - Endpoint: `POST /api/auth/forgot-password`
  - Endpoint: `POST /api/auth/verify-recovery-code`
  - Código de 6 dígitos válido por 15 minutos
  - Email stub (logs para demonstração)
  - Modal multi-step no frontend

### Gestão de Licenças
- [x] CRUD completo de licenças
- [x] Status: active, expired, suspended, pending, cancelled
- [x] Associação com clientes PF/PJ
- [x] Notificações de expiração

### Gestão de Clientes
- [x] Pessoa Física (CPF)
- [x] Pessoa Jurídica (CNPJ)
- [x] Dados de contato e endereço

### Sistema de Tickets
- [x] Criação de tickets por usuários
- [x] Tipos: renewal, support, problem, general
- [x] Status workflow: pending → approved/rejected → resolved → closed
- [x] Respostas de administradores

### Auditoria & Logs
- [x] Activity logs estruturados
- [x] Rastreamento de ações por usuário
- [x] Logs de segurança

---

## Arquitetura

### Backend
- FastAPI + Motor (MongoDB async)
- Pydantic para validação
- JWT para autenticação
- Rate limiting com fallback in-memory

### Frontend
- React 18
- Tailwind CSS
- Shadcn/UI components
- Sonner para toasts

### Database
- MongoDB
- Collections principais:
  - `tenants`, `users`, `licenses`
  - `tickets`, `activity_logs`
  - `password_recovery` (novo)

---

## Próximas Tarefas (Backlog)

### P1 - Fase 2: Documentação
- [ ] Manual do usuário no Help Center
- [ ] Manual do administrador
- [ ] Changelog técnico
- [ ] Apresentação "pitch deck"

### P2 - Fase 3: Polimento UI/UX
- [ ] Substituir `window.confirm` por modais customizados
- [ ] Melhorar animações e transições
- [ ] Revisão de design responsivo

### P3 - Funcionalidades Futuras
- [ ] Renovação self-service de licenças
- [ ] Histórico de pagamentos
- [ ] Download de certificado de licença
- [ ] Modularização do server.py
- [ ] Sistema de analytics avançado
- [ ] API pública para integrações

---

## Changelog Recente

### 25/01/2026
- **Implementado**: Sistema de recuperação de senha
  - Modal multi-step (email → código → nova senha)
  - Endpoints backend seguros
  - Código de 6 dígitos com expiração de 15 minutos
  - Email via stub (print para logs)
  - Link disponível em ambas as abas (Usuário e Admin)

### Sessões Anteriores
- Correções de bugs críticos de integridade de dados
- Otimização de performance (Redis fallback)
- Correções de segurança RBAC
- UI/UX melhorias (visibility toggle, UserDashboard)
- Sistema de tickets e auditoria

---

## Notas Técnicas

### Email Service (MOCKED)
O serviço de email está stub em `/app/backend/email_service.py`. Para produção, integrar com:
- SendGrid
- AWS SES
- SMTP

### Redis (Opcional)
O sistema funciona sem Redis usando fallback in-memory. Para produção, configurar Redis para:
- Rate limiting distribuído
- Refresh tokens
- Cache de sessões
