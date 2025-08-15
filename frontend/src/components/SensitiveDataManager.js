import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
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
  Eye, 
  EyeOff, 
  Shield, 
  Key, 
  Lock, 
  AlertTriangle, 
  Copy,
  CheckCircle,
  Info
} from 'lucide-react';
import { useAuth } from '../App';

// Utilitário para verificar se usuário pode ver dados sensíveis
const canViewSensitiveData = (userRole) => {
  const privilegedRoles = ['admin', 'super_admin', 'technical_lead'];
  return privilegedRoles.includes(userRole);
};

// Componente para campo mascarado/protegido
const SensitiveField = ({ 
  label, 
  value, 
  maskedValue, 
  fieldType = "text", 
  canView = false, 
  referenceKey = "",
  className = "",
  copyable = false 
}) => {
  const [showReal, setShowReal] = useState(false);
  const [copied, setCopied] = useState(false);

  const displayValue = (canView && showReal) ? value : (maskedValue || `[PROTEGIDO-${referenceKey}]`);
  
  const handleCopy = async () => {
    if (canView && value) {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getFieldIcon = () => {
    if (fieldType === "password") return <Lock className="w-4 h-4" />;
    if (fieldType === "key") return <Key className="w-4 h-4" />;
    return <Shield className="w-4 h-4" />;
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <Label className="flex items-center gap-2 text-sm font-medium text-gray-600">
        {getFieldIcon()}
        {label}
        {!canView && (
          <Badge variant="outline" className="text-xs bg-orange-50 text-orange-700 border-orange-200">
            <AlertTriangle className="w-3 h-3 mr-1" />
            Protegido
          </Badge>
        )}
      </Label>
      
      <div className="flex items-center gap-2">
        <Input
          type={showReal ? "text" : "password"}
          value={displayValue}
          readOnly
          className={`font-mono text-sm ${!canView ? 'bg-gray-100 text-gray-500' : 'bg-white'}`}
        />
        
        {canView && (
          <div className="flex gap-1">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowReal(!showReal)}
              className="px-2"
            >
              {showReal ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </Button>
            
            {copyable && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleCopy}
                className="px-2"
              >
                {copied ? <CheckCircle className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
              </Button>
            )}
          </div>
        )}
        
        {!canView && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled
            className="px-2 opacity-50"
          >
            <Lock className="w-4 h-4" />
          </Button>
        )}
      </div>
      
      {!canView && (
        <p className="text-xs text-gray-500 flex items-center gap-1">
          <Info className="w-3 h-3" />
          Dados protegidos. Referência: <code className="bg-gray-100 px-1 rounded">{referenceKey}</code>
        </p>
      )}
    </div>
  );
};

