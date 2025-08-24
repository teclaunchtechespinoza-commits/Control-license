import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Building, 
  Users, 
  Key, 
  Settings, 
  Plus, 
  Edit, 
  Trash2, 
  Eye, 
  AlertCircle, 
  CheckCircle,
  Clock,
  Ban,
  PlayCircle,
  BarChart3,
  Crown,
  Package
} from 'lucide-react';

const TenantAdmin = () => {
  const [tenants, setTenants] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [tenantStats, setTenantStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);

  // Form states
  const [createForm, setCreateForm] = useState({
    name: '',
    subdomain: '',
    contact_email: '',
    plan: 'FREE',
    admin_name: '',
    admin_email: '',
    admin_password: ''
  });

  const [editForm, setEditForm] = useState({
    name: '',
    contact_email: '',
    plan: 'FREE',
    max_users: 5,
    max_licenses: 100,
    max_clients: 50
  });

  const plans = [
    { value: 'FREE', label: 'Gratuito', color: 'bg-gray-100 text-gray-800' },
    { value: 'BASIC', label: 'Básico', color: 'bg-blue-100 text-blue-800' },
    { value: 'PROFESSIONAL', label: 'Profissional', color: 'bg-purple-100 text-purple-800' },
    { value: 'ENTERPRISE', label: 'Empresarial', color: 'bg-green-100 text-green-800' }
  ];

  const statuses = {
    'ACTIVE': { label: 'Ativo', color: 'bg-green-100 text-green-800', icon: CheckCircle },
    'INACTIVE': { label: 'Inativo', color: 'bg-gray-100 text-gray-800', icon: Clock },
    'SUSPENDED': { label: 'Suspenso', color: 'bg-red-100 text-red-800', icon: Ban },
    'TRIAL': { label: 'Trial', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
    'CANCELLED': { label: 'Cancelado', color: 'bg-red-100 text-red-800', icon: AlertCircle }
  };

  useEffect(() => {
    fetchTenants();
  }, []);

  const fetchTenants = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/tenants');
      setTenants(response.data);
      setError(null);
    } catch (err) {
      setError('Erro ao carregar tenants: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const fetchTenantStats = async (tenantId) => {
    try {
      const response = await axios.get(`/api/tenants/${tenantId}/stats`);
      setTenantStats(response.data);
    } catch (err) {
      console.error('Erro ao carregar estatísticas:', err);
    }
  };

  const handleCreateTenant = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post('/api/tenants', createForm);
      setShowCreateForm(false);
      setCreateForm({
        name: '',
        subdomain: '',
        contact_email: '',
        plan: 'FREE',
        admin_name: '',
        admin_email: '',
        admin_password: ''
      });
      fetchTenants();
      setError(null);
    } catch (err) {
      setError('Erro ao criar tenant: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTenant = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.put(`/api/tenants/${selectedTenant.id}`, editForm);
      setShowEditForm(false);
      setSelectedTenant(null);
      fetchTenants();
      setError(null);
    } catch (err) {
      setError('Erro ao atualizar tenant: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSuspendTenant = async (tenantId, reason = 'Suspensão administrativa') => {
    if (!window.confirm('Tem certeza que deseja suspender este tenant?')) return;
    
    setLoading(true);
    try {
      await axios.post(`/api/tenants/${tenantId}/suspend`, null, {
        params: { reason }
      });
      fetchTenants();
      setError(null);
    } catch (err) {
      setError('Erro ao suspender tenant: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleActivateTenant = async (tenantId) => {
    setLoading(true);
    try {
      await axios.post(`/api/tenants/${tenantId}/activate`);
      fetchTenants();
      setError(null);
    } catch (err) {
      setError('Erro ao ativar tenant: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const openEditForm = (tenant) => {
    setSelectedTenant(tenant);
    setEditForm({
      name: tenant.name,
      contact_email: tenant.contact_email,
      plan: tenant.plan,
      max_users: tenant.max_users,
      max_licenses: tenant.max_licenses,
      max_clients: tenant.max_clients
    });
    setShowEditForm(true);
  };

  const viewTenantStats = (tenant) => {
    setSelectedTenant(tenant);
    fetchTenantStats(tenant.id);
  };

  if (loading && tenants.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Building className="w-6 h-6 mr-2" />
            Administração Multi-Tenant
          </h1>
          <p className="text-gray-600 mt-1">Gerencie clientes SaaS e seus recursos</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Novo Tenant
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
          <AlertCircle className="w-4 h-4 inline mr-2" />
          {error}
        </div>
      )}

      {/* Tenants Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tenants.map((tenant) => {
          const StatusIcon = statuses[tenant.status]?.icon || AlertCircle;
          const statusInfo = statuses[tenant.status] || statuses['INACTIVE'];
          const planInfo = plans.find(p => p.value === tenant.plan) || plans[0];
          
          return (
            <div key={tenant.id} className="bg-white rounded-lg shadow-md p-6 border">
              {/* Tenant Header */}
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">{tenant.name}</h3>
                  <p className="text-sm text-gray-600">@{tenant.subdomain}</p>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => viewTenantStats(tenant)}
                    className="p-2 text-gray-400 hover:text-blue-600 rounded"
                    title="Ver Estatísticas"
                  >
                    <BarChart3 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => openEditForm(tenant)}
                    className="p-2 text-gray-400 hover:text-green-600 rounded"
                    title="Editar"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Status and Plan */}
              <div className="flex justify-between items-center mb-4">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusInfo.color} flex items-center`}>
                  <StatusIcon className="w-3 h-3 mr-1" />
                  {statusInfo.label}
                </span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${planInfo.color} flex items-center`}>
                  <Crown className="w-3 h-3 mr-1" />
                  {planInfo.label}
                </span>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-lg font-bold text-gray-900">{tenant.current_users || 0}</div>
                  <div className="text-xs text-gray-500">Usuários</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-gray-900">{tenant.current_licenses || 0}</div>
                  <div className="text-xs text-gray-500">Licenças</div>
                </div>
              </div>

              {/* Contact Info */}
              <div className="text-sm text-gray-600 mb-4">
                <p>{tenant.contact_email}</p>
                <p className="text-xs">Criado: {new Date(tenant.created_at).toLocaleDateString('pt-BR')}</p>
              </div>

              {/* Actions */}
              <div className="flex space-x-2">
                {tenant.status === 'ACTIVE' && (
                  <button
                    onClick={() => handleSuspendTenant(tenant.id)}
                    className="flex-1 bg-red-100 text-red-700 px-3 py-2 rounded text-sm hover:bg-red-200 flex items-center justify-center"
                  >
                    <Ban className="w-3 h-3 mr-1" />
                    Suspender
                  </button>
                )}
                {tenant.status === 'SUSPENDED' && (
                  <button
                    onClick={() => handleActivateTenant(tenant.id)}
                    className="flex-1 bg-green-100 text-green-700 px-3 py-2 rounded text-sm hover:bg-green-200 flex items-center justify-center"
                  >
                    <PlayCircle className="w-3 h-3 mr-1" />
                    Ativar
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Tenant Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Criar Novo Tenant</h2>
            <form onSubmit={handleCreateTenant} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Nome da Empresa</label>
                <input
                  type="text"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({...createForm, name: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Subdomínio</label>
                <input
                  type="text"
                  value={createForm.subdomain}
                  onChange={(e) => setCreateForm({...createForm, subdomain: e.target.value.toLowerCase()})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="empresaabc"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Email de Contato</label>
                <input
                  type="email"
                  value={createForm.contact_email}
                  onChange={(e) => setCreateForm({...createForm, contact_email: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Plano</label>
                <select
                  value={createForm.plan}
                  onChange={(e) => setCreateForm({...createForm, plan: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  {plans.map(plan => (
                    <option key={plan.value} value={plan.value}>{plan.label}</option>
                  ))}
                </select>
              </div>

              <hr className="my-4" />
              <h3 className="font-medium text-gray-900">Administrador do Tenant</h3>

              <div>
                <label className="block text-sm font-medium text-gray-700">Nome do Admin</label>
                <input
                  type="text"
                  value={createForm.admin_name}
                  onChange={(e) => setCreateForm({...createForm, admin_name: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Email do Admin</label>
                <input
                  type="email"
                  value={createForm.admin_email}
                  onChange={(e) => setCreateForm({...createForm, admin_email: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Senha do Admin</label>
                <input
                  type="password"
                  value={createForm.admin_password}
                  onChange={(e) => setCreateForm({...createForm, admin_password: e.target.value})}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  minLength="8"
                  required
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Criando...' : 'Criar Tenant'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Tenant Stats Modal */}
      {selectedTenant && tenantStats && !showEditForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">Estatísticas - {selectedTenant.name}</h2>
              <button
                onClick={() => {setSelectedTenant(null); setTenantStats(null);}}
                className="text-gray-400 hover:text-gray-600"
              >
                <span className="sr-only">Fechar</span>
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <Users className="w-8 h-8 text-blue-600 mr-3" />
                  <div>
                    <div className="text-2xl font-bold text-blue-900">{tenantStats.usage.current_users}</div>
                    <div className="text-blue-600 text-sm">Usuários</div>
                    <div className="text-xs text-gray-500">
                      Limite: {tenantStats.limits.max_users === -1 ? '∞' : tenantStats.limits.max_users}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <Key className="w-8 h-8 text-green-600 mr-3" />
                  <div>
                    <div className="text-2xl font-bold text-green-900">{tenantStats.usage.current_licenses}</div>
                    <div className="text-green-600 text-sm">Licenças</div>
                    <div className="text-xs text-gray-500">
                      Limite: {tenantStats.limits.max_licenses === -1 ? '∞' : tenantStats.limits.max_licenses}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <Building className="w-8 h-8 text-purple-600 mr-3" />
                  <div>
                    <div className="text-2xl font-bold text-purple-900">
                      {tenantStats.usage.current_clients_pf + tenantStats.usage.current_clients_pj}
                    </div>
                    <div className="text-purple-600 text-sm">Clientes</div>
                    <div className="text-xs text-gray-500">
                      PF: {tenantStats.usage.current_clients_pf} | PJ: {tenantStats.usage.current_clients_pj}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <Package className="w-8 h-8 text-orange-600 mr-3" />
                  <div>
                    <div className="text-2xl font-bold text-orange-900">
                      {tenantStats.usage.categories + tenantStats.usage.products}
                    </div>
                    <div className="text-orange-600 text-sm">Cadastros</div>
                    <div className="text-xs text-gray-500">
                      Cat: {tenantStats.usage.categories} | Prod: {tenantStats.usage.products}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Compliance Status */}
            <div className="bg-gray-50 p-4 rounded-lg mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">Status de Conformidade</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className={`flex items-center ${tenantStats.compliance.users_ok ? 'text-green-600' : 'text-red-600'}`}>
                  {tenantStats.compliance.users_ok ? <CheckCircle className="w-4 h-4 mr-2" /> : <AlertCircle className="w-4 h-4 mr-2" />}
                  <span className="text-sm">Usuários OK</span>
                </div>
                <div className={`flex items-center ${tenantStats.compliance.licenses_ok ? 'text-green-600' : 'text-red-600'}`}>
                  {tenantStats.compliance.licenses_ok ? <CheckCircle className="w-4 h-4 mr-2" /> : <AlertCircle className="w-4 h-4 mr-2" />}
                  <span className="text-sm">Licenças OK</span>
                </div>
                <div className={`flex items-center ${tenantStats.compliance.clients_ok ? 'text-green-600' : 'text-red-600'}`}>
                  {tenantStats.compliance.clients_ok ? <CheckCircle className="w-4 h-4 mr-2" /> : <AlertCircle className="w-4 h-4 mr-2" />}
                  <span className="text-sm">Clientes OK</span>
                </div>
              </div>
            </div>

            {/* Features */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-3">Recursos Habilitados</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {Object.entries(tenantStats.features).map(([feature, enabled]) => (
                  <div key={feature} className={`flex items-center text-sm ${enabled ? 'text-green-600' : 'text-gray-400'}`}>
                    {enabled ? <CheckCircle className="w-3 h-3 mr-2" /> : <AlertCircle className="w-3 h-3 mr-2" />}
                    <span className="capitalize">{feature.replace('_', ' ')}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TenantAdmin;