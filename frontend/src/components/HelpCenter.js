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
  ExternalLink
} from 'lucide-react';

const HelpCenter = ({ isOpen, onClose }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedSection, setExpandedSection] = useState(null);

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
• Chaves de acesso (WiFi, hardware keys)`
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
5. O usuário receberá as credenciais para primeiro acesso`
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
                          <div className="text-sm text-gray-700 whitespace-pre-line">
                            {section.content}
                          </div>
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
