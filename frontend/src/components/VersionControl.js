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
export const FooterVersion = () => (
  <VersionModal>
    <VersionDisplay compact showStatus />
  </VersionModal>
);

// Componente para header
export const HeaderVersion = () => (
  <VersionModal>
    <VersionDisplay showDate />
  </VersionModal>
);

// Componente completo para páginas administrativas
export const AdminVersionInfo = () => (
  <div className="bg-white border rounded-lg p-4">
    <h3 className="text-sm font-medium text-gray-700 mb-3">Informações da Versão</h3>
    <VersionDisplay showDetailed showStatus showDate />
    <VersionModal>
      <Button variant="outline" size="sm" className="mt-3">
        <Info className="w-4 h-4 mr-2" />
        Ver Detalhes
      </Button>
    </VersionModal>
  </div>
);

export { VersionDisplay, StatusBadge, VersionModal };
export default VersionDisplay;