import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { LicenseStatusBadge } from './ui/semantic-badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from './ui/dialog';
import { api } from '../api';
import { 
  Search,
  FileText, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  Calendar,
  Key,
  Users,
  Eye
} from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';

const UserLicenses = () => {
  const { user } = useAuth();
  const [licenses, setLicenses] = useState([]);
  const [filteredLicenses, setFilteredLicenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [selectedLicense, setSelectedLicense] = useState(null);

  useEffect(() => {
    fetchLicenses();
  }, []);

  useEffect(() => {
    filterLicenses();
  }, [licenses, searchTerm, statusFilter]);

  const fetchLicenses = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/licenses');
      setLicenses(response.data);
    } catch (error) {
      console.error('Failed to fetch licenses:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterLicenses = () => {
    let filtered = [...licenses];

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(license => 
        license.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        license.license_key.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (license.description && license.description.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(license => license.status === statusFilter);
    }

    setFilteredLicenses(filtered);
  };

  const getSemanticStatusIcon = (status) => {
    // Ícones semânticos WCAG com cores acessíveis
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
    // Badge semântico WCAG para licenças de usuário
    return <LicenseStatusBadge status={status} size="sm" />;
  };

  const openDetailsDialog = (license) => {
    setSelectedLicense(license);
    setShowDetailsDialog(true);
  };

  const closeDetailsDialog = () => {
    setSelectedLicense(null);
    setShowDetailsDialog(false);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Sem data limite';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const isExpiringSoon = (dateString) => {
    if (!dateString) return false;
    const expiryDate = new Date(dateString);
    const today = new Date();
    const daysUntilExpiry = Math.ceil((expiryDate - today) / (1000 * 60 * 60 * 24));
    return daysUntilExpiry <= 30 && daysUntilExpiry > 0;
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // Could add toast notification here
  };

  if (loading) {
    return <LoadingSpinner message="Carregando suas licenças..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Minhas Licenças</h1>
        <p className="text-gray-600 mt-2">
          Visualize e gerencie todas as suas licenças atribuídas
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Buscar por nome, chave ou descrição..."
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
                  <SelectItem value="all">Todos os Status</SelectItem>
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

      {/* Licenses Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total</p>
                <p className="text-2xl font-bold">{licenses.length}</p>
              </div>
              <FileText className="w-8 h-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Ativas</p>
                <p className="text-2xl font-bold text-green-600">
                  {licenses.filter(l => l.status === 'active').length}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-600">Expiradas</p>
                <p className="text-2xl font-bold text-red-600">
                  {licenses.filter(l => l.status === 'expired').length}
                </p>
              </div>
              <XCircle className="w-8 h-8 text-red-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-600">Expirando</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {licenses.filter(l => isExpiringSoon(l.expires_at)).length}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-yellow-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Licenses Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="w-5 h-5" />
            <span>Lista de Licenças</span>
            <span className="text-sm font-normal text-gray-500">
              ({filteredLicenses.length} de {licenses.length})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredLicenses.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Nenhuma licença encontrada
              </h3>
              <p className="text-gray-500">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Tente ajustar os filtros de busca'
                  : 'Você ainda não possui licenças atribuídas'
                }
              </p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nome</TableHead>
                    <TableHead>Chave da Licença</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Máx. Usuários</TableHead>
                    <TableHead>Data de Criação</TableHead>
                    <TableHead>Data de Expiração</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLicenses.map((license) => (
                    <TableRow key={license.id}>
                      <TableCell>
                        <div>
                          <div className="flex items-center space-x-2">
                            {getSemanticStatusIcon(license.status)}
                            <span className="font-medium">{license.name}</span>
                            {isExpiringSoon(license.expires_at) && (
                              <Badge variant="outline" className="text-warning border-warning/50 bg-warning-light">
                                ⚠ Expirando
                              </Badge>
                            )}
                          </div>
                          {license.description && (
                            <p className="text-sm text-gray-500 mt-1">
                              {license.description}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                            {license.license_key}
                          </code>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => copyToClipboard(license.license_key)}
                            className="h-6 w-6 p-0"
                          >
                            <Key className="w-3 h-3" />
                          </Button>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getSemanticStatusBadge(license.status)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <Users className="w-4 h-4 text-gray-400" />
                          <span>{license.max_users}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1 text-sm text-gray-500">
                          <Calendar className="w-4 h-4" />
                          <span>{formatDate(license.created_at)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1 text-sm text-gray-500">
                          <Calendar className="w-4 h-4" />
                          <span className={isExpiringSoon(license.expires_at) ? 'text-yellow-600 font-medium' : ''}>
                            {formatDate(license.expires_at)}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => openDetailsDialog(license)}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          Detalhes
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Modal de Detalhes da Licença */}
      <Dialog open={showDetailsDialog} onOpenChange={setShowDetailsDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-blue-600" />
              <span>Detalhes da Licença</span>
            </DialogTitle>
            <DialogDescription>
              Informações completas e detalhadas da licença selecionada
            </DialogDescription>
          </DialogHeader>
          
          {selectedLicense && (
            <div className="grid gap-6 py-4">
              {/* Informações Básicas */}
              <div className="space-y-4">
                <div className="flex items-center space-x-2 border-b pb-2">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <h3 className="font-medium">Informações Básicas</h3>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Nome da Licença</label>
                    <p className="font-medium">{selectedLicense.name}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Status</label>
                    <div className="mt-1">
                      {getSemanticStatusBadge(selectedLicense.status)}
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-500">Descrição</label>
                  <p>{selectedLicense.description || 'Sem descrição'}</p>
                </div>
              </div>

              {/* Informações da Licença */}
              <div className="space-y-4">
                <div className="flex items-center space-x-2 border-b pb-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <h3 className="font-medium">Informações da Licença</h3>
                </div>
                
                <div className="grid grid-cols-1 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Chave da Licença</label>
                    <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded-md border">
                      <code className="font-mono text-sm">{selectedLicense.license_key}</code>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => navigator.clipboard.writeText(selectedLicense.license_key)}
                      >
                        Copiar
                      </Button>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Máximo de Usuários</label>
                      <p className="font-medium">{selectedLicense.max_users || 'Ilimitado'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Usuários Ativos</label>
                      <p className="font-medium">{selectedLicense.active_users || 0}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Datas Importantes */}
              <div className="space-y-4">
                <div className="flex items-center space-x-2 border-b pb-2">
                  <Calendar className="w-4 h-4 text-purple-600" />
                  <h3 className="font-medium">Datas Importantes</h3>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Data de Criação</label>
                    <p>{formatDate(selectedLicense.created_at)}</p>
                  </div>
                  {selectedLicense.expires_at && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Data de Expiração</label>
                      <div className="flex items-center space-x-2">
                        <p className={isExpiringSoon(selectedLicense.expires_at) ? 'text-warning font-medium' : ''}>
                          {formatDate(selectedLicense.expires_at)}
                        </p>
                        {isExpiringSoon(selectedLicense.expires_at) && (
                          <Badge variant="outline" className="text-warning border-warning/50 bg-warning-light">
                            ⚠ Expirando
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}
                </div>
                
                {selectedLicense.updated_at && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">Última Atualização</label>
                    <p>{formatDate(selectedLicense.updated_at)}</p>
                  </div>
                )}
              </div>

              {/* Informações Adicionais */}
              {(selectedLicense.metadata || selectedLicense.features) && (
                <div className="space-y-4">
                  <div className="flex items-center space-x-2 border-b pb-2">
                    <AlertTriangle className="w-4 h-4 text-orange-600" />
                    <h3 className="font-medium">Informações Adicionais</h3>
                  </div>
                  
                  {selectedLicense.features && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Recursos Incluídos</label>
                      <div className="mt-1 space-y-1">
                        {selectedLicense.features.map((feature, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <CheckCircle className="w-3 h-3 text-green-500" />
                            <span className="text-sm">{feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {selectedLicense.metadata && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Metadados</label>
                      <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                        {JSON.stringify(selectedLicense.metadata, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={closeDetailsDialog}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserLicenses;