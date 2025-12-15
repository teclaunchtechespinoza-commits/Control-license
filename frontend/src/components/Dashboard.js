import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { LicenseStatusBadge, StatusBadgeWithDot } from './ui/semantic-badge';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { api } from '../api';
import { toast } from 'sonner';
import { 
  Users, 
  FileText, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  TrendingUp,
  Calendar,
  Plus,
  Edit,
  Trash2,
  Search
} from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentLicenses, setRecentLicenses] = useState([]);
  const [allLicenses, setAllLicenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingLicense, setEditingLicense] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [licenseForm, setLicenseForm] = useState({
    name: '',
    serial_number: '',
    plan_id: '',
    expires_at: '',
    description: ''
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Show welcome message only once per session using sessionStorage (more appropriate than localStorage)
  useEffect(() => {
    if (user && user.email) {
      const welcomeKey = `welcome_shown_${user.email}`;
      const welcomeShown = sessionStorage.getItem(welcomeKey);
      
      if (!welcomeShown) {
        // Use a more robust check to prevent multiple calls
        const timeoutId = setTimeout(() => {
          // Double check if still not shown to prevent race conditions
          if (!sessionStorage.getItem(welcomeKey)) {
            toast.success(`Bem-vindo de volta, ${user.name}!`);
            sessionStorage.setItem(welcomeKey, 'true');
          }
        }, 800); // Increased delay to avoid conflicts

        // Cleanup timeout on unmount
        return () => clearTimeout(timeoutId);
      }
    }
  }, [user?.email]); // Only depend on user.email to avoid unnecessary re-runs

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      


  const handleCreateLicense = async (e) => {
    e.preventDefault();
    try {
      const formData = { ...licenseForm };
      if (formData.expires_at) formData.expires_at = new Date(formData.expires_at).toISOString();
      Object.keys(formData).forEach(key => { if (!formData[key]) delete formData[key]; });
      
      await api.post('/licenses', formData);
      toast.success('Licença criada!');
      setShowCreateDialog(false);
      setLicenseForm({ name: '', serial_number: '', plan_id: '', expires_at: '', description: '' });
      setTimeout(fetchDashboardData, 500);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar');
    }
  };

  const handleEditLicense = async (e) => {
    e.preventDefault();
    try {
      const formData = { ...licenseForm };
      if (formData.expires_at) formData.expires_at = new Date(formData.expires_at).toISOString();
      Object.keys(formData).forEach(key => { if (!formData[key]) delete formData[key]; });
      
      await api.put(`/licenses/${editingLicense.id}`, formData);
      toast.success('Licença atualizada!');
      setShowEditDialog(false);
      setEditingLicense(null);
      setTimeout(fetchDashboardData, 500);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar');
    }
  };

  const handleDeleteLicense = async (licenseId) => {
    if (!window.confirm('Excluir esta licença?')) return;
    try {
      await api.delete(`/licenses/${licenseId}`);
      toast.success('Licença excluída!');
      setTimeout(fetchDashboardData, 500);
    } catch (error) {
      toast.error('Erro ao excluir');
    }
  };

  const openEditDialog = (license) => {
    setEditingLicense(license);
    setLicenseForm({
      name: license.name || '',
      serial_number: license.serial_number || '',
      plan_id: license.plan_id || '',
      expires_at: license.expires_at ? license.expires_at.split('T')[0] : '',
      description: license.description || ''
    });
    setShowEditDialog(true);
  };

  const filteredLicenses = allLicenses.filter(l => 
    searchTerm === '' || 
    l.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.serial_number?.toLowerCase().includes(searchTerm.toLowerCase())
  );

      if (user.role === 'admin' || user.role === 'super_admin') {
        const statsResponse = await api.get('/stats');
        setStats(statsResponse.data);
      }
      
      const licensesResponse = await api.get('/licenses');
      const sortedLicenses = licensesResponse.data.sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      );
      setAllLicenses(sortedLicenses);
      setRecentLicenses(sortedLicenses.slice(0, 5));
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSemanticStatusIcon = (status) => {
    // Ícones semânticos WCAG: nunca cor sozinha, sempre com contexto
    const iconConfig = {
      'active': { 
        Icon: CheckCircle, 
        className: "w-4 h-4 text-success", 
        ariaLabel: "Licença ativa - funcionando normalmente" 
      },
      'expired': { 
        Icon: XCircle, 
        className: "w-4 h-4 text-danger", 
        ariaLabel: "Licença expirada - renovação necessária" 
      },
      'suspended': { 
        Icon: AlertTriangle, 
        className: "w-4 h-4 text-warning", 
        ariaLabel: "Licença suspensa - requer atenção" 
      },
      'pending': { 
        Icon: Clock, 
        className: "w-4 h-4 text-info", 
        ariaLabel: "Licença pendente - aguardando processamento" 
      },
      'default': { 
        Icon: Clock, 
        className: "w-4 h-4 text-neutral", 
        ariaLabel: "Status desconhecido" 
      }
    };

    const config = iconConfig[status] || iconConfig['default'];
    const { Icon, className, ariaLabel } = config;
    
    return <Icon className={className} aria-label={ariaLabel} />;
  };

  const getSemanticStatusBadge = (status) => {
    // Usa o novo sistema de badges semânticos WCAG
    return <LicenseStatusBadge status={status} size="default" />;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  if (loading) {
    return <LoadingSpinner message="Carregando dashboard..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Bem-vindo, {user.name}!
        </h1>
        <p className="text-gray-600 mt-2">
          {user.role === 'admin' 
            ? 'Visão geral do sistema de controle de licenças' 
            : 'Aqui estão suas informações de licenças'
          }
        </p>
      </div>

      {/* Admin Stats */}
      {user.role === 'admin' && stats && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Total de Licenças
                </CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_licenses}</div>
                <p className="text-xs text-muted-foreground">
                  Todas as licenças no sistema
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Licenças Ativas
                </CardTitle>
                <CheckCircle className="h-4 w-4 text-success" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-success">{stats.active_licenses}</div>
                <div className="text-xs text-muted-foreground flex items-center mt-1">
                  <Progress 
                    value={stats.total_licenses > 0 ? (stats.active_licenses / stats.total_licenses) * 100 : 0} 
                    className="w-20 h-2 mr-2"
                  />
                  {stats.total_licenses > 0 ? 
                    Math.round((stats.active_licenses / stats.total_licenses) * 100) : 
                    0
                  }%
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Total de Usuários
                </CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_users}</div>
                <p className="text-xs text-muted-foreground">
                  Usuários registrados
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Licenças Expiradas
                </CardTitle>
                <XCircle className="h-4 w-4 text-danger" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-danger">{stats.expired_licenses}</div>
                <p className="text-xs text-muted-foreground">
                  Necessitam renovação
                </p>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {/* Recent Licenses */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <FileText className="w-5 h-5" />
              <span>Gerenciamento de Licenças</span>
            </CardTitle>
            {(user.role === 'admin' || user.role === 'super_admin') && (
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Nova Licença
              </Button>
            )}
          </div>
          <div className="flex items-center space-x-2 mt-4">
            <Search className="w-4 h-4 text-gray-400" />
            <Input
              placeholder="Buscar licença..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="max-w-sm"
            />
          </div>
        </CardHeader>
        <CardContent>
          {filteredLicenses.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Nenhuma licença encontrada</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredLicenses.map((license) => (
                <div key={license.id} className="flex items-center justify-between p-4 rounded-lg border hover:bg-gray-50">
                  <div className="flex items-center space-x-4 flex-1">
                    {getSemanticStatusIcon(license.status)}
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{license.name}</h4>
                      <p className="text-sm text-gray-500">Serial: {license.serial_number || license.license_key}</p>
                      <div className="flex items-center space-x-2 mt-1 text-xs text-gray-500">
                        <span>Criado: {formatDate(license.created_at)}</span>
                        {license.expires_at && (
                          <><span>•</span><span>Expira: {formatDate(license.expires_at)}</span></>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getSemanticStatusBadge(license.status)}
                    {(user.role === 'admin' || user.role === 'super_admin') && (
                      <>
                        <Button variant="outline" size="sm" onClick={() => openEditDialog(license)}>
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleDeleteLicense(license.id)}>
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal Criar */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nova Licença</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateLicense} className="space-y-4">
            <Input placeholder="Nome" value={licenseForm.name} onChange={(e) => setLicenseForm({...licenseForm, name: e.target.value})} required />
            <Input placeholder="Serial Number" value={licenseForm.serial_number} onChange={(e) => setLicenseForm({...licenseForm, serial_number: e.target.value})} />
            <Input placeholder="Plano" value={licenseForm.plan_id} onChange={(e) => setLicenseForm({...licenseForm, plan_id: e.target.value})} />
            <Input type="date" value={licenseForm.expires_at} onChange={(e) => setLicenseForm({...licenseForm, expires_at: e.target.value})} />
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>Cancelar</Button>
              <Button type="submit">Criar</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal Editar */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar Licença</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleEditLicense} className="space-y-4">
            <Input placeholder="Nome" value={licenseForm.name} onChange={(e) => setLicenseForm({...licenseForm, name: e.target.value})} required />
            <Input placeholder="Serial Number" value={licenseForm.serial_number} onChange={(e) => setLicenseForm({...licenseForm, serial_number: e.target.value})} />
            <Input placeholder="Plano" value={licenseForm.plan_id} onChange={(e) => setLicenseForm({...licenseForm, plan_id: e.target.value})} />
            <Input type="date" value={licenseForm.expires_at} onChange={(e) => setLicenseForm({...licenseForm, expires_at: e.target.value})} />
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowEditDialog(false)}>Cancelar</Button>
              <Button type="submit">Salvar</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Quick Actions for Regular Users */}
      {user.role !== 'admin' && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Ações Rápidas</CardTitle>
            <CardDescription>
              Navegue rapidamente para as funcionalidades principais
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <h3 className="font-medium text-gray-900 mb-2">Ver Todas as Licenças</h3>
                <p className="text-sm text-gray-500">
                  Visualize todas as suas licenças atribuídas
                </p>
              </div>
              <div className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer opacity-75">
                <h3 className="font-medium text-gray-900 mb-2">Solicitar Suporte</h3>
                <p className="text-sm text-gray-500">
                  Entre em contato para ajuda com suas licenças
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;