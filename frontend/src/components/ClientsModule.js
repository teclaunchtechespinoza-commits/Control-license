import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { CustomSemanticBadge, LicenseStatusBadge } from './ui/semantic-badge';
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
import { SensitiveDataSection, SensitiveDataEditor } from './SensitiveDataManager';
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
import { ScrollArea } from './ui/scroll-area';
import { api } from '../api';
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
  FileText,
  Building,
  FileCheck,
  Monitor,
  FileImage,
  AlertTriangle,
  Lock,
  Minus
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
  
  // Equipment data
  const [equipmentBrands, setEquipmentBrands] = useState([]);
  const [equipmentModels, setEquipmentModels] = useState([]);
  const [selectedBrandId, setSelectedBrandId] = useState('');
  
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
    
    // PJ specific - Expanded
    cnpj: '',
    cnpj_formato_informado: '',
    cnpj_normalizado: '',
    razao_social: '',
    nome_fantasia: '',
    data_abertura: '',
    natureza_juridica: '',
    cnae_principal: '',
    cnaes_secundarios: [],
    regime_tributario: '',
    porte_empresa: '',
    
    // Inscrições expandidas
    inscricao_estadual: '',
    ie_situacao: '',
    ie_uf: '',
    inscricao_municipal: '',
    inscricao_municipal_ccm: '',
    inscricoes_locais: [], // Array de inscrições locais
    
    // Responsáveis expandidos
    responsavel_legal_nome: '',
    responsavel_legal_cpf: '',
    responsavel_legal_email: '',
    responsavel_legal_telefone: '',
    
    // Procurador expandido
    procurador_nome: '',
    procurador_cpf: '',
    procurador_contato: '',
    procurador_email: '',
    procurador_telefone: '',
    procuracao_validade: '',
    procuracao_numero: '',
    
    // Certificado digital expandido
    certificado_digital: {
      tipo: '',
      numero_serie: '',
      emissor: '',
      validade: ''
    },
    
    // Documentos societários
    documentos_societarios: {
      contrato_social_url: '',
      estatuto_social_url: '',
      ultima_alteracao_url: '',
      ultima_alteracao_data: '',
      observacoes: ''
    },
    
    // Filiais expandidas
    filiais: [],
    
    // Address
    endereco_matriz: {
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
      equipment_id: '',
      equipment_serial: '',
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
    fetchEquipmentBrands();
  }, []);

  // Debug: Track formData changes
  useEffect(() => {
    console.log('DEBUG: formData state changed:', {
      razao_social: formData.razao_social,
      cnpj: formData.cnpj,
      email_principal: formData.email_principal,
      client_type: formData.client_type
    });
  }, [formData.razao_social, formData.cnpj, formData.email_principal, formData.client_type]);

  const fetchAllClients = async () => {
    try {
      setLoading(true);
      // Add cache-busting parameter
      const timestamp = Date.now();
      const [pfResponse, pjResponse] = await Promise.all([
        api.get('/clientes-pf', { params: { _: timestamp } }),
        api.get('/clientes-pj', { params: { _: timestamp } })
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

  // Equipment functions
  const fetchEquipmentBrands = async () => {
    try {
      const { data } = await api.get('/equipment-brands');
      setEquipmentBrands(data);
    } catch (error) {
      console.error('Failed to fetch equipment brands:', error);
    }
  };

  const fetchEquipmentModels = async (brandId = '') => {
    try {
      const { data } = brandId 
        ? await api.get('/equipment-models', { params: { brand_id: brandId } })
        : await api.get('/equipment-models');
      setEquipmentModels(data);
    } catch (error) {
      console.error('Failed to fetch equipment models:', error);
    }
  };

  const handleBrandChange = (brandId) => {
    setSelectedBrandId(brandId);
    setFormData(prev => ({
      ...prev,
      license_info: {
        ...prev.license_info,
        equipment_brand: brandId,
        equipment_model: '' // Reset model when brand changes
      }
    }));
    if (brandId) {
      fetchEquipmentModels(brandId);
    } else {
      setEquipmentModels([]);
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
      cnpj_formato_informado: '',
      cnpj_normalizado: '',
      razao_social: '',
      nome_fantasia: '',
      data_abertura: '',
      natureza_juridica: '',
      cnae_principal: '',
      cnaes_secundarios: [],
      regime_tributario: '',
      porte_empresa: '',
      inscricao_estadual: '',
      ie_situacao: '',
      ie_uf: '',
      inscricao_municipal: '',
      inscricao_municipal_ccm: '',
      inscricoes_locais: [],
      responsavel_legal_nome: '',
      responsavel_legal_cpf: '',
      responsavel_legal_email: '',
      responsavel_legal_telefone: '',
      procurador_nome: '',
      procurador_cpf: '',
      procurador_contato: '',
      procurador_email: '',
      procurador_telefone: '',
      procuracao_validade: '',
      procuracao_numero: '',
      certificado_digital: {
        tipo: '',
        numero_serie: '',
        emissor: '',
        validade: ''
      },
      documentos_societarios: {
        contrato_social_url: '',
        estatuto_social_url: '',
        ultima_alteracao_url: '',
        ultima_alteracao_data: '',
        observacoes: ''
      },
      filiais: [],
      endereco_matriz: {
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
    
    console.log('DEBUG: handleCreate started, current formData:', formData);
    console.log('DEBUG: handleCreate - razao_social:', formData.razao_social);
    console.log('DEBUG: handleCreate - cnpj:', formData.cnpj);
    console.log('DEBUG: handleCreate - email_principal:', formData.email_principal);
    
    try {
      const endpoint = activeTab === 'pf' ? '/clientes-pf' : '/clientes-pj';
      
      // Create properly structured data for backend
      const cleanedData = { ...formData };
      
      // CRITICAL FIX: Explicitly ensure required fields are included
      if (activeTab === 'pj') {
        cleanedData.razao_social = formData.razao_social;
        cleanedData.cnpj = formData.cnpj;
        cleanedData.email_principal = formData.email_principal;
      } else if (activeTab === 'pf') {
        cleanedData.nome_completo = formData.nome_completo;
        cleanedData.cpf = formData.cpf;
        cleanedData.email_principal = formData.email_principal;
      }
      
      // Fix enum values and field mappings
      if (cleanedData.porte_empresa === '') {
        delete cleanedData.porte_empresa;
      }
      if (cleanedData.regime_tributario === '') {
        delete cleanedData.regime_tributario;
      }
      if (cleanedData.origin_channel === '') {
        delete cleanedData.origin_channel;
      }
      
      // Fix address field mapping based on client type
      if (cleanedData.endereco_matriz) {
        if (activeTab === 'pf') {
          // PF uses 'address' field from ClientBase
          cleanedData.address = cleanedData.endereco_matriz;
          delete cleanedData.endereco_matriz;
        }
        // PJ keeps 'endereco_matriz' as is
      }
      
      // Clean empty nested objects and arrays - but preserve required fields
      const requiredFields = activeTab === 'pf' 
        ? ['nome_completo', 'cpf', 'email_principal']
        : ['razao_social', 'cnpj', 'email_principal'];
        
      Object.keys(cleanedData).forEach(key => {
        // Never touch required fields
        if (requiredFields.includes(key)) {
          return;
        }
        
        if (Array.isArray(cleanedData[key]) && cleanedData[key].length === 0) {
          delete cleanedData[key];
        } else if (typeof cleanedData[key] === 'object' && cleanedData[key] !== null) {
          // Check if object has any meaningful values
          const hasValues = Object.values(cleanedData[key]).some(val => 
            val !== '' && val !== null && val !== undefined && val !== false
          );
          if (!hasValues) {
            delete cleanedData[key];
          } else {
            // Clean empty string values within objects
            Object.keys(cleanedData[key]).forEach(nestedKey => {
              if (cleanedData[key][nestedKey] === '' || cleanedData[key][nestedKey] === null) {
                delete cleanedData[key][nestedKey];
              }
            });
          }
        } else if (cleanedData[key] === '' || cleanedData[key] === null) {
          delete cleanedData[key];
        }
      });
      
      // Debug logging for field mapping issue
      console.log('DEBUG: Original formData before cleaning:', formData);
      console.log('DEBUG: Required fields for', activeTab, ':', requiredFields);
      console.log('DEBUG: cleanedData before validation:', cleanedData);
      
      console.log('Sending data to backend:', cleanedData);
      
      // Ensure required fields for PF
      if (activeTab === 'pf') {
        if (!cleanedData.nome_completo || !cleanedData.cpf || !cleanedData.email_principal) {
          toast.error('Preencha todos os campos obrigatórios: Nome Completo, CPF e Email');
          return;
        }
      }
      
      // Ensure required fields for PJ
      if (activeTab === 'pj') {
        if (!cleanedData.razao_social || !cleanedData.cnpj || !cleanedData.email_principal) {
          toast.error('Preencha todos os campos obrigatórios: Razão Social, CNPJ e Email');
          return;
        }
        
        // Add CNPJ normalization for backend validation
        if (cleanedData.cnpj) {
          cleanedData.cnpj_normalizado = cleanedData.cnpj.replace(/\D/g, '');
        }
      }
      
      console.log('Sending data to backend:', cleanedData);
      
      const response = await axios.post(endpoint, cleanedData);
      toast.success(`Cliente ${activeTab.toUpperCase()} criado com sucesso!`);
      
      resetForm();
      setShowCreateDialog(false);
      fetchAllClients();
    } catch (error) {
      console.error('Failed to create client:', error);
      console.error('Error response:', error.response);
      
      // Better error handling
      let errorMessage = 'Erro ao criar cliente';
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          // Handle validation errors array
          const errors = error.response.data.detail.map(err => 
            `${err.loc ? err.loc.join('.') + ': ' : ''}${err.msg}`
          ).join(', ');
          errorMessage = `Erro de validação: ${errors}`;
        }
      } else if (error.response?.status === 422) {
        errorMessage = 'Dados inválidos. Verifique os campos preenchidos.';
      }
      
      toast.error(errorMessage);
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    
    try {
      const endpoint = activeTab === 'pf' ? `/clientes-pf/${editingClient.id}` : `/clientes-pj/${editingClient.id}`;
      
      // Apply same data cleaning logic as in handleCreate
      const cleanedData = { ...formData };
      
      // Fix enum values and field mappings
      if (cleanedData.porte_empresa === '') {
        delete cleanedData.porte_empresa;
      }
      if (cleanedData.regime_tributario === '') {
        delete cleanedData.regime_tributario;
      }
      if (cleanedData.origin_channel === '') {
        delete cleanedData.origin_channel;
      }
      
      // Fix address field mapping based on client type
      if (cleanedData.endereco_matriz) {
        if (activeTab === 'pf') {
          // PF uses 'address' field from ClientBase
          cleanedData.address = cleanedData.endereco_matriz;
          delete cleanedData.endereco_matriz;
        }
        // PJ keeps 'endereco_matriz' as is
      }
      
      // Clean empty nested objects and arrays - but preserve required fields
      const requiredFields = activeTab === 'pf' 
        ? ['nome_completo', 'cpf', 'email_principal']
        : ['razao_social', 'cnpj', 'email_principal'];
        
      Object.keys(cleanedData).forEach(key => {
        // Never touch required fields
        if (requiredFields.includes(key)) {
          return;
        }
        
        if (Array.isArray(cleanedData[key]) && cleanedData[key].length === 0) {
          delete cleanedData[key];
        } else if (typeof cleanedData[key] === 'object' && cleanedData[key] !== null) {
          // Check if object has any meaningful values
          const hasValues = Object.values(cleanedData[key]).some(val => 
            val !== '' && val !== null && val !== undefined && val !== false
          );
          if (!hasValues) {
            delete cleanedData[key];
          } else {
            // Clean empty string values within objects
            Object.keys(cleanedData[key]).forEach(nestedKey => {
              if (cleanedData[key][nestedKey] === '' || cleanedData[key][nestedKey] === null) {
                delete cleanedData[key][nestedKey];
              }
            });
          }
        } else if (cleanedData[key] === '' || cleanedData[key] === null) {
          delete cleanedData[key];
        }
      });
      
      // Add CNPJ normalization for PJ clients
      if (activeTab === 'pj' && cleanedData.cnpj) {
        cleanedData.cnpj_normalizado = cleanedData.cnpj.replace(/\D/g, '');
      }
      
      console.log('Sending data to backend for edit:', cleanedData);
      
      await axios.put(endpoint, cleanedData);
      toast.success(`Cliente ${activeTab.toUpperCase()} atualizado com sucesso!`);
      
      setShowEditDialog(false);
      setEditingClient(null);
      resetForm();
      fetchAllClients();
    } catch (error) {
      console.error('Failed to update client:', error);
      
      // Better error handling for edit
      let errorMessage = 'Erro ao atualizar cliente';
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          // Handle validation errors array
          const errors = error.response.data.detail.map(err => 
            `${err.loc ? err.loc.join('.') + ': ' : ''}${err.msg}`
          ).join(', ');
          errorMessage = `Erro de validação: ${errors}`;
        } else {
          // Handle other error object types
          errorMessage = 'Erro de validação. Verifique os dados preenchidos.';
        }
      } else if (error.response?.status === 422) {
        errorMessage = 'Dados inválidos. Verifique os campos preenchidos.';
      }
      
      toast.error(errorMessage);
    }
  };

  const handleDelete = async (clientId) => {
    try {
      const endpoint = activeTab === 'pf' ? `/clientes-pf/${clientId}` : `/clientes-pj/${clientId}`;
      await axios.delete(endpoint);
      toast.success(`Cliente ${activeTab.toUpperCase()} inativado com sucesso!`);
      setDeleteConfirmId(null);
      
      // Force refresh with small delay
      setTimeout(() => {
        fetchAllClients();
      }, 100);
    } catch (error) {
      console.error('Failed to delete client:', error);
      
      // Better error handling for delete
      let errorMessage = 'Erro ao inativar cliente';
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else {
          errorMessage = 'Erro ao processar solicitação. Tente novamente.';
        }
      }
      
      toast.error(errorMessage);
    }
  };

  const openCreateDialog = () => {
    resetForm();
    setFormData(prev => ({ ...prev, client_type: activeTab === 'pf' ? 'pf' : 'pj' }));
    console.log('DEBUG: Dialog opened, formData reset for tab:', activeTab);
    setShowCreateDialog(true);
  };

  const openEditDialog = (client) => {
    setEditingClient(client);
    setFormData({
      ...client,
      endereco_matriz: client.endereco_matriz || {
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
      },
      certificado_digital: client.certificado_digital || {
        tipo: '', numero_serie: '', emissor: '', validade: ''
      },
      documentos_societarios: client.documentos_societarios || {
        contrato_social_url: '', estatuto_social_url: '', ultima_alteracao_url: '',
        ultima_alteracao_data: '', observacoes: ''
      },
      filiais: client.filiais || [],
      inscricoes_locais: client.inscricoes_locais || []
    });
    setShowEditDialog(true);
  };

  const openViewDialog = (client) => {
    setViewingClient(client);
    setShowViewDialog(true);
  };

  // Helper functions for filiais and inscricoes
  const addFilial = () => {
    setFormData(prev => ({
      ...prev,
      filiais: [...prev.filiais, {
        cnpj_filial: '',
        ordem: '',
        nome_fantasia: '',
        endereco: {
          cep: '', logradouro: '', numero: '', complemento: '',
          bairro: '', municipio: '', uf: '', pais: 'Brasil'
        },
        is_active: true
      }]
    }));
  };

  const removeFilial = (index) => {
    setFormData(prev => ({
      ...prev,
      filiais: prev.filiais.filter((_, i) => i !== index)
    }));
  };

  const updateFilial = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      filiais: prev.filiais.map((filial, i) => 
        i === index ? { ...filial, [field]: value } : filial
      )
    }));
  };

  const addInscricaoLocal = () => {
    setFormData(prev => ({
      ...prev,
      inscricoes_locais: [...prev.inscricoes_locais, {
        numero: '',
        municipio: '',
        tipo: '',
        validade: ''
      }]
    }));
  };

  const removeInscricaoLocal = (index) => {
    setFormData(prev => ({
      ...prev,
      inscricoes_locais: prev.inscricoes_locais.filter((_, i) => i !== index)
    }));
  };

  const updateInscricaoLocal = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      inscricoes_locais: prev.inscricoes_locais.map((inscricao, i) => 
        i === index ? { ...inscricao, [field]: value } : inscricao
      )
    }));
  };

  const getSemanticStatusBadge = (status) => {
    // Usar diretamente o LicenseStatusBadge para consistência
    // Mapeamento direto para evitar conflitos
    switch(status) {
      case 'active':
        return <LicenseStatusBadge status="active" size="sm" />;
      case 'inactive':
        return <LicenseStatusBadge status="inactive" size="sm" />;
      case 'pending_verification':
        return <LicenseStatusBadge status="pending" size="sm" />;
      case 'blocked':
        return <LicenseStatusBadge status="blocked" size="sm" />;
      default:
        return <LicenseStatusBadge status="inactive" size="sm" />;
    }
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
                                  {getSemanticStatusBadge(client.status)}
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
                                    {client.regime_tributario && (
                                      <Badge variant="outline" className="mt-1">
                                        {client.regime_tributario.toUpperCase()}
                                      </Badge>
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
                                  {getSemanticStatusBadge(client.status)}
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

      {/* Expanded Create/Edit Dialog for PJ */}
      <Dialog open={showCreateDialog || showEditDialog} onOpenChange={(open) => {
        if (!open) {
          setShowCreateDialog(false);
          setShowEditDialog(false);
          setEditingClient(null);
          resetForm();
        }
      }}>
        <DialogContent className="sm:max-w-[1000px] max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle>
              {showCreateDialog ? 'Novo' : 'Editar'} Cliente {activeTab.toUpperCase()}
            </DialogTitle>
            <DialogDescription>
              {showCreateDialog ? 'Preencha os dados para criar' : 'Atualize os dados do'} cliente {activeTab === 'pf' ? 'pessoa física' : 'pessoa jurídica'}
            </DialogDescription>
          </DialogHeader>
          
          <ScrollArea className="h-[calc(90vh-200px)] pr-4">
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
                      <div className="space-y-2">
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
                            <SelectItem value="blocked">Bloqueado</SelectItem>
                          </SelectContent>
                        </Select>
                        
                        {/* Preview do badge semântico - sem redundância */}
                        {formData.status && (
                          <div className="flex items-center space-x-3 p-2 bg-gray-50 rounded-md border">
                            <span className="text-xs font-medium text-gray-500">Como aparecerá na lista:</span>
                            {getSemanticStatusBadge(formData.status)}
                          </div>
                        )}
                      </div>
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
                          name="nome_completo"
                          value={formData.nome_completo}
                          onChange={(e) => setFormData({...formData, nome_completo: e.target.value})}
                          required
                        />
                      </div>
                      
                      <div className="grid grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label>CPF *</Label>
                          <Input
                            name="cpf"
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
                      {/* EXPANDED PJ FORM */}
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Razão Social *</Label>
                          <Input
                            name="razao_social"
                            value={formData.razao_social}
                            onChange={(e) => {
                              console.log('DEBUG: razao_social onChange fired, value:', e.target.value);
                              setFormData(prev => ({...prev, razao_social: e.target.value}));
                            }}
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
                      
                      <div className="grid grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label>CNPJ *</Label>
                          <Input
                            name="cnpj"
                            value={formData.cnpj}
                            onChange={(e) => {
                              console.log('DEBUG: cnpj onChange fired, value:', e.target.value);
                              setFormData(prev => ({...prev, cnpj: e.target.value}));
                            }}
                            placeholder="00.000.000/0000-00"
                            required
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <Label>Data de Abertura</Label>
                          <Input
                            type="date"
                            value={formData.data_abertura}
                            onChange={(e) => setFormData({...formData, data_abertura: e.target.value})}
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <Label>Natureza Jurídica</Label>
                          <Input
                            value={formData.natureza_juridica}
                            onChange={(e) => setFormData({...formData, natureza_juridica: e.target.value})}
                            placeholder="Ex: LTDA, SA, etc."
                          />
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>CNAE Principal</Label>
                          <Input
                            value={formData.cnae_principal}
                            onChange={(e) => setFormData({...formData, cnae_principal: e.target.value})}
                            placeholder="0000-0/00"
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <Label>CNAEs Secundários</Label>
                          <Input
                            value={formData.cnaes_secundarios.join(', ')}
                            onChange={(e) => setFormData({...formData, cnaes_secundarios: e.target.value.split(', ').filter(Boolean)})}
                            placeholder="0000-0/00, 0000-0/00"
                          />
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Regime Tributário</Label>
                          <Select 
                            value={formData.regime_tributario || ''} 
                            onValueChange={(value) => setFormData({...formData, regime_tributario: value || null})}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Selecionar regime" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="mei">MEI</SelectItem>
                              <SelectItem value="simples">Simples Nacional</SelectItem>
                              <SelectItem value="lucro_presumido">Lucro Presumido</SelectItem>
                              <SelectItem value="lucro_real">Lucro Real</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div className="space-y-2">
                          <Label>Porte da Empresa</Label>
                          <Select 
                            value={formData.porte_empresa || ''} 
                            onValueChange={(value) => setFormData({...formData, porte_empresa: value || null})}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Selecionar porte" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="mei">MEI</SelectItem>
                              <SelectItem value="me">Microempresa (ME)</SelectItem>
                              <SelectItem value="epp">Empresa de Pequeno Porte (EPP)</SelectItem>
                              <SelectItem value="medio">Médio Porte</SelectItem>
                              <SelectItem value="grande">Grande Porte</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      {/* Inscrições Expandidas */}
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2 border-b pb-2">
                          <FileText className="w-4 h-4" />
                          <h3 className="font-medium">Inscrições e Registros</h3>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-4">
                          <div className="space-y-2">
                            <Label>Inscrição Estadual (IE)</Label>
                            <Input
                              value={formData.inscricao_estadual}
                              onChange={(e) => setFormData({...formData, inscricao_estadual: e.target.value})}
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Situação IE</Label>
                            <Select 
                              value={formData.ie_situacao || ''} 
                              onValueChange={(value) => setFormData({...formData, ie_situacao: value || null})}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Situação" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="contribuinte">Contribuinte</SelectItem>
                                <SelectItem value="isento">Isento</SelectItem>
                                <SelectItem value="nao_obrigado">Não Obrigado</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          
                          <div className="space-y-2">
                            <Label>UF da IE</Label>
                            <Input
                              value={formData.ie_uf}
                              onChange={(e) => setFormData({...formData, ie_uf: e.target.value})}
                              placeholder="SP"
                              maxLength={2}
                            />
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Inscrição Municipal (IM)</Label>
                            <Input
                              value={formData.inscricao_municipal}
                              onChange={(e) => setFormData({...formData, inscricao_municipal: e.target.value})}
                            />
                          </div>
                        </div>
                      </div>



                      {/* Responsável Legal Expandido */}
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2 border-b pb-2">
                          <UserCheck className="w-4 h-4" />
                          <h3 className="font-medium">Responsável Legal</h3>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Nome Completo</Label>
                            <Input
                              value={formData.responsavel_legal_nome}
                              onChange={(e) => setFormData({...formData, responsavel_legal_nome: e.target.value})}
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>CPF</Label>
                            <Input
                              value={formData.responsavel_legal_cpf}
                              onChange={(e) => setFormData({...formData, responsavel_legal_cpf: e.target.value})}
                              placeholder="000.000.000-00"
                            />
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Email</Label>
                            <Input
                              type="email"
                              value={formData.responsavel_legal_email}
                              onChange={(e) => setFormData({...formData, responsavel_legal_email: e.target.value})}
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Telefone</Label>
                            <Input
                              value={formData.responsavel_legal_telefone}
                              onChange={(e) => setFormData({...formData, responsavel_legal_telefone: e.target.value})}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Procurador Expandido */}
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2 border-b pb-2">
                          <Users className="w-4 h-4" />
                          <h3 className="font-medium">Procurador/Representante (Opcional)</h3>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-4">
                          <div className="space-y-2">
                            <Label>Nome</Label>
                            <Input
                              value={formData.procurador_nome}
                              onChange={(e) => setFormData({...formData, procurador_nome: e.target.value})}
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>CPF</Label>
                            <Input
                              value={formData.procurador_cpf}
                              onChange={(e) => setFormData({...formData, procurador_cpf: e.target.value})}
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Número da Procuração</Label>
                            <Input
                              value={formData.procuracao_numero}
                              onChange={(e) => setFormData({...formData, procuracao_numero: e.target.value})}
                            />
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-4">
                          <div className="space-y-2">
                            <Label>Email</Label>
                            <Input
                              type="email"
                              value={formData.procurador_email}
                              onChange={(e) => setFormData({...formData, procurador_email: e.target.value})}
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Telefone</Label>
                            <Input
                              value={formData.procurador_telefone}
                              onChange={(e) => setFormData({...formData, procurador_telefone: e.target.value})}
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Validade da Procuração</Label>
                            <Input
                              type="date"
                              value={formData.procuracao_validade}
                              onChange={(e) => setFormData({...formData, procuracao_validade: e.target.value})}
                            />
                          </div>
                        </div>
                      </div>





                      {/* Filiais Dinâmicas */}
                      <div className="space-y-4">
                        <div className="flex items-center justify-between border-b pb-2">
                          <div className="flex items-center space-x-2">
                            <Building className="w-4 h-4" />
                            <h3 className="font-medium">Filiais</h3>
                          </div>
                          <Button type="button" size="sm" onClick={addFilial}>
                            <Plus className="w-3 h-3 mr-1" />
                            Adicionar Filial
                          </Button>
                        </div>
                        
                        {formData.filiais?.map((filial, index) => (
                          <div key={index} className="border rounded-lg p-4 relative">
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="absolute top-2 right-2 text-red-600"
                              onClick={() => removeFilial(index)}
                            >
                              <Minus className="w-3 h-3" />
                            </Button>
                            
                            <div className="grid grid-cols-3 gap-4 mb-4">
                              <div className="space-y-2">
                                <Label>CNPJ da Filial</Label>
                                <Input
                                  value={filial.cnpj_filial}
                                  onChange={(e) => updateFilial(index, 'cnpj_filial', e.target.value)}
                                  placeholder="00.000.000/0000-00"
                                />
                              </div>
                              
                              <div className="space-y-2">
                                <Label>Ordem</Label>
                                <Input
                                  value={filial.ordem}
                                  onChange={(e) => updateFilial(index, 'ordem', e.target.value)}
                                  placeholder="001"
                                />
                              </div>
                              
                              <div className="space-y-2">
                                <Label>Nome Fantasia</Label>
                                <Input
                                  value={filial.nome_fantasia}
                                  onChange={(e) => updateFilial(index, 'nome_fantasia', e.target.value)}
                                />
                              </div>
                            </div>
                            
                            <div className="grid grid-cols-3 gap-4">
                              <div className="space-y-2">
                                <Label>CEP</Label>
                                <Input
                                  value={filial.endereco?.cep || ''}
                                  onChange={(e) => updateFilial(index, 'endereco', {...filial.endereco, cep: e.target.value})}
                                />
                              </div>
                              
                              <div className="space-y-2">
                                <Label>Logradouro</Label>
                                <Input
                                  value={filial.endereco?.logradouro || ''}
                                  onChange={(e) => updateFilial(index, 'endereco', {...filial.endereco, logradouro: e.target.value})}
                                />
                              </div>
                              
                              <div className="space-y-2">
                                <Label>Número</Label>
                                <Input
                                  value={filial.endereco?.numero || ''}
                                  onChange={(e) => updateFilial(index, 'endereco', {...filial.endereco, numero: e.target.value})}
                                />
                              </div>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4 mt-4">
                              <div className="space-y-2">
                                <Label>Município</Label>
                                <Input
                                  value={filial.endereco?.municipio || ''}
                                  onChange={(e) => updateFilial(index, 'endereco', {...filial.endereco, municipio: e.target.value})}
                                />
                              </div>
                              
                              <div className="space-y-2">
                                <Label>UF</Label>
                                <Input
                                  value={filial.endereco?.uf || ''}
                                  onChange={(e) => updateFilial(index, 'endereco', {...filial.endereco, uf: e.target.value})}
                                  maxLength={2}
                                />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Endereço da Matriz */}
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2 border-b pb-2">
                          <MapPin className="w-4 h-4" />
                          <h3 className="font-medium">Endereço da Matriz</h3>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-4">
                          <div className="space-y-2">
                            <Label>CEP</Label>
                            <Input
                              value={formData.endereco_matriz?.cep || ''}
                              onChange={(e) => setFormData({
                                ...formData, 
                                endereco_matriz: {...formData.endereco_matriz, cep: e.target.value}
                              })}
                              placeholder="00000-000"
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Logradouro</Label>
                            <Input
                              value={formData.endereco_matriz?.logradouro || ''}
                              onChange={(e) => setFormData({
                                ...formData, 
                                endereco_matriz: {...formData.endereco_matriz, logradouro: e.target.value}
                              })}
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Número</Label>
                            <Input
                              value={formData.endereco_matriz?.numero || ''}
                              onChange={(e) => setFormData({
                                ...formData, 
                                endereco_matriz: {...formData.endereco_matriz, numero: e.target.value}
                              })}
                            />
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-4">
                          <div className="space-y-2">
                            <Label>Complemento</Label>
                            <Input
                              value={formData.endereco_matriz?.complemento || ''}
                              onChange={(e) => setFormData({
                                ...formData, 
                                endereco_matriz: {...formData.endereco_matriz, complemento: e.target.value}
                              })}
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Bairro</Label>
                            <Input
                              value={formData.endereco_matriz?.bairro || ''}
                              onChange={(e) => setFormData({
                                ...formData, 
                                endereco_matriz: {...formData.endereco_matriz, bairro: e.target.value}
                              })}
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Município</Label>
                            <Input
                              value={formData.endereco_matriz?.municipio || ''}
                              onChange={(e) => setFormData({
                                ...formData, 
                                endereco_matriz: {...formData.endereco_matriz, municipio: e.target.value}
                              })}
                            />
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>UF</Label>
                            <Input
                              value={formData.endereco_matriz?.uf || ''}
                              onChange={(e) => setFormData({
                                ...formData, 
                                endereco_matriz: {...formData.endereco_matriz, uf: e.target.value}
                              })}
                              maxLength={2}
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>País</Label>
                            <Input
                              value={formData.endereco_matriz?.pais || 'Brasil'}
                              onChange={(e) => setFormData({
                                ...formData, 
                                endereco_matriz: {...formData.endereco_matriz, pais: e.target.value}
                              })}
                            />
                          </div>
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
                      name="email_principal"
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

                {/* Equipment Information */}
                <div className="space-y-4">
                  <div className="flex items-center space-x-2 border-b pb-2">
                    <Monitor className="w-4 h-4" />
                    <h3 className="font-medium">Informações de Equipamento</h3>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Marca do Equipamento</Label>
                      <Input
                        value={formData.license_info?.equipment_brand || ''}
                        onChange={(e) => setFormData({
                          ...formData,
                          license_info: {
                            ...formData.license_info,
                            equipment_brand: e.target.value
                          }
                        })}
                        placeholder="Digite a marca do equipamento"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Modelo do Equipamento</Label>
                      <Input
                        value={formData.license_info?.equipment_model || ''}
                        onChange={(e) => setFormData({
                          ...formData,
                          license_info: {
                            ...formData.license_info,
                            equipment_model: e.target.value
                          }
                        })}
                        placeholder="Digite o modelo do equipamento"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>ID do Equipamento</Label>
                      <Input
                        value={formData.license_info?.equipment_id || ''}
                        onChange={(e) => setFormData({
                          ...formData,
                          license_info: {
                            ...formData.license_info,
                            equipment_id: e.target.value
                          }
                        })}
                        placeholder="Ex: EQ-001"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Número de Série</Label>
                      <Input
                        value={formData.license_info?.equipment_serial || ''}
                        onChange={(e) => setFormData({
                          ...formData,
                          license_info: {
                            ...formData.license_info,
                            equipment_serial: e.target.value
                          }
                        })}
                        placeholder="Ex: SN123456789"
                      />
                    </div>
                  </div>
                </div>

                {/* Seção de Dados Sensíveis - Apenas para Administradores */}
                {user?.role === 'admin' && (
                  <div className="space-y-4 border-l-4 border-red-200 pl-4">
                    <div className="flex items-center justify-between border-b pb-2">
                      <div className="flex items-center space-x-2">
                        <Shield className="w-4 h-4 text-red-600" />
                        <h3 className="font-medium text-red-700">Dados Sensíveis (Confidencial)</h3>
                        <Badge className="bg-red-50 text-red-700 border-red-200">
                          <Lock className="w-3 h-3 mr-1" />
                          Acesso Restrito
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 p-3 bg-red-50 rounded-md">
                      <div className="space-y-2">
                        <Label className="text-red-700">ID Interno do Equipamento</Label>
                        <Input
                          value={formData.sensitive_data?.internal_equipment_id || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            sensitive_data: {
                              ...formData.sensitive_data,
                              internal_equipment_id: e.target.value
                            }
                          })}
                          placeholder="ID confidencial interno"
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label className="text-red-700">Endereço MAC</Label>
                        <Input
                          value={formData.sensitive_data?.mac_address || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            sensitive_data: {
                              ...formData.sensitive_data,
                              mac_address: e.target.value
                            }
                          })}
                          placeholder="00:00:00:00:00:00"
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label className="text-red-700">Usuário Admin</Label>
                        <Input
                          value={formData.sensitive_data?.admin_username || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            sensitive_data: {
                              ...formData.sensitive_data,
                              admin_username: e.target.value
                            }
                          })}
                          placeholder="Usuário administrador"
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label className="text-red-700">Senha Admin</Label>
                        <Input
                          type="password"
                          value={formData.sensitive_data?.admin_password || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            sensitive_data: {
                              ...formData.sensitive_data,
                              admin_password: e.target.value
                            }
                          })}
                          placeholder="••••••••"
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label className="text-red-700">Senha WiFi</Label>
                        <Input
                          type="password"
                          value={formData.sensitive_data?.wifi_password || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            sensitive_data: {
                              ...formData.sensitive_data,
                              wifi_password: e.target.value
                            }
                          })}
                          placeholder="••••••••"
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label className="text-red-700">Chave de Hardware</Label>
                        <Input
                          value={formData.sensitive_data?.hardware_key || ''}
                          onChange={(e) => setFormData({
                            ...formData,
                            sensitive_data: {
                              ...formData.sensitive_data,
                              hardware_key: e.target.value
                            }
                          })}
                          placeholder="Chave de hardware"
                        />
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 p-2 bg-amber-50 border border-amber-200 rounded-md">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      <p className="text-xs text-amber-700">
                        <strong>Atenção:</strong> Dados sensíveis serão mascarados para usuários sem permissão adequada.
                        Use a referência de licença para suporte técnico.
                      </p>
                    </div>
                  </div>
                )}

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
            </form>
          </ScrollArea>
          
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
            <Button 
              type="submit" 
              onClick={showCreateDialog ? handleCreate : handleEdit}
            >
              <Save className="w-4 h-4 mr-2" />
              {showCreateDialog ? 'Criar Cliente' : 'Salvar Alterações'}
            </Button>
          </DialogFooter>
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
                  {getSemanticStatusBadge(viewingClient.status)}
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium text-gray-500">Criado em</Label>
                <p>{formatDate(viewingClient.created_at)}</p>
              </div>
              
              <Separator />
              
              {/* Seção de Dados Sensíveis */}
              <SensitiveDataSection 
                sensitiveData={viewingClient.sensitive_data}
                clientId={viewingClient.id}
                licenseReference={`LIC-${viewingClient.id?.substring(0, 8).toUpperCase() || 'UNKNOWN'}`}
              />
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