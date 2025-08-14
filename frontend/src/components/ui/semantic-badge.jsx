import * as React from "react"
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils"

/**
 * Sistema de Badge Semântico WCAG 2.1 Compliant
 * 
 * REGRAS IMPLEMENTADAS:
 * - Nunca usar cor sozinha: ícone + label sempre presentes
 * - Contraste mínimo: ≥ 4.5:1 texto, ≥ 3:1 componentes
 * - Suporte daltonismo: cores color-blind safe
 * - Suporte tema claro/escuro via tokens CSS
 */

// Mapeamento semântico: Status → Cor → Ícone
const STATUS_CONFIG = {
  // OK → success (Licenças ativas, processos em dia)
  'active': {
    variant: 'success',
    label: 'Ativo',
    icon: '✓',
    ariaLabel: 'Status: Ativo - Licença funcionando normalmente'
  },
  'ok': {
    variant: 'success', 
    label: 'OK',
    icon: '✓',
    ariaLabel: 'Status: OK - Funcionando normalmente'
  },
  
  // Atenção → warning (Prazo se aproximando, ação recomendada)
  'suspended': {
    variant: 'warning',
    label: 'Suspenso',
    icon: '!',
    ariaLabel: 'Status: Suspenso - Requer atenção, licença temporariamente desabilitada'
  },
  'warning': {
    variant: 'warning',
    label: 'Atenção', 
    icon: '!',
    ariaLabel: 'Status: Atenção - Ação recomendada'
  },
  'approaching': {
    variant: 'warning',
    label: 'Vencendo',
    icon: '!',
    ariaLabel: 'Status: Vencendo - Prazo se aproximando, renovação necessária'
  },
  
  // Crítico → danger (Expirado, erro, bloqueado)
  'expired': {
    variant: 'danger',
    label: 'Expirado',
    icon: '✕',
    ariaLabel: 'Status: Expirado - Licença não está mais válida, renovação necessária'
  },
  'error': {
    variant: 'danger',
    label: 'Erro',
    icon: '✕', 
    ariaLabel: 'Status: Erro - Problema crítico identificado'
  },
  'blocked': {
    variant: 'danger',
    label: 'Bloqueado',
    icon: '✕',
    ariaLabel: 'Status: Bloqueado - Acesso negado por segurança'
  },
  
  // Pendente → info (Aguardando pagamento/validação) 
  'pending': {
    variant: 'info',
    label: 'Pendente',
    icon: '●',
    ariaLabel: 'Status: Pendente - Aguardando processamento ou validação'
  },
  'processing': {
    variant: 'info',
    label: 'Processando',
    icon: '●',
    ariaLabel: 'Status: Processando - Em andamento'
  },
  
  // Inativo → neutral (Desligado, sem efeito)
  'inactive': {
    variant: 'neutral',
    label: 'Inativo',
    icon: '○',
    ariaLabel: 'Status: Inativo - Desabilitado sem efeito no sistema'
  },
  'disabled': {
    variant: 'neutral',
    label: 'Desabilitado',
    icon: '○',
    ariaLabel: 'Status: Desabilitado - Funcionalidade desligada'
  }
}

// Variantes de badge semântico com design tokens WCAG
const semanticBadgeVariants = cva(
  "inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        // Success: Verde acessível (contraste ≥ 4.5:1)
        success: "bg-success-light text-success border border-success/20",
        
        // Warning: Laranja acessível (contraste ≥ 4.5:1) 
        warning: "bg-warning-light text-warning border border-warning/20",
        
        // Danger: Vermelho acessível (contraste ≥ 4.5:1)
        danger: "bg-danger-light text-danger border border-danger/20",
        
        // Info: Azul acessível (contraste ≥ 4.5:1)
        info: "bg-info-light text-info border border-info/20",
        
        // Neutral: Cinza neutro (contraste ≥ 4.5:1)  
        neutral: "bg-neutral-light text-neutral border border-neutral/20"
      },
      size: {
        sm: "text-xs px-2 py-0.5 gap-1",
        default: "text-xs px-3 py-1 gap-2", 
        lg: "text-sm px-4 py-2 gap-2"
      }
    },
    defaultVariants: {
      variant: "neutral",
      size: "default"
    }
  }
)

// Componente de dot/indicador visual
const StatusDot = ({ variant, className, ...props }) => (
  <span 
    className={cn(
      "inline-block w-2 h-2 rounded-full", 
      {
        "bg-success": variant === "success",
        "bg-warning": variant === "warning", 
        "bg-danger": variant === "danger",
        "bg-info": variant === "info",
        "bg-neutral": variant === "neutral"
      },
      className
    )}
    aria-hidden="true"
    {...props}
  />
)

// Badge Semântico Principal
function SemanticBadge({ 
  status = "inactive", 
  className,
  size = "default",
  showIcon = true,
  showDot = false,
  customLabel = null,
  customAriaLabel = null,
  ...props 
}) {
  // Buscar configuração do status ou usar fallback
  const config = STATUS_CONFIG[status] || STATUS_CONFIG['inactive']
  const { variant, label, icon, ariaLabel } = config
  
  // Permitir sobrescrever label e ariaLabel
  const displayLabel = customLabel || label
  const displayAriaLabel = customAriaLabel || ariaLabel

  return (
    <div 
      className={cn(semanticBadgeVariants({ variant, size }), className)} 
      role="status"
      aria-label={displayAriaLabel}
      {...props}
    >
      {/* Indicador visual: nunca cor sozinha */}
      {showDot && <StatusDot variant={variant} />}
      {showIcon && !showDot && (
        <span 
          className="font-bold leading-none" 
          aria-hidden="true"
        >
          {icon}
        </span>
      )}
      
      {/* Label textual: sempre presente para acessibilidade */}
      <span className="leading-none">
        {displayLabel}
      </span>
    </div>
  )
}

// Badge rápido para status de licença (uso mais comum)
function LicenseStatusBadge({ status, ...props }) {
  return <SemanticBadge status={status} showIcon={true} {...props} />
}

// Badge com dot para casos específicos  
function StatusBadgeWithDot({ status, ...props }) {
  return <SemanticBadge status={status} showDot={true} {...props} />
}

// Badge customizável para casos especiais
function CustomSemanticBadge({ 
  variant = "neutral", 
  label = "Status", 
  icon = "●",
  ariaLabel = "Status customizado",
  className,
  size = "default",
  ...props 
}) {
  return (
    <div 
      className={cn(semanticBadgeVariants({ variant, size }), className)} 
      role="status"
      aria-label={ariaLabel}
      {...props}
    >
      <span className="font-bold leading-none" aria-hidden="true">
        {icon}
      </span>
      <span className="leading-none">
        {label}
      </span>
    </div>
  )
}

export { 
  SemanticBadge, 
  LicenseStatusBadge,
  StatusBadgeWithDot,
  CustomSemanticBadge,
  semanticBadgeVariants,
  STATUS_CONFIG 
}