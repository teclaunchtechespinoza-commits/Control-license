import React, { useState } from 'react';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { 
  BookOpen,
  Search,
  Shield,
  Users,
  FileText,
  Key,
  Lock,
  Eye,
  Building2,
  UserCircle,
  Settings,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  ChevronRight,
  ChevronDown,
  ExternalLink,
  TrendingUp
} from 'lucide-react';

const HelpCenter = ({ isOpen, onClose }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedSection, setExpandedSection] = useState(null);
  const [engineeringChecklist, setEngineeringChecklist] = useState(() => {
    // Carregar estado do localStorage
    const saved = localStorage.getItem('engineering_checklist');
    return saved ? JSON.parse(saved) : {};
  });

  const toggleChecklistItem = (itemId) => {
    const newState = {
      ...engineeringChecklist,
      [itemId]: !engineeringChecklist[itemId]
    };
    setEngineeringChecklist(newState);
    localStorage.setItem('engineering_checklist', JSON.stringify(newState));
  };

  const toggleSection = (sectionId) => {
    setExpandedSection(expandedSection === sectionId ? null : sectionId);
  };

  const helpContent = [
    {
      id: 'sensitive-data',
      icon: Shield,
      title: '🔒 Sistema de Dados Sensíveis',
      category: 'Segurança',
      tags: ['confidencial', 'proteção', 'acesso'],
      sections: [
        {
          title: 'O que são Dados Sensíveis?',
          content: `O sistema protege informações confidenciais de equipamentos associados a clientes (PF/PJ), como:
• Credenciais de acesso (usuários e senhas)
• Identificadores de hardware (MAC address, serial number)
• Chaves de acesso (WiFi, hardware keys)`,
          image: 'https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&auto=format&fit=crop&q=60',
          imageCaption: 'Exemplo de interface de dados sensíveis protegidos'
        },
        {
          title: 'Quem pode ver os dados?',
          content: `✅ PODEM VER (roles privilegiados):
• admin - Administradores
• super_admin - Super administradores
• technical_lead - Líderes técnicos

❌ NÃO PODEM VER (dados mascarados):
• user - Usuários comuns
• Outros roles sem privilégio`
        },
        {
          title: 'Como funciona o mascaramento?',
          content: `Para usuários COM permissão:
• Campos aparecem mascarados (••••••••)
• Botão 👁️ "Ver" - Mostra valor real temporariamente
• Botão 📋 "Copiar" - Copia o valor real
• Badge: "Acesso Autorizado"

Para usuários SEM permissão:
• Campos mostram [PROTEGIDO-REF123]
• Botões ficam bloqueados 🔒
• Badge: "Acesso Restrito"
• Mensagem com código de referência para solicitar ao admin`
        },
        {
          title: 'Tipos de dados protegidos',
          content: `IDENTIFICAÇÃO:
• ID Interno do Equipamento
• Número de Série
• Endereço MAC
• Chave de Hardware

CREDENCIAIS:
• Usuário Administrador
• Senha Administrador
• Senha de Serviço
• Senha WiFi`
        },
        {
          title: 'Como editar dados sensíveis (Admin)',
          content: `1. Abra o cliente PJ desejado
2. Role até a seção "Dados Sensíveis (Confidencial)"
3. Clique em "Editar Dados Sensíveis" (botão só aparece para admins)
4. Modal se abre com todos os campos editáveis
5. Preencha/atualize as informações
6. Clique em "Salvar Dados Sensíveis"
7. Dados são salvos e mascarados automaticamente`
        }
      ]
    },
    {
      id: 'user-management',
      icon: Users,
      title: '👥 Gerenciamento de Usuários',
      category: 'Administração',
      tags: ['usuários', 'permissões', 'roles'],
      sections: [
        {
          title: 'Como criar um novo usuário',
          content: `1. Vá em Administração > Gerenciar Usuários
2. Clique em "Novo Usuário"
3. Preencha os campos obrigatórios:
   • Nome Completo
   • Email
   • Senha (mínimo 6 caracteres)
   • Função (Usuário ou Administrador)
4. Clique em "Criar Usuário"
5. O usuário receberá as credenciais para primeiro acesso`,
          image: 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&auto=format&fit=crop&q=60',
          imageCaption: 'Gerenciamento de usuários no painel administrativo'
        },
        {
          title: 'Como editar um usuário',
          content: `1. Vá em Administração > Gerenciar Usuários
2. Localize o usuário na lista
3. Clique no ícone de editar (✏️)
4. Você pode alterar:
   • Nome Completo
   • Email
   • Status (Ativo/Inativo)
5. Clique em "Salvar Alterações"

⚠️ Nota: A função (role) não pode ser alterada no modal de edição. Use o dropdown na tabela para isso.`
        },
        {
          title: 'Tipos de usuários (Roles)',
          content: `ADMIN:
• Acesso total ao sistema
• Pode criar e gerenciar usuários
• Visualiza dados sensíveis
• Acessa todas as funcionalidades

USER:
• Acesso limitado
• Visualiza apenas suas próprias licenças
• Não vê dados sensíveis (mascarados)
• Não pode gerenciar outros usuários`
        },
        {
          title: 'Como desativar um usuário',
          content: `1. Abra o usuário para edição
2. Altere o Status para "Inativo"
3. Salve as alterações

O usuário não conseguirá mais fazer login, mas seus dados são preservados no sistema.`
        }
      ]
    },
    {
      id: 'license-management',
      icon: FileText,
      title: '📄 Gerenciamento de Licenças',
      category: 'Operacional',
      tags: ['licenças', 'chaves', 'expiração'],
      sections: [
        {
          title: 'Como criar uma nova licença',
          content: `1. Vá em Administração > Gerenciar Licenças
2. Clique em "Nova Licença"
3. Preencha os campos obrigatórios:
   • Nome da Licença
   • Máximo de Usuários
4. Campos opcionais:
   • Descrição
   • Data de Expiração
   • Atribuir a Usuário
   • Categoria
   • Cliente (PF ou PJ)
   • Produto
   • Plano
5. Clique em "Criar Licença"
6. A chave da licença é gerada automaticamente`
        },
        {
          title: 'Status das licenças',
          content: `ATIVO (Verde):
• Licença válida e funcionando normalmente
• Dentro do prazo de validade

EXPIRADO (Vermelho):
• Licença fora do prazo de validade
• Necessita renovação

SUSPENSO (Amarelo):
• Licença temporariamente desativada
• Requer atenção administrativa

PENDENTE (Azul):
• Aguardando processamento
• Ainda não ativada`
        },
        {
          title: 'Como editar uma licença',
          content: `1. Localize a licença na lista
2. Clique no ícone de editar (✏️)
3. Modifique os campos desejados
4. Clique em "Salvar Alterações"

⚠️ Nota: A chave da licença não pode ser alterada após a criação.`
        },
        {
          title: 'Como atribuir licença a um usuário',
          content: `1. Edite a licença desejada
2. No campo "Usuário Atribuído", selecione o usuário
3. Salve as alterações

Você também pode atribuir/reatribuir licenças em lote através do painel administrativo.`
        }
      ]
    },
    {
      id: 'client-management',
      icon: Building2,
      title: '🏢 Gerenciamento de Clientes',
      category: 'Cadastros',
      tags: ['clientes', 'pf', 'pj', 'cnpj', 'cpf'],
      sections: [
        {
          title: 'Diferença entre Cliente PF e PJ',
          content: `PESSOA FÍSICA (PF):
• Identificada por CPF
• Campos: Nome Completo, CPF, Email, Telefone, Endereço
• Usado para clientes individuais

PESSOA JURÍDICA (PJ):
• Identificada por CNPJ
• Campos: Razão Social, CNPJ, Nome Fantasia, Email, Telefone, Endereço
• Inclui seção de Dados Sensíveis (Confidencial)
• Usado para empresas e organizações`
        },
        {
          title: 'Como cadastrar cliente PF',
          content: `1. Vá em Cadastros > Pessoas Físicas
2. Clique em "Nova Pessoa Física"
3. Preencha os dados:
   • Nome Completo (obrigatório)
   • CPF (obrigatório)
   • Email
   • Telefone
   • Data de Nascimento
   • Endereço completo
4. Clique em "Salvar Cliente"`
        },
        {
          title: 'Como cadastrar cliente PJ',
          content: `1. Vá em Cadastros > Pessoas Jurídicas
2. Clique em "Nova Pessoa Jurídica"
3. Preencha os dados:
   • Razão Social (obrigatório)
   • CNPJ (obrigatório)
   • Nome Fantasia
   • Email
   • Telefone
   • Endereço completo
4. (Opcional) Preencha os Dados Sensíveis se você for admin
5. Clique em "Salvar Cliente"`
        },
        {
          title: 'Como vincular cliente a uma licença',
          content: `Ao criar ou editar uma licença:
1. Localize a seção "Cliente"
2. Selecione entre "Cliente PF" ou "Cliente PJ"
3. Escolha o cliente desejado no dropdown
4. Salve a licença

⚠️ Nota: Uma licença pode ser vinculada a apenas um cliente (PF OU PJ), não ambos.`
        }
      ]
    },
    {
      id: 'authentication',
      icon: Key,
      title: '🔑 Sistema de Autenticação',
      category: 'Acesso',
      tags: ['login', 'senha', 'credenciais'],
      sections: [
        {
          title: 'Múltiplas formas de login',
          content: `O sistema aceita login através de:
• Email (ex: admin@example.com)
• Número de Série (ex: SER001)
• Formato Hexadecimal (ex: 0x1A2B3C)
• Código Decimal (ex: 123456789)
• Código Alfanumérico (ex: ABC123DEF)

Basta digitar qualquer formato no campo "Código de Identificação" e o sistema encontrará automaticamente.`
        },
        {
          title: 'Redirecionamento inteligente',
          content: `Após o login, o sistema redireciona automaticamente:

ADMIN:
→ /dashboard (Painel Administrativo)

USER:
→ /minhas-licencas (Visualização de Licenças)

Isso garante que cada usuário veja apenas o que precisa.`
        },
        {
          title: 'Como alterar senha',
          content: `1. Clique no seu avatar no canto superior direito
2. Selecione "Perfil"
3. Clique em "Alterar Senha"
4. Digite a senha atual
5. Digite a nova senha (mínimo 6 caracteres)
6. Confirme a nova senha
7. Clique em "Salvar Alterações"

⚠️ A senha será alterada imediatamente e você continuará logado.`
        },
        {
          title: 'Recuperação de senha',
          content: `Se esqueceu sua senha:
1. Na tela de login, clique em "Esqueci minha senha"
2. Digite seu email cadastrado
3. Você receberá um link de recuperação
4. Clique no link e defina uma nova senha

⚠️ O link expira em 1 hora por segurança.`
        }
      ]
    },
    {
      id: 'troubleshooting',
      icon: AlertCircle,
      title: '🔧 Solução de Problemas',
      category: 'Suporte',
      tags: ['erro', 'problema', 'bug'],
      sections: [
        {
          title: 'Não consigo fazer login',
          content: `Verifique:
✓ Email ou código de identificação está correto
✓ Senha está correta (atenção para maiúsculas/minúsculas)
✓ Sua conta está ativa (não desativada)
✓ Você está usando a aba correta (Usuário/Registrar)

Se o problema persistir, contate o administrador com o código de erro exibido.`
        },
        {
          title: 'Não vejo licenças no painel',
          content: `Possíveis causas:
• Nenhuma licença foi criada ainda
• Licenças não foram atribuídas a você
• Filtros de status estão ativos (verifique se não está filtrando apenas "Ativo" quando todas são "Expiradas")
• Problema de isolamento multi-tenancy (cada admin vê apenas suas próprias licenças)

Solução: Clique em "Limpar filtros" ou contate o administrador.`
        },
        {
          title: 'Erro ao criar/editar registro',
          content: `Se aparecer erro de validação:
1. Verifique se todos os campos obrigatórios (*) estão preenchidos
2. Verifique formatos (CPF: 000.000.000-00, CNPJ: 00.000.000/0000-00)
3. Verifique se o email é válido
4. Verifique se não há registros duplicados (CPF/CNPJ/Email já cadastrado)

Se o erro persistir, anote a mensagem completa e contate o suporte.`
        },
        {
          title: 'Interface não está atualizando',
          content: `Tente estas soluções:
1. Limpe o cache do navegador (Ctrl+Shift+Delete)
2. Atualize a página (F5 ou Ctrl+R)
3. Faça logout e login novamente
4. Tente em modo anônimo/privado do navegador
5. Teste em outro navegador

Se nada funcionar, pode ser um problema de servidor. Contate o administrador.`
        }
      ]
    },
    {
      id: 'multi-tenancy',
      icon: Building2,
      title: '🏢 Sistema Multi-Tenancy',
      category: 'Arquitetura',
      tags: ['multitenancy', 'isolamento', 'segurança', 'empresa'],
      sections: [
        {
          title: 'O que é Multi-Tenancy?',
          content: `Multi-tenancy é uma arquitetura onde múltiplas empresas (tenants) compartilham a mesma aplicação, mas cada uma tem seus dados completamente isolados.

CONCEITO:
• Cada empresa tem seu próprio "espaço" no sistema
• Dados são isolados por tenant_id
• Uma empresa NÃO consegue ver dados de outra
• Infraestrutura é compartilhada, mas dados não

ANALOGIA:
Imagine um prédio de apartamentos:
• Prédio = Sistema License Manager
• Apartamentos = Empresas (tenants)
• Cada apartamento tem sua própria chave
• Você não consegue entrar no apartamento do vizinho`,
          image: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&auto=format&fit=crop&q=60',
          imageCaption: 'Visualização conceitual de multi-tenancy: múltiplas empresas isoladas'
        },
        {
          title: 'Como funciona o isolamento?',
          content: `ISOLAMENTO AUTOMÁTICO:
Quando você faz login, o sistema:
1. Identifica seu tenant_id (empresa)
2. Todas as consultas são filtradas por esse ID
3. Você só vê licenças/usuários/clientes da sua empresa
4. Outras empresas não aparecem nos seus resultados

EXEMPLO PRÁTICO:
Empresa A (Autotech):
• Vê apenas suas 50 licenças
• Vê apenas seus 5 usuários
• Vê apenas seus 30 clientes

Empresa B (Competitor):
• Vê apenas suas 30 licenças
• Vê apenas seus 3 usuários
• Vê apenas seus 20 clientes

Elas NUNCA veem dados uma da outra!`
        },
        {
          title: 'Vantagens do Multi-Tenancy',
          content: `SEGURANÇA:
✓ Isolamento total de dados entre empresas
✓ Impossível acessar dados de outros tenants
✓ Cada empresa gerencia apenas seus próprios recursos

CUSTO:
✓ Infraestrutura compartilhada = custo menor
✓ Manutenção centralizada
✓ Updates automáticos para todos

ESCALABILIDADE:
✓ Adicionar nova empresa é instantâneo
✓ Não precisa criar nova instalação
✓ Sistema cresce automaticamente

MANUTENÇÃO:
✓ Um único sistema para manter
✓ Backups centralizados
✓ Monitoramento unificado`
        },
        {
          title: 'Quando você se registra',
          content: `O que acontece ao criar sua conta:
1. Sistema cria um novo tenant (empresa) automaticamente
2. Você se torna o primeiro admin dessa empresa
3. Recebe seu próprio tenant_id único
4. Seus dados ficam isolados desde o início
5. Você pode convidar outros usuários para sua empresa

PLANO FREE:
• Até 2 usuários
• Até 50 licenças
• Até 25 clientes
• 30 dias de trial

Depois pode fazer upgrade para planos maiores!`
        }
      ]
    },
    {
      id: 'sales-dashboard',
      icon: TrendingUp,
      title: '📊 Dashboard de Vendas',
      category: 'Ferramentas',
      tags: ['vendas', 'relatórios', 'renovação', 'dashboard'],
      sections: [
        {
          title: 'O que é o Sales Dashboard?',
          content: `O Sales Dashboard é uma ferramenta poderosa para:
• Visualizar licenças próximas do vencimento
• Identificar oportunidades de renovação
• Enviar lembretes via WhatsApp
• Acompanhar clientes em risco de cancelamento

ACESSO:
Menu superior → Métricas / Vendas

INFORMAÇÕES EXIBIDAS:
• Cliente e dados de contato
• Chave da licença
• Status (Venceu há X dias, Vence em X dias)
• Telefone (quando cadastrado)
• Botão de WhatsApp para contato rápido`
        },
        {
          title: 'Como usar os filtros',
          content: `FILTRO DE PERÍODO:
• 30 dias (padrão) - Licenças vencendo nos próximos 30 dias
• 60 dias - Visão mais ampla
• 90 dias - Planejamento de longo prazo

PESQUISA AVANÇADA:
Digite para buscar por:
• Nome do cliente
• Telefone
• Chave de licença
• Status (LOW, MEDIUM, HIGH)
• Valor (se cadastrado)

A busca é em tempo real!

BOTÃO LIMPAR:
Clique em "Limpar pesquisa" para voltar à lista completa`
        },
        {
          title: 'Envio de WhatsApp em massa',
          content: `FUNCIONALIDADE:
Envie mensagens de renovação para múltiplos clientes de uma vez.

COMO USAR:
1. Selecione os clientes (checkbox)
2. Clique em "Enviar WhatsApp em Massa"
3. Escolha ou crie uma mensagem template
4. Clique em "Enviar"
5. Sistema processa e envia automaticamente

VALIDAÇÕES:
✓ Cliente deve ter telefone cadastrado
✓ Licença deve estar válida ou próxima do vencimento
✓ Rate limiting: máximo 30 mensagens/minuto
✓ Idempotência: não envia duplicado em 1 hora

STATUS DO ENVIO:
• Sucesso: Mensagem enviada ✓
• Falha: Motivo do erro é exibido
• Bloqueado: Cliente sem telefone ou licença inválida`
        },
        {
          title: 'Interpretando os status',
          content: `STATUS DAS LICENÇAS:

🟢 ACTIVE (Verde):
• Licença válida e funcionando
• Sem ação imediata necessária

🟡 LOW (Amarelo):
• Vence em 7-30 dias
• Enviar lembrete de renovação

🟠 MEDIUM (Laranja):
• Vence em 3-7 dias
• Urgente: contatar cliente

🔴 HIGH (Vermelho):
• Venceu ou vence em 0-3 dias
• Crítico: ação imediata
• Cliente pode perder acesso

⚫ EXPIRED (Cinza):
• Licença expirada há mais de 30 dias
• Considerar reativação ou arquivamento`
        }
      ]
    },
    {
      id: 'security-privacy',
      icon: Lock,
      title: '🔒 Segurança e Privacidade (LGPD)',
      category: 'Segurança',
      tags: ['lgpd', 'privacidade', 'segurança', 'isolamento', 'dados'],
      sections: [
        {
          title: 'Conformidade LGPD',
          content: `O sistema está 100% conforme à Lei Geral de Proteção de Dados (LGPD):

ISOLAMENTO DE DADOS:
✓ Cada empresa/tenant tem dados completamente isolados
✓ Impossível acessar dados de outras empresas
✓ Filtros de tenant aplicados automaticamente em TODAS as consultas
✓ Auditoria completa de acessos

ARTIGOS LGPD ATENDIDOS:
✓ Art. 6º - Adequação: Dados tratados para finalidade legítima
✓ Art. 46 - Segurança: Medidas técnicas de proteção
✓ Art. 47 - Segregação: Dados de titulares isolados
✓ Art. 48 - Comunicação de Incidentes: Logs e auditoria

GARANTIAS DE PRIVACIDADE:
• Você NUNCA verá dados de outros clientes
• Outros clientes NUNCA verão seus dados
• Cada login acessa apenas seu próprio tenant
• Sistema multi-tenancy com isolamento rigoroso`,
          image: 'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&auto=format&fit=crop&q=60',
          imageCaption: 'Segurança e conformidade LGPD garantida'
        },
        {
          title: 'Como funciona o isolamento de dados?',
          content: `Quando você faz login, o sistema:

1. IDENTIFICA SEU TENANT:
   • Busca seu tenant_id único no banco
   • Associa sua sessão ao seu tenant
   • Todas as requisições carregam esse ID

2. FILTRA AUTOMATICAMENTE:
   • TODAS as consultas incluem tenant_id
   • Banco de dados só retorna SEUS dados
   • Outros tenants são invisíveis para você

3. VALIDA PERMISSÕES:
   • Verifica se você tem acesso ao recurso
   • Confirma que o recurso pertence ao seu tenant
   • Bloqueia acesso cross-tenant

EXEMPLO PRÁTICO:
Você (Empresa A - tenant_123):
  → Busca licenças
  → Sistema filtra: WHERE tenant_id = "123"
  → Retorna apenas SUAS licenças
  
Outra empresa (Empresa B - tenant_456):
  → Busca licenças
  → Sistema filtra: WHERE tenant_id = "456"
  → Retorna apenas licenças DELA
  
Resultado: ISOLAMENTO TOTAL ✅`
        },
        {
          title: 'Como testar se meu isolamento está funcionando?',
          content: `TESTE SIMPLES:
1. Cadastre nova conta com email diferente
2. Faça login com a nova conta
3. Vá ao Dashboard
4. Verifique contadores: DEVEM mostrar ZERO
   • 0 Licenças
   • 0 Usuários
   • 0 Clientes
   • 0 Contatos WhatsApp

Se você VER dados já existentes = BUG DE SEGURANÇA
Contate imediatamente o administrador!

INDICADORES DE ISOLAMENTO OK:
✅ Novo tenant começa com dados vazios
✅ Não vê licenças de outros
✅ Não vê usuários de outros
✅ Dashboard mostra apenas seus próprios dados`
        },
        {
          title: 'O que fazer se suspeitar de vazamento de dados?',
          content: `AÇÃO IMEDIATA:
1. NÃO COMPARTILHE informações vistas
2. ANOTE exatamente o que viu:
   • Que tela estava
   • Que dados apareceram
   • Horário do incidente
3. TIRE SCREENSHOT (se possível)
4. SAIA DO SISTEMA imediatamente
5. CONTATE o suporte técnico

INFORMAÇÕES A FORNECER:
• Seu email de login
• Tela onde viu os dados
• Descrição dos dados vistos
• Horário aproximado

O suporte irá:
• Investigar imediatamente
• Corrigir o problema
• Notificar afetados (se necessário)
• Documentar incidente para LGPD

IMPORTANTE: 
Vazamento de dados é CRIME pela LGPD.
Reporte sempre que suspeitar!`
        }
      ]
    },
    {
      id: 'registration-issues',
      icon: UserCircle,
      title: '👤 Problemas com Cadastro',
      category: 'Solução de Problemas',
      tags: ['registro', 'cadastro', 'senha', 'login'],
      sections: [
        {
          title: 'Erro: "Email já registrado"',
          content: `CAUSA:
Você está tentando usar um email que já existe no sistema.

SOLUÇÕES:
1. Use email diferente:
   ✓ seunome+empresa@gmail.com
   ✓ contato@suaempresa.com.br
   ✓ Variação do email existente

2. Recupere a senha do email existente:
   ✓ Clique em "Esqueci minha senha"
   ✓ Digite o email cadastrado
   ✓ Receba link de recuperação
   ✓ Defina nova senha

3. Se não lembra de ter cadastrado:
   ✓ Pode ter testado antes
   ✓ Outro colaborador pode ter usado
   ✓ Contate suporte para verificação`
        },
        {
          title: 'Erro: "As senhas não coincidem"',
          content: `CAUSA:
Senha e confirmação de senha estão diferentes.

SOLUÇÃO:
1. Digite a senha no primeiro campo
2. Digite EXATAMENTE a mesma senha no segundo campo
3. ATENÇÃO para:
   ✓ Maiúsculas e minúsculas
   ✓ Espaços no início ou fim
   ✓ Caracteres especiais
   
DICAS:
• Use o botão 👁️ para ver a senha
• Copie e cole entre os campos (Ctrl+C / Ctrl+V)
• Use gerenciador de senhas`
        },
        {
          title: 'Erro: "Conta requer redefinição de senha"',
          content: `CAUSA:
Conta foi criada mas senha não foi configurada corretamente.

SOLUÇÕES:
1. USUÁRIO NORMAL:
   ✓ Clique em "Esqueci minha senha"
   ✓ Siga o processo de recuperação
   
2. ADMIN DO SISTEMA:
   ✓ Contate suporte técnico
   ✓ Informe seu email
   ✓ Suporte resetará sua senha
   
3. PRIMEIRO ACESSO:
   ✓ Use a senha fornecida pelo admin
   ✓ Sistema pedirá para trocar
   ✓ Defina sua própria senha segura

PREVENÇÃO:
Sempre complete o cadastro com senha forte e anote em local seguro.`
        },
        {
          title: 'Cadastro criado mas não consigo fazer login',
          content: `VERIFICAÇÕES:
1. EMAIL CORRETO?
   ✓ Verifique se não tem espaços extras
   ✓ Confirme @ e domínio corretos
   ✓ Teste maiúsculas/minúsculas

2. SENHA CORRETA?
   ✓ Atenção para maiúsculas
   ✓ Verifique Caps Lock
   ✓ Teste copiar e colar

3. CONTA ATIVA?
   ✓ Admin pode ter desativado
   ✓ Pode estar pendente de aprovação
   ✓ Verifique email de confirmação

4. NAVEGADOR/CACHE:
   ✓ Limpe cache (Ctrl+Shift+Delete)
   ✓ Teste em modo anônimo
   ✓ Teste em outro navegador

Se nada funcionar:
→ Cadastre nova conta com email diferente
→ Ou contate suporte com seu email`
        }
      ]
    },
    {
      id: 'engineering-panel',
      icon: Settings,
      title: '🔧 Painel de Engenharia',
      category: 'Restrito - Engenharia',
      tags: ['admin', 'engenharia', 'desenvolvimento', 'roadmap', 'comercialização'],
      restrictedTo: ['super_admin', 'admin'], // Apenas super admins veem
      sections: [
        {
          title: '🎯 Avaliação para Comercialização',
          content: `STATUS ATUAL DO SISTEMA PARA VENDA:`,
          checklist: [
            {
              id: 'config_domain',
              priority: 'critical',
              title: 'Configurar domínio www.autotech.app.br',
              description: 'Migrar de preview para domínio próprio',
              category: 'Infraestrutura'
            },
            {
              id: 'backup_auto',
              priority: 'critical',
              title: 'Implementar backup automático diário',
              description: 'MongoDB backup com retenção de 30 dias',
              category: 'Infraestrutura'
            },
            {
              id: 'monitoring',
              priority: 'critical',
              title: 'Configurar monitoramento de uptime',
              description: 'Alertas por email/SMS se sistema cair',
              category: 'Infraestrutura'
            },
            {
              id: 'sla',
              priority: 'critical',
              title: 'Definir SLA de suporte',
              description: 'Ex: resposta em 24h úteis',
              category: 'Comercial'
            },
            {
              id: 'contract',
              priority: 'critical',
              title: 'Criar template de contrato',
              description: 'Termos de uso, responsabilidades, LGPD',
              category: 'Comercial'
            },
            {
              id: 'pricing',
              priority: 'critical',
              title: 'Definir política de preços',
              description: 'Planos Free, Basic, Premium, Enterprise',
              category: 'Comercial'
            },
            {
              id: 'load_test',
              priority: 'critical',
              title: 'Testar com dados reais (50+ licenças)',
              description: 'Simular uso real antes de vender',
              category: 'Qualidade'
            },
            {
              id: 'sales_tracking',
              priority: 'important',
              title: 'Implementar tracking no Sales Dashboard',
              description: 'Contatos, conversões, receita real',
              category: 'Funcionalidade'
            },
            {
              id: 'whatsapp_doc',
              priority: 'important',
              title: 'Documentar setup de WhatsApp Business',
              description: 'Guia passo a passo para clientes',
              category: 'Documentação'
            },
            {
              id: 'video_tutorials',
              priority: 'important',
              title: 'Criar vídeos tutoriais',
              description: '5-10 vídeos de 3-5min cada',
              category: 'Documentação'
            },
            {
              id: 'onboarding',
              priority: 'important',
              title: 'Preparar materiais de onboarding',
              description: 'Checklist de setup para novos clientes',
              category: 'Documentação'
            },
            {
              id: 'stress_test',
              priority: 'important',
              title: 'Testes de carga (100 usuários simultâneos)',
              description: 'Garantir performance sob carga',
              category: 'Qualidade'
            }
          ]
        },
        {
          title: '🚀 Roadmap Técnico',
          content: `FUNCIONALIDADES PLANEJADAS POR PRIORIDADE:`,
          checklist: [
            {
              id: 'redis_cache',
              priority: 'high',
              title: 'Cache Redis para queries frequentes',
              description: 'Melhorar performance em 50%+',
              category: 'Performance'
            },
            {
              id: 'audit_log',
              priority: 'high',
              title: 'Sistema de Audit Log completo',
              description: 'Rastrear todas as ações críticas',
              category: 'Segurança'
            },
            {
              id: 'export_reports',
              priority: 'medium',
              title: 'Exportação de relatórios (PDF/Excel)',
              description: 'Licenças, clientes, vendas',
              category: 'Funcionalidade'
            },
            {
              id: 'email_notifications',
              priority: 'medium',
              title: 'Notificações por email',
              description: 'Alertas de expiração, renovações',
              category: 'Funcionalidade'
            },
            {
              id: 'mobile_app',
              priority: 'low',
              title: 'Aplicativo Mobile (React Native)',
              description: 'iOS e Android',
              category: 'Expansão'
            },
            {
              id: 'public_api',
              priority: 'low',
              title: 'API Pública para Integrações',
              description: 'Permitir integrações externas',
              category: 'Expansão'
            }
          ]
        },
        {
          title: '⚠️ Issues Conhecidos',
          content: `PROBLEMAS IDENTIFICADOS E STATUS DE CORREÇÃO:`,
          checklist: [
            {
              id: 'fix_sales_metrics',
              priority: 'high',
              title: 'Sales Dashboard - Métricas zeradas',
              description: 'Implementar tracking real de vendas',
              category: 'Bug/Feature'
            },
            {
              id: 'whatsapp_rate_limit',
              priority: 'medium',
              title: 'WhatsApp - Rate limiting não testado em prod',
              description: 'Testar com API real',
              category: 'Integração'
            },
            {
              id: 'tenant_isolation_test',
              priority: 'high',
              title: 'Testes de isolamento multi-tenant',
              description: 'Garantir 100% de isolamento',
              category: 'Segurança'
            }
          ]
        },
        {
          title: '💰 Estratégia de Go-to-Market',
          content: `PLANO DE LANÇAMENTO COMERCIAL:

FASE 1 - Beta (0-3 clientes):
• Preço: Gratuito por 30 dias
• Objetivo: Coletar feedback, encontrar bugs
• Duração: 1 mês

FASE 2 - Early Adopters (3-10 clientes):
• Preço: 50-70% desconto
• Contrato: 6 meses
• Suporte: Dedicado

FASE 3 - Lançamento Comercial (10+ clientes):
• Preço: Tabela completa
• Contratos: Anuais
• Marketing: Ativo

PREÇOS SUGERIDOS (mensais):
🆓 Free: R$ 0 (2 users, 50 licenses)
💼 Basic: R$ 199 (5 users, 200 licenses)
⭐ Premium: R$ 499 (20 users, 1000 licenses)
👑 Enterprise: R$ 999+ (ilimitado, customizado)`
        }
      ]
    },
    {
      id: 'best-practices',
      icon: CheckCircle,
      title: '✨ Melhores Práticas',
      category: 'Recomendações',
      tags: ['dicas', 'segurança', 'organização'],
      sections: [
        {
          title: 'Segurança de senha',
          content: `Recomendações:
✓ Use no mínimo 8 caracteres
✓ Combine letras maiúsculas, minúsculas, números e símbolos
✓ Não use informações pessoais (nome, data de nascimento)
✓ Não reutilize senhas de outros sistemas
✓ Troque sua senha a cada 90 dias
✓ Nunca compartilhe sua senha

Exemplo de senha forte: T3ch@2024!Sec`
        },
        {
          title: 'Organização de licenças',
          content: `Dicas para manter suas licenças organizadas:
• Use nomes descritivos (ex: "Licença Premium - Empresa ABC")
• Preencha a descrição com detalhes importantes
• Associe sempre ao cliente correto (PF ou PJ)
• Defina datas de expiração realistas
• Use categorias para agrupar licenças similares
• Revise periodicamente licenças expiradas

Isso facilita a busca e manutenção futura.`
        },
        {
          title: 'Cadastro de clientes',
          content: `Boas práticas ao cadastrar clientes:
• Valide CPF/CNPJ antes de cadastrar
• Mantenha dados de contato atualizados (email, telefone)
• Preencha endereço completo para fins fiscais
• Para PJ, preencha Dados Sensíveis apenas se necessário
• Use campo de observações para informações adicionais
• Mantenha um padrão de nomenclatura consistente

Dados completos facilitam comunicação e suporte.`
        },
        {
          title: 'Proteção de dados sensíveis',
          content: `Para admins que gerenciam dados sensíveis:
• Só preencha dados sensíveis quando realmente necessário
• Não compartilhe senhas por email ou chat
• Use o botão "Copiar" ao invés de digitar manualmente
• Sempre oculte os dados após visualizar (botão de ocultar)
• Forneça apenas o código de referência para usuários comuns
• Revise periodicamente quem tem acesso aos dados
• Mantenha log de quem acessou informações críticas

A segurança depende do uso responsável.`
        }
      ]
    }
  ];

  const filteredContent = helpContent.filter(item => {
    const searchLower = searchTerm.toLowerCase();
    return (
      item.title.toLowerCase().includes(searchLower) ||
      item.category.toLowerCase().includes(searchLower) ||
      item.tags.some(tag => tag.includes(searchLower)) ||
      item.sections.some(section => 
        section.title.toLowerCase().includes(searchLower) ||
        section.content.toLowerCase().includes(searchLower)
      )
    );
  });

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl">
            <BookOpen className="w-6 h-6 text-blue-600" />
            Central de Ajuda e Documentação
          </DialogTitle>
          <DialogDescription>
            Encontre guias, tutoriais e respostas para suas dúvidas sobre o sistema
          </DialogDescription>
        </DialogHeader>

        {/* Search Bar */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Buscar por tópico, funcionalidade ou palavra-chave..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Results Info */}
        {searchTerm && (
          <div className="text-sm text-gray-600 mb-2">
            {filteredContent.length} resultado(s) encontrado(s)
          </div>
        )}

        {/* Content Area - Scrollable */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {filteredContent.length === 0 ? (
            <div className="text-center py-12">
              <HelpCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Nenhum resultado encontrado
              </h3>
              <p className="text-gray-500">
                Tente usar palavras-chave diferentes ou navegue pelas categorias abaixo
              </p>
            </div>
          ) : (
            filteredContent.map((item) => {
              const Icon = item.icon;
              const isExpanded = expandedSection === item.id;

              return (
                <div key={item.id} className="border rounded-lg overflow-hidden">
                  {/* Header */}
                  <button
                    onClick={() => toggleSection(item.id)}
                    className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="w-5 h-5 text-blue-600" />
                      <div className="text-left">
                        <h3 className="font-semibold text-gray-900">{item.title}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {item.category}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {item.sections.length} tópico(s)
                          </span>
                        </div>
                      </div>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-500" />
                    )}
                  </button>

                  {/* Content */}
                  {isExpanded && (
                    <div className="p-4 bg-white space-y-6">
                      {item.sections.map((section, idx) => (
                        <div key={idx} className="border-l-4 border-blue-500 pl-4">
                          <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-blue-600" />
                            {section.title}
                          </h4>
                          <div className="text-sm text-gray-700 whitespace-pre-line mb-4">
                            {section.content}
                          </div>
                          
                          {/* Renderizar checklist interativo se existir */}
                          {section.checklist && (
                            <div className="space-y-2 mt-4">
                              {section.checklist.map((checkItem) => {
                                const isChecked = engineeringChecklist[checkItem.id] || false;
                                const priorityColors = {
                                  critical: 'bg-red-50 border-red-200',
                                  high: 'bg-orange-50 border-orange-200',
                                  important: 'bg-yellow-50 border-yellow-200',
                                  medium: 'bg-blue-50 border-blue-200',
                                  low: 'bg-gray-50 border-gray-200'
                                };
                                const priorityBadges = {
                                  critical: 'bg-red-100 text-red-800',
                                  high: 'bg-orange-100 text-orange-800',
                                  important: 'bg-yellow-100 text-yellow-800',
                                  medium: 'bg-blue-100 text-blue-800',
                                  low: 'bg-gray-100 text-gray-800'
                                };
                                
                                return (
                                  <div 
                                    key={checkItem.id}
                                    className={`p-3 rounded-lg border ${priorityColors[checkItem.priority]} ${isChecked ? 'opacity-60' : ''}`}
                                  >
                                    <div className="flex items-start gap-3">
                                      <input
                                        type="checkbox"
                                        checked={isChecked}
                                        onChange={() => toggleChecklistItem(checkItem.id)}
                                        className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                                      />
                                      <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                          <span className={`text-xs px-2 py-0.5 rounded ${priorityBadges[checkItem.priority]}`}>
                                            {checkItem.priority.toUpperCase()}
                                          </span>
                                          <span className="text-xs text-gray-500">{checkItem.category}</span>
                                        </div>
                                        <p className={`font-medium text-sm ${isChecked ? 'line-through text-gray-500' : 'text-gray-900'}`}>
                                          {checkItem.title}
                                        </p>
                                        <p className="text-xs text-gray-600 mt-1">
                                          {checkItem.description}
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}
                              
                              {/* Barra de progresso */}
                              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-sm font-medium text-gray-700">Progresso</span>
                                  <span className="text-sm font-bold text-blue-600">
                                    {Math.round((section.checklist.filter(item => engineeringChecklist[item.id]).length / section.checklist.length) * 100)}%
                                  </span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div 
                                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                    style={{
                                      width: `${(section.checklist.filter(item => engineeringChecklist[item.id]).length / section.checklist.length) * 100}%`
                                    }}
                                  />
                                </div>
                                <p className="text-xs text-gray-500 mt-2">
                                  {section.checklist.filter(item => engineeringChecklist[item.id]).length} de {section.checklist.length} concluídos
                                </p>
                              </div>
                            </div>
                          )}
                          
                          {/* Renderizar imagem se existir */}
                          {section.image && (
                            <div className="mt-4 rounded-lg overflow-hidden border border-gray-200">
                              <img 
                                src={section.image} 
                                alt={section.title}
                                className="w-full h-auto max-h-96 object-contain bg-gray-50"
                                loading="lazy"
                              />
                              {section.imageCaption && (
                                <div className="px-3 py-2 bg-gray-50 text-xs text-gray-600 italic">
                                  {section.imageCaption}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="mt-4 pt-4 border-t flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>Precisa de mais ajuda?</span>
          </div>
          <a
            href="mailto:suporte@licensemanager.com"
            className="text-blue-600 hover:underline flex items-center gap-1"
          >
            Contate o Suporte
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default HelpCenter;
