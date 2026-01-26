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
- [x] **Sistema de Aprovação de Registros (26/01/2026)**
  - Novos registros ficam com status `pending`
  - Login bloqueado até aprovação
  - Painel Admin para aprovar/rejeitar
  - Tela de "Aguardando Aprovação" após registro

### UI/UX Melhorias (26/01/2026)
- [x] **Login Unificado** - Uma única aba para email e código
- [x] **Abas com cores diferenciadas** - Azul (Entrar) / Verde (Registrar)
- [x] **Detecção inteligente** - Mostra "📧 Email" ou "🔑 Código"
- [x] **Link "Esqueci senha"** aparece só quando é email

### Gestão de Licenças
- [x] CRUD completo de licenças
- [x] Status: active, expired, suspended, pending, cancelled
- [x] Associação com clientes PF/PJ
- [x] Notificações de expiração

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

### 26/01/2026 - Sistema de Aprovação de Registros
- **Implementado**: Fluxo completo de aprovação de registros
  - Novos usuários ficam com `approval_status: pending`
  - Login bloqueado com mensagem amigável até aprovação
  - Endpoints: `/admin/pending-registrations`, `/admin/registrations/{id}/approve`, `/admin/registrations/{id}/reject`
  - Componente `PendingApprovals.js` no Admin Panel
  - Tela de "Aguardando Aprovação" após registro
  
- **Implementado**: Unificação do Login
  - Uma única aba para login (email ou código)
  - Detecção automática do tipo de credencial
  - Abas com cores diferenciadas (Entrar=azul, Registrar=verde)

### 25/01/2026 - Recuperação de Senha
- Modal multi-step para recuperação
- Código de 6 dígitos válido por 15 minutos

---

## Próximas Tarefas (Backlog)

### P1 - Documentação
- [ ] Manual do usuário no Help Center
- [ ] Manual do administrador
- [ ] Changelog técnico visível

### P2 - Polimento UI/UX
- [ ] Substituir `window.confirm` por modais customizados
- [ ] Melhorar animações e transições

### P3 - Funcionalidades Futuras
- [ ] Notificação por email quando registro for aprovado
- [ ] Renovação self-service de licenças
- [ ] Histórico de pagamentos
- [ ] Modularização do server.py

---

## Notas Técnicas

### Email Service (MOCKED)
O serviço de email está stub. Para produção, integrar com SendGrid/AWS SES.

### Aprovação de Registros
- Status: `pending`, `approved`, `rejected`
- Campos adicionais: `approved_by`, `approved_at`, `rejection_reason`
