import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
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
  FileText, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  Calendar,
  Key,
  RefreshCw,
  MessageSquare,
  Headphones,
  Shield,
  Copy,
  Check
} from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';

/**
 * 🎯 UserLicenseView - Interface Unificada para Usuários
 * Visual limpo e profissional focado nas necessidades do usuário
 */
const UserLicenseView = () => {
  const { user } = useAuth();
  
  const [licenses, setLicenses] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLicense, setSelectedLicense] = useState(null);
  const [copiedKey, setCopiedKey] = useState(null);
  
  const [showRenewalModal, setShowRenewalModal] = useState(false);
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [supportMessage, setSupportMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [licensesRes, ticketsRes] = await Promise.all([
        api.get('/user/licenses').catch(() => ({ data: [] })),
        api.get('/tickets').catch(() => ({ data: [] }))
      ]);
      setLicenses(licensesRes.data || []);
      setTickets(ticketsRes.data || []);
    } catch (err) {
      console.error('Erro ao carregar dados:', err);
    } finally {
      setLoading(false);
    }
  };

  const getDaysRemaining = (expiresAt) => {
    if (!expiresAt) return null;
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffTime = expiry - now;
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const getStatusConfig = (status, daysRemaining) => {
    if (status === 'expired' || (daysRemaining !== null && daysRemaining <= 0)) {
      return { color: 'bg-red-100 text-red-700 border-red-200', icon: XCircle, label: 'Expirada' };
    }
    if (status === 'suspended') {
      return { color: 'bg-gray-100 text-gray-700 border-gray-200', icon: Clock, label: 'Suspensa' };
    }
    if (daysRemaining !== null && daysRemaining <= 30) {
      return { color: 'bg-yellow-100 text-yellow-700 border-yellow-200', icon: AlertTriangle, label: 'Expirando' };
    }
    if (status === 'active') {
      return { color: 'bg-green-100 text-green-700 border-green-200', icon: CheckCircle, label: 'Ativa' };
    }
    return { color: 'bg-blue-100 text-blue-700 border-blue-200', icon: Clock, label: 'Pendente' };
  };

  const copyLicenseKey = (key) => {
    navigator.clipboard.writeText(key);
    setCopiedKey(key);
    toast.success('Chave copiada!');
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleRenewalRequest = async () => {
    if (!selectedLicense) return;
    setSubmitting(true);
    try {
      await api.post('/tickets', {
        type: 'renewal',
        title: `Solicitação de Renovação - ${selectedLicense.name}`,
        description: `Solicito a renovação da licença: ${selectedLicense.name} (${selectedLicense.license_key})`,
        license_id: selectedLicense.id,
        priority: 'medium'
      });
      toast.success('Solicitação de renovação enviada!');
      setShowRenewalModal(false);
      setSelectedLicense(null);
      fetchData();
    } catch (err) {
      toast.error('Erro ao enviar solicitação');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSupportRequest = async () => {
    if (!supportMessage.trim()) {
      toast.error('Descreva sua dúvida ou problema');
      return;
    }
    setSubmitting(true);
    try {
      await api.post('/tickets', {
        type: 'support',
        title: 'Solicitação de Suporte',
        description: supportMessage,
        license_id: selectedLicense?.id || null,
        priority: 'medium'
      });
      toast.success('Solicitação de suporte enviada!');
      setShowSupportModal(false);
      setSupportMessage('');
      setSelectedLicense(null);
      fetchData();
    } catch (err) {
      toast.error('Erro ao enviar solicitação');
    } finally {
      setSubmitting(false);
    }
  };

  const stats = {
    total: licenses.length,
    active: licenses.filter(l => l.status === 'active').length,
    expiring: licenses.filter(l => {
      const days = getDaysRemaining(l.expires_at);
      return l.status === 'active' && days !== null && days <= 30 && days > 0;
    }).length,
    pendingTickets: tickets.filter(t => t.status === 'pending').length
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                Olá, {user?.name?.split(' ')[0] || 'Usuário'}!
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Gerencie suas licenças e solicite suporte
              </p>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                setSelectedLicense(null);
                setShowSupportModal(true);
              }}
            >
              <Headphones className="w-4 h-4 mr-2" />
              Suporte
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-6">
        {/* Cards de Resumo */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          <Card className="bg-white shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-50 rounded-lg">
                  <FileText className="w-4 h-4 text-blue-600" />
                </div>
                <div>
                  <p className="text-xl font-bold text-gray-900">{stats.total}</p>
                  <p className="text-xs text-gray-500">Total</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-50 rounded-lg">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
                <div>
                  <p className="text-xl font-bold text-green-600">{stats.active}</p>
                  <p className="text-xs text-gray-500">Ativas</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-50 rounded-lg">
                  <AlertTriangle className="w-4 h-4 text-yellow-600" />
                </div>
                <div>
                  <p className="text-xl font-bold text-yellow-600">{stats.expiring}</p>
                  <p className="text-xs text-gray-500">Expirando</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-50 rounded-lg">
                  <MessageSquare className="w-4 h-4 text-purple-600" />
                </div>
                <div>
                  <p className="text-xl font-bold text-purple-600">{stats.pendingTickets}</p>
                  <p className="text-xs text-gray-500">Solicitações</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Lista de Licenças */}
        <Card className="bg-white shadow-sm mb-6">
          <CardHeader className="border-b py-3 px-4">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Key className="w-4 h-4 text-gray-400" />
              Minhas Licenças
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {licenses.length === 0 ? (
              <div className="text-center py-10">
                <Shield className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500 text-sm">Nenhuma licença encontrada</p>
                <p className="text-xs text-gray-400 mt-1">
                  Entre em contato com seu administrador
                </p>
              </div>
            ) : (
              <div className="divide-y">
                {licenses.map((license) => {
                  const daysRemaining = getDaysRemaining(license.expires_at);
                  const statusConfig = getStatusConfig(license.status, daysRemaining);
                  const StatusIcon = statusConfig.icon;

                  return (
                    <div key={license.id} className="p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-medium text-gray-900 text-sm">
                              {license.name}
                            </h3>
                            <Badge className={`${statusConfig.color} border text-xs font-normal`}>
                              <StatusIcon className="w-3 h-3 mr-1" />
                              {statusConfig.label}
                            </Badge>
                          </div>
                          
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <div className="flex items-center gap-1">
                              <Key className="w-3 h-3" />
                              <code className="bg-gray-100 px-1.5 py-0.5 rounded">
                                {license.license_key}
                              </code>
                              <button
                                onClick={() => copyLicenseKey(license.license_key)}
                                className="p-0.5 hover:bg-gray-200 rounded"
                              >
                                {copiedKey === license.license_key ? (
                                  <Check className="w-3 h-3 text-green-600" />
                                ) : (
                                  <Copy className="w-3 h-3" />
                                )}
                              </button>
                            </div>
                            
                            {license.expires_at && (
                              <div className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {daysRemaining !== null && daysRemaining > 0 ? (
                                  <span><strong>{daysRemaining}</strong> dias restantes</span>
                                ) : daysRemaining === 0 ? (
                                  <span className="text-red-600 font-medium">Expira hoje!</span>
                                ) : (
                                  <span className="text-red-600">Expirou {formatDate(license.expires_at)}</span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-1">
                          {license.status === 'active' && daysRemaining !== null && daysRemaining <= 30 && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-yellow-600 border-yellow-300 hover:bg-yellow-50 text-xs h-7"
                              onClick={() => {
                                setSelectedLicense(license);
                                setShowRenewalModal(true);
                              }}
                            >
                              <RefreshCw className="w-3 h-3 mr-1" />
                              Renovar
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 w-7 p-0"
                            onClick={() => {
                              setSelectedLicense(license);
                              setShowSupportModal(true);
                            }}
                          >
                            <Headphones className="w-3 h-3" />
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

        {/* Solicitações */}
        {tickets.length > 0 && (
          <Card className="bg-white shadow-sm">
            <CardHeader className="border-b py-3 px-4">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-gray-400" />
                Minhas Solicitações
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y">
                {tickets.slice(0, 5).map((ticket) => (
                  <div key={ticket.id} className="p-3 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900 text-sm">{ticket.title}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {ticket.type === 'renewal' ? '🔄 Renovação' : '💬 Suporte'} • {formatDate(ticket.created_at)}
                      </p>
                    </div>
                    <Badge 
                      className={`text-xs ${
                        ticket.status === 'approved' ? 'bg-green-100 text-green-700' :
                        ticket.status === 'rejected' ? 'bg-red-100 text-red-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}
                    >
                      {ticket.status === 'approved' ? '✓ Aprovado' :
                       ticket.status === 'rejected' ? '✗ Recusado' :
                       '⏳ Pendente'}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Modal de Renovação */}
      <Dialog open={showRenewalModal} onOpenChange={setShowRenewalModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base">
              <RefreshCw className="w-4 h-4 text-yellow-600" />
              Solicitar Renovação
            </DialogTitle>
            <DialogDescription className="text-sm">
              Sua solicitação será enviada para aprovação.
            </DialogDescription>
          </DialogHeader>
          
          {selectedLicense && (
            <div className="py-3">
              <div className="bg-gray-50 rounded-lg p-3 mb-3">
                <p className="font-medium text-sm">{selectedLicense.name}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Chave: {selectedLicense.license_key}
                </p>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowRenewalModal(false)}>
              Cancelar
            </Button>
            <Button 
              size="sm"
              onClick={handleRenewalRequest} 
              disabled={submitting}
              className="bg-yellow-600 hover:bg-yellow-700"
            >
              {submitting ? 'Enviando...' : 'Confirmar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal de Suporte */}
      <Dialog open={showSupportModal} onOpenChange={setShowSupportModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base">
              <Headphones className="w-4 h-4 text-blue-600" />
              Solicitar Suporte
            </DialogTitle>
            <DialogDescription className="text-sm">
              Descreva sua dúvida ou problema.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-3">
            {selectedLicense && (
              <div className="bg-blue-50 rounded-lg p-2 text-xs text-blue-700 mb-3">
                Referente: <strong>{selectedLicense.name}</strong>
              </div>
            )}
            
            <Textarea
              placeholder="Descreva detalhadamente..."
              value={supportMessage}
              onChange={(e) => setSupportMessage(e.target.value)}
              rows={3}
              className="resize-none text-sm"
            />
          </div>

          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => {
              setShowSupportModal(false);
              setSupportMessage('');
            }}>
              Cancelar
            </Button>
            <Button 
              size="sm"
              onClick={handleSupportRequest} 
              disabled={submitting || !supportMessage.trim()}
            >
              {submitting ? 'Enviando...' : 'Enviar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserLicenseView;
