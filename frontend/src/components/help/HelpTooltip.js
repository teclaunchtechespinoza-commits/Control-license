import React, { useState } from 'react';
import { useHelp } from './HelpProvider';
import { HelpCircle, Info, Lightbulb, AlertTriangle, CheckCircle } from 'lucide-react';

const HelpTooltip = ({ 
  module, 
  section, 
  children, 
  trigger = "hover", 
  position = "top",
  size = "default",
  variant = "default",
  disabled = false,
  className = "",
  showIcon = true,
  customContent = null
}) => {
  const { 
    getHelpFor, 
    showTooltips, 
    trackHelpUsage, 
    openHelpModal,
    userPreferences 
  } = useHelp();
  
  const [isVisible, setIsVisible] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  
  // Se tooltips estão desabilitados globalmente
  if (!showTooltips || disabled) {
    return children;
  }
  
  // Buscar conteúdo de ajuda
  const helpContent = customContent || getHelpFor(module, section);
  
  // Se não há conteúdo, não renderizar tooltip
  if (!helpContent) {
    return children;
  }
  
  // Controle de visibilidade
  const handleShow = () => {
    setIsVisible(true);
    trackHelpUsage('tooltip_show', module, section);
  };
  
  const handleHide = () => {
    setIsVisible(false);
  };
  
  const handleClick = () => {
    if (trigger === "click") {
      setIsVisible(!isVisible);
      trackHelpUsage('tooltip_click', module, section);
    }
  };
  
  const handleMoreInfo = (e) => {
    e.stopPropagation();
    openHelpModal(module, section);
    handleHide();
    trackHelpUsage('tooltip_more_info', module, section);
  };
  
  // Configurações de posição
  const getPositionClasses = () => {
    const baseClasses = "absolute z-50 px-3 py-2 text-sm bg-gray-900 text-white rounded-lg shadow-lg pointer-events-none";
    const maxWidth = size === "large" ? "max-w-sm" : size === "small" ? "max-w-xs" : "max-w-xs";
    
    const positions = {
      top: "bottom-full left-1/2 transform -translate-x-1/2 mb-2",
      bottom: "top-full left-1/2 transform -translate-x-1/2 mt-2", 
      left: "right-full top-1/2 transform -translate-y-1/2 mr-2",
      right: "left-full top-1/2 transform -translate-y-1/2 ml-2",
    };
    
    return `${baseClasses} ${maxWidth} ${positions[position]}`;
  };
  
  // Ícone baseado no tipo de conteúdo
  const getIcon = () => {
    if (!showIcon) return null;
    
    if (helpContent.tips) return <Lightbulb className="w-4 h-4 text-yellow-400 flex-shrink-0" />;
    if (helpContent.warnings) return <AlertTriangle className="w-4 h-4 text-orange-400 flex-shrink-0" />;
    if (helpContent.benefits) return <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />;
    return <Info className="w-4 h-4 text-blue-400 flex-shrink-0" />;
  };
  
  // Renderizar conteúdo do tooltip
  const renderTooltipContent = () => {
    return (
      <div className={`space-y-2 ${isVisible ? 'animate-in fade-in-0 zoom-in-95' : ''}`}>
        {/* Título */}
        <div className="flex items-center gap-2">
          {getIcon()}
          <h4 className="font-semibold text-white">{helpContent.title}</h4>
        </div>
        
        {/* Descrição */}
        {helpContent.description && (
          <p className="text-gray-200 text-sm leading-relaxed">
            {helpContent.description}
          </p>
        )}
        
        {/* Tips */}
        {helpContent.tips && helpContent.tips.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-yellow-300">💡 Dicas:</p>
            <ul className="space-y-1">
              {helpContent.tips.slice(0, 3).map((tip, index) => (
                <li key={index} className="text-xs text-gray-200 flex items-start gap-1">
                  <span className="text-yellow-400 flex-shrink-0">•</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Benefits */}
        {helpContent.benefits && helpContent.benefits.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-green-300">✅ Benefícios:</p>
            <ul className="space-y-1">
              {helpContent.benefits.slice(0, 2).map((benefit, index) => (
                <li key={index} className="text-xs text-gray-200 flex items-start gap-1">
                  <span className="text-green-400 flex-shrink-0">•</span>
                  <span>{benefit}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Warnings */}
        {helpContent.warnings && helpContent.warnings.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-orange-300">⚠️ Atenção:</p>
            <ul className="space-y-1">
              {helpContent.warnings.slice(0, 2).map((warning, index) => (
                <li key={index} className="text-xs text-gray-200 flex items-start gap-1">
                  <span className="text-orange-400 flex-shrink-0">•</span>
                  <span>{warning}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Steps */}
        {helpContent.steps && helpContent.steps.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-blue-300">📋 Passos:</p>
            <ol className="space-y-1">
              {helpContent.steps.slice(0, 3).map((step, index) => (
                <li key={index} className="text-xs text-gray-200 flex items-start gap-1">
                  <span className="text-blue-400 flex-shrink-0">{index + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>
        )}
        
        {/* Shortcuts */}
        {helpContent.shortcuts && helpContent.shortcuts.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-purple-300">⌨️ Atalhos:</p>
            {helpContent.shortcuts.slice(0, 2).map((shortcut, index) => (
              <kbd key={index} className="text-xs bg-gray-800 px-1 py-0.5 rounded">
                {shortcut}
              </kbd>
            ))}
          </div>
        )}
        
        {/* Botão "Mais informações" se houver conteúdo adicional */}
        {(helpContent.tips?.length > 3 || 
          helpContent.benefits?.length > 2 || 
          helpContent.steps?.length > 3 ||
          helpContent.insights ||
          helpContent.examples) && (
          <div className="border-t border-gray-700 pt-2 mt-2">
            <button 
              onClick={handleMoreInfo}
              className="text-xs text-blue-300 hover:text-blue-200 transition-colors pointer-events-auto"
            >
              Ver mais informações →
            </button>
          </div>
        )}
      </div>
    );
  };
  
  // Event handlers baseados no trigger
  const getEventHandlers = () => {
    if (trigger === "hover") {
      return {
        onMouseEnter: handleShow,
        onMouseLeave: handleHide,
      };
    } else if (trigger === "click") {
      return {
        onClick: handleClick,
      };
    } else if (trigger === "focus") {
      return {
        onFocus: handleShow,
        onBlur: handleHide,
      };
    }
    return {};
  };
  
  return (
    <div className={`relative inline-block ${className}`} {...getEventHandlers()}>
      {children}
      
      {/* Tooltip */}
      {isVisible && (
        <>
          {/* Backdrop para click trigger */}
          {trigger === "click" && (
            <div 
              className="fixed inset-0 z-40" 
              onClick={() => setIsVisible(false)}
            />
          )}
          
          {/* Tooltip content */}
          <div className={getPositionClasses()}>
            {renderTooltipContent()}
            
            {/* Seta do tooltip */}
            <div className={`absolute w-2 h-2 bg-gray-900 transform rotate-45 ${
              position === "top" ? "top-full left-1/2 -translate-x-1/2 -mt-1" :
              position === "bottom" ? "bottom-full left-1/2 -translate-x-1/2 -mb-1" :
              position === "left" ? "left-full top-1/2 -translate-y-1/2 -ml-1" :
              position === "right" ? "right-full top-1/2 -translate-y-1/2 -mr-1" : ""
            }`} />
          </div>
        </>
      )}
    </div>
  );
};

// Componente especializado para ícones de ajuda
export const HelpIcon = ({ 
  module, 
  section, 
  size = 16,
  className = "",
  variant = "default"
}) => {
  const variants = {
    default: "text-gray-400 hover:text-gray-600",
    primary: "text-blue-400 hover:text-blue-600", 
    success: "text-green-400 hover:text-green-600",
    warning: "text-yellow-400 hover:text-yellow-600",
  };
  
  return (
    <HelpTooltip 
      module={module} 
      section={section}
      trigger="hover"
      showIcon={false}
    >
      <HelpCircle 
        size={size}
        className={`cursor-help transition-colors ${variants[variant]} ${className}`}
      />
    </HelpTooltip>
  );
};

// Componente para textos com ajuda inline
export const HelpText = ({ 
  module, 
  section, 
  children,
  className = "",
  underline = true
}) => {
  return (
    <HelpTooltip 
      module={module} 
      section={section}
      trigger="hover"
      showIcon={false}
    >
      <span className={`cursor-help ${underline ? 'border-b border-dotted border-gray-400' : ''} ${className}`}>
        {children}
      </span>
    </HelpTooltip>
  );
};

export default HelpTooltip;