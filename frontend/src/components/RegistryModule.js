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
  FolderOpen,
  Building,
  Package,
  CreditCard,
  Eye,
  Save,
  X,
  Tag
} from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';

const RegistryModule = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('categories');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Data states
  const [categories, setCategories] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [products, setProducts] = useState([]);
  const [licensePlans, setLicensePlans] = useState([]);
  
  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  
  // Form states
  const [formData, setFormData] = useState({});

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      const [categoriesRes, companiesRes, productsRes, plansRes] = await Promise.all([
        axios.get('/categories'),
        axios.get('/companies'),
        axios.get('/products'),
        axios.get('/license-plans')
      ]);
      
      setCategories(categoriesRes.data);
      setCompanies(companiesRes.data);
      setProducts(productsRes.data);
      setLicensePlans(plansRes.data);
    } catch (error) {
      console.error('Failed to fetch registry data:', error);
      toast.error('Erro ao carregar dados dos cadastros');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({});
  };

  const getTabConfig = () => {
    const configs = {
      categories: {
        title: 'Categorias',
        icon: FolderOpen,
        data: categories,
        endpoint: 'categories',
        fields: [
          { name: 'name', label: 'Nome', type: 'text', required: true },
          { name: 'description', label: 'Descrição', type: 'textarea' },
          { name: 'color', label: 'Cor', type: 'color' },
          { name: 'icon', label: 'Ícone', type: 'text' }
        ]
      },
      companies: {
        title: 'Empresas',
        icon: Building,
        data: companies,
        endpoint: 'companies',
        fields: [
          { name: 'name', label: 'Nome da Empresa', type: 'text', required: true },
          { name: 'email', label: 'Email', type: 'email' },
          { name: 'phone', label: 'Telefone', type: 'tel' },
          { name: 'website', label: 'Website', type: 'url' },
          { name: 'address', label: 'Endereço', type: 'textarea' },
          { name: 'city', label: 'Cidade', type: 'text' },
          { name: 'state', label: 'Estado', type: 'text' },
          { name: 'country', label: 'País', type: 'text', defaultValue: 'Brasil' },
          { name: 'size', label: 'Porte', type: 'select', options: [
            { value: 'small', label: 'Pequeno' },
            { value: 'medium', label: 'Médio' },
            { value: 'large', label: 'Grande' },
            { value: 'enterprise', label: 'Corporativo' }
          ]},
          { name: 'notes', label: 'Observações', type: 'textarea' }
        ]
      },
      products: {
        title: 'Produtos',
        icon: Package,
        data: products,
        endpoint: 'products',
        fields: [
          { name: 'name', label: 'Nome do Produto', type: 'text', required: true },
          { name: 'version', label: 'Versão', type: 'text', defaultValue: '1.0' },
          { name: 'description', label: 'Descrição', type: 'textarea' },
          { name: 'category_id', label: 'Categoria', type: 'select', 
            options: categories.map(cat => ({ value: cat.id, label: cat.name })) },
          { name: 'price', label: 'Preço', type: 'number' },
          { name: 'currency', label: 'Moeda', type: 'text', defaultValue: 'BRL' },
          { name: 'requirements', label: 'Requisitos', type: 'textarea' }
        ]
      },
      plans: {
        title: 'Planos de Licença',
        icon: CreditCard,
        data: licensePlans,
        endpoint: 'license-plans',
        fields: [
          { name: 'name', label: 'Nome do Plano', type: 'text', required: true },
          { name: 'description', label: 'Descrição', type: 'textarea' },
          { name: 'max_users', label: 'Máx. Usuários', type: 'number', defaultValue: 1 },
          { name: 'duration_days', label: 'Duração (dias)', type: 'number' },
          { name: 'price', label: 'Preço', type: 'number' },
          { name: 'currency', label: 'Moeda', type: 'text', defaultValue: 'BRL' }
        ]
      }
    };
    
    return configs[activeTab];
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    
    try {
      const config = getTabConfig();
      await axios.post(`/${config.endpoint}`, formData);
      toast.success(`${config.title.slice(0, -1)} criado com sucesso!`);
      
      resetForm();
      setShowCreateDialog(false);
      fetchAllData();
    } catch (error) {
      console.error(`Failed to create ${activeTab}:`, error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : `Erro ao criar ${activeTab}`;
      toast.error(errorMessage);
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    
    try {
      const config = getTabConfig();
      await axios.put(`/${config.endpoint}/${editingItem.id}`, formData);
      toast.success(`${config.title.slice(0, -1)} atualizado com sucesso!`);
      
      setShowEditDialog(false);
      setEditingItem(null);
      resetForm();
      fetchAllData();
    } catch (error) {
      console.error(`Failed to update ${activeTab}:`, error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : `Erro ao atualizar ${activeTab}`;
      toast.error(errorMessage);
    }
  };

  const handleDelete = async (itemId) => {
    try {
      const config = getTabConfig();
      await axios.delete(`/${config.endpoint}/${itemId}`);
      toast.success(`${config.title.slice(0, -1)} excluído com sucesso!`);
      setDeleteConfirmId(null);
      fetchAllData();
    } catch (error) {
      console.error(`Failed to delete ${activeTab}:`, error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : `Erro ao excluir ${activeTab}`;
      toast.error(errorMessage);
    }
  };

  const openCreateDialog = () => {
    resetForm();
    const config = getTabConfig();
    const defaultData = {};
    config.fields.forEach(field => {
      if (field.defaultValue) {
        defaultData[field.name] = field.defaultValue;
      }
    });
    setFormData(defaultData);
    setShowCreateDialog(true);
  };

  const openEditDialog = (item) => {
    setEditingItem(item);
    setFormData(item);
    setShowEditDialog(true);
  };

  const renderFormField = (field) => {
    switch (field.type) {
      case 'textarea':
        return (
          <Textarea
            id={field.name}
            value={formData[field.name] || ''}
            onChange={(e) => setFormData({...formData, [field.name]: e.target.value})}
            required={field.required}
            rows={3}
          />
        );
      
      case 'select':
        return (
          <Select 
            value={formData[field.name] || ''} 
            onValueChange={(value) => setFormData({...formData, [field.name]: value || null})}
          >
            <SelectTrigger>
              <SelectValue placeholder={`Nenhum ${field.label.toLowerCase()} selecionado`} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      
      case 'color':
        return (
          <div className="flex gap-2">
            <Input
              id={field.name}
              type="color"
              value={formData[field.name] || '#3B82F6'}
              onChange={(e) => setFormData({...formData, [field.name]: e.target.value})}
              className="w-20 h-10"
            />
            <Input
              type="text"
              value={formData[field.name] || '#3B82F6'}
              onChange={(e) => setFormData({...formData, [field.name]: e.target.value})}
              className="flex-1"
              placeholder="#3B82F6"
            />
          </div>
        );
      
      default:
        return (
          <Input
            id={field.name}
            type={field.type}
            value={formData[field.name] || ''}
            onChange={(e) => setFormData({...formData, [field.name]: e.target.value})}
            required={field.required}
            step={field.type === 'number' ? '0.01' : undefined}
          />
        );
    }
  };

  const renderTableData = (item, config) => {
    switch (activeTab) {
      case 'categories':
        return (
          <>
            <TableCell>
              <div className="flex items-center space-x-2">
                <div 
                  className="w-4 h-4 rounded-full" 
                  style={{ backgroundColor: item.color || '#3B82F6' }}
                />
                <span className="font-medium">{item.name}</span>
              </div>
            </TableCell>
            <TableCell>
              <span className="text-sm text-gray-500">{item.description || 'Sem descrição'}</span>
            </TableCell>
            <TableCell>
              <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">
                {item.icon || 'folder'}
              </code>
            </TableCell>
          </>
        );
      
      case 'companies':
        return (
          <>
            <TableCell>
              <div>
                <div className="font-medium">{item.name}</div>
                {item.email && (
                  <div className="text-sm text-gray-500">{item.email}</div>
                )}
              </div>
            </TableCell>
            <TableCell>
              <span className="text-sm">{item.phone || 'Não informado'}</span>
            </TableCell>
            <TableCell>
              <Badge variant="outline">
                {item.size === 'small' && 'Pequeno'}
                {item.size === 'medium' && 'Médio'}
                {item.size === 'large' && 'Grande'}
                {item.size === 'enterprise' && 'Corporativo'}
              </Badge>
            </TableCell>
            <TableCell>
              <span className="text-sm">{item.city && item.state ? `${item.city}, ${item.state}` : 'Não informado'}</span>
            </TableCell>
          </>
        );
      
      case 'products':
        const category = categories.find(c => c.id === item.category_id);
        return (
          <>
            <TableCell>
              <div>
                <div className="font-medium">{item.name}</div>
                <div className="text-sm text-gray-500">v{item.version}</div>
              </div>
            </TableCell>
            <TableCell>
              {category ? (
                <div className="flex items-center space-x-1">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: category.color || '#3B82F6' }}
                  />
                  <span className="text-sm">{category.name}</span>
                </div>
              ) : (
                <span className="text-sm text-gray-400">Sem categoria</span>
              )}
            </TableCell>
            <TableCell>
              {item.price ? (
                <span className="text-sm">
                  {new Intl.NumberFormat('pt-BR', {
                    style: 'currency',
                    currency: item.currency || 'BRL'
                  }).format(item.price)}
                </span>
              ) : (
                <span className="text-sm text-gray-400">Não informado</span>
              )}
            </TableCell>
          </>
        );
      
      case 'plans':
        return (
          <>
            <TableCell>
              <div>
                <div className="font-medium">{item.name}</div>
                {item.description && (
                  <div className="text-sm text-gray-500">{item.description}</div>
                )}
              </div>
            </TableCell>
            <TableCell>
              <div className="text-sm">{item.max_users} usuários</div>
            </TableCell>
            <TableCell>
              <div className="text-sm">
                {item.duration_days ? `${item.duration_days} dias` : 'Sem limite'}
              </div>
            </TableCell>
            <TableCell>
              {item.price ? (
                <span className="text-sm font-medium">
                  {new Intl.NumberFormat('pt-BR', {
                    style: 'currency',
                    currency: item.currency || 'BRL'
                  }).format(item.price)}
                </span>
              ) : (
                <span className="text-sm text-gray-400">Gratuito</span>
              )}
            </TableCell>
          </>
        );
      
      default:
        return null;
    }
  };

  const getTableHeaders = () => {
    switch (activeTab) {
      case 'categories':
        return ['Nome', 'Descrição', 'Ícone', 'Ações'];
      case 'companies':
        return ['Empresa', 'Telefone', 'Porte', 'Localização', 'Ações'];
      case 'products':
        return ['Produto', 'Categoria', 'Preço', 'Ações'];
      case 'plans':
        return ['Plano', 'Usuários', 'Duração', 'Preço', 'Ações'];
      default:
        return [];
    }
  };

  const filteredData = () => {
    const config = getTabConfig();
    if (!searchTerm) return config.data;
    
    return config.data.filter(item => 
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.description && item.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (item.email && item.email.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  };

  if (loading) {
    return <LoadingSpinner message="Carregando módulos de cadastro..." />;
  }

  const config = getTabConfig();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
          <Tag className="w-8 h-8 text-blue-600" />
          <span>Módulos de Cadastro</span>
        </h1>
        <p className="text-gray-600 mt-2">
          Gerencie categorias, empresas, produtos e planos de licença
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 mb-6">
          <TabsTrigger value="categories" className="flex items-center space-x-2">
            <FolderOpen className="w-4 h-4" />
            <span>Categorias</span>
          </TabsTrigger>
          <TabsTrigger value="companies" className="flex items-center space-x-2">
            <Building className="w-4 h-4" />
            <span>Empresas</span>
          </TabsTrigger>
          <TabsTrigger value="products" className="flex items-center space-x-2">
            <Package className="w-4 h-4" />
            <span>Produtos</span>
          </TabsTrigger>
          <TabsTrigger value="plans" className="flex items-center space-x-2">
            <CreditCard className="w-4 h-4" />
            <span>Planos</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab Content */}
        {['categories', 'companies', 'products', 'plans'].map(tabValue => (
          <TabsContent key={tabValue} value={tabValue}>
            {/* Actions Bar */}
            <Card className="mb-6">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center space-x-2">
                      <config.icon className="w-5 h-5" />
                      <span>Gerenciar {config.title}</span>
                    </CardTitle>
                    <CardDescription>
                      Cadastre e gerencie {config.title.toLowerCase()} do sistema
                    </CardDescription>
                  </div>
                  <Button onClick={openCreateDialog}>
                    <Plus className="w-4 h-4 mr-2" />
                    Novo
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                      <Input
                        placeholder={`Buscar ${config.title.toLowerCase()}...`}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-9"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Data Table */}
            <Card>
              <CardContent className="pt-6">
                {filteredData().length === 0 ? (
                  <div className="text-center py-8">
                    <config.icon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {searchTerm ? 'Nenhum resultado encontrado' : `Nenhum ${config.title.slice(0, -1).toLowerCase()} cadastrado`}
                    </h3>
                    <p className="text-gray-500 mb-4">
                      {searchTerm 
                        ? 'Tente ajustar os termos de busca'
                        : `Comece criando o primeiro ${config.title.slice(0, -1).toLowerCase()}`
                      }
                    </p>
                    {!searchTerm && (
                      <Button onClick={openCreateDialog}>
                        <Plus className="w-4 h-4 mr-2" />
                        Criar {config.title.slice(0, -1)}
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          {getTableHeaders().map(header => (
                            <TableHead key={header}>{header}</TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredData().map((item) => (
                          <TableRow key={item.id}>
                            {renderTableData(item, config)}
                            <TableCell className="text-right">
                              <div className="flex justify-end space-x-1">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => openEditDialog(item)}
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => setDeleteConfirmId(item.id)}
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
        ))}
      </Tabs>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Criar {config?.title?.slice(0, -1)}</DialogTitle>
            <DialogDescription>
              Preencha os dados para criar um novo {config?.title?.slice(0, -1)?.toLowerCase()}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="grid gap-4 py-4">
              {config?.fields?.map(field => (
                <div key={field.name} className="space-y-2">
                  <Label htmlFor={field.name}>
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </Label>
                  {renderFormField(field)}
                </div>
              ))}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                <X className="w-4 h-4 mr-2" />
                Cancelar
              </Button>
              <Button type="submit">
                <Save className="w-4 h-4 mr-2" />
                Criar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Editar {config?.title?.slice(0, -1)}</DialogTitle>
            <DialogDescription>
              Atualize os dados do {config?.title?.slice(0, -1)?.toLowerCase()}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEdit}>
            <div className="grid gap-4 py-4">
              {config?.fields?.map(field => (
                <div key={field.name} className="space-y-2">
                  <Label htmlFor={field.name}>
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </Label>
                  {renderFormField(field)}
                </div>
              ))}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowEditDialog(false)}>
                <X className="w-4 h-4 mr-2" />
                Cancelar
              </Button>
              <Button type="submit">
                <Save className="w-4 h-4 mr-2" />
                Salvar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={deleteConfirmId !== null} onOpenChange={() => setDeleteConfirmId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar Exclusão</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. O {config?.title?.slice(0, -1)?.toLowerCase()} será removido permanentemente.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              onClick={() => handleDelete(deleteConfirmId)}
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default RegistryModule;