// Sistema de Versionamento do License Manager
export const VERSION_CONFIG = {
  // Versão atual do sistema
  version: "1.3.0",
  
  // Status da versão
  status: "stable", // "stable", "beta", "rc", "alpha", "dev"
  
  // Informações da versão
  releaseDate: "2025-08-21",
  buildNumber: "20250821001",
  
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

export default VERSION_CONFIG;