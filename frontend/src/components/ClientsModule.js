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
import { Separator } from './ui/separator';
import { Switch } from './ui/switch';
import axios from 'axios';
import { toast } from 'sonner';
import { 
  Plus,
  Edit,
  Trash2,
  Search,
  Users,
  Building2,
  UserCheck,
  Eye,
  Save,
  X,
  Phone,
  Mail,
  MapPin,
  CreditCard,
  Shield,
  Monitor,
  FileText
} from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';

const ClientsModule = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pf');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Data states
  const [clientesPF, setClientesPF] = useState([]);
  const [clientesPJ, setClientesPJ] = useState([]);
  
  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showViewDialog, setShowViewDialog] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [viewingClient, setViewingClient] = useState(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  
  // Form states
  const [formData, setFormData] = useState({
    client_type: 'pf',
    status: 'active',
    origin_channel: '',
    email_principal: '',
    telefone: '',
    celular: '',
    whatsapp: '',
    contact_preference: 'email',
    
    // PF specific
    nome_completo: '',
    cpf: '',
    rg_numero: '',
    rg_orgao_emissor: '',
    rg_uf: '',
    data_nascimento: '',
    nacionalidade: 'Brasileira',
    nome_mae: '',
    profissao: '',
    
    // PJ specific
    cnpj: '',
    razao_social: '',
    nome_fantasia: '',
    data_abertura: '',
    natureza_juridica: '',
    cnae_principal: '',
    regime_tributario: '',
    porte_empresa: '',
    inscricao_estadual: '',
    ie_situacao: '',
    ie_uf: '',
    inscricao_municipal: '',
    responsavel_legal_nome: '',
    responsavel_legal_cpf: '',
    responsavel_legal_email: '',
    responsavel_legal_telefone: '',
    
    // Address
    address: {
      cep: '',
      logradouro: '',
      numero: '',
      complemento: '',
      bairro: '',
      municipio: '',
      uf: '',
      pais: 'Brasil'
    },
    
    // Contacts
    billing_contact: {
      name: '',
      email: '',
      phone: ''
    },
    technical_contact: {
      name: '',
      email: '',
      phone: ''
    },
    
    // Remote Access
    remote_access: {
      system_type: '',
      access_id: '',
      is_host: false,
      last_analyst: '',
      last_access: ''
    },
    
    // License Info
    license_info: {
      plan_type: '',
      license_quantity: 1,
      equipment_brand: '',
      equipment_model: '',
      billing_cycle: 'monthly',
      billing_day: 1,
      payment_method: 'boleto',
      nfe_email: ''
    },
    
    // LGPD
    lgpd_consent: {
      finalidade: 'Prestação de serviços de software',
      base_legal: 'Execução de contrato',
      privacy_policy_accepted: false,
      marketing_opt_in: false
    },
    
    internal_notes: ''
  });

  useEffect(() => {
    fetchAllClients();
  }, []);

  const fetchAllClients = async () => {
    try {
      setLoading(true);
      const [pfResponse, pjResponse] = await Promise.all([
        axios.get('/clientes-pf'),
        axios.get('/clientes-pj')
      ]);
      
      setClientesPF(pfResponse.data);
      setClientesPJ(pjResponse.data);
    } catch (error) {
      console.error('Failed to fetch clients:', error);
      toast.error('Erro ao carregar clientes');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      client_type: activeTab === 'pf' ? 'pf' : 'pj',
      status: 'active',
      origin_channel: '',
      email_principal: '',
      telefone: '',
      celular: '',
      whatsapp: '',
      contact_preference: 'email',
      nome_completo: '',
      cpf: '',
      rg_numero: '',
      rg_orgao_emissor: '',
      rg_uf: '',
      data_nascimento: '',
      nacionalidade: 'Brasileira',
      nome_mae: '',
      profissao: '',
      cnpj: '',
      razao_social: '',
      nome_fantasia: '',
      data_abertura: '',
      natureza_juridica: '',
      cnae_principal: '',
      regime_tributario: '',
      porte_empresa: '',
      inscricao_estadual: '',
      ie_situacao: '',
      ie_uf: '',
      inscricao_municipal: '',
      responsavel_legal_nome: '',
      responsavel_legal_cpf: '',
      responsavel_legal_email: '',
      responsavel_legal_telefone: '',
      address: {
        cep: '',
        logradouro: '',
        numero: '',
        complemento: '',
        bairro: '',
        municipio: '',
        uf: '',
        pais: 'Brasil'
      },
      billing_contact: {
        name: '',
        email: '',
        phone: ''
      },
      technical_contact: {
        name: '',
        email: '',
        phone: ''
      },
      remote_access: {
        system_type: '',
        access_id: '',
        is_host: false,
        last_analyst: '',
        last_access: ''
      },
      license_info: {
        plan_type: '',
        license_quantity: 1,
        equipment_brand: '',
        equipment_model: '',
        billing_cycle: 'monthly',
        billing_day: 1,
        payment_method: 'boleto',
        nfe_email: ''
      },
      lgpd_consent: {
        finalidade: 'Prestação de serviços de software',
        base_legal: 'Execução de contrato',
        privacy_policy_accepted: false,
        marketing_opt_in: false
      },
      internal_notes: ''
    });
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    
    try {
      const endpoint = activeTab === 'pf' ? '/clientes-pf' : '/clientes-pj';
      
      // Clean empty nested objects
      const cleanedData = { ...formData };
      if (cleanedData.address && Object.values(cleanedData.address).every(v => !v || v === 'Brasil')) {
        delete cleanedData.address;
      }
      if (cleanedData.billing_contact && Object.values(cleanedData.billing_contact).every(v => !v)) {
        delete cleanedData.billing_contact;
      }
      if (cleanedData.technical_contact && Object.values(cleanedData.technical_contact).every(v => !v)) {
        delete cleanedData.technical_contact;
      }
      if (cleanedData.remote_access && Object.values(cleanedData.remote_access).every(v => !v && v !== false)) {
        delete cleanedData.remote_access;
      }
      
      await axios.post(endpoint, cleanedData);
      toast.success(`Cliente ${activeTab.toUpperCase()} criado com sucesso!`);
      
      resetForm();
      setShowCreateDialog(false);
      fetchAllClients();
    } catch (error) {
      console.error('Failed to create client:', error);
      toast.error(error.response?.data?.detail || 'Erro ao criar cliente');
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    
    try {
      const endpoint = activeTab === 'pf' ? `/clientes-pf/${editingClient.id}` : `/clientes-pj/${editingClient.id}`;
      
      await axios.put(endpoint, formData);
      toast.success(`Cliente ${activeTab.toUpperCase()} atualizado com sucesso!`);
      
      setShowEditDialog(false);
      setEditingClient(null);
      resetForm();
      fetchAllClients();
    } catch (error) {
      console.error('Failed to update client:', error);
      toast.error(error.response?.data?.detail || 'Erro ao atualizar cliente');
    }
  };

  const handleDelete = async (clientId) => {
    try {
      const endpoint = activeTab === 'pf' ? `/clientes-pf/${clientId}` : `/clientes-pj/${clientId}`;
      await axios.delete(endpoint);
      toast.success(`Cliente ${activeTab.toUpperCase()} inativado com sucesso!`);
      setDeleteConfirmId(null);
      fetchAllClients();
    } catch (error) {
      console.error('Failed to delete client:', error);
      toast.error(error.response?.data?.detail || 'Erro ao inativar cliente');
    }
  };

  const openCreateDialog = () => {
    resetForm();
    setFormData(prev => ({ ...prev, client_type: activeTab === 'pf' ? 'pf' : 'pj' }));
    setShowCreateDialog(true);
  };

  const openEditDialog = (client) => {
    setEditingClient(client);
    setFormData({
      ...client,
      address: client.address || {
        cep: '', logradouro: '', numero: '', complemento: '',
        bairro: '', municipio: '', uf: '', pais: 'Brasil'
      },
      billing_contact: client.billing_contact || { name: '', email: '', phone: '' },
      technical_contact: client.technical_contact || { name: '', email: '', phone: '' },
      remote_access: client.remote_access || {
        system_type: '', access_id: '', is_host: false, last_analyst: '', last_access: ''
      },
      license_info: client.license_info || {
        plan_type: '', license_quantity: 1, equipment_brand: '', equipment_model: '',
        billing_cycle: 'monthly', billing_day: 1, payment_method: 'boleto', nfe_email: ''
      },
      lgpd_consent: client.lgpd_consent || {
        finalidade: 'Prestação de serviços de software',
        base_legal: 'Execução de contrato',
        privacy_policy_accepted: false,
        marketing_opt_in: false
      }
    });
    setShowEditDialog(true);
  };

  const openViewDialog = (client) => {
    setViewingClient(client);
    setShowViewDialog(true);
  };

  const getStatusBadge = (status) => {
    const variants = {
      active: 'default',
      inactive: 'secondary',
      pending_verification: 'outline'
    };
    
    const labels = {
      active: 'Ativo',
      inactive: 'Inativo',
      pending_verification: 'Pendente'
    };

    return (
      <Badge variant={variants[status]}>
        {labels[status]}
      </Badge>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Não informado';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const formatDocument = (document, type) => {
    if (!document) return 'Não informado';
    
    if (type === 'cpf') {
      return document.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    } else if (type === 'cnpj') {
      return document.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
    
    return document;
  };

  const getCurrentData = () => {
    return activeTab === 'pf' ? clientesPF : clientesPJ;
  };

  const filteredData = () => {
    const data = getCurrentData();
    if (!searchTerm) return data;
    
    return data.filter(client => {
      const searchLower = searchTerm.toLowerCase();
      if (activeTab === 'pf') {
        return (
          client.nome_completo?.toLowerCase().includes(searchLower) ||
          client.cpf?.includes(searchTerm) ||
          client.email_principal?.toLowerCase().includes(searchLower)
        );
      } else {
        return (
          client.razao_social?.toLowerCase().includes(searchLower) ||
          client.nome_fantasia?.toLowerCase().includes(searchLower) ||
          client.cnpj?.includes(searchTerm) ||
          client.email_principal?.toLowerCase().includes(searchLower)
        );
      }
    });
  };

  if (loading) {
    return <LoadingSpinner message="Carregando clientes..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
          <Users className="w-8 h-8 text-blue-600" />
          <span>Cadastro de Clientes</span>
        </h1>
        <p className="text-gray-600 mt-2">
          Sistema completo de cadastro de Pessoas Físicas e Jurídicas com compliance LGPD
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="pf" className="flex items-center space-x-2">
            <UserCheck className="w-4 h-4" />
            <span>Pessoas Físicas ({clientesPF.length})</span>
          </TabsTrigger>
          <TabsTrigger value="pj" className="flex items-center space-x-2">
            <Building2 className="w-4 h-4" />
            <span>Pessoas Jurídicas ({clientesPJ.length})</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab Content */}
        {['pf', 'pj'].map(tabValue => (
          <TabsContent key={tabValue} value={tabValue}>
            {/* Actions Bar */}
            <Card className="mb-6">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center space-x-2">
                      {tabValue === 'pf' ? <UserCheck className="w-5 h-5" /> : <Building2 className="w-5 h-5" />}
                      <span>Gerenciar {tabValue === 'pf' ? 'Pessoas Físicas' : 'Pessoas Jurídicas'}</span>
                    </CardTitle>
                    <CardDescription>
                      Cadastro completo com dados pessoais, endereços, contatos e informações técnicas
                    </CardDescription>
                  </div>
                  <Button onClick={openCreateDialog}>
                    <Plus className="w-4 h-4 mr-2" />
                    Novo Cliente {tabValue.toUpperCase()}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                      <Input
                        placeholder={`Buscar por ${tabValue === 'pf' ? 'nome, CPF ou' : 'razão social, CNPJ ou'} email...`}
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
                    {tabValue === 'pf' ? <UserCheck className="w-12 h-12 text-gray-300 mx-auto mb-4" /> : <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-4" />}
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {searchTerm ? 'Nenhum resultado encontrado' : `Nenhuma ${tabValue === 'pf' ? 'pessoa física' : 'pessoa jurídica'} cadastrada`}
                    </h3>
                    <p className="text-gray-500 mb-4">
                      {searchTerm 
                        ? 'Tente ajustar os termos de busca'
                        : `Comece criando o primeiro cliente ${tabValue.toUpperCase()}`
                      }
                    </p>
                    {!searchTerm && (
                      <Button onClick={openCreateDialog}>
                        <Plus className="w-4 h-4 mr-2" />
                        Criar Cliente {tabValue.toUpperCase()}
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          {tabValue === 'pf' ? (
                            <>
                              <TableHead>Nome Completo</TableHead>
                              <TableHead>CPF</TableHead>
                              <TableHead>Email</TableHead>
                              <TableHead>Telefones</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead className="text-right">Ações</TableHead>
                            </>
                          ) : (
                            <>
                              <TableHead>Razão Social</TableHead>
                              <TableHead>CNPJ</TableHead>
                              <TableHead>Email</TableHead>
                              <TableHead>Responsável</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead className="text-right">Ações</TableHead>
                            </>
                          )}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredData().map((client) => (
                          <TableRow key={client.id}>
                            {tabValue === 'pf' ? (
                              <>
                                <TableCell>
                                  <div>
                                    <div className="font-medium">{client.nome_completo}</div>
                                    {client.profissao && (
                                      <div className="text-sm text-gray-500">{client.profissao}</div>
                                    )}
                                  </div>
                                </TableCell>
                                <TableCell>
                                  <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                                    {formatDocument(client.cpf, 'cpf')}
                                  </code>
                                </TableCell>
                                <TableCell>
                                  <div className="flex items-center space-x-1">
                                    <Mail className="w-3 h-3 text-gray-400" />
                                    <span className="text-sm">{client.email_principal}</span>
                                  </div>
                                </TableCell>
                                <TableCell>
                                  <div className="space-y-1">
                                    {client.celular && (
                                      <div className="flex items-center space-x-1 text-sm">
                                        <Phone className="w-3 h-3 text-gray-400" />
                                        <span>{client.celular}</span>
                                      </div>
                                    )}
                                    {client.whatsapp && client.whatsapp !== client.celular && (
                                      <div className="flex items-center space-x-1 text-sm text-green-600">
                                        <span>WhatsApp: {client.whatsapp}</span>
                                      </div>
                                    )}
                                  </div>
                                </TableCell>
                                <TableCell>
                                  {getStatusBadge(client.status)}
                                </TableCell>
                                <TableCell className="text-right">
                                  <div className="flex justify-end space-x-1">
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => openViewDialog(client)}
                                    >
                                      <Eye className="w-4 h-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => openEditDialog(client)}
                                    >
                                      <Edit className="w-4 h-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => setDeleteConfirmId(client.id)}
                                      className="text-red-600 hover:text-red-700"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </Button>
                                  </div>
                                </TableCell>
                              </>
                            ) : (
                              <>
                                <TableCell>
                                  <div>
                                    <div className="font-medium">{client.razao_social}</div>
                                    {client.nome_fantasia && (
                                      <div className="text-sm text-gray-500">{client.nome_fantasia}</div>
                                    )}
                                  </div>
                                </TableCell>
                                <TableCell>
                                  <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                                    {formatDocument(client.cnpj, 'cnpj')}
                                  </code>
                                </TableCell>
                                <TableCell>
                                  <div className="flex items-center space-x-1">
                                    <Mail className="w-3 h-3 text-gray-400" />
                                    <span className="text-sm">{client.email_principal}</span>
                                  </div>
                                </TableCell>
                                <TableCell>
                                  {client.responsavel_legal_nome ? (
                                    <div>
                                      <div className="text-sm font-medium">{client.responsavel_legal_nome}</div>
                                      {client.responsavel_legal_email && (
                                        <div className="text-xs text-gray-500">{client.responsavel_legal_email}</div>
                                      )}
                                    </div>
                                  ) : (
                                    <span className="text-sm text-gray-400">Não informado</span>
                                  )}
                                </TableCell>
                                <TableCell>
                                  {getStatusBadge(client.status)}
                                </TableCell>
                                <TableCell className="text-right">
                                  <div className="flex justify-end space-x-1">
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => openViewDialog(client)}
                                    >
                                      <Eye className="w-4 h-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => openEditDialog(client)}
                                    >
                                      <Edit className="w-4 h-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => setDeleteConfirmId(client.id)}
                                      className="text-red-600 hover:text-red-700"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </Button>
                                  </div>
                                </TableCell>
                              </>
                            )}
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

      {/* Create/Edit Dialog - Due to complexity, I'll implement a simplified version */}
      <Dialog open={showCreateDialog || showEditDialog} onOpenChange={(open) => {
        if (!open) {
          setShowCreateDialog(false);
          setShowEditDialog(false);
          setEditingClient(null);
          resetForm();
        }
      }}>
        <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {showCreateDialog ? 'Novo' : 'Editar'} Cliente {activeTab.toUpperCase()}
            </DialogTitle>
            <DialogDescription>
              {showCreateDialog ? 'Preencha os dados para criar' : 'Atualize os dados do'} cliente {activeTab === 'pf' ? 'pessoa física' : 'pessoa jurídica'}
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={showCreateDialog ? handleCreate : handleEdit}>
            <div className="grid gap-6 py-4">
              {/* Basic Information */}
              <div className="space-y-4">
                <div className="flex items-center space-x-2 border-b pb-2">
                  <Users className="w-4 h-4" />
                  <h3 className="font-medium">Informações Básicas</h3>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Status</Label>
                    <Select 
                      value={formData.status || ''} 
                      onValueChange={(value) => setFormData({...formData, status: value})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecionar status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="active">Ativo</SelectItem>
                        <SelectItem value="inactive">Inativo</SelectItem>
                        <SelectItem value="pending_verification">Pendente Verificação</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Canal de Origem</Label>
                    <Select 
                      value={formData.origin_channel || ''} 
                      onValueChange={(value) => setFormData({...formData, origin_channel: value || null})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Como chegou até nós" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="website">Website</SelectItem>
                        <SelectItem value="whatsapp">WhatsApp</SelectItem>
                        <SelectItem value="partner">Parceiro</SelectItem>
                        <SelectItem value="referral">Indicação</SelectItem>
                        <SelectItem value="phone">Telefone</SelectItem>
                        <SelectItem value="email">Email</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                {activeTab === 'pf' ? (
                  <>
                    <div className="space-y-2">
                      <Label>Nome Completo *</Label>
                      <Input
                        value={formData.nome_completo}
                        onChange={(e) => setFormData({...formData, nome_completo: e.target.value})}
                        required
                      />
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label>CPF *</Label>
                        <Input
                          value={formData.cpf}
                          onChange={(e) => setFormData({...formData, cpf: e.target.value})}
                          placeholder="000.000.000-00"
                          required
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label>Data de Nascimento</Label>
                        <Input
                          type="date"
                          value={formData.data_nascimento}
                          onChange={(e) => setFormData({...formData, data_nascimento: e.target.value})}
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label>Nacionalidade</Label>
                        <Input
                          value={formData.nacionalidade}
                          onChange={(e) => setFormData({...formData, nacionalidade: e.target.value})}
                        />
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="space-y-2">
                      <Label>Razão Social *</Label>
                      <Input
                        value={formData.razao_social}
                        onChange={(e) => setFormData({...formData, razao_social: e.target.value})}
                        required
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>CNPJ *</Label>
                        <Input
                          value={formData.cnpj}
                          onChange={(e) => setFormData({...formData, cnpj: e.target.value})}
                          placeholder="00.000.000/0000-00"
                          required
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label>Nome Fantasia</Label>
                        <Input
                          value={formData.nome_fantasia}
                          onChange={(e) => setFormData({...formData, nome_fantasia: e.target.value})}
                        />
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Contact Information */}
              <div className="space-y-4">
                <div className="flex items-center space-x-2 border-b pb-2">
                  <Phone className="w-4 h-4" />
                  <h3 className="font-medium">Contatos</h3>
                </div>
                
                <div className="space-y-2">
                  <Label>Email Principal *</Label>
                  <Input
                    type="email"
                    value={formData.email_principal}
                    onChange={(e) => setFormData({...formData, email_principal: e.target.value})}
                    required
                  />
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Telefone</Label>
                    <Input
                      value={formData.telefone}
                      onChange={(e) => setFormData({...formData, telefone: e.target.value})}
                      placeholder="(11) 3000-0000"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Celular</Label>
                    <Input
                      value={formData.celular}
                      onChange={(e) => setFormData({...formData, celular: e.target.value})}
                      placeholder="(11) 99999-9999"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>WhatsApp</Label>
                    <Input
                      value={formData.whatsapp}
                      onChange={(e) => setFormData({...formData, whatsapp: e.target.value})}
                      placeholder="(11) 99999-9999"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Preferência de Contato</Label>
                  <Select 
                    value={formData.contact_preference} 
                    onValueChange={(value) => setFormData({...formData, contact_preference: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="email">Email</SelectItem>
                      <SelectItem value="phone">Telefone</SelectItem>
                      <SelectItem value="whatsapp">WhatsApp</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Remote Access Information */}
              <div className="space-y-4">
                <div className="flex items-center space-x-2 border-b pb-2">
                  <Monitor className="w-4 h-4" />
                  <h3 className="font-medium">Acesso Remoto</h3>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Sistema de Acesso</Label>
                    <Select 
                      value={formData.remote_access?.system_type || ''} 
                      onValueChange={(value) => setFormData({
                        ...formData, 
                        remote_access: {...formData.remote_access, system_type: value || null}
                      })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecionar sistema" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="teamviewer">TeamViewer</SelectItem>
                        <SelectItem value="anydesk">AnyDesk</SelectItem>
                        <SelectItem value="chrome_remote">Chrome Remote Desktop</SelectItem>
                        <SelectItem value="windows_remote">Windows Remote Desktop</SelectItem>
                        <SelectItem value="vnc">VNC</SelectItem>
                        <SelectItem value="other">Outro</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>ID do Acesso (TeamViewer, AnyDesk, etc.)</Label>
                    <Input
                      value={formData.remote_access?.access_id || ''}
                      onChange={(e) => setFormData({
                        ...formData, 
                        remote_access: {...formData.remote_access, access_id: e.target.value}
                      })}
                      placeholder="123 456 789"
                    />
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={formData.remote_access?.is_host || false}
                    onCheckedChange={(checked) => setFormData({
                      ...formData, 
                      remote_access: {...formData.remote_access, is_host: checked}
                    })}
                  />
                  <Label>É Host (permite conexões)</Label>
                </div>
              </div>

              {/* LGPD Compliance */}
              <div className="space-y-4">
                <div className="flex items-center space-x-2 border-b pb-2">
                  <Shield className="w-4 h-4" />
                  <h3 className="font-medium">LGPD / Conformidade</h3>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Finalidade do Tratamento</Label>
                    <Input
                      value={formData.lgpd_consent?.finalidade || ''}
                      onChange={(e) => setFormData({
                        ...formData, 
                        lgpd_consent: {...formData.lgpd_consent, finalidade: e.target.value}
                      })}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Base Legal</Label>
                    <Input
                      value={formData.lgpd_consent?.base_legal || ''}
                      onChange={(e) => setFormData({
                        ...formData, 
                        lgpd_consent: {...formData.lgpd_consent, base_legal: e.target.value}
                      })}
                    />
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={formData.lgpd_consent?.privacy_policy_accepted || false}
                      onCheckedChange={(checked) => setFormData({
                        ...formData, 
                        lgpd_consent: {...formData.lgpd_consent, privacy_policy_accepted: checked}
                      })}
                    />
                    <Label>Aceita Política de Privacidade</Label>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={formData.lgpd_consent?.marketing_opt_in || false}
                      onCheckedChange={(checked) => setFormData({
                        ...formData, 
                        lgpd_consent: {...formData.lgpd_consent, marketing_opt_in: checked}
                      })}
                    />
                    <Label>Aceita receber comunicações de marketing</Label>
                  </div>
                </div>
              </div>

              {/* Internal Notes */}
              <div className="space-y-4">
                <div className="flex items-center space-x-2 border-b pb-2">
                  <FileText className="w-4 h-4" />
                  <h3 className="font-medium">Observações Internas</h3>
                </div>
                
                <div className="space-y-2">
                  <Label>Notas (visível apenas internamente)</Label>
                  <Textarea
                    value={formData.internal_notes}
                    onChange={(e) => setFormData({...formData, internal_notes: e.target.value})}
                    rows={3}
                    placeholder="Observações, histórico, notas técnicas..."
                  />
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => {
                setShowCreateDialog(false);
                setShowEditDialog(false);
                setEditingClient(null);
                resetForm();
              }}>
                <X className="w-4 h-4 mr-2" />
                Cancelar
              </Button>
              <Button type="submit">
                <Save className="w-4 h-4 mr-2" />
                {showCreateDialog ? 'Criar Cliente' : 'Salvar Alterações'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={deleteConfirmId !== null} onOpenChange={() => setDeleteConfirmId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar Inativação</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação irá inativar o cliente {activeTab.toUpperCase()}. O registro será mantido para fins de auditoria, mas não aparecerá nas listas ativas.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              onClick={() => handleDelete(deleteConfirmId)}
            >
              Inativar Cliente
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* View Dialog - Simple implementation */}
      <Dialog open={showViewDialog} onOpenChange={setShowViewDialog}>
        <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Detalhes do Cliente {activeTab.toUpperCase()}
            </DialogTitle>
          </DialogHeader>
          {viewingClient && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium text-gray-500">
                    {activeTab === 'pf' ? 'Nome' : 'Razão Social'}
                  </Label>
                  <p className="font-medium">
                    {activeTab === 'pf' ? viewingClient.nome_completo : viewingClient.razao_social}
                  </p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-500">
                    {activeTab === 'pf' ? 'CPF' : 'CNPJ'}
                  </Label>
                  <p className="font-mono text-sm">
                    {activeTab === 'pf' 
                      ? formatDocument(viewingClient.cpf, 'cpf') 
                      : formatDocument(viewingClient.cnpj, 'cnpj')
                    }
                  </p>
                </div>
              </div>
              
              <Separator />
              
              <div>
                <Label className="text-sm font-medium text-gray-500">Email Principal</Label>
                <p>{viewingClient.email_principal}</p>
              </div>
              
              <div>
                <Label className="text-sm font-medium text-gray-500">Status</Label>
                <div className="mt-1">
                  {getStatusBadge(viewingClient.status)}
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium text-gray-500">Criado em</Label>
                <p>{formatDate(viewingClient.created_at)}</p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowViewDialog(false)}>
              Fechar
            </Button>
            {viewingClient && (
              <Button onClick={() => {
                setShowViewDialog(false);
                openEditDialog(viewingClient);
              }}>
                <Edit className="w-4 h-4 mr-2" />
                Editar
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ClientsModule;