import React from 'react';
import { CheckCircle, XCircle, AlertTriangle, Ban, Wifi, WifiOff, Loader2 } from 'lucide-react';

/**
 * StatusBadge - Componente de status animado para certificados
 * Estados: valid, expiring, expired, revoked
 * Servidor: online, offline, checking
 */
const StatusBadge = ({ 
  certificateStatus = 'valid',  // 'valid' | 'expiring' | 'expired' | 'revoked'
  serverStatus = 'online',      // 'online' | 'offline' | 'checking'
  daysRemaining = null 
}) => {
  
  // Configurações de status do certificado
  const certificateConfig = {
    valid: {
      icon: CheckCircle,
      label: 'VÁLIDO',
      sublabel: 'Certificado ativo',
      colorClass: 'text-green-500',
      bgClass: 'bg-green-50',
      borderClass: 'border-green-500',
      glowClass: 'shadow-[0_0_30px_rgba(34,197,94,0.4)]',
      ringClass: 'ring-green-500/30',
    },
    expiring: {
      icon: AlertTriangle,
      label: 'EXPIRANDO',
      sublabel: 'Renovar em breve',
      colorClass: 'text-amber-500',
      bgClass: 'bg-amber-50',
      borderClass: 'border-amber-500',
      glowClass: 'shadow-[0_0_30px_rgba(245,158,11,0.4)]',
      ringClass: 'ring-amber-500/30',
    },
    expired: {
      icon: XCircle,
      label: 'EXPIRADO',
      sublabel: 'Certificado vencido',
      colorClass: 'text-red-500',
      bgClass: 'bg-red-50',
      borderClass: 'border-red-500',
      glowClass: '',
      ringClass: 'ring-red-500/30',
    },
    revoked: {
      icon: Ban,
      label: 'REVOGADO',
      sublabel: 'Certificado cancelado',
      colorClass: 'text-gray-500',
      bgClass: 'bg-gray-100',
      borderClass: 'border-gray-400',
      glowClass: '',
      ringClass: 'ring-gray-400/30',
    },
  };

  // Configurações de status do servidor
  const serverConfig = {
    online: {
      icon: Wifi,
      label: 'Servidor Online',
      dotClass: 'bg-green-500',
      pulseClass: 'animate-pulse',
    },
    offline: {
      icon: WifiOff,
      label: 'Servidor Offline',
      dotClass: 'bg-red-500',
      pulseClass: '',
    },
    checking: {
      icon: Loader2,
      label: 'Verificando...',
      dotClass: 'bg-yellow-500',
      pulseClass: 'animate-spin',
    },
  };

  const certConfig = certificateConfig[certificateStatus] || certificateConfig.valid;
  const servConfig = serverConfig[serverStatus] || serverConfig.checking;
  const CertIcon = certConfig.icon;
  const ServIcon = servConfig.icon;

  // Determinar mensagem de dias
  const getDaysMessage = () => {
    if (daysRemaining === null) return null;
    if (daysRemaining > 0) return `${daysRemaining} dias restantes`;
    if (daysRemaining === 0) return 'Expira hoje';
    return `Expirado há ${Math.abs(daysRemaining)} dias`;
  };

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Badge Principal do Certificado */}
      <div 
        className={`
          relative p-8 rounded-2xl border-2 
          ${certConfig.bgClass} ${certConfig.borderClass}
          ${certConfig.glowClass}
          transition-all duration-500
          ring-4 ${certConfig.ringClass}
        `}
      >
        {/* Ícone Principal com Animação */}
        <div className="flex flex-col items-center gap-3">
          <div className={`relative ${certConfig.colorClass}`}>
            {certificateStatus === 'valid' ? (
              // Checkmark animado SVG
              <div className="relative">
                <svg 
                  className="w-20 h-20" 
                  viewBox="0 0 52 52"
                >
                  {/* Círculo de fundo com pulse */}
                  <circle 
                    className="stroke-current fill-none animate-[pulse_2s_ease-in-out_infinite]" 
                    cx="26" cy="26" r="24" 
                    strokeWidth="2"
                    opacity="0.3"
                  />
                  {/* Checkmark com draw animation */}
                  <path 
                    className="stroke-current fill-none" 
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M14 27l8 8 16-16"
                    style={{
                      strokeDasharray: 50,
                      strokeDashoffset: 0,
                      animation: 'draw-check 0.8s ease-out forwards'
                    }}
                  />
                </svg>
                {/* Glow effect */}
                <div className="absolute inset-0 rounded-full bg-green-500/20 blur-xl animate-[pulse_3s_ease-in-out_infinite]" />
              </div>
            ) : certificateStatus === 'expiring' ? (
              <div className="relative">
                <AlertTriangle className="w-20 h-20 animate-[bounce_1s_ease-in-out_infinite]" />
                <div className="absolute inset-0 rounded-full bg-amber-500/20 blur-xl animate-[pulse_1.5s_ease-in-out_infinite]" />
              </div>
            ) : (
              <CertIcon className="w-20 h-20" />
            )}
          </div>
          
          <span className={`text-3xl font-bold ${certConfig.colorClass}`}>
            {certConfig.label}
          </span>
          
          <span className="text-sm text-gray-500">
            {certConfig.sublabel}
          </span>
          
          {daysRemaining !== null && certificateStatus !== 'revoked' && (
            <span className={`
              text-sm font-medium px-3 py-1 rounded-full
              ${daysRemaining <= 0 ? 'bg-red-100 text-red-700' : 
                daysRemaining <= 30 ? 'bg-amber-100 text-amber-700' : 
                'bg-green-100 text-green-700'}
            `}>
              {getDaysMessage()}
            </span>
          )}
        </div>
      </div>

      {/* Status do Servidor */}
      <div className="flex items-center gap-3 px-4 py-2 bg-gray-50 rounded-full">
        {/* Dot Animado */}
        <span className="relative flex h-3 w-3">
          {serverStatus === 'online' && (
            <span 
              className={`
                absolute inline-flex h-full w-full rounded-full opacity-75
                ${servConfig.dotClass} animate-ping
              `}
            />
          )}
          <span 
            className={`
              relative inline-flex rounded-full h-3 w-3
              ${servConfig.dotClass}
            `}
          />
        </span>
        
        {/* Ícone e Label */}
        <ServIcon 
          className={`w-4 h-4 text-gray-600 ${serverStatus === 'checking' ? 'animate-spin' : ''}`} 
        />
        <span className="text-sm text-gray-600 font-medium">{servConfig.label}</span>
      </div>

      {/* CSS para animação de draw */}
      <style jsx>{`
        @keyframes draw-check {
          0% { stroke-dashoffset: 50; }
          100% { stroke-dashoffset: 0; }
        }
      `}</style>
    </div>
  );
};

export default StatusBadge;
