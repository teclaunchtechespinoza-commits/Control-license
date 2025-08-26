import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { useApiCache } from '../hooks/useApiCache';
import { 
  Building, 
  ChevronDown, 
  Check, 
  Crown, 
  Globe 
} from 'lucide-react';

const TenantSelector = ({ currentUser }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Use cached API calls
  const { data: myTenant, loading: tenantLoading, error: tenantError } = useApiCache('/my-tenant', [currentUser?.id]);
  const { data: availableTenants, loading: tenantsLoading } = useApiCache(
    currentUser?.role === 'super_admin' ? '/tenants' : null, 
    [currentUser?.role]
  );

  const plans = {
    'FREE': { label: 'Gratuito', color: 'text-gray-600', bgColor: 'bg-gray-50' },
    'BASIC': { label: 'Básico', color: 'text-blue-600', bgColor: 'bg-blue-50' },
    'PROFESSIONAL': { label: 'Profissional', color: 'text-purple-600', bgColor: 'bg-purple-50' },
    'ENTERPRISE': { label: 'Empresarial', color: 'text-green-600', bgColor: 'bg-green-50' }
  };

  const handleTenantSwitch = async (tenantId) => {
    if (!currentUser || currentUser.role !== 'super_admin') {
      return;
    }

    setLoading(true);
    try {
      // Definir header X-Tenant-ID para próximas requisições
      axios.defaults.headers.common['X-Tenant-ID'] = tenantId;
      
      setIsOpen(false);
      
      // Recarregar página para aplicar o novo contexto de tenant
      setTimeout(() => {
        window.location.reload();
      }, 500);
      
    } catch (err) {
      console.error('Erro ao trocar tenant:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatSubdomain = (subdomain) => {
    return subdomain ? `@${subdomain}` : '';
  };

  const getPlanInfo = (plan) => {
    const normalizedPlan = plan?.toUpperCase();
    return plans[normalizedPlan] || plans['FREE'];
  };

  if (!myTenant) {
    return (
      <div className="flex items-center space-x-2 text-gray-500">
        <Building className="w-4 h-4 animate-pulse" />
        <span className="text-sm">Carregando...</span>
      </div>
    );
  }

  const planInfo = getPlanInfo(myTenant.plan);

  // Se não é super admin, mostrar apenas informações do tenant atual
  if (currentUser?.role !== 'super_admin') {
    return (
      <div className="flex items-center space-x-3 bg-white rounded-lg px-3 py-2 border border-gray-200">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${planInfo.bgColor}`}>
          <Building className={`w-4 h-4 ${planInfo.color}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-medium text-gray-900 truncate">
              {myTenant.name}
            </h3>
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${planInfo.color} ${planInfo.bgColor}`}>
              <Crown className="w-3 h-3 mr-1" />
              {planInfo.label}
            </span>
          </div>
          <p className="text-xs text-gray-500 truncate">
            {formatSubdomain(myTenant.subdomain)}
          </p>
        </div>
      </div>
    );
  }

  // Super admin - mostrar seletor completo
  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={loading}
        className="flex items-center space-x-3 bg-white rounded-lg px-3 py-2 border border-gray-200 hover:border-gray-300 transition-colors w-full min-w-[280px] disabled:opacity-50"
      >
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${planInfo.bgColor}`}>
          <Building className={`w-4 h-4 ${planInfo.color}`} />
        </div>
        <div className="flex-1 min-w-0 text-left">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-medium text-gray-900 truncate">
              {myTenant.name}
            </h3>
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${planInfo.color} ${planInfo.bgColor}`}>
              <Crown className="w-3 h-3 mr-1" />
              {planInfo.label}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <p className="text-xs text-gray-500 truncate">
              {formatSubdomain(myTenant.subdomain)}
            </p>
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
              <Globe className="w-3 h-3 mr-1" />
              Super Admin
            </span>
          </div>
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
          <div className="py-2">
            <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-100">
              Trocar Contexto de Tenant
            </div>
            
            {availableTenants.map((tenant) => {
              const tenantPlanInfo = getPlanInfo(tenant.plan);
              const isCurrentTenant = tenant.id === myTenant?.id;
              
              return (
                <button
                  key={tenant.id}
                  onClick={() => handleTenantSwitch(tenant.id)}
                  disabled={loading || isCurrentTenant}
                  className={`w-full px-3 py-2 text-left hover:bg-gray-50 transition-colors flex items-center space-x-3 ${
                    isCurrentTenant ? 'bg-blue-50 cursor-default' : 'cursor-pointer'
                  } disabled:opacity-50`}
                >
                  <div className={`w-6 h-6 rounded flex items-center justify-center ${tenantPlanInfo.bgColor}`}>
                    <Building className={`w-3 h-3 ${tenantPlanInfo.color}`} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {tenant.name}
                      </span>
                      {isCurrentTenant && (
                        <Check className="w-4 h-4 text-blue-600" />
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500 truncate">
                        {formatSubdomain(tenant.subdomain)}
                      </span>
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${tenantPlanInfo.color} ${tenantPlanInfo.bgColor}`}>
                        {tenantPlanInfo.label}
                      </span>
                      
                      {tenant.status !== 'ACTIVE' && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                          {tenant.status}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Overlay para fechar dropdown */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default TenantSelector;