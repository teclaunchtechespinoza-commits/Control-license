import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from './ui/dialog';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from './ui/table';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';
import { api } from '../api';
import { toast } from 'sonner';
import { 
  Plus,
  Edit,
  Trash2,
  Search,
  RefreshCw,
  Calendar,
  User,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  History,
  Key,
  FileText,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Users
} from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';

const LicenseManagement = () => {
  const { user } = useAuth();
  
  // Estados principais
  const [licenses, setLicenses] = useState([]);
  const [salespeople, setSalespeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Estados de modais
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showRenewDialog, setShowRenewDialog] = useState(false);
  const [showHistoryDialog, setShowHistoryDialog] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  
  // Estados de dados selecionados
  const [selectedLicense, setSelectedLicense] = useState(null);
  const [renewalHistory, setRenewalHistory] = useState([]);
  
  // Estados de formulários
  const [licenseForm, setLicenseForm] = useState({
    name: '',
    description: '',
    serial_number: '',
    manufacturer: '',
    model: '',
    max_users: 1,
    validity_days: 365,
    salesperson_id: '',
    salesperson_name: '',
    status: 'pending'
  });
  
  const [renewForm, setRenewForm] = useState({
    validity_days: 365,
    notes: ''
  });
  
  // Estado para expandir detalhes
  const [expandedRow, setExpandedRow] = useState(null);

  // Carregar dados
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [licensesRes, salespeopleRes] = await Promise.all([
        api.get('/licenses'),
        api.get('/admin/salespeople')
      ]);
      
      setLicenses(licensesRes.data || []);
      setSalespeople(salespeopleRes.data?.salespeople || []);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      toast.error('Erro ao carregar licenças');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Reset form
  const resetForm = () => {
    setLicenseForm({
      name: '',
      description: '',
      serial_number: '',
      manufacturer: '',
      model: '',
      max_users: 1,
      validity_days: 365,
      salesperson_id: '',
      salesperson_name: '',
      status: 'pending'
    });
  };

  // Criar licença
  const handleCreateLicense = async (e) => {
    e.preventDefault();
    try {
      // Calcular data de expiração baseada em validity_days
      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + licenseForm.validity_days);
      
      const payload = {
        ...licenseForm,
        expires_at: expiresAt.toISOString(),
        activation_date: new Date().toISOString()
      };
      
      await api.post('/licenses', payload);
      toast.success('Licença criada com sucesso!');
      setShowCreateDialog(false);
      resetForm();
      fetchData();
    } catch (error) {
      console.error('Erro ao criar licença:', error);
      toast.error(error.response?.data?.detail || 'Erro ao criar licença');
    }
  };

  // Editar licença
  const handleEditLicense = async (e) => {
    e.preventDefault();
    if (!selectedLicense) return;
    
    try {
      await api.put(`/licenses/${selectedLicense.id}`, licenseForm);
      toast.success('Licença atualizada com sucesso!');
      setShowEditDialog(false);
      setSelectedLicense(null);
      resetForm();
      fetchData();
    } catch (error) {
      console.error('Erro ao atualizar licença:', error);
      toast.error(error.response?.data?.detail || 'Erro ao atualizar licença');
    }
  };

  // Renovar licença
  const handleRenewLicense = async () => {
    if (!selectedLicense) return;
    
    try {
      const response = await api.post(`/licenses/${selectedLicense.id}/renew`, renewForm);
      toast.success(response.data.message);
      setShowRenewDialog(false);
      setSelectedLicense(null);
      setRenewForm({ validity_days: 365, notes: '' });
      fetchData();
    } catch (error) {
      console.error('Erro ao renovar licença:', error);
      toast.error(error.response?.data?.detail || 'Erro ao renovar licença');
    }
  };

  // Carregar histórico de renovações
  const loadRenewalHistory = async (license) => {
    try {
      const response = await api.get(`/licenses/${license.id}/history`);
      setRenewalHistory(response.data.renewal_history || []);
      setSelectedLicense(license);
      setShowHistoryDialog(true);
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
      toast.error('Erro ao carregar histórico de renovações');
    }
  };

  // Deletar licença
  const handleDeleteLicense = async () => {
    if (!deleteConfirmId) return;
    
    try {
      await api.delete(`/licenses/${deleteConfirmId}`);
      toast.success('Licença excluída com sucesso!');
      setDeleteConfirmId(null);
      fetchData();
    } catch (error) {
      console.error('Erro ao excluir licença:', error);
      toast.error(error.response?.data?.detail || 'Erro ao excluir licença');
    }
  };

  // Abrir modal de edição
  const openEditDialog = (license) => {
    setSelectedLicense(license);
    setLicenseForm({
      name: license.name || '',
      description: license.description || '',
      serial_number: license.serial_number || '',
      manufacturer: license.manufacturer || '',
      model: license.model || '',
      max_users: license.max_users || 1,
      validity_days: license.validity_days || 365,
      salesperson_id: license.salesperson_id || '',
      salesperson_name: license.salesperson_name || '',
      status: license.status || 'pending'
    });
    setShowEditDialog(true);
  };

  // Abrir modal de renovação
  const openRenewDialog = (license) => {
    setSelectedLicense(license);
    setRenewForm({
      validity_days: license.validity_days || 365,
      notes: ''
    });
    setShowRenewDialog(true);
  };

  // Atualizar vendedor no formulário
  const handleSalespersonChange = (salespersonId) => {
    // Tratar "none" como string vazia (sem vendedor)
    const actualId = salespersonId === 'none' ? '' : salespersonId;
    const salesperson = salespeople.find(s => s.id === actualId);
    setLicenseForm({
      ...licenseForm,
      salesperson_id: actualId,
      salesperson_name: salesperson?.name || ''
    });
  };

  // Calcular dias restantes
  const calculateDaysRemaining = (expiresAt) => {
    if (!expiresAt) return null;
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diff = Math.ceil((expiry - now) / (1000 * 60 * 60 * 24));
    return diff;
  };

  // Obter cor do badge de dias restantes
  const getDaysRemainingBadge = (days) => {
    if (days === null) return <Badge variant="outline">Sem limite</Badge>;
    if (days < 0) return <Badge className="bg-red-600 text-white">{Math.abs(days)} dias expirado</Badge>;
    if (days <= 30) return <Badge className="bg-orange-500 text-white">{days} dias</Badge>;
    if (days <= 90) return <Badge className="bg-yellow-500 text-black">{days} dias</Badge>;
    return <Badge className="bg-green-600 text-white">{days} dias</Badge>;
  };

  // Obter badge de status
  const getStatusBadge = (status) => {
    const configs = {
      active: { color: 'bg-green-100 text-green-800', icon: CheckCircle, label: 'Ativa' },
      expired: { color: 'bg-red-100 text-red-800', icon: XCircle, label: 'Expirada' },
      suspended: { color: 'bg-orange-100 text-orange-800', icon: AlertTriangle, label: 'Suspensa' },
      pending: { color: 'bg-blue-100 text-blue-800', icon: Clock, label: 'Pendente' },
      cancelled: { color: 'bg-gray-100 text-gray-800', icon: XCircle, label: 'Cancelada' }
    };
    const config = configs[status] || configs.pending;
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </span>
    );
  };

  // Formatar data
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  // Formatar data/hora
  const formatDateTime = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Filtrar licenças
  const filteredLicenses = licenses.filter(license => {
    const matchesSearch = 
      (license.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      (license.serial_number?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      (license.license_key?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      (license.manufacturer?.toLowerCase() || '').includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || license.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return <LoadingSpinner message="Carregando licenças..." />;
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-full" data-testid="license-management">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Key className="w-8 h-8 text-blue-600" />
          Gestão de Licenças
        </h1>
        <p className="text-gray-600 mt-2">
          Gerencie licenças, renovações e vendedores
        </p>
      </div>

      {/* Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Ativas</p>
                <p className="text-2xl font-bold text-green-600">
                  {licenses.filter(l => l.status === 'active').length}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Expirando (30d)</p>
                <p className="text-2xl font-bold text-orange-600">
                  {licenses.filter(l => {
                    const days = calculateDaysRemaining(l.expires_at);
                    return days !== null && days > 0 && days <= 30;
                  }).length}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-orange-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-red-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Expiradas</p>
                <p className="text-2xl font-bold text-red-600">
                  {licenses.filter(l => l.status === 'expired').length}
                </p>
              </div>
              <XCircle className="w-8 h-8 text-red-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total</p>
                <p className="text-2xl font-bold text-blue-600">{licenses.length}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros e Ações */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Buscar por nome, serial, chave..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                  data-testid="search-input"
                />
              </div>
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]" data-testid="status-filter">
                <SelectValue placeholder="Filtrar por status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os status</SelectItem>
                <SelectItem value="active">Ativas</SelectItem>
                <SelectItem value="pending">Pendentes</SelectItem>
                <SelectItem value="expired">Expiradas</SelectItem>
                <SelectItem value="suspended">Suspensas</SelectItem>
                <SelectItem value="cancelled">Canceladas</SelectItem>
              </SelectContent>
            </Select>
            
            <Button onClick={fetchData} variant="outline" data-testid="refresh-btn">
              <RefreshCw className="w-4 h-4 mr-2" />
              Atualizar
            </Button>
            
            <Button onClick={() => setShowCreateDialog(true)} data-testid="new-license-btn">
              <Plus className="w-4 h-4 mr-2" />
              Nova Licença
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tabela de Licenças */}
      <Card>
        <CardHeader>
          <CardTitle>Licenças ({filteredLicenses.length})</CardTitle>
          <CardDescription>
            Clique em uma linha para expandir detalhes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[30px]"></TableHead>
                  <TableHead>Nome / Serial</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Dias Restantes</TableHead>
                  <TableHead>Vendedor</TableHead>
                  <TableHead>Validade (dias)</TableHead>
                  <TableHead>Renovações</TableHead>
                  <TableHead className="text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLicenses.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                      <FileText className="w-12 h-12 mx-auto mb-2 opacity-30" />
                      Nenhuma licença encontrada
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredLicenses.map((license) => (
                    <React.Fragment key={license.id}>
                      <TableRow 
                        className="cursor-pointer hover:bg-gray-50"
                        onClick={() => setExpandedRow(expandedRow === license.id ? null : license.id)}
                      >
                        <TableCell>
                          {expandedRow === license.id ? (
                            <ChevronUp className="w-4 h-4 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                          )}
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{license.name}</p>
                            <p className="text-xs text-gray-500">
                              {license.serial_number || license.license_key}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>{getStatusBadge(license.status)}</TableCell>
                        <TableCell>
                          {getDaysRemainingBadge(calculateDaysRemaining(license.expires_at))}
                        </TableCell>
                        <TableCell>
                          {license.salesperson_name ? (
                            <span className="flex items-center gap-1">
                              <User className="w-3 h-3 text-gray-400" />
                              {license.salesperson_name}
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <span className="font-mono">{license.validity_days || 365}</span>
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              loadRenewalHistory(license);
                            }}
                            className="text-blue-600"
                            data-testid={`history-btn-${license.id}`}
                          >
                            <History className="w-4 h-4 mr-1" />
                            {(license.renewal_history || []).length}
                          </Button>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openRenewDialog(license)}
                              className="text-green-600 hover:text-green-700"
                              title="Renovar"
                              data-testid={`renew-btn-${license.id}`}
                            >
                              <RotateCcw className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openEditDialog(license)}
                              className="text-blue-600 hover:text-blue-700"
                              title="Editar"
                              data-testid={`edit-btn-${license.id}`}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setDeleteConfirmId(license.id)}
                              className="text-red-600 hover:text-red-700"
                              title="Excluir"
                              data-testid={`delete-btn-${license.id}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                      
                      {/* Linha expandida com detalhes */}
                      {expandedRow === license.id && (
                        <TableRow className="bg-gray-50">
                          <TableCell colSpan={8}>
                            <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              <div>
                                <p className="text-gray-500">Fabricante</p>
                                <p className="font-medium">{license.manufacturer || '-'}</p>
                              </div>
                              <div>
                                <p className="text-gray-500">Modelo</p>
                                <p className="font-medium">{license.model || '-'}</p>
                              </div>
                              <div>
                                <p className="text-gray-500">Ativação</p>
                                <p className="font-medium">{formatDate(license.activation_date)}</p>
                              </div>
                              <div>
                                <p className="text-gray-500">Expiração</p>
                                <p className="font-medium">{formatDate(license.expires_at)}</p>
                              </div>
                              <div>
                                <p className="text-gray-500">Chave</p>
                                <p className="font-mono text-xs">{license.license_key}</p>
                              </div>
                              <div>
                                <p className="text-gray-500">Máx. Usuários</p>
                                <p className="font-medium">{license.max_users}</p>
                              </div>
                              <div className="col-span-2">
                                <p className="text-gray-500">Descrição</p>
                                <p className="font-medium">{license.description || '-'}</p>
                              </div>
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Modal Criar/Editar Licença */}
      <Dialog open={showCreateDialog || showEditDialog} onOpenChange={(open) => {
        if (!open) {
          setShowCreateDialog(false);
          setShowEditDialog(false);
          setSelectedLicense(null);
          resetForm();
        }
      }}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {showEditDialog ? 'Editar Licença' : 'Nova Licença'}
            </DialogTitle>
            <DialogDescription>
              {showEditDialog 
                ? 'Atualize as informações da licença'
                : 'Preencha os dados para criar uma nova licença'}
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={showEditDialog ? handleEditLicense : handleCreateLicense}>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Nome *</Label>
                  <Input
                    id="name"
                    value={licenseForm.name}
                    onChange={(e) => setLicenseForm({...licenseForm, name: e.target.value})}
                    placeholder="Nome da licença"
                    required
                    data-testid="license-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="serial">Número de Série</Label>
                  <Input
                    id="serial"
                    value={licenseForm.serial_number}
                    onChange={(e) => setLicenseForm({...licenseForm, serial_number: e.target.value})}
                    placeholder="Serial do equipamento"
                    data-testid="license-serial-input"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="manufacturer">Fabricante</Label>
                  <Input
                    id="manufacturer"
                    value={licenseForm.manufacturer}
                    onChange={(e) => setLicenseForm({...licenseForm, manufacturer: e.target.value})}
                    placeholder="Ex: Dell, HP, Cisco"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="model">Modelo</Label>
                  <Input
                    id="model"
                    value={licenseForm.model}
                    onChange={(e) => setLicenseForm({...licenseForm, model: e.target.value})}
                    placeholder="Modelo do equipamento"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="validity_days">Validade (dias)</Label>
                  <Input
                    id="validity_days"
                    type="number"
                    min="1"
                    value={licenseForm.validity_days}
                    onChange={(e) => setLicenseForm({...licenseForm, validity_days: parseInt(e.target.value) || 365})}
                    data-testid="license-validity-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max_users">Máx. Usuários</Label>
                  <Input
                    id="max_users"
                    type="number"
                    min="1"
                    value={licenseForm.max_users}
                    onChange={(e) => setLicenseForm({...licenseForm, max_users: parseInt(e.target.value) || 1})}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="status">Status</Label>
                  <Select 
                    value={licenseForm.status} 
                    onValueChange={(value) => setLicenseForm({...licenseForm, status: value})}
                  >
                    <SelectTrigger data-testid="license-status-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pending">Pendente</SelectItem>
                      <SelectItem value="active">Ativa</SelectItem>
                      <SelectItem value="suspended">Suspensa</SelectItem>
                      <SelectItem value="expired">Expirada</SelectItem>
                      <SelectItem value="cancelled">Cancelada</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="salesperson">Vendedor Responsável</Label>
                <Select 
                  value={licenseForm.salesperson_id || 'none'} 
                  onValueChange={handleSalespersonChange}
                >
                  <SelectTrigger data-testid="license-salesperson-select">
                    <SelectValue placeholder="Selecionar vendedor" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Nenhum</SelectItem>
                    {salespeople.map(sp => (
                      <SelectItem key={sp.id} value={sp.id}>
                        <span className="flex items-center gap-2">
                          <Users className="w-3 h-3" />
                          {sp.name} ({sp.email})
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Descrição</Label>
                <Textarea
                  id="description"
                  value={licenseForm.description}
                  onChange={(e) => setLicenseForm({...licenseForm, description: e.target.value})}
                  placeholder="Observações sobre a licença..."
                  rows={3}
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => {
                setShowCreateDialog(false);
                setShowEditDialog(false);
                resetForm();
              }}>
                Cancelar
              </Button>
              <Button type="submit" data-testid="save-license-btn">
                {showEditDialog ? 'Salvar Alterações' : 'Criar Licença'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal Renovar Licença */}
      <Dialog open={showRenewDialog} onOpenChange={setShowRenewDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <RotateCcw className="w-5 h-5 text-green-600" />
              Renovar Licença
            </DialogTitle>
            <DialogDescription>
              {selectedLicense && (
                <span>Renovar: <strong>{selectedLicense.name}</strong></span>
              )}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {selectedLicense && (
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500">Status atual:</span>
                  {getStatusBadge(selectedLicense.status)}
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Expira em:</span>
                  <span>{formatDate(selectedLicense.expires_at)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Dias restantes:</span>
                  {getDaysRemainingBadge(calculateDaysRemaining(selectedLicense.expires_at))}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="renew_days">Dias de renovação</Label>
              <Input
                id="renew_days"
                type="number"
                min="1"
                value={renewForm.validity_days}
                onChange={(e) => setRenewForm({...renewForm, validity_days: parseInt(e.target.value) || 365})}
                data-testid="renew-days-input"
              />
              <p className="text-xs text-gray-500">
                Nova expiração será calculada a partir da data atual ou expiração anterior (o que for maior)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="renew_notes">Observações</Label>
              <Textarea
                id="renew_notes"
                value={renewForm.notes}
                onChange={(e) => setRenewForm({...renewForm, notes: e.target.value})}
                placeholder="Motivo da renovação, observações..."
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRenewDialog(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleRenewLicense} 
              className="bg-green-600 hover:bg-green-700"
              data-testid="confirm-renew-btn"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Renovar Licença
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Histórico de Renovações */}
      <Dialog open={showHistoryDialog} onOpenChange={setShowHistoryDialog}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <History className="w-5 h-5 text-blue-600" />
              Histórico de Renovações
            </DialogTitle>
            <DialogDescription>
              {selectedLicense && (
                <span>Licença: <strong>{selectedLicense.name}</strong></span>
              )}
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            {renewalHistory.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <History className="w-12 h-12 mx-auto mb-2 opacity-30" />
                <p>Nenhuma renovação registrada</p>
              </div>
            ) : (
              <div className="space-y-4">
                {renewalHistory.map((entry, index) => (
                  <div 
                    key={entry.id || index} 
                    className="border rounded-lg p-4 bg-gray-50"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="font-medium">Renovação #{renewalHistory.length - index}</p>
                        <p className="text-sm text-gray-500">
                          {formatDateTime(entry.renewal_date)}
                        </p>
                      </div>
                      <Badge className="bg-green-100 text-green-800">
                        +{entry.validity_days} dias
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm mt-3">
                      <div>
                        <p className="text-gray-500">Expiração anterior</p>
                        <p>{formatDate(entry.previous_expiration) || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Nova expiração</p>
                        <p>{formatDate(entry.new_expiration)}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Renovado por</p>
                        <p className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {entry.renewed_by_name}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">Email</p>
                        <p className="text-xs">{entry.renewed_by_email}</p>
                      </div>
                    </div>
                    
                    {entry.notes && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-gray-500 text-sm">Observações</p>
                        <p className="text-sm">{entry.notes}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowHistoryDialog(false)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Confirmação de Exclusão */}
      <AlertDialog open={deleteConfirmId !== null} onOpenChange={() => setDeleteConfirmId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar Exclusão</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. A licença será permanentemente removida do sistema.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700 text-white"
              onClick={handleDeleteLicense}
              data-testid="confirm-delete-btn"
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default LicenseManagement;
