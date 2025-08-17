/**
 * Help System - Base de Conhecimento
 * Contém todas as informações contextuais do sistema
 */

export const HELP_DATABASE = {
  // Dashboard Principal
  "dashboard": {
    "overview": {
      title: "Dashboard Principal",
      description: "Visão geral do sistema com métricas principais de licenças e usuários",
      tips: [
        "Cards mostram estatísticas em tempo real",
        "Gráficos são atualizados automaticamente",
        "Clique nos números para ver detalhes"
      ],
      shortcuts: ["Alt+D para voltar ao dashboard"]
    },
    "metrics": {
      title: "Métricas do Sistema",
      description: "Indicadores principais de performance e uso",
      tips: [
        "Licenças Ativas: Total de licenças funcionais",
        "Usuários Cadastrados: Clientes no sistema",
        "Taxa de Renovação: % de renovações bem-sucedidas"
      ]
    }
  },

  // Dashboard de Vendas
  "sales-dashboard": {
    "overview": {
      title: "Dashboard de Vendas",
      description: "Transforma alertas técnicos em oportunidades de vendas automáticas",
      tips: [
        "Licenças expirando viram leads automáticos",
        "WhatsApp tem 60% mais resposta que email",
        "Mensagens personalizadas por urgência",
        "Sistema prioriza por valor potencial"
      ],
      benefits: [
        "Aumenta taxa de renovação em 40-60%",
        "Reduz churn de clientes",
        "Automatiza follow-up de vendas",
        "Gera receita 24/7"
      ]
    },
    "metrics": {
      title: "Métricas de Vendas",
      description: "KPIs principais para acompanhar performance de vendas",
      tips: [
        "Taxa de Conversão: % de renovações vs contatos",
        "Receita Potencial: Valor total de oportunidades",
        "Contatos por Canal: WhatsApp, telefone, email",
        "Alertas por Prioridade: High, Medium, Low"
      ]
    },
    "whatsapp-send": {
      title: "Envio de WhatsApp",
      description: "Envia mensagem personalizada para renovação de licenças",
      steps: [
        "1. Sistema detecta licença expirando",
        "2. Gera template baseado na urgência (T-30, T-7, T-1)",
        "3. Personaliza com dados do cliente",
        "4. Envia via WhatsApp automaticamente",
        "5. Registra resultado para analytics"
      ],
      tips: [
        "T-30: Mensagem amigável de lembrete",
        "T-7: Urgente com oferta especial", 
        "T-1: Crítico com desconto",
        "Vencida: Reativação imediata"
      ]
    },
    "bulk-whatsapp": {
      title: "Campanha em Lote",
      description: "Envia mensagens para múltiplos clientes simultaneamente",
      tips: [
        "Selecione alertas usando checkboxes",
        "Máximo 50 mensagens por lote",
        "Delay automático entre envios",
        "Relatório detalhado de resultados"
      ],
      warnings: [
        "Use com moderação para evitar spam",
        "Verifique números antes do envio",
        "Monitore taxa de resposta"
      ]
    },
    "analytics": {
      title: "Analytics de Vendas",
      description: "Métricas avançadas por canal e vendedor",
      insights: [
        "WhatsApp: Maior taxa de resposta",
        "Telefone: Melhor taxa de conversão",
        "Email: Maior alcance mas menor engajamento",
        "Vendedores top: João (23 conversões), Maria (19)"
      ]
    }
  },

  // WhatsApp Integration
  "whatsapp": {
    "connection": {
      title: "Conexão WhatsApp",
      description: "Configure e gerencie a conexão com WhatsApp Business",
      steps: [
        "1. Abra WhatsApp no celular",
        "2. Vá em Configurações > Dispositivos Conectados",
        "3. Clique em 'Conectar Dispositivo'",
        "4. Escaneie o QR code mostrado aqui",
        "5. Confirme a conexão no celular"
      ],
      tips: [
        "Use um número dedicado para o negócio",
        "Mantenha o celular sempre conectado",
        "QR code expira em 60 segundos",
        "Reconexão automática em caso de queda"
      ]
    },
    "status": {
      title: "Status da Conexão",
      description: "Monitor do status da conexão WhatsApp em tempo real",
      statuses: {
        "connected": "✅ Conectado e funcionando",
        "qr_generated": "📱 QR code disponível para scan",
        "disconnected": "❌ Desconectado",
        "reconnecting": "🔄 Tentando reconectar"
      }
    }
  },

  // Client Management  
  "clients": {
    "overview": {
      title: "Gestão de Clientes",
      description: "Cadastro completo de Pessoa Física (PF) e Pessoa Jurídica (PJ)",
      tips: [
        "PF: Para clientes individuais",
        "PJ: Para empresas e organizações",
        "Dados sensíveis são mascarados por segurança",
        "LGPD: Todos os dados são protegidos"
      ]
    },
    "pf": {
      title: "Pessoa Física (PF)",
      description: "Cadastro de clientes individuais",
      required_fields: [
        "Nome completo",
        "CPF (validação automática)",
        "Email de contato",
        "Telefone/WhatsApp"
      ],
      optional_fields: [
        "Data de nascimento",
        "Endereço completo",
        "Observações"
      ]
    },
    "pj": {
      title: "Pessoa Jurídica (PJ)", 
      description: "Cadastro de empresas e organizações",
      required_fields: [
        "Razão social",
        "CNPJ (validação automática)",
        "Email corporativo",
        "Telefone comercial"
      ],
      optional_fields: [
        "Nome fantasia",
        "Inscrição estadual",
        "Endereço da sede",
        "Responsável técnico"
      ]
    }
  },

  // License Management
  "licenses": {
    "overview": {
      title: "Gerenciamento de Licenças",
      description: "Controle completo do ciclo de vida das licenças",
      tips: [
        "Status é atualizado automaticamente",
        "Alertas de vencimento são enviados automaticamente",
        "Histórico completo de renovações"
      ]
    },
    "status": {
      title: "Status das Licenças",
      description: "Diferentes estados do ciclo de vida",
      statuses: {
        "active": "✅ Ativa e funcionando",
        "expiring": "⚠️ Expirando em breve",
        "expired": "❌ Vencida",
        "suspended": "⏸️ Suspensa",
        "cancelled": "🚫 Cancelada"
      }
    }
  },

  // Registry Module
  "registry": {
    "overview": {
      title: "Módulo de Registro", 
      description: "Configuração de categorias, produtos e planos de licença",
      tips: [
        "Organize produtos por categoria",
        "Configure preços e durações",
        "Defina regras de renovação automática"
      ]
    },
    "categories": {
      title: "Categorias de Produtos",
      description: "Organize produtos em categorias lógicas",
      examples: [
        "Software: Aplicativos e sistemas",
        "Hardware: Equipamentos e dispositivos", 
        "Serviços: Consultorias e suporte",
        "Licenças: Certificados e permissões"
      ]
    }
  },

  // Admin Panel
  "admin": {
    "overview": {
      title: "Painel Administrativo",
      description: "Ferramentas avançadas para administradores do sistema",
      capabilities: [
        "Gestão completa de usuários",
        "Configurações do sistema",
        "Logs e auditoria",
        "Backup e restore"
      ],
      security: "Acesso restrito a administradores"
    },
    "users": {
      title: "Gestão de Usuários",
      description: "Controle de acesso e permissões",
      tips: [
        "Diferentes níveis de acesso (Admin, User)",
        "Ativação/desativação rápida",
        "Histórico de login e atividades",
        "Reset de senha automático"
      ]
    }
  },

  // Maintenance
  "maintenance": {
    "overview": {
      title: "Módulo de Manutenção",
      description: "Logs do sistema e ferramentas de diagnóstico",
      tips: [
        "Logs em tempo real",
        "Filtros por data e tipo",
        "Export para análise externa",
        "Alertas de erro automáticos"
      ]
    },
    "logs": {
      title: "Logs do Sistema",
      description: "Registro detalhado de todas as atividades",
      types: [
        "INFO: Operações normais",
        "WARN: Situações de atenção",
        "ERROR: Erros e falhas",
        "DEBUG: Informações técnicas"
      ]
    }
  },

  // General System
  "system": {
    "navigation": {
      title: "Navegação do Sistema",
      description: "Como navegar eficientemente pelo sistema",
      shortcuts: [
        "Alt+D: Dashboard principal",
        "Alt+V: Dashboard de vendas",
        "Alt+C: Clientes",
        "Alt+L: Licenças",
        "Esc: Fechar modais"
      ]
    },
    "search": {
      title: "Sistema de Busca",
      description: "Como encontrar informações rapidamente",
      tips: [
        "Use * para busca parcial",
        "Combine termos com espaço",
        "Filtros avançados disponíveis",
        "Resultados em tempo real"
      ]
    }
  }
};

// Função helper para buscar ajuda
export const getHelpContent = (module, section) => {
  return HELP_DATABASE[module]?.[section] || null;
};

// Função para buscar todas as seções de um módulo
export const getModuleHelp = (module) => {
  return HELP_DATABASE[module] || {};
};

// Função para buscar ajuda por palavra-chave
export const searchHelp = (keyword) => {
  const results = [];
  const searchTerm = keyword.toLowerCase();
  
  Object.entries(HELP_DATABASE).forEach(([module, sections]) => {
    Object.entries(sections).forEach(([section, content]) => {
      const searchText = `${content.title} ${content.description}`.toLowerCase();
      if (searchText.includes(searchTerm)) {
        results.push({
          module,
          section,
          ...content,
          relevance: searchText.indexOf(searchTerm)
        });
      }
    });
  });
  
  return results.sort((a, b) => a.relevance - b.relevance);
};