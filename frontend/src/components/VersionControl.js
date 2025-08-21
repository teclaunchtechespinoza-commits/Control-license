import React, { useState } from 'react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter
} from './ui/dialog';
import { 
  Info,
  GitBranch,
  Calendar,
  Hash,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap
} from 'lucide-react';
import { getVersionInfo, VERSION_CONFIG, getLicensingInfo } from '../config/version';

// Função para obter ícones dos recursos
const getFeatureIcon = (index) => {
  const icons = [
    // 0 - Sistema de licenças
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2h2zm-1 4a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1zm1 3a1 1 0 100 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
    </svg>,
    // 1 - Dashboard
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
      <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
    </svg>,
    // 2 - Alertas
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
    </svg>,
    // 3 - WhatsApp
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
    </svg>,
    // 4 - Multi-tenancy
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path d="M4 3a2 2 0 100 4h12a2 2 0 100-4H4z" />
      <path fillRule="evenodd" d="M3 8a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
    </svg>,
    // 5 - RBAC
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
    </svg>,
    // 6 - Clientes PF/PJ
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM9 16a7 7 0 00-7-7H1a1 1 0 000 2h1a5 5 0 011 .217V16a1 1 0 001 1h10a1 1 0 001-1v-4.783A5 5 0 0116 11h1a1 1 0 100-2h-1a7 7 0 00-7 7z" />
    </svg>,
    // 7 - Notificações
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
    </svg>,
    // 8 - Cadastros
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
    </svg>,
    // 9 - APIs
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
    </svg>,
    // 10 - Logs
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M3 4a1 1 0 011-1h4a1 1 0 010 2H6.414l2.293 2.293a1 1 0 11-1.414 1.414L5 6.414V8a1 1 0 01-2 0V4zm9 1a1 1 0 010-2h4a1 1 0 011 1v4a1 1 0 01-2 0V6.414l-2.293 2.293a1 1 0 11-1.414-1.414L13.586 5H12zm-9 7a1 1 0 012 0v1.586l2.293-2.293a1 1 0 111.414 1.414L6.414 15H8a1 1 0 010 2H4a1 1 0 01-1-1v-4zm13-1a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 010-2h1.586l-2.293-2.293a1 1 0 111.414-1.414L15.586 13H14a1 1 0 01-1-1z" clipRule="evenodd" />
    </svg>,
    // 11 - Interface WCAG
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clipRule="evenodd" />
    </svg>,
    // 12 - LGPD
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
    </svg>,
    // 13 - Versionamento
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
    </svg>,
    // 14 - Backup
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path d="M5.5 13a3.5 3.5 0 01-.369-6.98 4 4 0 117.753-1.977A4.5 4.5 0 1113.5 13H11V9.413l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13H5.5z" />
      <path d="M9 13h2v5a1 1 0 11-2 0v-5z" />
    </svg>,
    // 15 - Relatórios
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
    </svg>,
    // 16 - Usuários granulares
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
    </svg>,
    // 17 - Multi-empresa
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-6a1 1 0 00-1-1H9a1 1 0 00-1 1v6a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z" clipRule="evenodd" />
    </svg>,
    // 18 - Help/Onboarding
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
    </svg>,
    // 19 - Performance
    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
    </svg>
  ];
  
  return icons[index] || icons[0];
};

