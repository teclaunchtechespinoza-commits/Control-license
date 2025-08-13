import React, { useState, useEffect } from 'react';
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
import axios from 'axios';
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
  const [users, setUsers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [products, setProducts] = useState([]);
  const [licensePlans, setLicensePlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showCreateLicenseDialog, setShowCreateLicenseDialog] = useState(false);
  const [showEditLicenseDialog, setShowEditLicenseDialog] = useState(false);
  const [editingLicense, setEditingLicense] = useState(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [activeTab, setActiveTab] = useState('licenses');

  // Form states
  const [licenseForm, setLicenseForm] = useState({
    name: '',
    description: '',
    max_users: 1,
    expires_at: '',
    assigned_user_id: '',
    category_id: '',
    company_id: '',
    product_id: '',
    plan_id: '',
    features: []
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [licensesResponse, usersResponse, categoriesResponse, companiesResponse, productsResponse, plansResponse] = await Promise.all([
        axios.get('/licenses'),
        axios.get('/users'),
        axios.get('/categories'),
        axios.get('/companies'),
        axios.get('/products'),
        axios.get('/license-plans')
      ]);
      
      setLicenses(licensesResponse.data);
      setUsers(usersResponse.data);
      setCategories(categoriesResponse.data);
      setCompanies(companiesResponse.data);
      setProducts(productsResponse.data);
      setLicensePlans(plansResponse.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Erro ao carregar dados');
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
      assigned_user_id: '',
      category_id: '',
      company_id: '',
      product_id: '',
      plan_id: '',
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

      await axios.post('/licenses', formData);
      toast.success('Licença criada com sucesso!');
      
      resetLicenseForm();
      setShowCreateLicenseDialog(false);
      fetchData();
    } catch (error) {
      console.error('Failed to create license:', error);
      toast.error(error.response?.data?.detail || 'Erro ao criar licença');
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

      await axios.put(`/licenses/${editingLicense.id}`, formData);
      toast.success('Licença atualizada com sucesso!');
      
      setShowEditLicenseDialog(false);
      setEditingLicense(null);
      resetLicenseForm();
      fetchData();
    } catch (error) {
      console.error('Failed to update license:', error);
      toast.error(error.response?.data?.detail || 'Erro ao atualizar licença');
    }
  };

  const handleDeleteLicense = async (licenseId) => {
    try {
      await axios.delete(`/licenses/${licenseId}`);
      toast.success('Licença excluída com sucesso!');
      setDeleteConfirmId(null);
      fetchData();
    } catch (error) {
      console.error('Failed to delete license:', error);
      toast.error(error.response?.data?.detail || 'Erro ao excluir licença');
    }
  };

  const handleUpdateUserRole = async (userId, newRole) => {
    try {
      await axios.put(`/users/${userId}/role?role=${newRole}`);
      toast.success('Função do usuário atualizada com sucesso!');
      fetchData();
    } catch (error) {
      console.error('Failed to update user role:', error);
      toast.error(error.response?.data?.detail || 'Erro ao atualizar função do usuário');
    }
  };

  const openEditDialog = (license) => {
    setEditingLicense(license);
    setLicenseForm({
      name: license.name,
      description: license.description || '',
      max_users: license.max_users,
      expires_at: license.expires_at ? license.expires_at.split('T')[0] : '',
      assigned_user_id: license.assigned_user_id || '',
      category_id: license.category_id || '',
      company_id: license.company_id || '',
      product_id: license.product_id || '',
      plan_id: license.plan_id || '',
      features: license.features || []
    });
    setShowEditLicenseDialog(true);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'expired':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'suspended':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      active: 'default',
      expired: 'destructive',
      suspended: 'secondary',
      pending: 'outline'
    };
    
    const labels = {
      active: 'Ativo',
      expired: 'Expirado',
      suspended: 'Suspenso',
      pending: 'Pendente'
    };

    return (
      <Badge variant={variants[status]}>
        {labels[status]}
      </Badge>
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

  if (loading) {
    return <LoadingSpinner message="Carregando painel administrativo..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
            <span>Gerenciar Licenças</span>
          </TabsTrigger>
          <TabsTrigger value="users" className="flex items-center space-x-2">
            <Users className="w-4 h-4" />
            <span>Gerenciar Usuários</span>
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
                            value={licenseForm.assigned_user_id} 
                            onValueChange={(value) => setLicenseForm({...licenseForm, assigned_user_id: value})}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Selecionar usuário" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="">Nenhum usuário</SelectItem>
                              {users.filter(u => u.role !== 'admin').map(user => (
                                <SelectItem key={user.id} value={user.id}>
                                  {user.name} ({user.email})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
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
                      ? 'Tente ajustar os filtros de busca'
                      : 'Crie sua primeira licença para começar'
                    }
                  </p>
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
                              {getStatusIcon(license.status)}
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
                            {getStatusBadge(license.status)}
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
                                className="text-red-600 hover:text-red-700"
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
              <CardTitle>Gerenciar Usuários</CardTitle>
              <CardDescription>
                Visualize e gerencie os usuários do sistema
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nome</TableHead>
                      <TableHead>Email</TableHead>
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
                        <TableCell>{userData.email}</TableCell>
                        <TableCell>
                          <Badge variant={userData.role === 'admin' ? 'default' : 'secondary'}>
                            {userData.role === 'admin' ? 'Admin' : 'Usuário'}
                          </Badge>
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
                          {userData.id !== user.id && (
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
                          )}
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
                <Label htmlFor="edit-user">Usuário Atribuído</Label>
                <Select 
                  value={licenseForm.assigned_user_id} 
                  onValueChange={(value) => setLicenseForm({...licenseForm, assigned_user_id: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecionar usuário" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Nenhum usuário</SelectItem>
                    {users.filter(u => u.role !== 'admin').map(user => (
                      <SelectItem key={user.id} value={user.id}>
                        {user.name} ({user.email})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
              className="bg-red-600 hover:bg-red-700"
              onClick={() => handleDeleteLicense(deleteConfirmId)}
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default AdminPanel;