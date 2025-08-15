/**
 * GUIA DE ATUALIZAÇÃO DE VERSÕES
 * ================================
 * 
 * Como atualizar a versão do License Manager:
 * 
 * 1. Abra o arquivo: /app/frontend/src/config/version.js
 * 
 * 2. Altere as seguintes propriedades no VERSION_CONFIG:
 *    - version: "1.2.0" → "1.3.0" (nova versão)
 *    - status: "beta" → "stable" (quando estável) ou "beta"/"alpha"/"dev"
 *    - releaseDate: "2025-01-15" → data atual
 *    - buildNumber: incrementar o último número
 * 
 * 3. Adicione o changelog da nova versão no objeto 'changelog'
 * 
 * 4. Atualize o 'versionHistory' com a versão anterior
 * 
 * EXEMPLO DE ATUALIZAÇÃO:
 * =======================
 */

// EXEMPLO: Atualizando para versão 1.3.0
export const VERSION_UPDATE_EXAMPLE = {
  version: "1.3.0",
  status: "beta", // ou "stable" quando testado
  releaseDate: "2025-01-20",
  buildNumber: "20250120001",
  
  // Novo changelog
  changelog: {
    "1.3.0": {
      date: "2025-01-20",
      status: "beta",
      type: "feature",
      changes: {
        added: [
          "Sistema de controle de versão integrado",
          "Modal detalhado com changelog",
          "Badge de status de versão no rodapé",
          "Painel administrativo de versão"
        ],
        fixed: [
          "Correções gerais de UI/UX",
          "Melhorias de performance"
        ],
        changed: [
          "Interface atualizada com informações de versão",
          "Rodapé modernizado"
        ]
      },
      breaking: false,
      migration: null
    },
    // Manter versões anteriores...
    "1.2.0": {
      // ... conteúdo da versão anterior
    }
  },

  // Atualizar histórico
  versionHistory: [
    {
      version: "1.2.0", // versão anterior vai para histórico
      date: "2025-01-15",
      status: "stable",
      description: "Sistema semântico WCAG e melhorias gerais"
    },
    {
      version: "1.1.0",
      date: "2025-01-10", 
      status: "stable",
      description: "Implementação dos módulos principais"
    }
    // ... demais versões
  ]
};

/**
 * TIPOS DE STATUS DE VERSÃO:
 * ==========================
 * 
 * "stable"  - Versão estável, testada, pronta para produção
 * "beta"    - Versão beta, funcional mas pode ter bugs menores
 * "rc"      - Release Candidate, quase estável, últimos testes
 * "alpha"   - Versão alpha, funcional mas instável
 * "dev"     - Versão de desenvolvimento, muito instável
 * 
 * TIPOS DE RELEASE:
 * =================
 * 
 * "major"   - Mudanças grandes, breaking changes (1.0.0 → 2.0.0)
 * "minor"   - Novas funcionalidades, compatível (1.0.0 → 1.1.0)  
 * "patch"   - Correções de bugs, compatível (1.0.0 → 1.0.1)
 * "hotfix"  - Correções urgentes em produção
 */

/**
 * WORKFLOW RECOMENDADO:
 * =====================
 * 
 * 1. DESENVOLVIMENTO:
 *    - status: "dev" ou "alpha"
 *    - version: incrementar minor ou patch
 * 
 * 2. TESTES INTERNOS:
 *    - status: "beta"
 *    - Validar funcionalidades
 * 
 * 3. RELEASE CANDIDATE:
 *    - status: "rc" 
 *    - Testes finais, validação completa
 * 
 * 4. PRODUÇÃO:
 *    - status: "stable"
 *    - Deploy para produção
 * 
 * EXEMPLO PRÁTICO:
 * ================
 * 
 * // Fase de desenvolvimento
 * version: "1.3.0", status: "alpha"
 * 
 * // Implementação completa  
 * version: "1.3.0", status: "beta"
 * 
 * // Testes finalizados
 * version: "1.3.0", status: "rc"
 * 
 * // Release final
 * version: "1.3.0", status: "stable"
 */

export default VERSION_UPDATE_EXAMPLE;