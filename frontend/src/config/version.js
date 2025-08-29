// Sistema de Versionamento do License Manager
export const VERSION_CONFIG = {
  // Versão atual do sistema
  version: "1.3.1",
  
  // Status da versão
  status: "stable", // "stable", "beta", "rc", "alpha", "dev"
  
  // Informações da versão
  releaseDate: "2024-12-29",
  buildNumber: "20241229001",
  
  // Informações da empresa e licenciamento
  company: {
    name: "Autotech Services Importações LTDA",
    shortName: "AutoTech",
    contact: {
      support: "autotechserviceimport@gmail.com",
      legal: "autotechserviceimport@gmail.com", 
      documentation: "autotechserviceimport@gmail.com"
    },
    copyright: "© 2025 AutoTech. Todos os direitos reservados.",
    website: null // Pode ser adicionado futuramente
  },
  
  // Informações do software
  software: {
    name: "Sistema de Gerenciamento de Licenças",
    englishName: "License Management System",
    description: "Sistema completo de gerenciamento de licenças empresariais com multi-tenancy, RBAC e integração WhatsApp Business para conversão de vendas.",
    license: "Licença Proprietária",
    licenseTerms: "Software proprietário da AutoTech Services. Uso restrito aos termos de licenciamento.",
    
    // Tecnologias utilizadas
    technologies: {
      backend: ["FastAPI (Python)", "Motor (MongoDB)", "JWT Authentication", "Pydantic", "Redis"],
      frontend: ["React 18", "Tailwind CSS", "Radix UI", "React Router", "Axios"],
      database: ["MongoDB com Motor (AsyncIO)"],
      integrations: ["WhatsApp Business API (Baileys)", "Node.js Microservice"],
      architecture: ["Full-stack RESTful", "Multi-tenancy", "RBAC", "Microserviços"],
      utilities: ["Sistema de Logs", "WCAG 2.1", "Versionamento Semântico"]
    },
    
    // Recursos principais do sistema
    features: [
      "Sistema completo de gerenciamento de licenças empresariais",
      "Dashboard de vendas com métricas em tempo real",
      "Alertas automatizados de renovação com priorização",
      "Integração WhatsApp Business API para conversão de vendas",
      "Sistema multi-tenancy pronto para SaaS",
      "Controle de acesso baseado em funções (RBAC) completo",
      "Gerenciamento avançado de clientes PF e PJ",
      "Sistema de notificações inteligente",
      "Cadastros centralizados (categorias, produtos, empresas)",
      "APIs RESTful para integrações externas",
      "Sistema de logs e auditoria completo",
      "Interface responsiva e acessível (WCAG 2.1)",
      "Mascaramento de dados sensíveis (LGPD)",
      "Sistema de versionamento e controle de mudanças",
      "Backup automático e recuperação de dados",
      "Relatórios e análises avançadas",
      "Gestão de usuários e permissões granulares",
      "Configuração multi-empresa (tenant)",
      "Sistema de help e onboarding integrado",
      "Otimização para alta performance e escalabilidade"
    ],
    
    // Conformidades e certificações
    compliance: [
      "LGPD - Lei Geral de Proteção de Dados",
      "WCAG 2.1 - Diretrizes de Acessibilidade",
      "Boas práticas de segurança em APIs",
      "Padrões REST para integrações",
      "Versionamento semântico"
    ]
  },
  
  // Changelog da versão atual
  changelog: {
    "1.3.0": {
      date: "2025-08-21",
      status: "stable",
      type: "major", // "major", "minor", "patch", "hotfix"
      changes: {
        added: [
          "Dashboard de Vendas com WhatsApp Business API integrado",
          "Sistema de Licenças Expirando - 378 oportunidades de renovação",
          "Geração massiva de dados de teste (2.470+ registros)",
          "Padronização de contadores em todas as abas do sistema",
          "Correção completa de timeout MongoDB para sessões longas",
          "Normalização de enums (client_type, regime_tributario, status)",
          "Sistema de alertas de expiração com priorização automática"
        ],
        fixed: [
          "Correção crítica de endpoints de Clientes PF/PJ (206 PF + 25 PJ)",
          "Resolução completa de erros WhatsApp serialization",
          "Fix de validação Pydantic em todos os modelos",
          "Correção de comunicação frontend-backend (URLs externas)",
          "Eliminação de erros 'dict object has no attribute status'",
          "Resolução de problemas de tenant filtering",
          "Correção de enum LicenseStatus (adicionado 'cancelled')"
        ],
        changed: [
          "Todas as abas agora mostram contadores dinâmicos em tempo real",
          "Interface padronizada com informações contextuais",
          "Melhor experiência do usuário com dados sempre visíveis",
          "Otimização de queries do MongoDB com configurações avançadas",
          "Estrutura de dados normalizada para consistência"
        ],
        improved: [
          "Performance do sistema com configuração de pool MongoDB",
          "Estabilidade geral com correção de race conditions",
          "Experiência de vendedores com dashboard funcional",
          "Monitoramento de licenças com alertas automáticos",
          "Integração WhatsApp para conversão de alertas em vendas"
        ],
        security: [
          "Correção de problemas de mascaramento de dados",
          "Validação robusta de todos os endpoints críticos",
          "Tratamento adequado de erros sem exposição de dados internos"
        ]
      },
      breaking: false,
      migration: "Sistema atualizado automaticamente - não requer migração manual",
      stats: {
        "fixes_applied": 15,
        "endpoints_corrected": 8, 
        "new_features": 7,
        "test_records_generated": 2470,
        "expiring_licenses_tracked": 378
      }
    },
    "1.2.0": {
      date: "2025-01-15",
      status: "beta",
      type: "feature", // "major", "minor", "patch", "hotfix"
      changes: {
        added: [
          "Sistema de cores semânticas WCAG 2.1 compliant",
          "Modal de detalhes completo para licenças",
          "Gerenciamento de clientes PF e PJ",
          "Sistema de status bloqueado/ativo/pendente",
          "Módulo de manutenção com logs"
        ],
        fixed: [
          "Correção de validação de status 'blocked'",
          "Resolução de falha CSS no badge semântico",
          "Correção de mapeamento de dados PJ",
          "Fix de JSON serialization no backend"
        ],
        changed: [
          "Interface redesenhada com sistema semântico",
          "Melhorias de acessibilidade em todo sistema",
          "Otimização de performance dos formulários"
        ],
        security: [
          "Validação robusta de entrada de dados",
          "Sanitização de campos de formulário"
        ]
      },
      breaking: false,
      migration: null
    }
  },

  // Histórico de versões
  versionHistory: [
    {
      version: "1.3.0",
      date: "2025-08-21", 
      status: "stable",
      description: "Major update - Dashboard de Vendas, correções críticas e padronização completa"
    },
    {
      version: "1.2.0",
      date: "2025-01-15", 
      status: "beta",
      description: "Sistema de cores semânticas e gerenciamento de clientes"
    },
    {
      version: "1.1.0",
      date: "2025-01-10", 
      status: "stable",
      description: "Implementação dos módulos principais"
    },
    {
      version: "1.0.0",
      date: "2025-01-05",
      status: "stable", 
      description: "Release inicial - MVP funcional"
    }
  ],

  // Configurações de exibição
  display: {
    showInFooter: true,
    showInHeader: false,
    showBuildNumber: false,
    showChangelogLink: true,
    compactMode: false
  },

  // Links e informações adicionais
  links: {
    changelog: "/changelog",
    releases: "/releases", 
    documentation: "/docs",
    github: null // URL do repositório se disponível
  }
};

