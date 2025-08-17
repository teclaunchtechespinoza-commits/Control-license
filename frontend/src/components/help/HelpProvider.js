import React, { createContext, useContext, useState, useEffect } from 'react';
import { getHelpContent, getModuleHelp, searchHelp, HELP_DATABASE } from '../../lib/help/help-data';

// Context
const HelpContext = createContext();

// Hook para usar o contexto
export const useHelp = () => {
  const context = useContext(HelpContext);
  if (!context) {
    throw new Error('useHelp must be used within HelpProvider');
  }
  return context;
};

// Provider Component
export const HelpProvider = ({ children }) => {
  // Estados do sistema de ajuda
  const [showTooltips, setShowTooltips] = useState(true);
  const [currentTour, setCurrentTour] = useState(null);
  const [tourStep, setTourStep] = useState(0);
  const [isOnboardingActive, setIsOnboardingActive] = useState(false);
  const [helpModalOpen, setHelpModalOpen] = useState(false);
  const [selectedHelpContent, setSelectedHelpContent] = useState(null);
  const [userPreferences, setUserPreferences] = useState({
    tooltipEnabled: true,
    autoTour: true,
    helpLevel: 'beginner' // beginner, intermediate, advanced
  });

  // Carregar preferências do localStorage
  useEffect(() => {
    const savedPrefs = localStorage.getItem('help-preferences');
    if (savedPrefs) {
      try {
        const prefs = JSON.parse(savedPrefs);
        setUserPreferences(prev => ({ ...prev, ...prefs }));
        setShowTooltips(prefs.tooltipEnabled ?? true);
      } catch (error) {
        console.warn('Error loading help preferences:', error);
      }
    }
  }, []);

  // Salvar preferências
  const updatePreferences = (newPrefs) => {
    const updatedPrefs = { ...userPreferences, ...newPrefs };
    setUserPreferences(updatedPrefs);
    localStorage.setItem('help-preferences', JSON.stringify(updatedPrefs));
    
    // Aplicar mudanças imediatas
    if ('tooltipEnabled' in newPrefs) {
      setShowTooltips(newPrefs.tooltipEnabled);
    }
  };

  // Função principal para obter conteúdo de ajuda
  const getHelpFor = (module, section) => {
    return getHelpContent(module, section);
  };

  // Buscar ajuda por módulo completo
  const getModuleHelpContent = (module) => {
    return getModuleHelp(module);
  };

  // Buscar ajuda por palavra-chave
  const searchHelpContent = (keyword) => {
    return searchHelp(keyword);
  };

  // Controle de tooltips
  const toggleTooltips = () => {
    const newValue = !showTooltips;
    setShowTooltips(newValue);
    updatePreferences({ tooltipEnabled: newValue });
  };

  // Sistema de tours guiados
  const startTour = (tourName) => {
    const tour = TOURS[tourName];
    if (tour) {
      setCurrentTour(tour);
      setTourStep(0);
      setIsOnboardingActive(true);
    }
  };

  const nextTourStep = () => {
    if (currentTour && tourStep < currentTour.steps.length - 1) {
      setTourStep(tourStep + 1);
    } else {
      endTour();
    }
  };

  const previousTourStep = () => {
    if (tourStep > 0) {
      setTourStep(tourStep - 1);
    }
  };

  const endTour = () => {
    setCurrentTour(null);
    setTourStep(0);
    setIsOnboardingActive(false);
  };

  // Modal de ajuda
  const openHelpModal = (module, section) => {
    const content = getHelpFor(module, section);
    if (content) {
      setSelectedHelpContent({ module, section, ...content });
      setHelpModalOpen(true);
    }
  };

  const closeHelpModal = () => {
    setHelpModalOpen(false);
    setSelectedHelpContent(null);
  };

  // Detecção automática de primeiro uso
  const checkFirstTime = () => {
    const isFirstTime = !localStorage.getItem('help-first-visit');
    if (isFirstTime) {
      localStorage.setItem('help-first-visit', 'false');
      if (userPreferences.autoTour) {
        setTimeout(() => startTour('welcome'), 1000);
      }
    }
    return isFirstTime;
  };

  // Analytics de ajuda (opcional)
  const trackHelpUsage = (action, module = null, section = null) => {
    // Aqui podemos integrar com analytics
    console.log('Help Analytics:', { action, module, section, timestamp: new Date() });
    
    // Exemplo: enviar para o backend
    // fetch('/api/analytics/help', { 
    //   method: 'POST', 
    //   body: JSON.stringify({ action, module, section }) 
    // });
  };

  // Context value
  const contextValue = {
    // Estado
    showTooltips,
    currentTour,
    tourStep,
    isOnboardingActive,
    helpModalOpen,
    selectedHelpContent,
    userPreferences,
    
    // Funções de conteúdo
    getHelpFor,
    getModuleHelpContent,
    searchHelpContent,
    
    // Controles de tooltip
    toggleTooltips,
    
    // Controles de tour
    startTour,
    nextTourStep,
    previousTourStep,
    endTour,
    
    // Modal de ajuda
    openHelpModal,
    closeHelpModal,
    
    // Configurações
    updatePreferences,
    checkFirstTime,
    
    // Analytics
    trackHelpUsage
  };

  return (
    <HelpContext.Provider value={contextValue}>
      {children}
    </HelpContext.Provider>
  );
};

