import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  User, 
  Mail, 
  Building, 
  Calendar,
  Loader2,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';

const PendingApprovals = () => {
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [rejectDialog, setRejectDialog] = useState({ open: false, user: null });
  const [rejectReason, setRejectReason] = useState('');

  const fetchPendingUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/pending-registrations');
      setPendingUsers(response.data.registrations || []);
    } catch (error) {
      console.error('Erro ao buscar registros pendentes:', error);
      toast.error('Erro ao carregar registros pendentes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingUsers();
  }, []);

  const handleApprove = async (userId, email) => {
    try {
      setActionLoading(userId);
      await api.post(`/admin/registrations/${userId}/approve`);
      toast.success(`Registro de ${email} aprovado com sucesso!`);
      fetchPendingUsers();
    } catch (error) {
      console.error('Erro ao aprovar:', error);
      toast.error(error.response?.data?.detail || 'Erro ao aprovar registro');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async () => {
    if (!rejectDialog.user) return;
    
    try {
      setActionLoading(rejectDialog.user.id);
      await api.post(`/admin/registrations/${rejectDialog.user.id}/reject`, {
        action: 'reject',
        reason: rejectReason || 'Não informado'
      });
      toast.success(`Registro de ${rejectDialog.user.email} rejeitado.`);
      setRejectDialog({ open: false, user: null });
      setRejectReason('');
      fetchPendingUsers();
    } catch (error) {
      console.error('Erro ao rejeitar:', error);
      toast.error(error.response?.data?.detail || 'Erro ao rejeitar registro');
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-3 text-gray-500">Carregando registros pendentes...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-amber-500" />
              Registros Pendentes de Aprovação
            </CardTitle>
            <CardDescription>
              Gerencie as solicitações de novos usuários no sistema
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchPendingUsers}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </CardHeader>
        <CardContent>
          {pendingUsers.length === 0 ? (
            <div className="text-center py-12">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">Nenhum registro pendente</h3>
              <p className="text-gray-500 mt-1">Todos os registros foram processados.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingUsers.map((user) => (
                <div
                  key={user.id}
                  className="border rounded-lg p-4 bg-white hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
                          <User className="h-5 w-5 text-amber-600" />
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-900">{user.name}</h4>
                          <div className="flex items-center gap-1 text-sm text-gray-500">
                            <Mail className="h-3 w-3" />
                            {user.email}
                          </div>
                        </div>
                        <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                          <Clock className="h-3 w-3 mr-1" />
                          Pendente
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
                        <div className="flex items-center gap-2 text-gray-500">
                          <Building className="h-4 w-4" />
                          <span>{user.tenant_name || 'Novo Tenant'}</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-500">
                          <Calendar className="h-4 w-4" />
                          <span>{formatDate(user.created_at)}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex gap-2 ml-4">
                      <Button
                        size="sm"
                        className="bg-green-600 hover:bg-green-700"
                        onClick={() => handleApprove(user.id, user.email)}
                        disabled={actionLoading === user.id}
                      >
                        {actionLoading === user.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <>
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Aprovar
                          </>
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-red-600 border-red-200 hover:bg-red-50"
                        onClick={() => setRejectDialog({ open: true, user })}
                        disabled={actionLoading === user.id}
                      >
                        <XCircle className="h-4 w-4 mr-1" />
                        Rejeitar
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dialog de Rejeição */}
      <Dialog open={rejectDialog.open} onOpenChange={(open) => !open && setRejectDialog({ open: false, user: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              Rejeitar Registro
            </DialogTitle>
            <DialogDescription>
              Você está prestes a rejeitar o registro de <strong>{rejectDialog.user?.email}</strong>.
              Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="reject-reason">Motivo da rejeição (opcional)</Label>
              <Input
                id="reject-reason"
                placeholder="Ex: Dados incompletos, email suspeito..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRejectDialog({ open: false, user: null })}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={actionLoading === rejectDialog.user?.id}
            >
              {actionLoading === rejectDialog.user?.id ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <XCircle className="h-4 w-4 mr-2" />
              )}
              Confirmar Rejeição
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PendingApprovals;