// Utilidades para versão
export const getVersionInfo = () => {
  const { version, status, releaseDate, buildNumber } = VERSION_CONFIG;
  
  return {
    version,
    status,
    releaseDate,
    buildNumber,
    displayVersion: `v${version}${status !== 'stable' ? `-${status}` : ''}`,
    isStable: status === 'stable',
    isBeta: status === 'beta',
    isDev: status === 'dev' || status === 'alpha'
  };
};

// Função para atualizar versão facilmente
export const updateVersion = (newVersion, newStatus = "beta", changes = {}) => {
  // Esta função seria usada durante desenvolvimento
  // para atualizar facilmente a versão
  console.log(`Updating to version ${newVersion} (${newStatus})`);
  
  // Em ambiente real, isso atualizaria o arquivo de configuração
  return {
    version: newVersion,
    status: newStatus,
    releaseDate: new Date().toISOString().split('T')[0],
    buildNumber: `${new Date().toISOString().split('T')[0].replace(/-/g, '')}001`,
    changes
  };
};

// Função para obter informações de licenciamento formatadas
export const getLicensingInfo = () => {
  return {
    title: "🛈 Informações da Versão e Licenciamento",
    sections: {
      identification: {
        title: "📋 IDENTIFICAÇÃO DO SOFTWARE",
        items: {
          "Nome do Software": "Sistema de Gerenciamento de Licenças (License Management System)",
          "Versão Atual": `${VERSION_CONFIG.version} (${VERSION_CONFIG.status})`,
          "Data de Lançamento": VERSION_CONFIG.releaseDate,
          "Build": VERSION_CONFIG.buildNumber,
          "Desenvolvedor": VERSION_CONFIG.company.name
        }
      },
      
      technologies: {
        title: "🛠️ TECNOLOGIAS UTILIZADAS",
        items: {
          "Backend": VERSION_CONFIG.software.technologies.backend.join(", "),
          "Frontend": VERSION_CONFIG.software.technologies.frontend.join(", "),
          "Banco de Dados": VERSION_CONFIG.software.technologies.database.join(", "),
          "Integrações": VERSION_CONFIG.software.technologies.integrations.join(", "),
          "Arquitetura": VERSION_CONFIG.software.technologies.architecture.join(", "),
          "Utilidades": VERSION_CONFIG.software.technologies.utilities.join(", ")
        }
      },
      
      licensing: {
        title: "⚖️ LICENCIAMENTO",
        content: [
          `Este software está licenciado sob a ${VERSION_CONFIG.software.license}.`,
          `${VERSION_CONFIG.software.licenseTerms}`,
          "",
          "Funcionalidades Licenciadas:",
          "• Sistema completo de gerenciamento de licenças empresariais",
          "• Dashboard de vendas com integração WhatsApp Business",
          "• Controle de acesso baseado em funções (RBAC)",
          "• Sistema multi-tenancy para SaaS",
          "• APIs RESTful para integrações externas"
        ]
      },
      
      copyright: {
        title: "🛡️ PATENTE E DIREITOS AUTORAIS",
        content: [
          VERSION_CONFIG.company.copyright,
          "",
          "Este software pode conter funcionalidades proprietárias e métodos patenteados relacionados ao gerenciamento automatizado de licenças e integração WhatsApp para vendas. O uso, reprodução ou distribuição não autorizada deste sistema pode violar leis de propriedade intelectual brasileiras e internacionais."
        ]
      },
      
      terms: {
        title: "📜 TERMOS DE USO E POLÍTICA DE PRIVACIDADE", 
        content: [
          "O uso deste software implica na aceitação dos Termos de Uso e da Política de Privacidade da AutoTech Services.",
          "",
          "Conformidade LGPD: Este sistema está em conformidade com a Lei Geral de Proteção de Dados (LGPD) brasileira, garantindo a proteção e privacidade dos dados dos usuários."
        ]
      },
      
      contact: {
        title: "📞 CONTATO PARA SUPORTE",
        items: {
          "Suporte Técnico": VERSION_CONFIG.company.contact.support,
          "Questões Legais": VERSION_CONFIG.company.contact.legal,
          "Documentação": VERSION_CONFIG.company.contact.documentation
        }
      },
      
      features: {
        title: "🌟 RECURSOS PRINCIPAIS",
        items: VERSION_CONFIG.software.features
      },
      
      compliance: {
        title: "✅ CONFORMIDADES",
        items: VERSION_CONFIG.software.compliance
      }
    }
  };
};

export default VERSION_CONFIG;