// Seção completa de dados sensíveis
const SensitiveDataSection = ({ sensitiveData, clientId, licenseReference }) => {
  const { user } = useAuth();
  const canView = canViewSensitiveData(user?.role);
  const [showSection, setShowSection] = useState(false);

  if (!sensitiveData) {
    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-2 border-b pb-2">
          <Shield className="w-4 h-4 text-gray-400" />
          <h3 className="font-medium text-gray-500">Dados Sensíveis</h3>
          <Badge variant="outline" className="text-xs">
            Não configurado
          </Badge>
        </div>
        <p className="text-sm text-gray-500">Nenhum dado sensível cadastrado para este cliente.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between border-b pb-2">
        <div className="flex items-center space-x-2">
          <Shield className="w-4 h-4 text-red-600" />
          <h3 className="font-medium">Dados Sensíveis do Equipamento</h3>
          {canView ? (
            <Badge className="bg-green-50 text-green-700 border-green-200">
              <CheckCircle className="w-3 h-3 mr-1" />
              Acesso Autorizado
            </Badge>
          ) : (
            <Badge className="bg-orange-50 text-orange-700 border-orange-200">
              <Lock className="w-3 h-3 mr-1" />
              Acesso Restrito
            </Badge>
          )}
        </div>
        
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowSection(!showSection)}
        >
          {showSection ? 'Ocultar' : 'Mostrar'} Dados
          {showSection ? <EyeOff className="w-4 h-4 ml-2" /> : <Eye className="w-4 h-4 ml-2" />}
        </Button>
      </div>

      {showSection && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg border">
          {/* IDs e Números */}
          <div className="space-y-4">
            <h4 className="font-medium text-sm text-gray-700 border-b pb-1">Identificação</h4>
            
            {sensitiveData.internal_equipment_id && (
              <SensitiveField
                label="ID Interno do Equipamento"
                value={sensitiveData.internal_equipment_id}
                maskedValue={sensitiveData.internal_equipment_id}
                fieldType="key"
                canView={canView}
                referenceKey={licenseReference}
                copyable
              />
            )}
            
            {sensitiveData.serial_number && (
              <SensitiveField
                label="Número de Série"
                value={sensitiveData.serial_number}
                maskedValue={sensitiveData.serial_number}
                fieldType="key"
                canView={canView}
                referenceKey={licenseReference}
                copyable
              />
            )}
            
            {sensitiveData.mac_address && (
              <SensitiveField
                label="Endereço MAC"
                value={sensitiveData.mac_address}
                maskedValue={sensitiveData.mac_address}
                fieldType="key"
                canView={canView}
                referenceKey={licenseReference}
                copyable
              />
            )}
          </div>

          {/* Credenciais */}
          <div className="space-y-4">
            <h4 className="font-medium text-sm text-gray-700 border-b pb-1">Credenciais</h4>
            
            {sensitiveData.admin_username && (
              <SensitiveField
                label="Usuário Administrador"
                value={sensitiveData.admin_username}
                maskedValue="[PROTEGIDO]"
                fieldType="text"
                canView={canView}
                referenceKey={licenseReference}
                copyable
              />
            )}
            
            {sensitiveData.admin_password && (
              <SensitiveField
                label="Senha Administrador"
                value={sensitiveData.admin_password}
                maskedValue="[PROTEGIDO]"
                fieldType="password"
                canView={canView}
                referenceKey={licenseReference}
                copyable
              />
            )}
            
            {sensitiveData.service_password && (
              <SensitiveField
                label="Senha de Serviço"
                value={sensitiveData.service_password}
                maskedValue="[PROTEGIDO]"
                fieldType="password"
                canView={canView}
                referenceKey={licenseReference}
                copyable
              />
            )}
            
            {sensitiveData.wifi_password && (
              <SensitiveField
                label="Senha WiFi"
                value={sensitiveData.wifi_password}
                maskedValue="[PROTEGIDO]"
                fieldType="password"
                canView={canView}
                referenceKey={licenseReference}
                copyable
              />
            )}
          </div>

          {/* Informações de Acesso */}
          {!canView && (
            <div className="md:col-span-2 p-3 bg-amber-50 border border-amber-200 rounded-md">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span className="text-sm font-medium text-amber-800">Dados Protegidos</span>
              </div>
              <p className="text-xs text-amber-700">
                Seu nível de acesso não permite visualizar dados sensíveis. 
                Entre em contato com um administrador se precisar acessar estas informações.
              </p>
              <p className="text-xs text-amber-600 mt-1">
                <strong>Referência para suporte:</strong> <code>{licenseReference}</code>
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Modal para adicionar/editar dados sensíveis (apenas admins)
const SensitiveDataEditor = ({ clientId, sensitiveData, onSave }) => {
  const { user } = useAuth();
  const canEdit = canViewSensitiveData(user?.role);
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState(sensitiveData || {});

  if (!canEdit) return null;

  const handleSave = () => {
    onSave(formData);
    setIsOpen(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="flex items-center gap-2">
          <Shield className="w-4 h-4" />
          Editar Dados Sensíveis
        </Button>
      </DialogTrigger>
      
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-red-600" />
            Gerenciar Dados Sensíveis
          </DialogTitle>
          <DialogDescription>
            Gerencie informações confidenciais do cliente. Estes dados são protegidos e mascarados para usuários sem permissão.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>ID Interno do Equipamento</Label>
              <Input
                value={formData.internal_equipment_id || ''}
                onChange={(e) => setFormData({...formData, internal_equipment_id: e.target.value})}
                placeholder="ID interno confidencial"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Número de Série</Label>
              <Input
                value={formData.serial_number || ''}
                onChange={(e) => setFormData({...formData, serial_number: e.target.value})}
                placeholder="Serial number"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Endereço MAC</Label>
              <Input
                value={formData.mac_address || ''}
                onChange={(e) => setFormData({...formData, mac_address: e.target.value})}
                placeholder="00:00:00:00:00:00"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Chave de Hardware</Label>
              <Input
                value={formData.hardware_key || ''}
                onChange={(e) => setFormData({...formData, hardware_key: e.target.value})}
                placeholder="Hardware key"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Usuário Administrador</Label>
              <Input
                value={formData.admin_username || ''}
                onChange={(e) => setFormData({...formData, admin_username: e.target.value})}
                placeholder="username"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Senha Administrador</Label>
              <Input
                type="password"
                value={formData.admin_password || ''}
                onChange={(e) => setFormData({...formData, admin_password: e.target.value})}
                placeholder="••••••••"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Senha de Serviço</Label>
              <Input
                type="password"
                value={formData.service_password || ''}
                onChange={(e) => setFormData({...formData, service_password: e.target.value})}
                placeholder="••••••••"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Senha WiFi</Label>
              <Input
                type="password"
                value={formData.wifi_password || ''}
                onChange={(e) => setFormData({...formData, wifi_password: e.target.value})}
                placeholder="••••••••"
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSave}>
            Salvar Dados Sensíveis
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export { SensitiveField, SensitiveDataSection, SensitiveDataEditor, canViewSensitiveData };
export default SensitiveDataSection;