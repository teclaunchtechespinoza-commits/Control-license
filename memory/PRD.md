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
- [x] **Security Hardening v1.4.0 (31/01/2026)** ✨

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
- [x] Módulo de Importação de Dados (CSV/Excel)
- [x] **Gestão Avançada de Licenças (31/01/2026)** ✨

### Módulo de Gestão Avançada (NOVO - 31/01/2026)
- [x] Campo `validity_days` editável (padrão 365 dias)
- [x] Associação com vendedor (`salesperson_id` - admins existentes)
- [x] Histórico de renovações (`renewal_history`)
- [x] Endpoint de renovação com registro automático
- [x] Visualização de histórico de renovações
- [x] Interface completa em `/gestao-licencas`
- [x] Estatísticas: ativas, expirando, expiradas, total

### Sistema de Certificados Digitais (NOVO - 06/03/2026) ✨
- [x] Geração de certificados digitais para licenças
- [x] QR Code para validação pública
- [x] Página pública de validação (`/certificado/:code`)
- [x] Status animado: VÁLIDO, INVÁLIDO, EXPIRANDO, EXPIRADO
- [x] Indicador de conectividade "Servidor Online"
- [x] Download de certificado em PDF (WeasyPrint)
- [x] Compartilhamento via link ou Web Share API
- [x] Credenciais de acesso geradas automaticamente
- [x] Hash SHA256 para validação de integridade

**Campos do Histórico de Renovação:**
- `renewal_date` - Data/hora da renovação
- `previous_expiration` - Expiração anterior
- `new_expiration` - Nova expiração
- `validity_days` - Dias aplicados
- `renewed_by_id/name/email` - Quem renovou
- `notes` - Observações

### Módulo de Importação
- [x] Upload de arquivos CSV/Excel
- [x] Pré-visualização antes de importar
- [x] Detecção automática de conflitos (Serial duplicado)
- [x] Mapeamento flexível de colunas
- [x] Histórico de importações
- [x] Relatório detalhado de importação

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

### 06/03/2026 - Sistema de Certificados Digitais v1.5.0
- **Implementado**: Sistema completo de geração de certificados
  - Backend: `certificate_system.py`, `pdf_generator.py`, `templates/certificate_template.html`
  - Endpoints: `POST /api/licenses/{id}/certificate/generate`, `GET /api/certificates/{code}`, `GET /api/certificates/{code}/pdf`
  - Todos endpoints públicos funcionam sem autenticação
  - QR Code gerado automaticamente com link de validação
  - PDF gerado server-side com WeasyPrint
  - Hash SHA256 para integridade

- **Frontend**: Página pública de validação
  - Componentes: `CertificateValidation.js`, `StatusBadge.js`
  - Rota pública: `/certificado/:code` (fora do AuthProvider)
  - Status animado com CSS keyframes
  - Botões: Baixar PDF, Copiar Link, Compartilhar

- **Bug Fix**: Corrigido roteamento de rotas públicas
  - Rota `/certificado/:code` estava redirecionando para `/login`
  - Movida para fora do `AuthProvider` em `App.js`

### 31/01/2026 - Security Hardening v1.4.0
- **Implementado**: Fortalecimento de segurança do sistema
  - `SecretMaskingFilter` em `structured_logger.py` - Mascara secrets automaticamente em logs
  - Script `scripts/security_audit.py` - Auditoria automatizada de código
  - Script `scripts/setup_secrets.py` - Gerador de secrets seguros
  - Atualização do `.env.example` com documentação completa
  - Verificação: .env no .gitignore, módulos de segurança existentes

- **Bug Fix**: Corrigido erro de Select.Item com value="" no frontend
  - Componente `LicenseManagement.js` linha 755
  - SelectItem não aceita value vazio, alterado para value="none"

### 31/01/2026 - Módulo de Gestão Avançada de Licenças
- **Implementado**: Sistema completo de gestão avançada de licenças
  - Modelo `RenewalHistoryEntry` para histórico de renovações
  - Novos campos em `License`: `validity_days`, `salesperson_id`, `salesperson_name`, `renewal_history`
  - Endpoint `GET /api/admin/salespeople` - Lista admins como vendedores
  - Endpoint `POST /api/licenses/{id}/renew` - Renovar com histórico
  - Endpoint `GET /api/licenses/{id}/history` - Buscar histórico
  - Atualização de `PUT /api/licenses/{id}` com novos campos
  - Componente `LicenseManagement.js` com interface completa
  - Rota `/gestao-licencas` no frontend
  - Link "Gestão Avançada" no menu de Licenças

- **Bug Fix**: Corrigido erro de comparação de timezone em `renew_license`
  - MongoDB retorna datetime naive, código usava aware
  - Adicionada normalização de timezone antes de comparar

### 30/01/2026 - Módulo de Importação de Dados
- Sistema completo de importação CSV/Excel
- Endpoints: `/api/import/preview`, `/api/import/execute`, `/api/import/history`
- Interface drag-and-drop para upload

### 26/01/2026 - Sistema de Aprovação de Registros
- Fluxo completo de aprovação de registros
- Login unificado com detecção automática

---

## API Endpoints - Gestão Avançada

```
GET  /api/admin/salespeople              - Listar vendedores (admins do tenant)
POST /api/licenses/{id}/renew            - Renovar licença
GET  /api/licenses/{id}/history          - Histórico de renovações
PUT  /api/licenses/{id}                  - Atualizar (inclui novos campos)
```

**Exemplo de renovação:**
```json
POST /api/licenses/{id}/renew
{
  "validity_days": 365,
  "notes": "Renovação anual"
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Licença renovada com sucesso por 365 dias",
  "license": {...},
  "renewal_entry": {
    "id": "uuid",
    "renewal_date": "2026-01-31T13:47:49Z",
    "previous_expiration": "2026-12-31T00:00:00Z",
    "new_expiration": "2027-12-31T00:00:00Z",
    "validity_days": 365,
    "renewed_by_name": "Super Administrator",
    "notes": "Renovação anual"
  }
}
```

---

## Próximas Tarefas (Backlog)

### P1 - Documentação & Apresentação
- [ ] Manual do usuário no Help Center
- [ ] Manual do administrador
- [ ] Changelog técnico visível
- [ ] Pitch deck para apresentação

### P2 - Melhorias de Importação
- [ ] Suporte a Excel (.xlsx) com múltiplas abas
- [ ] Agendamento de importação automática
- [ ] Mapeamento customizável de colunas

### P3 - Funcionalidades Futuras
- [ ] Notificação por email quando registro for aprovado
- [ ] Renovação self-service de licenças
- [ ] Histórico de pagamentos
- [ ] Download de certificado de licença
- [ ] Modularização do server.py

---

## Notas Técnicas

### Email Service (MOCKED)
O serviço de email está stub. Para produção, integrar com SendGrid/AWS SES.

### Timezone Handling
MongoDB pode retornar datetimes naive ou aware. Sempre normalizar com:
```python
if dt.tzinfo is None:
    dt = dt.replace(tzinfo=timezone.utc)
```

### X-Tenant-ID Header
Obrigatório em todas as requisições autenticadas. O frontend adiciona automaticamente via interceptor do axios.

---

## Testes

Arquivo de testes: `/app/backend/tests/test_license_management.py`
- 13 testes cobrindo todos os endpoints de gestão avançada
- Usa `requests.Session` para manter cookies de autenticação
- Todos os testes passando ✅
