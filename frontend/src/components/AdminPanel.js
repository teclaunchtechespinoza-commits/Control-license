import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { LicenseStatusBadge, CustomSemanticBadge } from './ui/semantic-badge';
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
  DialogTitle, 
  DialogTrigger 
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
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
  Users,
  FileText,
  Settings,
  Eye,
  EyeOff,
  Key,
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Shield,
  UserPlus
} from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';

const AdminPanel = () => {
  const { user } = useAuth();
  const [licenses, setLicenses] = useState([]);
  const [licensesTotal, setLicensesTotal] = useState(0); // Total real no banco
  const [users, setUsers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [clientesPF, setClientesPF] = useState([]);
  const [clientesPJ, setClientesPJ] = useState([]);
  const [products, setProducts] = useState([]);
  const [licensePlans, setLicensePlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showCreateLicenseDialog, setShowCreateLicenseDialog] = useState(false);
  const [showEditLicenseDialog, setShowEditLicenseDialog] = useState(false);
  const [editingLicense, setEditingLicense] = useState(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [showCreateUserDialog, setShowCreateUserDialog] = useState(false);
  const [showEditUserDialog, setShowEditUserDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'user'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [activeTab, setActiveTab] = useState('licenses');

  // Form states
  const [licenseForm, setLicenseForm] = useState({
    name: '',
    description: '',
    max_users: 1,
    expires_at: '',
    assigned_user_id: null,
    category_id: null,
    client_pf_id: null,
    client_pj_id: null,
    product_id: null,
    plan_id: null,
    features: []
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      // Force fresh data - no cache
      const timestamp = Date.now();
      const cacheControl = { 
        headers: { 
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        },
        params: { _: timestamp, refresh: 'true' }
      };
      
      const [licensesResponse, licensesCountResponse, usersResponse, categoriesResponse, pfResponse, pjResponse, productsResponse, plansResponse] = await Promise.all([
        api.get('/licenses', cacheControl),
        api.get('/licenses/count', cacheControl), // 🔧 NOVO: Buscar total real
        api.get('/users', cacheControl),
        api.get('/categories', cacheControl),
        api.get('/clientes-pf', cacheControl),
        api.get('/clientes-pj', cacheControl),
        api.get('/products', cacheControl),
        api.get('/license-plans', cacheControl)
      ]);
      
      // Update state with fresh data
      setLicenses(licensesResponse.data || []);
      setLicensesTotal(licensesCountResponse.data?.total || 0); // 🔧 Total real
      setUsers(usersResponse.data || []);
      setCategories(categoriesResponse.data || []);
      setClientesPF(pfResponse.data || []);
      setClientesPJ(pjResponse.data || []);
      setProducts(productsResponse.data || []);
      setLicensePlans(plansResponse.data || []);
      
      // Log para debug
      console.log('📊 Dados atualizados:', {
        licenses: licensesResponse.data?.length || 0,
        users: usersResponse.data?.length || 0,
        categories: categoriesResponse.data?.length || 0,
        clientesPF: pfResponse.data?.length || 0,
        clientesPJ: pjResponse.data?.length || 0
      });
      
      // Limpar filtros se não houver resultados
      if (licensesResponse.data?.length === 0 && statusFilter !== 'all') {
        setStatusFilter('all');
        toast.info('Filtros limpos - nenhuma licença encontrada');
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Erro ao carregar dados. Tentando novamente...');
      // Retry once after 1 second
      setTimeout(() => fetchData(), 1000);
    } finally {
      setLoading(false);
    }
  };

  const resetLicenseForm = () => {
    setLicenseForm({
      name: '',
      description: '',
      max_users: 1,
      expires_at: '',
      assigned_user_id: null,
      category_id: null,
      client_pf_id: null,
      client_pj_id: null,
      product_id: null,
      plan_id: null,
      features: []
    });
  };

  const handleCreateLicense = async (e) => {
    e.preventDefault();
    
    try {
      const formData = { ...licenseForm };
      
      // Convert expires_at to proper format if provided
      if (formData.expires_at) {
        formData.expires_at = new Date(formData.expires_at).toISOString();
      } else {
        delete formData.expires_at;
      }

      // Remove null fields before sending
      Object.keys(formData).forEach(key => {
        if (formData[key] === null || formData[key] === '') {
          delete formData[key];
        }
      });

      await api.post('/licenses', formData);
      toast.success('Licença criada com sucesso!');
      
      resetLicenseForm();
      setShowCreateLicenseDialog(false);
      
      // 🔧 FIX: Aguardar 500ms para garantir que banco confirme transação antes de buscar dados
      setTimeout(() => {
        fetchData();
      }, 500);
    } catch (error) {
      console.error('Failed to create license:', error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : 'Erro ao criar licença';
      toast.error(errorMessage);
    }
  };

  const handleEditLicense = async (e) => {
    e.preventDefault();
    
    try {
      const formData = { ...licenseForm };
      
      // Convert expires_at to proper format if provided
      if (formData.expires_at) {
        formData.expires_at = new Date(formData.expires_at).toISOString();
      }

      // Remove null fields before sending
      Object.keys(formData).forEach(key => {
        if (formData[key] === null || formData[key] === '') {
          delete formData[key];
        }
      });

      await api.put(`/licenses/${editingLicense.id}`, formData);
      toast.success('Licença atualizada com sucesso!');
      
      setShowEditLicenseDialog(false);
      setEditingLicense(null);
      resetLicenseForm();
      
      // 🔧 FIX: Aguardar 500ms para garantir que banco confirme transação
      setTimeout(() => {
        fetchData();
      }, 500);
    } catch (error) {
      console.error('Failed to update license:', error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : 'Erro ao atualizar licença';
      toast.error(errorMessage);
    }
  };

  const handleDeleteLicense = async (licenseId) => {
    try {
      await api.delete(`/licenses/${licenseId}`);
      toast.success('Licença excluída com sucesso!');
      setDeleteConfirmId(null);
      
      // 🔧 FIX: Aguardar 500ms para garantir que banco confirme transação
      setTimeout(() => {
        fetchData();
      }, 500);
    } catch (error) {
      console.error('Failed to delete license:', error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : 'Erro ao excluir licença';
      toast.error(errorMessage);
    }
  };

  const handleUpdateUserRole = async (userId, newRole) => {
    try {
      // 🔧 FIX: Enviar role no body ao invés de params
      await api.put(`/users/${userId}/role`, { role: newRole });
      toast.success('Função atualizada com sucesso!');
      
      // Atualização mais rápida
      setTimeout(() => {
        fetchData();
      }, 200);
    } catch (error) {
      console.error('Failed to update user role:', error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : 'Erro ao atualizar função do usuário';
      toast.error(errorMessage);
    }
  };

  const handleDeleteUser = async (userId) => {
    try {
      await api.delete(`/users/${userId}`);
      toast.success('Usuário excluído com sucesso!');
      
      setTimeout(() => {
        fetchData();
      }, 500);
    } catch (error) {
      console.error('Failed to delete user:', error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : 'Erro ao excluir usuário';
      toast.error(errorMessage);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/users', userForm);
      toast.success(`Usuário ${response.data.name} criado com sucesso!`);
      
      // Limpar formulário
      setUserForm({
        name: '',
        email: '',
        password: '',
        role: 'user'
      });
      setShowCreateUserDialog(false);
      setShowPassword(false); // Resetar visibilidade da senha
      
      // Forçar atualização imediata
      setTimeout(() => {
        fetchData();
      }, 300);
    } catch (error) {
      console.error('Failed to create user:', error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : 'Erro ao criar usuário';
      toast.error(errorMessage);
    }
  };

  const openEditDialog = (license) => {
    // 🔧 FIX: Forçar refresh da lista de usuários ao abrir modal
    fetchData();
    
    setEditingLicense(license);
    setLicenseForm({
      name: license.name,
      description: license.description || '',
      max_users: license.max_users,
      expires_at: license.expires_at ? license.expires_at.split('T')[0] : '',
      assigned_user_id: license.assigned_user_id || null,
      category_id: license.category_id || null,
      client_pf_id: license.client_pf_id || null,
      client_pj_id: license.client_pj_id || null,
      product_id: license.product_id || null,
      plan_id: license.plan_id || null,
      features: license.features || []
    });
    setShowEditLicenseDialog(true);
  };

  const getSemanticStatusIcon = (status) => {
    // Sistema semântico WCAG: ícones + cores acessíveis
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
    // Badge semântico WCAG: ícone + label, contraste ≥ 4.5:1
    return <LicenseStatusBadge status={status} size="sm" />;
  };

  const getUserRoleBadge = (role) => {
    // Badge semântico para roles de usuário
    const roleConfig = {
      'admin': { 
        variant: 'info', 
        label: 'Admin', 
        icon: '⚡',
        ariaLabel: 'Papel: Administrador - acesso total ao sistema'
      },
      'user': { 
        variant: 'neutral', 
        label: 'Usuário', 
        icon: '👤',
        ariaLabel: 'Papel: Usuário padrão - acesso limitado'
      }
    };

    const config = roleConfig[role] || roleConfig['user'];
    return (
      <CustomSemanticBadge
        variant={config.variant}
        label={config.label}
        icon={config.icon}
        ariaLabel={config.ariaLabel}
        size="sm"
      />
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Sem limite';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const getUserName = (userId) => {
    const foundUser = users.find(u => u.id === userId);
    return foundUser ? foundUser.name : 'Não atribuído';
  };

  const filteredLicenses = licenses.filter(license => {
    const matchesSearch = license.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         license.license_key.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || license.status === statusFilter;
    return matchesSearch && matchesStatus;
  });
  
  // Debug: Log quando há diferença entre total e filtrado
  if (licenses.length !== filteredLicenses.length) {
    console.log(`🔍 Filtro aplicado: ${filteredLicenses.length} de ${licenses.length} licenças`, {
      searchTerm,
      statusFilter,
      statuses: [...new Set(licenses.map(l => l.status))]
    });
  }

  if (loading) {
    return <LoadingSpinner message="Carregando painel administrativo..." />;
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-full">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
          <Shield className="w-8 h-8 text-blue-600" />
          <span>Painel Administrativo</span>
        </h1>
        <p className="text-gray-600 mt-2">
          Gerencie licenças, usuários e configurações do sistema
        </p>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="licenses" className="flex items-center space-x-2">
            <FileText className="w-4 h-4" />
            <span>Gerenciar Licenças (Total: {licensesTotal})</span>
          </TabsTrigger>
          <TabsTrigger value="users" className="flex items-center space-x-2">
            <Users className="w-4 h-4" />
            <span>Gerenciar Usuários ({users.length})</span>
          </TabsTrigger>
        </TabsList>

        {/* Licenses Tab */}
        <TabsContent value="licenses">
          {/* Filters and Actions */}
          <Card className="mb-6">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>Gerenciar Licenças</CardTitle>
                  <CardDescription>
                    Crie, edite e gerencie todas as licenças do sistema
                  </CardDescription>
                </div>
                <Dialog open={showCreateLicenseDialog} onOpenChange={setShowCreateLicenseDialog}>
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="w-4 h-4 mr-2" />
                      Nova Licença
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader>
                      <DialogTitle>Criar Nova Licença</DialogTitle>
                      <DialogDescription>
                        Preencha os dados para criar uma nova licença
                      </DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleCreateLicense}>
                      <div className="grid gap-4 py-4">
                        <div className="space-y-2">
                          <Label htmlFor="name">Nome da Licença</Label>
                          <Input
                            id="name"
                            value={licenseForm.name}
                            onChange={(e) => setLicenseForm({...licenseForm, name: e.target.value})}
                            required
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <Label htmlFor="description">Descrição (opcional)</Label>
                          <Textarea
                            id="description"
                            value={licenseForm.description}
                            onChange={(e) => setLicenseForm({...licenseForm, description: e.target.value})}
                            rows={3}
                          />
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="max_users">Máx. Usuários</Label>
                            <Input
                              id="max_users"
                              type="number"
                              min="1"
                              value={licenseForm.max_users}
                              onChange={(e) => setLicenseForm({...licenseForm, max_users: parseInt(e.target.value)})}
                              required
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label htmlFor="expires_at">Data de Expiração</Label>
                            <Input
                              id="expires_at"
                              type="date"
                              value={licenseForm.expires_at}
                              onChange={(e) => setLicenseForm({...licenseForm, expires_at: e.target.value})}
                            />
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <Label htmlFor="assigned_user">Atribuir a Usuário (opcional)</Label>
                          <Select 
                            value={licenseForm.assigned_user_id || ''} 
                            onValueChange={(value) => setLicenseForm({...licenseForm, assigned_user_id: value || null})}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Nenhum usuário selecionado" />
                            </SelectTrigger>
                            <SelectContent>
                              {users.filter(u => u.role !== 'admin').map(user => (
                                <SelectItem key={user.id} value={user.id}>
                                  {user.name} ({user.email})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="category">Categoria (opcional)</Label>
                            <Select 
                              value={licenseForm.category_id || ''} 
                              onValueChange={(value) => setLicenseForm({...licenseForm, category_id: value || null})}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Nenhuma categoria" />
                              </SelectTrigger>
                              <SelectContent>
                                {categories.map(category => (
                                  <SelectItem key={category.id} value={category.id}>
                                    {category.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          
                          <div className="space-y-2">
                            <Label htmlFor="client_pf">Cliente PF (opcional)</Label>
                            <Select 
                              value={licenseForm.client_pf_id || ''} 
                              onValueChange={(value) => setLicenseForm({...licenseForm, client_pf_id: value || null, client_pj_id: null})}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Nenhum cliente PF" />
                              </SelectTrigger>
                              <SelectContent>
                                {clientesPF.map(client => (
                                  <SelectItem key={client.id} value={client.id}>
                                    {client.nome_completo}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          
                          <div className="space-y-2">
                            <Label htmlFor="client_pj">Cliente PJ (opcional)</Label>
                            <Select 
                              value={licenseForm.client_pj_id || ''} 
                              onValueChange={(value) => setLicenseForm({...licenseForm, client_pj_id: value || null, client_pf_id: null})}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Nenhum cliente PJ" />
                              </SelectTrigger>
                              <SelectContent>
                                {clientesPJ.map(client => (
                                  <SelectItem key={client.id} value={client.id}>
                                    {client.razao_social}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="product">Produto (opcional)</Label>
                            <Select 
                              value={licenseForm.product_id || ''} 
                              onValueChange={(value) => setLicenseForm({...licenseForm, product_id: value || null})}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Nenhum produto" />
                              </SelectTrigger>
                              <SelectContent>
                                {products.map(product => (
                                  <SelectItem key={product.id} value={product.id}>
                                    {product.name} v{product.version}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          
                          <div className="space-y-2">
                            <Label htmlFor="plan">Plano (opcional)</Label>
                            <Select 
                              value={licenseForm.plan_id || ''} 
                              onValueChange={(value) => setLicenseForm({...licenseForm, plan_id: value || null})}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Nenhum plano" />
                              </SelectTrigger>
                              <SelectContent>
                                {licensePlans.map(plan => (
                                  <SelectItem key={plan.id} value={plan.id}>
                                    {plan.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => setShowCreateLicenseDialog(false)}>
                          Cancelar
                        </Button>
                        <Button type="submit">
                          Criar Licença
                        </Button>
                      </DialogFooter>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="Buscar licenças..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>
                <div className="sm:w-48">
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger>
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos</SelectItem>
                      <SelectItem value="active">Ativo</SelectItem>
                      <SelectItem value="pending">Pendente</SelectItem>
                      <SelectItem value="expired">Expirado</SelectItem>
                      <SelectItem value="suspended">Suspenso</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Licenses Table */}
          <Card>
            <CardContent className="pt-6">
              {filteredLicenses.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Nenhuma licença encontrada
                  </h3>
                  <p className="text-gray-500 mb-4">
                    {searchTerm || statusFilter !== 'all' 
                      ? `Mostrando 0 de ${licenses.length} licenças. Tente limpar os filtros ou ajustar a busca.`
                      : 'Crie sua primeira licença para começar'
                    }
                  </p>
                  {(searchTerm || statusFilter !== 'all') && (
                    <div className="flex justify-center gap-2">
                      {searchTerm && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setSearchTerm('')}
                        >
                          Limpar busca
                        </Button>
                      )}
                      {statusFilter !== 'all' && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setStatusFilter('all')}
                        >
                          Mostrar todos os status
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Nome</TableHead>
                        <TableHead>Chave</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Usuário Atribuído</TableHead>
                        <TableHead>Criado</TableHead>
                        <TableHead>Expira</TableHead>
                        <TableHead className="text-right">Ações</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredLicenses.map((license) => (
                        <TableRow key={license.id}>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              {getSemanticStatusIcon(license.status)}
                              <div>
                                <div className="font-medium">{license.name}</div>
                                {license.description && (
                                  <div className="text-sm text-gray-500">
                                    {license.description}
                                  </div>
                                )}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                              {license.license_key}
                            </code>
                          </TableCell>
                          <TableCell>
                            {getSemanticStatusBadge(license.status)}
                          </TableCell>
                          <TableCell>
                            <span className="text-sm">
                              {getUserName(license.assigned_user_id)}
                            </span>
                          </TableCell>
                          <TableCell>
                            <span className="text-sm text-gray-500">
                              {formatDate(license.created_at)}
                            </span>
                          </TableCell>
                          <TableCell>
                            <span className="text-sm text-gray-500">
                              {formatDate(license.expires_at)}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end space-x-1">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openEditDialog(license)}
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setDeleteConfirmId(license.id)}
                                className="text-danger hover:text-danger/80 hover:border-danger/50"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Gerenciar Usuários</CardTitle>
                  <CardDescription>
                    Visualize e gerencie os usuários do sistema
                  </CardDescription>
                </div>
                <Button onClick={() => setShowCreateUserDialog(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Novo Usuário
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nome</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Função</TableHead>
                      <TableHead>Data de Cadastro</TableHead>
                      <TableHead>Último Login</TableHead>
                      <TableHead className="text-right">Ações</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((userData) => (
                      <TableRow key={userData.id}>
                        <TableCell>
                          <div className="font-medium">{userData.name}</div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm text-gray-600">{userData.email}</div>
                        </TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            userData.is_active 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {userData.is_active ? 'Ativo' : 'Inativo'}
                          </span>
                        </TableCell>
                        <TableCell>
                          {userData.id !== user.id ? (
                            <Select 
                              value={userData.role} 
                              onValueChange={(newRole) => handleUpdateUserRole(userData.id, newRole)}
                            >
                              <SelectTrigger className="w-28">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="user">Usuário</SelectItem>
                                <SelectItem value="admin">Admin</SelectItem>
                              </SelectContent>
                            </Select>
                          ) : (
                            <span className="text-sm text-gray-600 capitalize">{userData.role}</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-gray-500">
                            {formatDate(userData.created_at)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-gray-500">
                            {userData.last_login ? formatDate(userData.last_login) : 'Nunca'}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            {userData.id !== user.id && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    setEditingUser(userData);
                                    setShowEditUserDialog(true);
                                  }}
                                  className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                  title="Editar usuário"
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    if (window.confirm('Tem certeza que deseja excluir este usuário?')) {
                                      handleDeleteUser(userData.id);
                                    }
                                  }}
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                  title="Excluir usuário"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit License Dialog */}
      <Dialog open={showEditLicenseDialog} onOpenChange={setShowEditLicenseDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Editar Licença</DialogTitle>
            <DialogDescription>
              Atualize os dados da licença
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditLicense}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="edit-name">Nome da Licença</Label>
                <Input
                  id="edit-name"
                  value={licenseForm.name}
                  onChange={(e) => setLicenseForm({...licenseForm, name: e.target.value})}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="edit-description">Descrição</Label>
                <Textarea
                  id="edit-description"
                  value={licenseForm.description}
                  onChange={(e) => setLicenseForm({...licenseForm, description: e.target.value})}
                  rows={3}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-max-users">Máx. Usuários</Label>
                  <Input
                    id="edit-max-users"
                    type="number"
                    min="1"
                    value={licenseForm.max_users}
                    onChange={(e) => setLicenseForm({...licenseForm, max_users: parseInt(e.target.value)})}
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="edit-expires">Data de Expiração</Label>
                  <Input
                    id="edit-expires"
                    type="date"
                    value={licenseForm.expires_at}
                    onChange={(e) => setLicenseForm({...licenseForm, expires_at: e.target.value})}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="edit-user">Usuário Atribuído</Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => fetchData()}
                    className="text-xs text-blue-600 hover:text-blue-700"
                  >
                    🔄 Atualizar Lista
                  </Button>
                </div>
                <Select 
                  value={licenseForm.assigned_user_id || ''} 
                  onValueChange={(value) => setLicenseForm({...licenseForm, assigned_user_id: value || null})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Nenhum usuário selecionado" />
                  </SelectTrigger>
                  <SelectContent>
                    {users.filter(u => u.role !== 'admin').map(user => (
                      <SelectItem key={user.id} value={user.id}>
                        {user.name} ({user.email})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500">
                  {users.filter(u => u.role !== 'admin').length} usuários disponíveis
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-category">Categoria</Label>
                  <Select 
                    value={licenseForm.category_id || ''} 
                    onValueChange={(value) => setLicenseForm({...licenseForm, category_id: value || null})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Nenhuma categoria" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map(category => (
                        <SelectItem key={category.id} value={category.id}>
                          {category.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="edit-client-pf">Cliente PF</Label>
                  <Select 
                    value={licenseForm.client_pf_id || ''} 
                    onValueChange={(value) => setLicenseForm({...licenseForm, client_pf_id: value || null, client_pj_id: null})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Nenhum cliente PF" />
                    </SelectTrigger>
                    <SelectContent>
                      {clientesPF.map(client => (
                        <SelectItem key={client.id} value={client.id}>
                          {client.nome_completo}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="edit-client-pj">Cliente PJ</Label>
                  <Select 
                    value={licenseForm.client_pj_id || ''} 
                    onValueChange={(value) => setLicenseForm({...licenseForm, client_pj_id: value || null, client_pf_id: null})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Nenhum cliente PJ" />
                    </SelectTrigger>
                    <SelectContent>
                      {clientesPJ.map(client => (
                        <SelectItem key={client.id} value={client.id}>
                          {client.razao_social}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-product">Produto</Label>
                  <Select 
                    value={licenseForm.product_id || ''} 
                    onValueChange={(value) => setLicenseForm({...licenseForm, product_id: value || null})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Nenhum produto" />
                    </SelectTrigger>
                    <SelectContent>
                      {products.map(product => (
                        <SelectItem key={product.id} value={product.id}>
                          {product.name} v{product.version}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="edit-plan">Plano</Label>
                  <Select 
                    value={licenseForm.plan_id || ''} 
                    onValueChange={(value) => setLicenseForm({...licenseForm, plan_id: value || null})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Nenhum plano" />
                    </SelectTrigger>
                    <SelectContent>
                      {licensePlans.map(plan => (
                        <SelectItem key={plan.id} value={plan.id}>
                          {plan.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowEditLicenseDialog(false)}>
                Cancelar
              </Button>
              <Button type="submit">
                Salvar Alterações
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
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
              className="bg-danger hover:bg-danger/90 text-danger-foreground"
              onClick={() => handleDeleteLicense(deleteConfirmId)}
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      {/* Modal de Criar Novo Usuário */}
      <Dialog open={showCreateUserDialog} onOpenChange={setShowCreateUserDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Criar Novo Usuário</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateUser} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="user-name">Nome Completo *</Label>
              <Input
                id="user-name"
                value={userForm.name}
                onChange={(e) => setUserForm({...userForm, name: e.target.value})}
                placeholder="Digite o nome completo"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-email">Email *</Label>
              <Input
                id="user-email"
                type="email"
                value={userForm.email}
                onChange={(e) => setUserForm({...userForm, email: e.target.value})}
                placeholder="usuario@exemplo.com"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-password">Senha *</Label>
              <div className="relative">
                <Input
                  id="user-password"
                  type={showPassword ? "text" : "password"}
                  value={userForm.password}
                  onChange={(e) => setUserForm({...userForm, password: e.target.value})}
                  placeholder="Mínimo 6 caracteres"
                  minLength={6}
                  className="pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-role">Função *</Label>
              <Select 
                value={userForm.role} 
                onValueChange={(value) => setUserForm({...userForm, role: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">Usuário</SelectItem>
                  <SelectItem value="admin">Administrador</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateUserDialog(false)}>
                Cancelar
              </Button>
              <Button type="submit">
                Criar Usuário
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal de Edição de Usuário */}
      <Dialog open={showEditUserDialog} onOpenChange={setShowEditUserDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Detalhes do Usuário</DialogTitle>
          </DialogHeader>
          {editingUser && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">Nome</label>
                  <p className="mt-1 text-sm text-gray-900">{editingUser.name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Email</label>
                  <p className="mt-1 text-sm text-gray-900">{editingUser.email}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Função</label>
                  <p className="mt-1 text-sm text-gray-900 capitalize">{editingUser.role}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Status</label>
                  <p className="mt-1">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      editingUser.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {editingUser.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">ID</label>
                  <p className="mt-1 text-xs text-gray-600 font-mono">{editingUser.id}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Tenant ID</label>
                  <p className="mt-1 text-xs text-gray-600 font-mono">{editingUser.tenant_id || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Data de Cadastro</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {editingUser.created_at ? new Date(editingUser.created_at).toLocaleString('pt-BR') : 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Último Login</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {editingUser.last_login ? new Date(editingUser.last_login).toLocaleString('pt-BR') : 'Nunca'}
                  </p>
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => setShowEditUserDialog(false)}>
                  Fechar
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminPanel;