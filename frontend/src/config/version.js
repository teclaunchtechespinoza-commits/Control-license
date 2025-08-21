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