// Definição de tours disponíveis
const TOURS = {
  welcome: {
    name: 'Bem-vindo ao Sistema',
    description: 'Tour introdutório para novos usuários',
    steps: [
      {
        target: '[data-tour="dashboard"]',
        title: 'Dashboard Principal',
        content: 'Aqui você vê todas as métricas principais do sistema: licenças ativas, usuários e estatísticas.',
        position: 'bottom'
      },
      {
        target: '[data-tour="sales-dashboard"]',
        title: 'Dashboard de Vendas',
        content: 'Transforme alertas de vencimento em oportunidades de vendas! O WhatsApp automático aumenta renovações em 40%.',
        position: 'bottom'
      },
      {
        target: '[data-tour="clients"]',
        title: 'Gestão de Clientes',
        content: 'Cadastre e gerencie clientes PF e PJ com total segurança e conformidade LGPD.',
        position: 'bottom'
      },
      {
        target: '[data-tour="licenses"]',
        title: 'Controle de Licenças',
        content: 'Acompanhe o ciclo completo de vida das licenças: ativas, expirando, vencidas.',
        position: 'bottom'
      }
    ]
  },
  
  sales_dashboard: {
    name: 'Dashboard de Vendas',
    description: 'Como usar o sistema de vendas WhatsApp',
    steps: [
      {
        target: '[data-tour="sales-metrics"]',
        title: 'Métricas de Vendas',
        content: 'Acompanhe taxa de conversão, receita potencial e performance por canal.',
        position: 'bottom'
      },
      {
        target: '[data-tour="expiring-licenses"]',
        title: 'Licenças Expirando',
        content: 'Cada linha é uma oportunidade de renovação. Clique em WhatsApp para enviar mensagem personalizada.',
        position: 'top'
      },
      {
        target: '[data-tour="bulk-actions"]',
        title: 'Ações em Lote',
        content: 'Selecione múltiplas licenças e envie campanhas WhatsApp para todos simultaneamente.',
        position: 'top'
      }
    ]
  },
  
  whatsapp_setup: {
    name: 'Configuração WhatsApp',
    description: 'Como conectar e usar o WhatsApp Business',
    steps: [
      {
        target: '[data-tour="whatsapp-status"]',
        title: 'Status da Conexão',
        content: 'Monitore se o WhatsApp está conectado e funcionando.',
        position: 'bottom'
      },
      {
        target: '[data-tour="qr-code"]',
        title: 'QR Code',
        content: 'Escaneie com WhatsApp no celular para conectar. O código expira em 60 segundos.',
        position: 'bottom'
      },
      {
        target: '[data-tour="message-templates"]',
        title: 'Templates de Mensagem',
        content: 'Mensagens são personalizadas automaticamente baseadas na urgência: T-30, T-7, T-1 dias.',
        position: 'bottom'
      }
    ]
  }
};

export default HelpProvider;