// Badge de status da versão
const StatusBadge = ({ status }) => {
  const statusConfig = {
    'stable': { 
      variant: 'default', 
      icon: CheckCircle, 
      label: 'Estável',
      className: 'bg-success-light text-success border-success/20'
    },
    'beta': { 
      variant: 'secondary', 
      icon: AlertCircle, 
      label: 'Beta',
      className: 'bg-info-light text-info border-info/20'
    },
    'rc': { 
      variant: 'outline', 
      icon: Clock, 
      label: 'Release Candidate',
      className: 'bg-warning-light text-warning border-warning/20'
    },
    'alpha': { 
      variant: 'destructive', 
      icon: Zap, 
      label: 'Alpha',
      className: 'bg-danger-light text-danger border-danger/20'
    },
    'dev': { 
      variant: 'outline', 
      icon: GitBranch, 
      label: 'Desenvolvimento',
      className: 'bg-neutral-light text-neutral border-neutral/20'
    }
  };

  const config = statusConfig[status] || statusConfig['dev'];
  const { icon: Icon, label, className } = config;

  return (
    <Badge className={`${className} flex items-center gap-1 text-xs`}>
      <Icon className="w-3 h-3" />
      {label}
    </Badge>
  );
};

// Componente principal de versão
const VersionDisplay = ({ 
  showDetailed = false, 
  showStatus = true, 
  showDate = false,
  compact = false 
}) => {
  const versionInfo = getVersionInfo();
  
  if (compact) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className="font-mono">{versionInfo.displayVersion}</span>
        {showStatus && <StatusBadge status={versionInfo.status} />}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        <GitBranch className="w-4 h-4 text-blue-600" />
        <span className="font-mono text-sm font-medium">
          {versionInfo.displayVersion}
        </span>
      </div>
      
      {showStatus && <StatusBadge status={versionInfo.status} />}
      
      {showDate && (
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Calendar className="w-3 h-3" />
          <span>{versionInfo.releaseDate}</span>
        </div>
      )}
      
      {showDetailed && (
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <Hash className="w-3 h-3" />
          <span className="font-mono">{versionInfo.buildNumber}</span>
        </div>
      )}
    </div>
  );
};

