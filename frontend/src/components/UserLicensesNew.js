import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { LicenseStatusBadge } from './ui/semantic-badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
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
import { toast } from 'sonner';
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
  Eye,
  Download,
  RefreshCw,
  MessageSquare,
  Bell,
  Activity,
  TrendingUp,
  AlertCircle as AlertCircleIcon,
  HelpCircle
} from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';

const UserLicenses = () => {
  const { user } = useAuth();
  
  // Estados principais
  const [licenses, setLicenses] = useState([]);
  const [filteredLicenses, setFilteredLicenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Estados de filtros
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Estados de modais
  const [selectedLicense, setSelectedLicense] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showRenewalModal, setShowRenewalModal] = useState(false);
  const [showProblemModal, setShowProblemModal] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);
  
  // Estados de tickets
  const [renewalNotes, setRenewalNotes] = useState('');
  const [problemType, setProblemType] = useState('technical');
  const [problemDescription, setProblemDescription] = useState('');
  const [submittingTicket, setSubmittingTicket] = useState(false);
  
  // Estados de histórico e notificações
  const [activityLogs, setActivityLogs] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  
  // Estados de estatísticas
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    expiring: 0,
    expired: 0,
    nextExpiry: null
  });

  // Buscar dados ao carregar
  useEffect(() => {
    fetchAllData();
  }, []);

  // Filtrar licenças quando busca ou filtro mudam
  useEffect(() => {
    filterLicenses();
  }, [searchTerm, statusFilter, licenses]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchLicenses(),
        fetchActivityLogs(),
        fetchNotifications()
      ]);
    } catch (err) {
      console.error('Erro ao carregar dados:', err);
      setError('Erro ao carregar seus dados. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const fetchLicenses = async () => {
    try {
      const response = await api.get('/user/licenses');
      const licensesData = response.data || [];
      setLicenses(licensesData);
      calculateStats(licensesData);
    } catch (err) {
      console.error('Erro ao buscar licenças:', err);
      toast.error('Erro ao carregar suas licenças');
    }
  };

  const fetchActivityLogs = async () => {
    try {
      const response = await api.get('/activity-logs/my?limit=10');
      setActivityLogs(response.data || []);
    } catch (err) {
      console.error('Erro ao buscar logs:', err);
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
    } catch (err) {
      console.error('Erro ao buscar notificações:', err);
    }
  };

  const calculateStats = (licensesData) => {
    const now = new Date();
    const thirtyDaysFromNow = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
    
    const active = licensesData.filter(l => l.status === 'active').length;
    const expired = licensesData.filter(l => l.status === 'expired').length;
    const expiring = licensesData.filter(l => {
      if (l.status !== 'active') return false;
      const expiryDate = new Date(l.expires_at);
      return expiryDate <= thirtyDaysFromNow && expiryDate > now;
    }).length;

    // Encontrar próxima expiração
    const activeLicenses = licensesData.filter(l => l.status === 'active');
    let nextExpiry = null;
    if (activeLicenses.length > 0) {
      const sortedByExpiry = activeLicenses.sort((a, b) => 
        new Date(a.expires_at) - new Date(b.expires_at)
      );
      nextExpiry = sortedByExpiry[0]?.expires_at;
    }

    setStats({
      total: licensesData.length,
      active,
      expiring,
      expired,
      nextExpiry
    });
  };

  const filterLicenses = () => {
    let filtered = licenses;

    // Filtro de busca
    if (searchTerm) {
      filtered = filtered.filter(license =>
        (license.name?.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (license.serial_number?.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (license.id?.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Filtro de status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(license => license.status === statusFilter);
    }

    setFilteredLicenses(filtered);
  };

  const handleRequestRenewal = async () => {
    if (!selectedLicense) return;
    
    setSubmittingTicket(true);
    try {
      await api.post('/tickets', {
        type: 'renewal',
        title: `Renovação da Licença ${selectedLicense.name || selectedLicense.id}`,
        description: renewalNotes || `Solicitação de renovação da licença ${selectedLicense.serial_number || selectedLicense.id}`,
        priority: 'medium',
        license_id: selectedLicense.id
      });
      
      toast.success('Solicitação de renovação enviada com sucesso!');
      setShowRenewalModal(false);
      setRenewalNotes('');
      fetchActivityLogs();
      fetchNotifications();
    } catch (err) {
      console.error('Erro ao solicitar renovação:', err);
      toast.error('Erro ao enviar solicitação. Tente novamente.');
    } finally {
      setSubmittingTicket(false);
    }
  };

  const handleReportProblem = async () => {
    if (!selectedLicense) return;
    
    if (!problemDescription.trim()) {
      toast.error('Por favor, descreva o problema');
      return;
    }
    
    setSubmittingTicket(true);
    try {
      await api.post('/tickets', {
        type: 'problem',
        title: `Problema com Licença ${selectedLicense.name || selectedLicense.id}`,
        description: problemDescription,
        priority: problemType === 'urgent' ? 'high' : 'medium',
        license_id: selectedLicense.id
      });
      
      toast.success('Problema reportado com sucesso!');
      setShowProblemModal(false);
      setProblemDescription('');
      setProblemType('technical');
      fetchActivityLogs();
      fetchNotifications();
    } catch (err) {
      console.error('Erro ao reportar problema:', err);
      toast.error('Erro ao enviar reporte. Tente novamente.');
    } finally {
      setSubmittingTicket(false);
    }
  };

  const handleRequestHelp = async () => {
    const confirmed = window.confirm('Seu administrador será notificado sobre sua solicitação de ajuda. Deseja continuar?');
    
    if (!confirmed) {
      setShowHelpModal(false);
      return;
    }
    
    setSubmittingTicket(true);
    try {
      await api.post('/tickets', {
        type: 'support',
        title: 'Solicitação de Suporte',
        description: 'Preciso de ajuda com minhas licenças',
        priority: 'low'
      });
      
      toast.success('Solicitação enviada! Seu admin foi notificado.');
      setShowHelpModal(false);
      fetchActivityLogs();
      fetchNotifications();
    } catch (err) {
      console.error('Erro ao solicitar ajuda:', err);
      toast.error('Erro ao enviar solicitação. Tente novamente.');
    } finally {
      setSubmittingTicket(false);
    }
  };

  const getDaysUntilExpiry = (expiresAt) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffTime = expiry - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header com saudação */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg p-6 text-white shadow-lg">
        <h1 className="text-3xl font-bold mb-2">
          👋 Olá, {user?.name}!
        </h1>
        <p className="text-blue-100">
          {stats.total > 0 ? (
            <>
              Suas Licenças: <span className="font-semibold">{stats.active} ativas</span>
              {stats.expiring > 0 && (
                <>, <span className="font-semibold text-yellow-300">{stats.expiring} vencendo em 30 dias</span></>
              )}
              {stats.expired > 0 && (
                <>, <span className="font-semibold text-red-300">{stats.expired} expiradas</span></>
              )}
            </>
          ) : (
            'Você ainda não possui licenças'
          )}
        </p>
      </div>

      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total de Licenças</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold text-gray-900">{stats.total}</span>
              <FileText className="w-5 h-5 text-gray-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Licenças Ativas</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold text-green-600">{stats.active}</span>
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Vencendo em 30 dias</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold text-yellow-600">{stats.expiring}</span>
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Próximo Vencimento</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline space-x-2">
              {stats.nextExpiry ? (
                <>
                  <span className="text-xl font-bold text-gray-900">
                    {getDaysUntilExpiry(stats.nextExpiry)} dias
                  </span>
                  <Calendar className="w-5 h-5 text-gray-400" />
                </>
              ) : (
                <span className="text-sm text-gray-500">N/A</span>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alerta de vencimento próximo */}
      {stats.expiring > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start space-x-3">
          <AlertTriangle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-yellow-900">⚠️ Atenção: Licenças vencendo em breve</h3>
            <p className="text-yellow-700 mt-1">
              Você tem {stats.expiring} {stats.expiring === 1 ? 'licença que vence' : 'licenças que vencem'} nos próximos 30 dias.
            </p>
            <Button 
              variant="outline" 
              size="sm" 
              className="mt-2 border-yellow-600 text-yellow-700 hover:bg-yellow-100"
              onClick={() => setStatusFilter('active')}
            >
              Ver Detalhes
            </Button>
          </div>
        </div>
      )}

      {/* Barra de ações */}
      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <CardTitle>📋 Minhas Licenças</CardTitle>
            <div className="flex flex-col md:flex-row gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  type="text"
                  placeholder="Buscar licença..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 w-full md:w-64"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full md:w-48">
                  <SelectValue placeholder="Filtrar por status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  <SelectItem value="active">Ativas</SelectItem>
                  <SelectItem value="pending">Pendentes</SelectItem>
                  <SelectItem value="expired">Expiradas</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                onClick={() => setShowHelpModal(true)}
                className="flex items-center space-x-2"
              >
                <HelpCircle className="w-4 h-4" />
                <span>Preciso de Ajuda</span>
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredLicenses.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Nenhuma licença encontrada com esses filtros'
                  : 'Você ainda não possui licenças'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredLicenses.map((license) => {
                const daysUntilExpiry = getDaysUntilExpiry(license.expires_at);
                const isExpiringSoon = daysUntilExpiry <= 30 && daysUntilExpiry > 0;
                const isExpired = license.status === 'expired';

                return (
                  <div 
                    key={license.id}
                    className={`border rounded-lg p-4 transition-all hover:shadow-md ${
                      isExpired ? 'border-red-200 bg-red-50' : 
                      isExpiringSoon ? 'border-yellow-200 bg-yellow-50' : 
                      'border-gray-200 bg-white'
                    }`}
                  >
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="font-semibold text-lg text-gray-900">
                            {license.name || `Licença #${license.serial_number || license.id?.slice(0, 8)}`}
                          </h3>
                          <LicenseStatusBadge status={license.status} />
                        </div>
                        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                          <span className="flex items-center space-x-1">
                            <Key className="w-4 h-4" />
                            <span>{license.serial_number || 'N/A'}</span>
                          </span>
                          <span className="flex items-center space-x-1">
                            <Calendar className="w-4 h-4" />
                            <span>
                              {license.status === 'active' ? (
                                isExpiringSoon ? (
                                  <span className="text-yellow-700 font-medium">
                                    Vence em {daysUntilExpiry} dias ({formatDate(license.expires_at)})
                                  </span>
                                ) : (
                                  `Válida até ${formatDate(license.expires_at)}`
                                )
                              ) : license.status === 'expired' ? (
                                <span className="text-red-700 font-medium">
                                  Expirada desde {formatDate(license.expires_at)}
                                </span>
                              ) : (
                                `Validade: ${formatDate(license.expires_at)}`
                              )}
                            </span>
                          </span>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedLicense(license);
                            setShowDetailsModal(true);
                          }}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          Ver Detalhes
                        </Button>
                        
                        {license.status === 'active' && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              className="text-blue-600 border-blue-600 hover:bg-blue-50"
                            >
                              <Download className="w-4 h-4 mr-1" />
                              Certificado
                            </Button>
                            {isExpiringSoon && (
                              <Button
                                variant="default"
                                size="sm"
                                className="bg-yellow-600 hover:bg-yellow-700"
                                onClick={() => {
                                  setSelectedLicense(license);
                                  setShowRenewalModal(true);
                                }}
                              >
                                <RefreshCw className="w-4 h-4 mr-1" />
                                Solicitar Renovação
                              </Button>
                            )}
                          </>
                        )}
                        
                        {license.status === 'expired' && (
                          <Button
                            variant="default"
                            size="sm"
                            className="bg-red-600 hover:bg-red-700"
                            onClick={() => {
                              setSelectedLicense(license);
                              setShowRenewalModal(true);
                            }}
                          >
                            <RefreshCw className="w-4 h-4 mr-1" />
                            Renovar Urgente
                          </Button>
                        )}
                        
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-orange-600 border-orange-600 hover:bg-orange-50"
                          onClick={() => {
                            setSelectedLicense(license);
                            setShowProblemModal(true);
                          }}
                        >
                          <MessageSquare className="w-4 h-4 mr-1" />
                          Reportar Problema
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Histórico Recente */}
      {activityLogs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="w-5 h-5" />
              <span>📜 Histórico Recente</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {activityLogs.slice(0, 5).map((log) => (
                <div key={log.id} className="flex items-start space-x-3 text-sm">
                  <div className="flex-shrink-0 mt-1">
                    {log.activity_type === 'license_renewed' && <CheckCircle className="w-4 h-4 text-green-600" />}
                    {log.activity_type === 'ticket_created' && <Clock className="w-4 h-4 text-blue-600" />}
                    {log.activity_type === 'certificate_downloaded' && <Download className="w-4 h-4 text-purple-600" />}
                    {!['license_renewed', 'ticket_created', 'certificate_downloaded'].includes(log.activity_type) && (
                      <Activity className="w-4 h-4 text-gray-600" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-gray-700">{log.description}</p>
                    <p className="text-gray-400 text-xs mt-1">{formatDateTime(log.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Modal de Detalhes */}
      <Dialog open={showDetailsModal} onOpenChange={setShowDetailsModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Detalhes da Licença</DialogTitle>
          </DialogHeader>
          {selectedLicense && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">Nome</label>
                  <p className="text-gray-900">{selectedLicense.name || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Status</label>
                  <div className="mt-1">
                    <LicenseStatusBadge status={selectedLicense.status} />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Serial Number</label>
                  <p className="text-gray-900 font-mono">{selectedLicense.serial_number || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Validade</label>
                  <p className="text-gray-900">{formatDate(selectedLicense.expires_at)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Plano</label>
                  <p className="text-gray-900">{selectedLicense.plan_id || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Criada em</label>
                  <p className="text-gray-900">{formatDate(selectedLicense.created_at)}</p>
                </div>
              </div>
              {selectedLicense.description && (
                <div>
                  <label className="text-sm font-medium text-gray-600">Descrição</label>
                  <p className="text-gray-900 mt-1">{selectedLicense.description}</p>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailsModal(false)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal de Renovação */}
      <Dialog open={showRenewalModal} onOpenChange={setShowRenewalModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Solicitar Renovação de Licença</DialogTitle>
            <DialogDescription>
              Sua solicitação será enviada para aprovação do administrador.
            </DialogDescription>
          </DialogHeader>
          {selectedLicense && (
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="font-medium text-gray-900">
                  {selectedLicense.name || `Licença #${selectedLicense.id?.slice(0, 8)}`}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  Serial: {selectedLicense.serial_number || 'N/A'}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Observações (opcional)
                </label>
                <Textarea
                  value={renewalNotes}
                  onChange={(e) => setRenewalNotes(e.target.value)}
                  placeholder="Adicione informações adicionais sobre a renovação..."
                  rows={4}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRenewalModal(false)} disabled={submittingTicket}>
              Cancelar
            </Button>
            <Button onClick={handleRequestRenewal} disabled={submittingTicket}>
              {submittingTicket ? 'Enviando...' : 'Solicitar Renovação'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal de Reportar Problema */}
      <Dialog open={showProblemModal} onOpenChange={setShowProblemModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reportar Problema</DialogTitle>
            <DialogDescription>
              Descreva o problema e nosso suporte entrará em contato.
            </DialogDescription>
          </DialogHeader>
          {selectedLicense && (
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="font-medium text-gray-900">
                  {selectedLicense.name || `Licença #${selectedLicense.id?.slice(0, 8)}`}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo de Problema
                </label>
                <Select value={problemType} onValueChange={setProblemType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="technical">Problema Técnico</SelectItem>
                    <SelectItem value="billing">Faturamento</SelectItem>
                    <SelectItem value="access">Acesso</SelectItem>
                    <SelectItem value="urgent">Urgente</SelectItem>
                    <SelectItem value="other">Outro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Descrição do Problema *
                </label>
                <Textarea
                  value={problemDescription}
                  onChange={(e) => setProblemDescription(e.target.value)}
                  placeholder="Descreva o problema em detalhes..."
                  rows={5}
                  required
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowProblemModal(false)} disabled={submittingTicket}>
              Cancelar
            </Button>
            <Button onClick={handleReportProblem} disabled={submittingTicket || !problemDescription.trim()}>
              {submittingTicket ? 'Enviando...' : 'Enviar Reporte'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal de Ajuda */}
      <Dialog open={showHelpModal} onOpenChange={setShowHelpModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Precisa de Ajuda?</DialogTitle>
            <DialogDescription>
              Seu administrador será notificado sobre sua solicitação.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                💡 Ao confirmar, um ticket de suporte será criado e seu administrador receberá uma notificação para entrar em contato com você.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowHelpModal(false)} disabled={submittingTicket}>
              Cancelar
            </Button>
            <Button onClick={handleRequestHelp} disabled={submittingTicket}>
              {submittingTicket ? 'Enviando...' : 'Confirmar Solicitação'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserLicenses;
