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
import PendingApprovals from './PendingApprovals';
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
  Lock,
  Unlock,
  RotateCw,
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Shield,
  UserPlus,
  Bell,
  MessageSquare,
  Activity,
  AlertCircle
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
  
  // Estados para controle avançado de usuários
  const [showResetPasswordDialog, setShowResetPasswordDialog] = useState(false);
  const [resetPasswordUser, setResetPasswordUser] = useState(null);
  const [resetPasswordForm, setResetPasswordForm] = useState({
    newPassword: '',
    confirmPassword: '',
    generateAuto: true,
    forceChange: true
  });
  const [generatedPassword, setGeneratedPassword] = useState('');

  // Estados para tickets e aprovações
  const [tickets, setTickets] = useState([]);
  const [pendingTickets, setPendingTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showTicketModal, setShowTicketModal] = useState(false);
  const [ticketResponse, setTicketResponse] = useState('');
  const [processingTicket, setProcessingTicket] = useState(false);
  const [pendingRegistrationsCount, setPendingRegistrationsCount] = useState(0);
  
  // Estados para logs de auditoria
  const [activityLogs, setActivityLogs] = useState([]);
  const [selectedUserForLogs, setSelectedUserForLogs] = useState('all');
  
  // Estados para notificações
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);


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

  const fetchTickets = async () => {
    try {
      const response = await api.get('/tickets');
      const allTickets = response.data || [];
      setTickets(allTickets);
      
      // Filtrar tickets pendentes
      const pending = allTickets.filter(t => t.status === 'pending');
      setPendingTickets(pending);
    } catch (error) {
      console.error('Erro ao buscar tickets:', error);
    }
  };

  const fetchPendingRegistrationsCount = async () => {
    try {
      const response = await api.get('/admin/pending-count');
      setPendingRegistrationsCount(response.data.count || 0);
    } catch (error) {
      console.error('Erro ao buscar contagem de aprovações pendentes:', error);
    }
  };

  const fetchActivityLogs = async (userEmail = null) => {
    try {
      const url = userEmail && userEmail !== 'all' 
        ? `/activity-logs?user_email=${userEmail}&limit=50`
        : '/activity-logs?limit=50';
      const response = await api.get(url);
      setActivityLogs(response.data || []);
    } catch (error) {
      console.error('Erro ao buscar logs:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const [notifsResponse, countResponse] = await Promise.all([
        api.get('/notifications'),
        api.get('/notifications/unread/count')
      ]);
      setNotifications(notifsResponse.data || []);
      setUnreadCount(countResponse.data.count || 0);
    } catch (error) {
      console.error('Erro ao buscar notificações:', error);
    }
  };

  // Atualizar fetchData para incluir tickets e notificações
  useEffect(() => {
    if (activeTab === 'approvals') {
      fetchTickets();
      fetchPendingRegistrationsCount();
    } else if (activeTab === 'logs') {
      fetchActivityLogs(selectedUserForLogs);
    }
  }, [activeTab, selectedUserForLogs]);

  // Buscar contagem de aprovações pendentes ao carregar
  useEffect(() => {
    fetchPendingRegistrationsCount();
  }, []);

  // Buscar notificações ao carregar
  useEffect(() => {
    fetchNotifications();
    // Atualizar a cada 30 segundos
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleApproveTicket = async (ticketId) => {
    setProcessingTicket(true);
    try {
      await api.put(`/tickets/${ticketId}`, {
        status: 'approved',
        admin_response: ticketResponse || 'Solicitação aprovada'
      });
      toast.success('Ticket aprovado com sucesso!');
      setShowTicketModal(false);
      setTicketResponse('');
      fetchTickets();
      fetchNotifications();
    } catch (error) {
      console.error('Erro ao aprovar ticket:', error);
      toast.error('Erro ao aprovar ticket');
    } finally {
      setProcessingTicket(false);
    }
  };

  const handleRejectTicket = async (ticketId) => {
    if (!ticketResponse.trim()) {
      toast.error('Por favor, adicione uma justificativa para a rejeição');
      return;
    }
    
    setProcessingTicket(true);
    try {
      await api.put(`/tickets/${ticketId}`, {
        status: 'rejected',
        admin_response: ticketResponse
      });
      toast.success('Ticket rejeitado');
      setShowTicketModal(false);
      setTicketResponse('');
      fetchTickets();
      fetchNotifications();
    } catch (error) {
      console.error('Erro ao rejeitar ticket:', error);
      toast.error('Erro ao rejeitar ticket');
    } finally {
      setProcessingTicket(false);
    }
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
  };

  const getTicketTypeLabel = (type) => {
    const labels = {
      renewal: 'Renovação',
      support: 'Suporte',
      problem: 'Problema',
      general: 'Geral'
    };
    return labels[type] || type;
  };

  const getTicketPriorityColor = (priority) => {
    const colors = {
      low: 'bg-gray-100 text-gray-800',
      medium: 'bg-blue-100 text-blue-800',
      high: 'bg-orange-100 text-orange-800',
      urgent: 'bg-red-100 text-red-800'
    };
    return colors[priority] || colors.medium;
  };

  const getActivityIcon = (activityType) => {
    switch (activityType) {
      case 'license_viewed': return <Eye className="w-4 h-4 text-blue-600" />;
      case 'license_renewed': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'certificate_downloaded': return <FileText className="w-4 h-4 text-purple-600" />;
      case 'ticket_created': return <Clock className="w-4 h-4 text-orange-600" />;
      case 'login': return <Users className="w-4 h-4 text-gray-600" />;
      default: return <Settings className="w-4 h-4 text-gray-600" />;
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

  // ✨ NOVO: Funções de Controle Avançado de Usuários
  
  const handleResetPassword = async () => {
    try {
      const requestData = {
        new_password: resetPasswordForm.generateAuto ? null : resetPasswordForm.newPassword,
        force_change: resetPasswordForm.forceChange,
        notify_user: false
      };
      
      const response = await api.post(`/admin/users/${resetPasswordUser.id}/reset-password`, requestData);
      
      if (response.data.temporary_password) {
        setGeneratedPassword(response.data.temporary_password);
        toast.success('Senha resetada! Copie a senha temporária antes de fechar.');
      } else {
        toast.success('Senha resetada com sucesso!');
        setShowResetPasswordDialog(false);
        setResetPasswordUser(null);
      }
      
      setTimeout(() => {
        fetchData();
      }, 300);
    } catch (error) {
      console.error('Failed to reset password:', error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : 'Erro ao resetar senha';
      toast.error(errorMessage);
    }
  };
  
  const handleBlockUser = async (userId, isBlocked) => {
    try {
      if (isBlocked) {
        await api.put(`/admin/users/${userId}/unblock`);
        toast.success('Usuário desbloqueado com sucesso!');
      } else {
        await api.put(`/admin/users/${userId}/block`, { reason: 'Bloqueado pelo administrador' });
        toast.success('Usuário bloqueado com sucesso!');
      }
      
      setTimeout(() => {
        fetchData();
      }, 300);
    } catch (error) {
      console.error('Failed to block/unblock user:', error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : 'Erro ao bloquear/desbloquear usuário';
      toast.error(errorMessage);
    }
  };
  
  const openResetPasswordDialog = async (user) => {
    setResetPasswordUser(user);
    setResetPasswordForm({
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
      generateAuto: false,
      forceChange: true,
      isEditing: false,
      originalPassword: '',
      isLoading: true
    });
    setGeneratedPassword('');
    setShowResetPasswordDialog(true);
    
    // Buscar senha atual do usuário (para ambientes de teste/demo)
    try {
      console.log('Buscando senha para:', user.id);
      const response = await api.get(`/admin/users/${user.id}/password-info`);
      console.log('Resposta:', response.data);
      
      if (response.data.password_hint) {
        setResetPasswordForm(prev => ({
          ...prev,
          currentPassword: response.data.password_hint,
          originalPassword: response.data.password_hint,
          newPassword: response.data.password_hint,
          isLoading: false
        }));
      } else {
        setResetPasswordForm(prev => ({
          ...prev,
          isLoading: false
        }));
      }
    } catch (error) {
      console.error('Erro ao buscar senha:', error);
      setResetPasswordForm(prev => ({
        ...prev,
        isLoading: false
      }));
    }
  };
  
  const copyGeneratedPassword = () => {
    navigator.clipboard.writeText(generatedPassword);
    toast.success('Senha copiada para área de transferência!');
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
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="users" className="flex items-center space-x-2">
            <Users className="w-4 h-4" />
            <span>Usuários ({users.length})</span>
          </TabsTrigger>
          <TabsTrigger value="approvals" className="flex items-center space-x-2 relative">
            <MessageSquare className="w-4 h-4" />
            <span>Aprovações</span>
            {(pendingTickets.length + pendingRegistrationsCount) > 0 && (
              <Badge className="ml-2 bg-red-600 text-white">
                {pendingTickets.length + pendingRegistrationsCount}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="logs" className="flex items-center space-x-2">
            <Activity className="w-4 h-4" />
            <span>Logs</span>
          </TabsTrigger>
        </TabsList>

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
              <div className="rounded-md border overflow-x-auto">
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
                            {/* Super admin pode editar qualquer usuário, outros admins não podem editar a si mesmos */}
                            {(user.role === 'super_admin' || userData.id !== user.id) && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => openResetPasswordDialog(userData)}
                                  className="text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                                  title="Resetar senha"
                                >
                                  <RotateCw className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleBlockUser(userData.id, !userData.is_active)}
                                  className={userData.is_active 
                                    ? "text-orange-600 hover:text-orange-700 hover:bg-orange-50"
                                    : "text-green-600 hover:text-green-700 hover:bg-green-50"
                                  }
                                  title={userData.is_active ? "Bloquear usuário" : "Desbloquear usuário"}
                                >
                                  {userData.is_active ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                                </Button>
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


        {/* Tab de Solicitações/Aprovações */}
        <TabsContent value="approvals">
          {/* Seção de Aprovações de Registros */}
          <div className="mb-6">
            <PendingApprovals />
          </div>
          
          {/* Seção de Solicitações/Tickets */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Solicitações de Tickets</span>
                {pendingTickets.length > 0 && (
                  <Badge className="bg-red-600">{pendingTickets.length} aguardando</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {tickets.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p>Nenhuma solicitação no momento</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {tickets.map((ticket) => (
                    <div key={ticket.id} className={`border rounded-lg p-4 ${ticket.status === 'pending' ? 'border-yellow-300 bg-yellow-50' : 'border-gray-200'}`}>
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h3 className="font-semibold text-gray-900">{ticket.title}</h3>
                            <Badge className={getTicketPriorityColor(ticket.priority)}>
                              {ticket.priority}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{ticket.description}</p>
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span>Tipo: {getTicketTypeLabel(ticket.type)}</span>
                            <span>Por: {ticket.created_by_name}</span>
                            <span>{formatDateTime(ticket.created_at)}</span>
                          </div>
                        </div>
                        <div className="flex flex-col space-y-2 ml-4">
                          {ticket.status === 'pending' ? (
                            <>
                              <Button size="sm" className="bg-green-600 hover:bg-green-700" onClick={() => {
                                setSelectedTicket(ticket);
                                setShowTicketModal(true);
                              }}>
                                <CheckCircle className="w-4 h-4 mr-1" />
                                Aprovar
                              </Button>
                              <Button size="sm" variant="outline" className="border-red-600 text-red-600 hover:bg-red-50" onClick={() => {
                                setSelectedTicket(ticket);
                                setShowTicketModal(true);
                              }}>
                                <XCircle className="w-4 h-4 mr-1" />
                                Rejeitar
                              </Button>
                            </>
                          ) : (
                            <Badge variant="outline">{ticket.status}</Badge>
                          )}
                        </div>
                      </div>
                      {ticket.admin_response && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <p className="text-sm text-gray-700"><strong>Resposta:</strong> {ticket.admin_response}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab de Logs */}
        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Logs de Auditoria</CardTitle>
                <Select value={selectedUserForLogs} onValueChange={setSelectedUserForLogs}>
                  <SelectTrigger className="w-64">
                    <SelectValue placeholder="Filtrar por usuário" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos os usuários</SelectItem>
                    {users.map(user => (
                      <SelectItem key={user.id} value={user.email}>
                        {user.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              {activityLogs.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Activity className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p>Nenhuma atividade registrada</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {activityLogs.map((log) => (
                    <div key={log.id} className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-gray-50">
                      <div className="flex-shrink-0 mt-1">
                        {getActivityIcon(log.activity_type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <p className="font-medium text-gray-900">{log.user_name}</p>
                          <span className="text-xs text-gray-500">{formatDateTime(log.created_at)}</span>
                        </div>
                        <p className="text-sm text-gray-600">{log.description}</p>
                        {log.ip_address && (
                          <p className="text-xs text-gray-400 mt-1">IP: {log.ip_address}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

      </Tabs>



      {/* Modal de Aprovação de Ticket */}
      <Dialog open={showTicketModal} onOpenChange={setShowTicketModal}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Aprovar/Rejeitar Solicitação</DialogTitle>
          </DialogHeader>
          {selectedTicket && (
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">{selectedTicket.title}</h3>
                  <Badge className={getTicketPriorityColor(selectedTicket.priority)}>
                    {selectedTicket.priority}
                  </Badge>
                </div>
                <p className="text-sm text-gray-600">{selectedTicket.description}</p>
                <div className="text-xs text-gray-500 space-y-1">
                  <p>Tipo: {getTicketTypeLabel(selectedTicket.type)}</p>
                  <p>Criado por: {selectedTicket.created_by_name} ({selectedTicket.created_by})</p>
                  <p>Data: {formatDateTime(selectedTicket.created_at)}</p>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Resposta/Observação</label>
                <Textarea
                  value={ticketResponse}
                  onChange={(e) => setTicketResponse(e.target.value)}
                  placeholder="Adicione uma resposta ou observação..."
                  rows={4}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTicketModal(false)} disabled={processingTicket}>
              Cancelar
            </Button>
            <Button 
              variant="outline" 
              className="border-red-600 text-red-600 hover:bg-red-50"
              onClick={() => selectedTicket && handleRejectTicket(selectedTicket.id)}
              disabled={processingTicket}
            >
              {processingTicket ? 'Processando...' : 'Rejeitar'}
            </Button>
            <Button 
              className="bg-green-600 hover:bg-green-700"
              onClick={() => selectedTicket && handleApproveTicket(selectedTicket.id)}
              disabled={processingTicket}
            >
              {processingTicket ? 'Processando...' : 'Aprovar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit License Dialog */}
      <Dialog open={showEditLicenseDialog} onOpenChange={setShowEditLicenseDialog}>
        <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
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

      {/* Modal de Reset de Senha */}
      <Dialog open={showResetPasswordDialog} onOpenChange={setShowResetPasswordDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Key className="w-5 h-5 text-purple-600" />
              Gerenciar Senha
            </DialogTitle>
            <DialogDescription>
              {resetPasswordUser && `Usuário: ${resetPasswordUser.email}`}
            </DialogDescription>
          </DialogHeader>
          {generatedPassword ? (
            <div className="space-y-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="font-semibold text-green-900">Senha atualizada com sucesso!</span>
                </div>
                <p className="text-sm text-green-700 mb-3">
                  Nova senha do usuário:
                </p>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={generatedPassword}
                    readOnly
                    className="flex-1 px-3 py-2 bg-white border border-green-300 rounded font-mono text-sm"
                  />
                  <Button onClick={copyGeneratedPassword} size="sm">
                    <CheckCircle className="w-4 h-4 mr-1" />
                    Copiar
                  </Button>
                </div>
              </div>
              <DialogFooter>
                <Button onClick={() => {
                  setShowResetPasswordDialog(false);
                  setResetPasswordUser(null);
                  setGeneratedPassword('');
                }}>
                  Fechar
                </Button>
              </DialogFooter>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Indicador de carregamento */}
              {resetPasswordForm.isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RotateCw className="w-6 h-6 animate-spin text-purple-600 mr-2" />
                  <span className="text-gray-500">Carregando informações...</span>
                </div>
              ) : (
                <>
                  {/* Campo de Senha Atual/Nova */}
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <Lock className="w-4 h-4 text-gray-500" />
                      Senha do Usuário
                    </Label>
                    <div className="relative">
                      <Input
                        type={showPassword ? "text" : "password"}
                        placeholder={resetPasswordForm.originalPassword ? "Senha carregada" : "Digite uma nova senha"}
                        value={resetPasswordForm.newPassword}
                        onChange={(e) => setResetPasswordForm({
                          ...resetPasswordForm, 
                          newPassword: e.target.value,
                          isEditing: e.target.value !== resetPasswordForm.originalPassword
                        })}
                        className="pr-10"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                    </div>
                    
                    {/* Indicador de alteração */}
                    {resetPasswordForm.isEditing && (
                      <div className="flex items-center gap-2 text-amber-600 text-sm">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Senha será alterada ao salvar</span>
                      </div>
                    )}
                    
                    {resetPasswordForm.originalPassword && !resetPasswordForm.isEditing && (
                      <p className="text-xs text-green-600 flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" />
                        Senha atual carregada. Edite para alterar.
                      </p>
                    )}
                    
                    {!resetPasswordForm.originalPassword && !resetPasswordForm.isLoading && (
                      <p className="text-xs text-gray-500">
                        Nenhuma senha registrada. Defina uma nova senha.
                      </p>
                    )}
                  </div>

                  {/* Opção de gerar senha automática */}
                  <div className="pt-3 border-t">
                    <Button 
                      variant="outline" 
                      className="w-full"
                  onClick={() => {
                    const autoPassword = Math.random().toString(36).slice(-8) + Math.random().toString(36).slice(-4).toUpperCase();
                    setResetPasswordForm({
                      ...resetPasswordForm,
                      newPassword: autoPassword,
                      isEditing: true
                    });
                  }}
                >
                  <RotateCw className="w-4 h-4 mr-2" />
                  Gerar Senha Automática
                </Button>
              </div>

              <DialogFooter className="gap-2">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowResetPasswordDialog(false);
                    setResetPasswordUser(null);
                  }}
                >
                  Cancelar
                </Button>
                <Button 
                  onClick={async () => {
                    if (!resetPasswordForm.newPassword || resetPasswordForm.newPassword.length < 6) {
                      toast.error('Senha deve ter pelo menos 6 caracteres');
                      return;
                    }
                    
                    try {
                      const response = await api.put(`/admin/users/${resetPasswordUser.id}/password`, {
                        new_password: resetPasswordForm.newPassword
                      });
                      
                      if (response.data.success) {
                        setGeneratedPassword(response.data.new_password);
                        toast.success('Senha atualizada com sucesso!');
                        fetchData();
                      }
                    } catch (error) {
                      toast.error(error.response?.data?.detail || 'Erro ao atualizar senha');
                    }
                  }}
                  disabled={!resetPasswordForm.newPassword || resetPasswordForm.newPassword.length < 6}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Salvar Senha
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal de Edição de Usuário */}
      <Dialog open={showEditUserDialog} onOpenChange={setShowEditUserDialog}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Editar Usuário</DialogTitle>
            <DialogDescription>
              Atualize as informações do usuário
            </DialogDescription>
          </DialogHeader>
          {editingUser && (
            <form onSubmit={async (e) => {
              e.preventDefault();
              try {
                // Update user information
                await api.put(`/users/${editingUser.id}`, {
                  name: editingUser.name,
                  email: editingUser.email,
                  is_active: editingUser.is_active
                });
                toast.success('Usuário atualizado com sucesso!');
                setShowEditUserDialog(false);
                setEditingUser(null);
                
                // Refresh data
                setTimeout(() => {
                  fetchData();
                }, 300);
              } catch (error) {
                console.error('Failed to update user:', error);
                const errorMessage = typeof error.response?.data?.detail === 'string' 
                  ? error.response.data.detail 
                  : 'Erro ao atualizar usuário';
                toast.error(errorMessage);
              }
            }}>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-user-name">Nome Completo</Label>
                  <Input
                    id="edit-user-name"
                    value={editingUser.name}
                    onChange={(e) => setEditingUser({...editingUser, name: e.target.value})}
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="edit-user-email">Email</Label>
                  <Input
                    id="edit-user-email"
                    type="email"
                    value={editingUser.email}
                    onChange={(e) => setEditingUser({...editingUser, email: e.target.value})}
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="edit-user-active">Status</Label>
                  <Select 
                    value={editingUser.is_active ? 'true' : 'false'} 
                    onValueChange={(value) => setEditingUser({...editingUser, is_active: value === 'true'})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="true">Ativo</SelectItem>
                      <SelectItem value="false">Inativo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase">ID</label>
                    <p className="mt-1 text-xs text-gray-600 font-mono break-all">{editingUser.id}</p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase">Função</label>
                    <p className="mt-1 text-sm text-gray-900 capitalize">{editingUser.role}</p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase">Cadastrado em</label>
                    <p className="mt-1 text-xs text-gray-600">
                      {editingUser.created_at ? new Date(editingUser.created_at).toLocaleString('pt-BR') : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase">Último Login</label>
                    <p className="mt-1 text-xs text-gray-600">
                      {editingUser.last_login ? new Date(editingUser.last_login).toLocaleString('pt-BR') : 'Nunca'}
                    </p>
                  </div>
                </div>
              </div>
              <DialogFooter className="mt-6 flex-col sm:flex-row gap-2">
                <Button 
                  type="button" 
                  variant="outline" 
                  className="text-amber-600 border-amber-300 hover:bg-amber-50"
                  onClick={() => {
                    setResetPasswordUser(editingUser);
                    setShowResetPasswordDialog(true);
                  }}
                >
                  <Key className="h-4 w-4 mr-2" />
                  Alterar Senha
                </Button>
                <div className="flex gap-2">
                  <Button type="button" variant="outline" onClick={() => {
                    setShowEditUserDialog(false);
                    setEditingUser(null);
                  }}>
                    Cancelar
                  </Button>
                  <Button type="submit">
                    Salvar Alterações
                  </Button>
                </div>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminPanel;