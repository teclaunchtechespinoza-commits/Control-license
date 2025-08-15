import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { LicenseStatusBadge, StatusBadgeWithDot } from './ui/semantic-badge';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';
import axios from 'axios';
import { 
  Users, 
  FileText, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  TrendingUp,
  Calendar
} from 'lucide-react';
import { AdminVersionInfo } from './VersionControl';
import LoadingSpinner from './LoadingSpinner';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentLicenses, setRecentLicenses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch stats if admin
      if (user.role === 'admin') {
        const statsResponse = await axios.get('/stats');
        setStats(statsResponse.data);
      }
      
      // Fetch recent licenses
      const licensesResponse = await axios.get('/licenses');
      const sortedLicenses = licensesResponse.data.sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      );
      setRecentLicenses(sortedLicenses.slice(0, 5));
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSemanticStatusIcon = (status) => {
    // Ícones semânticos WCAG: nunca cor sozinha, sempre com contexto
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
    // Usa o novo sistema de badges semânticos WCAG
    return <LicenseStatusBadge status={status} size="default" />;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  if (loading) {
    return <LoadingSpinner message="Carregando dashboard..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Bem-vindo, {user.name}!
        </h1>
        <p className="text-gray-600 mt-2">
          {user.role === 'admin' 
            ? 'Visão geral do sistema de controle de licenças' 
            : 'Aqui estão suas informações de licenças'
          }
        </p>
      </div>

      {/* Admin Stats */}
      {user.role === 'admin' && stats && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Total de Licenças
                </CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_licenses}</div>
                <p className="text-xs text-muted-foreground">
                  Todas as licenças no sistema
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Licenças Ativas
                </CardTitle>
                <CheckCircle className="h-4 w-4 text-success" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-success">{stats.active_licenses}</div>
                <div className="text-xs text-muted-foreground flex items-center mt-1">
                  <Progress 
                    value={(stats.active_licenses / stats.total_licenses) * 100} 
                    className="w-20 h-2 mr-2"
                  />
                  {Math.round((stats.active_licenses / stats.total_licenses) * 100)}%
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Total de Usuários
                </CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_users}</div>
                <p className="text-xs text-muted-foreground">
                  Usuários registrados
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Licenças Expiradas
                </CardTitle>
                <XCircle className="h-4 w-4 text-danger" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-danger">{stats.expired_licenses}</div>
                <p className="text-xs text-muted-foreground">
                  Necessitam renovação
                </p>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {/* Recent Licenses */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5" />
            <span>
              {user.role === 'admin' ? 'Licenças Recentes' : 'Minhas Licenças'}
            </span>
          </CardTitle>
          <CardDescription>
            {user.role === 'admin' 
              ? 'Últimas licenças criadas no sistema'
              : 'Licenças atribuídas a você'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          {recentLicenses.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Nenhuma licença encontrada
              </h3>
              <p className="text-gray-500">
                {user.role === 'admin' 
                  ? 'Comece criando uma nova licença no painel administrativo'
                  : 'Você ainda não possui licenças atribuídas'
                }
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {recentLicenses.map((license, index) => (
                <div key={license.id}>
                  <div className="flex items-center justify-between p-4 rounded-lg border">
                    <div className="flex items-center space-x-4">
                      {getSemanticStatusIcon(license.status)}
                      <div>
                        <h4 className="font-medium text-gray-900">
                          {license.name}
                        </h4>
                        <p className="text-sm text-gray-500">
                          Chave: {license.license_key}
                        </p>
                        <div className="flex items-center space-x-2 mt-1">
                          <Calendar className="w-3 h-3 text-gray-400" />
                          <span className="text-xs text-gray-500">
                            Criado em {formatDate(license.created_at)}
                          </span>
                          {license.expires_at && (
                            <>
                              <span className="text-xs text-gray-300">•</span>
                              <span className="text-xs text-gray-500">
                                Expira em {formatDate(license.expires_at)}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {getSemanticStatusBadge(license.status)}
                      {license.max_users > 1 && (
                        <Badge variant="outline">
                          {license.max_users} usuários
                        </Badge>
                      )}
                    </div>
                  </div>
                  {index < recentLicenses.length - 1 && <Separator />}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions for Regular Users */}
      {user.role !== 'admin' && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Ações Rápidas</CardTitle>
            <CardDescription>
              Navegue rapidamente para as funcionalidades principais
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <h3 className="font-medium text-gray-900 mb-2">Ver Todas as Licenças</h3>
                <p className="text-sm text-gray-500">
                  Visualize todas as suas licenças atribuídas
                </p>
              </div>
              <div className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer opacity-75">
                <h3 className="font-medium text-gray-900 mb-2">Solicitar Suporte</h3>
                <p className="text-sm text-gray-500">
                  Entre em contato para ajuda com suas licenças
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;