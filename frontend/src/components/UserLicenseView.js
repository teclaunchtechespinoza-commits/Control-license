import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { LicenseStatusBadge } from './ui/semantic-badge';
import { api } from '../api';
import { 
  FileText, 
  Calendar, 
  User,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';

const UserLicenseView = () => {
  const { user } = useAuth();
  const [licenses, setLicenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchUserLicenses();
  }, []);

  const fetchUserLicenses = async () => {
    try {
      setLoading(true);
      setError(null);

      // Buscar licenças do usuário atual
      const response = await api.get('/user/licenses');
      setLicenses(response.data || []);

    } catch (error) {
      console.error('Erro ao buscar licenças:', error);
      setError('Erro ao carregar suas licenças. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'expired':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'expiring_soon':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('pt-BR');
    } catch {
      return 'Data inválida';
    }
  };

  const getDaysRemaining = (expiresAt) => {
    if (!expiresAt) return null;
    try {
      const today = new Date();
      const expiration = new Date(expiresAt);
      const diffTime = expiration - today;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return diffDays;
    } catch {
      return null;
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Cabeçalho */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <User className="h-6 w-6 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">Minhas Licenças</h1>
        </div>
        <p className="text-gray-600">
          Visualize o status e informações das suas licenças ativas
        </p>
      </div>

      {/* Informações do Usuário */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Informações do Usuário
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span className="text-sm font-medium text-gray-500">Nome:</span>
              <p className="text-lg text-gray-900">{user?.name || 'N/A'}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-500">Identificador:</span>
              <p className="text-lg text-gray-900">{user?.serial_number || user?.email || 'N/A'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Licenças */}
      {error ? (
        <Card>
          <CardContent className="text-center py-8">
            <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-600">{error}</p>
            <button 
              onClick={fetchUserLicenses}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Tentar Novamente
            </button>
          </CardContent>
        </Card>
      ) : licenses.length === 0 ? (
        <Card>
          <CardContent className="text-center py-8">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Nenhuma licença encontrada
            </h3>
            <p className="text-gray-600">
              Você não possui licenças registradas no momento.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {licenses.map((license) => {
            const daysRemaining = getDaysRemaining(license.expires_at);
            const isExpired = daysRemaining !== null && daysRemaining < 0;
            const isExpiringSoon = daysRemaining !== null && daysRemaining <= 30 && daysRemaining >= 0;

            return (
              <Card key={license.id} className="border-l-4 border-l-blue-500">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {getStatusIcon(license.status)}
                        {license.name || 'Licença sem nome'}
                      </CardTitle>
                      <CardDescription>
                        Produto: {license.product_name || 'N/A'}
                      </CardDescription>
                    </div>
                    <div className="text-right">
                      <LicenseStatusBadge status={license.status} />
                      {daysRemaining !== null && (
                        <div className="mt-2">
                          {isExpired ? (
                            <Badge variant="destructive">
                              Venceu há {Math.abs(daysRemaining)} dias
                            </Badge>
                          ) : isExpiringSoon ? (
                            <Badge variant="warning">
                              Vence em {daysRemaining} dias
                            </Badge>
                          ) : (
                            <Badge variant="success">
                              {daysRemaining} dias restantes
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                      <span className="text-sm font-medium text-gray-500">Data de Início:</span>
                      <p className="text-gray-900">{formatDate(license.created_at)}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-500">Data de Expiração:</span>
                      <p className={`font-medium ${isExpired ? 'text-red-600' : isExpiringSoon ? 'text-yellow-600' : 'text-green-600'}`}>
                        {formatDate(license.expires_at)}
                      </p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-500">Categoria:</span>
                      <p className="text-gray-900">{license.category_name || 'N/A'}</p>
                    </div>
                    {license.serial_number && (
                      <div>
                        <span className="text-sm font-medium text-gray-500">Número de Série:</span>
                        <p className="text-gray-900 font-mono">{license.serial_number}</p>
                      </div>
                    )}
                    {license.license_key && (
                      <div>
                        <span className="text-sm font-medium text-gray-500">Chave da Licença:</span>
                        <p className="text-gray-900 font-mono text-sm break-all">{license.license_key}</p>
                      </div>
                    )}
                    {license.value && (
                      <div>
                        <span className="text-sm font-medium text-gray-500">Valor:</span>
                        <p className="text-gray-900">R$ {license.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                      </div>
                    )}
                  </div>
                  
                  {license.description && (
                    <div className="mt-4 pt-4 border-t">
                      <span className="text-sm font-medium text-gray-500">Descrição:</span>
                      <p className="text-gray-900 mt-1">{license.description}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default UserLicenseView;