// Modal detalhado com changelog
const VersionModal = ({ children, open, setOpen }) => {
  const [activeTab, setActiveTab] = useState('version');
  const versionInfo = getVersionInfo();
  const currentChangelog = VERSION_CONFIG.changelog[versionInfo.version];
  const licensingInfo = getLicensingInfo();

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button className="flex items-center gap-2 hover:bg-gray-50 rounded-md p-2 transition-colors">
          {children}
        </button>
      </DialogTrigger>
      
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-blue-600" />
            <span>License Manager {versionInfo.displayVersion}</span>
          </DialogTitle>
          <DialogDescription>
            Informações detalhadas sobre a versão atual do sistema
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Tabs Navigation */}
          <div className="border-b">
            <nav className="flex gap-4">
              <button
                onClick={() => setActiveTab('version')}
                className={`py-2 px-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'version' 
                    ? 'border-blue-500 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                📊 Versão Atual
              </button>
              <button
                onClick={() => setActiveTab('licensing')}
                className={`py-2 px-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'licensing' 
                    ? 'border-blue-500 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                🛈 Licenciamento
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'version' && (
            <div className="space-y-6">
          {/* Informações da Versão */}
          <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="text-sm font-medium text-gray-600">Versão</label>
              <p className="font-mono text-lg font-bold">{versionInfo.displayVersion}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Status</label>
              <div className="mt-1">
                <StatusBadge status={versionInfo.status} />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Data de Release</label>
              <p className="flex items-center gap-1">
                <Calendar className="w-4 h-4 text-gray-400" />
                {versionInfo.releaseDate}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Build</label>
              <p className="font-mono text-sm">#{versionInfo.buildNumber}</p>
            </div>
          </div>

          {/* Changelog da Versão Atual */}
          {currentChangelog && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Novidades desta Versão</h3>
              
              {currentChangelog.changes.added?.length > 0 && (
                <div className="space-y-2">
                  <h4 className="flex items-center gap-2 text-sm font-medium text-green-700">
                    <CheckCircle className="w-4 h-4" />
                    Adicionado
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 ml-6">
                    {currentChangelog.changes.added.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {currentChangelog.changes.fixed?.length > 0 && (
                <div className="space-y-2">
                  <h4 className="flex items-center gap-2 text-sm font-medium text-blue-700">
                    <Info className="w-4 h-4" />
                    Corrigido
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 ml-6">
                    {currentChangelog.changes.fixed.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {currentChangelog.changes.changed?.length > 0 && (
                <div className="space-y-2">
                  <h4 className="flex items-center gap-2 text-sm font-medium text-orange-700">
                    <AlertCircle className="w-4 h-4" />
                    Modificado
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 ml-6">
                    {currentChangelog.changes.changed.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Histórico de Versões */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Histórico de Versões</h3>
            <div className="space-y-2">
              {VERSION_CONFIG.versionHistory.map((version, index) => (
                <div key={version.version} className="flex items-center justify-between p-3 border rounded-md">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-medium">v{version.version}</span>
                    <StatusBadge status={version.status} />
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Calendar className="w-3 h-3" />
                    <span>{version.date}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        )}
        
        {/* Licensing Tab */}
        {activeTab === 'licensing' && (
          <div className="space-y-6">
            {Object.entries(licensingInfo.sections).map(([key, section]) => (
              <div key={key} className="space-y-3">
                <h3 className="text-lg font-semibold text-gray-800">{section.title}</h3>
                
                {section.items && (
                  <div className="grid grid-cols-1 gap-3 p-4 bg-gray-50 rounded-lg">
                    {Object.entries(section.items).map(([label, value]) => (
                      <div key={label}>
                        <label className="text-sm font-medium text-gray-600">{label}</label>
                        {Array.isArray(value) ? (
                          key === 'features' ? (
                            // Layout especial para recursos principais
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2">
                              {value.map((item, idx) => (
                                <div key={idx} className="flex items-start gap-3 p-3 bg-white rounded-lg border shadow-sm hover:shadow-md transition-shadow">
                                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                    {getFeatureIcon(idx)}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-gray-900 leading-tight">{item}</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : key === 'compliance' ? (
                            // Layout especial para conformidades
                            <div className="grid grid-cols-1 gap-2 mt-2">
                              {value.map((item, idx) => (
                                <div key={idx} className="flex items-center gap-3 p-2 bg-green-50 rounded-md border border-green-200">
                                  <div className="flex-shrink-0">
                                    <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                                      <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                      </svg>
                                    </div>
                                  </div>
                                  <p className="text-sm font-medium text-green-800">{item}</p>
                                </div>
                              ))}
                            </div>
                          ) : (
                            // Layout padrão para outras listas
                            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 ml-2">
                              {value.map((item, idx) => (
                                <li key={idx}>{item}</li>
                              ))}
                            </ul>
                          )
                        ) : (
                          <p className="text-sm text-gray-700">{value}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                
                {section.content && (
                  <div className="p-4 bg-gray-50 rounded-lg">
                    {section.content.map((line, idx) => (
                      <p key={idx} className="text-sm text-gray-700 mb-2 last:mb-0">
                        {line}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Fechar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Componente para rodapé
export const FooterVersion = () => {
  const [open, setOpen] = useState(false);
  return (
    <VersionModal open={open} setOpen={setOpen}>
      <VersionDisplay compact showStatus />
    </VersionModal>
  );
};

// Componente para header
export const HeaderVersion = () => {
  const [open, setOpen] = useState(false);
  return (
    <VersionModal open={open} setOpen={setOpen}>
      <VersionDisplay showDate />
    </VersionModal>
  );
};

// Componente completo para páginas administrativas
export const AdminVersionInfo = () => {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-white border rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold mb-2">Informações da Versão</h3>
          <VersionDisplay showDetailed showStatus showDate />
        </div>
        <VersionModal open={open} setOpen={setOpen}>
          <Button variant="outline" size="sm">
            <GitBranch className="w-4 h-4 mr-2" />
            Ver Detalhes
          </Button>
        </VersionModal>
      </div>
    </div>
  );
};

export { VersionDisplay, StatusBadge, VersionModal };
export default VersionDisplay;