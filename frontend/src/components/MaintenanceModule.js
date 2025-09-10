import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { SemanticBadge, CustomSemanticBadge } from './ui/semantic-badge';
import { 
  RefreshCw, 
  Trash2, 
  FileText, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Shield,
  Users,
  Key,
  Plus,
  Edit,
  UserPlus,
  Settings,
  Activity,
  TrendingUp,
  Database,
  Clock
} from 'lucide-react';
import { api } from '../api';
import { toast } from 'sonner';

const MaintenanceModule = () => {
  // Estados para logs
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [totalLines, setTotalLines] = useState(0);
  const [showingLines, setShowingLines] = useState(0);

  // Estados para RBAC
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [users, setUsers] = useState([]);
  const [rbacLoading, setRbacLoading] = useState(false);

  // Estados para logs avançados e monitoramento
  const [advancedLogs, setAdvancedLogs] = useState([]);
  const [logFilters, setLogFilters] = useState({
    level: '',
    category: '',
    limit: 50
  });
  const [systemHealth, setSystemHealth] = useState(null);
  const [logsLoading, setLogsLoading] = useState(false);

  // Função para carregar logs avançados
  const fetchAdvancedLogs = async () => {
    try {
      setLogsLoading(true);
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      const queryParams = new URLSearchParams();
      if (logFilters.level) queryParams.append('level', logFilters.level);
      if (logFilters.category) queryParams.append('category', logFilters.category);
      queryParams.append('limit', logFilters.limit.toString());
      
      const { data } = await api.get('/system/logs/advanced', { 
        params: Object.fromEntries(new URLSearchParams(queryParams))
      });
      
      setAdvancedLogs(data.logs || []);
      console.log('📊 Logs avançados carregados:', data);
    } catch (error) {
      console.error('Erro ao carregar logs avançados:', error);
      toast.error('Erro ao carregar logs avançados');
    } finally {
      setLogsLoading(false);
    }
  };

  // Função para verificar saúde do sistema
  const checkSystemHealth = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      const { data: health } = await api.get('/system/health-check');
      setSystemHealth(health);
        
      // Alertar sobre problemas críticos
      if (health.overall_status !== 'healthy') {
        toast.warning(
          `⚠️ Sistema com status: ${health.overall_status.toUpperCase()}`,
          {
            description: health.alerts?.join(', ') || 'Verifique os componentes',
            duration: 8000
          }
        );
      }
      
      console.log('💚 Health check realizado:', health);
    } catch (error) {
      console.error('Erro no health check:', error);
      toast.error('Erro ao verificar saúde do sistema');
    }
  };

  // Função para detectar erros em loop e alertar
  const detectLoopErrors = () => {
    if (advancedLogs.length === 0) return;
    
    // Detectar padrões de erro repetitivos
    const recentLogs = advancedLogs.slice(0, 10);
    const errorLogs = recentLogs.filter(log => log.level === 'ERROR' || log.level === 'CRITICAL');
    
    if (errorLogs.length >= 5) {
      // Mais de 5 erros nos últimos 10 logs - possível loop
      const errorMessages = errorLogs.map(log => log.message);
      const uniqueErrors = [...new Set(errorMessages)];
      
      if (uniqueErrors.length < errorMessages.length / 2) {
        // Muitos erros similares - provável loop
        toast.error(
          '🔄 LOOP DE ERRO DETECTADO!',
          {
            description: `${errorLogs.length} erros similares detectados. Verifique o sistema.`,
            action: {
              label: "Ver Detalhes",
              onClick: () => {
                console.error('🔄 Loop de erros detectado:', errorLogs);
                toast.info(`Erros repetitivos: ${uniqueErrors.join(', ')}`);
              }
            },
            duration: 10000
          }
        );
      }
    }
  };

  // Estados para painel de status
  const [statusStats, setStatusStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    totalRoles: 0,
    systemRoles: 0,
    totalPermissions: 0,
    recentActivity: []
  });

  // Estados para diálogos
  const [roleDialogOpen, setRoleDialogOpen] = useState(false);
  const [permissionDialogOpen, setPermissionDialogOpen] = useState(false);
  const [assignRoleDialogOpen, setAssignRoleDialogOpen] = useState(false);

  // Estados para formulários
  const [newRole, setNewRole] = useState({ name: '', description: '', permissions: [] });
  const [newPermission, setNewPermission] = useState({ 
    name: '', 
    description: '', 
    resource: '', 
    action: '' 
  });
  const [selectedUser, setSelectedUser] = useState('');
  const [selectedRoles, setSelectedRoles] = useState([]);

  // Funções para logs
  const fetchLogs = async () => {
    try {
      setLoading(true);
      const { data } = await api.get('/maintenance/logs', { params: { lines: 100 } });
      setLogs(data.logs);
      setTotalLines(data.total_lines);
      setShowingLines(data.showing);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      toast.error('Erro ao carregar logs de manutenção');
    } finally {
      setLoading(false);
    }
  };

  const clearLogs = async () => {
    try {
      setLoading(true);
      await api.post('/maintenance/clear-logs');
      toast.success('Logs limpos com sucesso');
      await fetchLogs();
    } catch (error) {
      console.error('Failed to clear logs:', error);
      toast.error('Erro ao limpar logs');
    } finally {
      setLoading(false);
    }
  };

  // Função para garantir URL correto (máscara)
  const getApiUrl = (endpoint) => {
    const backendUrl = process.env.REACT_APP_BACKEND_URL || window.location.origin;
    return `${backendUrl}/api/${endpoint}`;
  };

  // Função para diagnóstico direto do RBAC
  const testRbacDirect = async () => {
    try {
      console.log('=== TESTE DIRETO RBAC ===');
      
      const backendUrl = process.env.REACT_APP_BACKEND_URL || window.location.origin;
      console.log('Backend URL:', backendUrl);
      
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      console.log('Token existe:', !!token);
      console.log('Token preview:', token ? token.substring(0, 50) + '...' : 'NENHUM');
      
      if (!token) {
        toast.error('Token não encontrado - faça login primeiro');
        return;
      }

      // Teste direto com URL completo
      const testUrl = `${backendUrl}/api/rbac/roles`;
      console.log('Testando URL:', testUrl);
      
      const response = await api.get('/rbac/roles');
      
      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));
      
      if (response.ok) {
        const data = await response.json();
        console.log('Dados RBAC recebidos:', data);
        console.log('Tipo dos dados:', typeof data, Array.isArray(data));
        toast.success(`✅ RBAC FUNCIONANDO! ${Array.isArray(data) ? data.length : 'N/A'} roles encontradas`);
        
        // Tentar atualizar os dados diretamente
        if (Array.isArray(data)) {
          setRoles(data);
          console.log('Estados roles atualizados com sucesso');
        }
      } else {
        const errorText = await response.text();
        console.error('Erro na resposta:', response.status, errorText);
        toast.error(`❌ Erro RBAC: ${response.status} - ${errorText}`);
      }
      
    } catch (error) {
      console.error('Erro no teste direto:', error);
      console.error('Stack trace:', error.stack);
      toast.error(`❌ Erro de conexão: ${error.message}`);
    }
  };

  // Funções para RBAC
  const fetchRbacData = async () => {
    try {
      setRbacLoading(true);
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      // Verificação crítica: não fazer requisições sem token
      if (!token) {
        console.warn('No token available for RBAC data fetch');
        toast.error('Sessão não encontrada. Faça login novamente.');
        setRbacLoading(false);
        return;
      }
      
      console.log('Buscando dados RBAC com token válido...');
      console.log('Backend URL:', process.env.REACT_APP_BACKEND_URL);
      
      // Usar API central que injeta Authorization + X-Tenant-ID automaticamente
      const [rolesResponse, permissionsResponse, usersResponse] = await Promise.all([
        api.get('/rbac/roles'),
        api.get('/rbac/permissions'),
        api.get('/users')
      ]);

      const rolesData = rolesResponse.data;
      const permissionsData = permissionsResponse.data;
      const usersData = usersResponse.data;

      console.log('Dados RBAC carregados:', { 
        roles: rolesData.length, 
        permissions: permissionsData.length, 
        users: usersData.length 
      });

      setRoles(rolesData);
      setPermissions(permissionsData);
      setUsers(usersData);

      // Calcular estatísticas para o painel de status
      const stats = {
        totalUsers: (usersData || []).length,
        activeUsers: (usersData || []).filter(user => user.is_active).length,
        totalRoles: (rolesData || []).length,
        systemRoles: (rolesData || []).filter(role => role.is_system).length,
        totalPermissions: (permissionsData || []).length,
        recentActivity: [
          ...(rolesData || []).slice(-3).map(role => ({
            type: 'role_created',
            message: `Papel "${role.name}" criado`,
            timestamp: role.created_at,
            icon: '👑'
          })),
          ...(permissionsData || []).slice(-2).map(permission => ({
            type: 'permission_created', 
            message: `Permissão "${permission.name}" criada`,
            timestamp: permission.created_at,
            icon: '🔑'
          }))
        ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 5)
      };

      setStatusStats(stats);
    } catch (error) {
      console.error('Failed to fetch RBAC data:', error);
      toast.error('Erro ao carregar dados RBAC');
      
      // Limpar estados em caso de erro para evitar problemas de tipo
      setRoles([]);
      setPermissions([]);
      setUsers([]);
      setStatusStats({
        totalUsers: 0,
        activeUsers: 0,
        totalRoles: 0,
        systemRoles: 0,
        totalPermissions: 0,
        recentActivity: []
      });
    } finally {
      setRbacLoading(false);
    }
  };

  // Função para verificar duplicatas antes de criar role
  const checkRoleDuplicates = async (roleName) => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const { data: result } = await api.get('/system/check-duplicates/role');
      return result;
      }
      
      return { has_duplicates: false };
    } catch (error) {
      console.error('Erro ao verificar duplicatas:', error);
      return { has_duplicates: false };
    }
  };

  const createRole = async () => {
    try {
      // PASSO 1: Verificar duplicatas ANTES de tentar criar
      if (newRole.name.trim()) {
        console.log('🔍 Verificando duplicatas para role:', newRole.name);
        
        const duplicateCheck = await checkRoleDuplicates(newRole.name);
        
        if (duplicateCheck.has_duplicates) {
          const existing = duplicateCheck.existing_role;
          const systemWarning = existing.is_system ? ' (PAPEL DO SISTEMA)' : '';
          
          // Mostrar erro detalhado com sugestões
          toast.error(
            `❌ JÁ EXISTE: "${newRole.name}"${systemWarning}`,
            {
              description: `Papel já existe. ID: ${existing.id}`,
              action: {
                label: "Ver Sugestões",
                onClick: () => {
                  const suggestions = duplicateCheck.suggestions || [
                    `${newRole.name} v2`,
                    `${newRole.name} Custom`,
                    `${newRole.name} ${new Date().getFullYear()}`
                  ];
                  
                  toast.info(
                    "💡 Sugestões de nomes alternativos:",
                    {
                      description: suggestions.join(', '),
                      duration: 8000
                    }
                  );
                }
              },
              duration: 6000
            }
          );
          
          // NÃO prosseguir com a criação
          return;
        }
      }
      
      // PASSO 2: Prosseguir com criação se não houver duplicatas
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      const { data: createdRole } = await api.post('/rbac/roles', newRole);
        toast.success(
          `✅ Papel "${createdRole.name}" criado com sucesso!`,
          {
            description: `ID: ${createdRole.id}`,
            duration: 4000
          }
        );
        
        setRoleDialogOpen(false);
        setNewRole({ name: '', description: '', permissions: [] });
        await fetchRbacData();
      } else {
        const errorData = await response.json();
        
        // Tratar erro estruturado do backend
        if (errorData.detail && typeof errorData.detail === 'object') {
          const detail = errorData.detail;
          
          if (detail.type === 'DUPLICATE_ROLE') {
            toast.error(
              `❌ ${detail.message}`,
              {
                description: `Sugestões: ${detail.suggestions?.join(', ') || 'Tente um nome diferente'}`,
                duration: 6000
              }
            );
          } else {
            toast.error(`❌ Erro: ${detail.message || errorData.detail}`);
          }
        } else {
          toast.error(`❌ Erro ao criar papel: ${errorData.detail || 'Erro desconhecido'}`);
        }
      }
    } catch (error) {
      console.error('Erro na criação de papel:', error);
      toast.error(
        '❌ Erro de conexão ao criar papel',
        {
          description: 'Verifique sua conexão e tente novamente',
          duration: 4000
        }
      );
    }
  };

  const createPermission = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      await api.post('/rbac/permissions', newPermission);
      toast.success('Permissão criada com sucesso');
      setPermissionDialogOpen(false);
      setNewPermission({ name: '', description: '', resource: '', action: '' });
      await fetchRbacData();
    } catch (error) {
      console.error('Failed to create permission:', error);
      toast.error('Erro ao criar permissão');
    }
  };

  const assignRoles = async () => {
    try {
      const token = localStorage.getItem('access_token');
      await api.post('/rbac/assign-roles', {
        user_id: selectedUser,
        role_ids: selectedRoles
      });
      
      toast.success('Papéis atribuídos com sucesso');
      setAssignRoleDialogOpen(false);
      setSelectedUser('');
      setSelectedRoles([]);
      await fetchRbacData();
    } catch (error) {
      console.error('Failed to assign roles:', error);
      toast.error('Erro ao atribuir papéis');
    }
  };

  const deleteRole = async (roleId) => {
    try {
      const token = localStorage.getItem('access_token');
      await api.delete(`/rbac/roles/${roleId}`);
      
      toast.success('Papel excluído com sucesso');
      await fetchRbacData();
    } catch (error) {
      console.error('Failed to delete role:', error);
      toast.error('Erro ao excluir papel');
    }
  };

  const getRoleVariant = (role) => {
    if (role.name === 'Super Admin') return 'danger';
    if (role.name === 'Admin') return 'warning';
    if (role.name === 'Manager') return 'info';
    return 'neutral';
  };

  const getPermissionVariant = (permission) => {
    if (permission.action === 'manage' || permission.name === '*') return 'danger';
    if (permission.action === 'create' || permission.action === 'update') return 'warning';
    if (permission.action === 'read') return 'success';
    return 'info';
  };

  const getLogIcon = (line) => {
    if (line.includes('[ERROR]')) return <XCircle className="w-4 h-4 text-danger" aria-label="Erro crítico" />;
    if (line.includes('[INFO]')) return <CheckCircle className="w-4 h-4 text-success" aria-label="Informação" />;
    if (line.includes('[DEBUG]')) return <FileText className="w-4 h-4 text-info" aria-label="Debug" />;
    return <AlertTriangle className="w-4 h-4 text-warning" aria-label="Aviso" />;
  };

  const getLogColorClass = (line) => {
    if (line.includes('[ERROR]')) return 'text-danger bg-danger-light';
    if (line.includes('[INFO]')) return 'text-success bg-success-light';
    if (line.includes('[DEBUG]')) return 'text-info bg-info-light';
    return 'text-neutral bg-neutral-light';
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString('pt-BR');
  };

  useEffect(() => {
    fetchLogs();
    
    // Aguardar um pouco para garantir que a autenticação foi completada
    // antes de tentar carregar dados RBAC
    const timer = setTimeout(() => {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      if (token) {
        console.log('Inicializando carregamento de dados RBAC...');
        fetchRbacData();
      } else {
        console.log('Token não disponível no useEffect, aguardando autenticação...');
        // Tentar novamente após mais tempo
        setTimeout(() => {
          fetchRbacData();
        }, 2000);
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
          <Settings className="w-8 h-8 text-blue-600" />
          <span>Módulo de Manutenção</span>
        </h1>
        <p className="text-gray-600 mt-2">
          Sistema de logs e gerenciamento de permissões (RBAC)
        </p>
      </div>

      <Tabs defaultValue="logs" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="logs" className="flex items-center space-x-2">
            <FileText className="w-4 h-4" />
            <span>Logs do Sistema ({logs.length})</span>
          </TabsTrigger>
          <TabsTrigger value="rbac" className="flex items-center space-x-2">
            <Shield className="w-4 h-4" />
            <span>Controle de Acesso ({users.length} usuários)</span>
          </TabsTrigger>
          <TabsTrigger value="status" className="flex items-center space-x-2">
            <Activity className="w-4 h-4" />
            <span>Painel de Status</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab de Logs */}
        <TabsContent value="logs" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <FileText className="w-5 h-5" />
                  <span>Logs do Sistema</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    onClick={fetchLogs}
                    variant="outline"
                    size="sm"
                    disabled={loading}
                  >
                    <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                    Atualizar
                  </Button>
                  <Button
                    onClick={clearLogs}
                    variant="outline"
                    size="sm"
                    disabled={loading}
                    className="text-danger hover:bg-danger-light hover:border-danger/50"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Limpar Logs
                  </Button>
                </div>
              </CardTitle>
              <CardDescription>
                Mostrando {showingLines} de {totalLines} linhas de log
                {showingLines < totalLines && ` (últimas ${showingLines})`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto">
                {loading ? (
                  <div className="text-center text-gray-400 py-8">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                    Carregando logs...
                  </div>
                ) : logs.length === 0 ? (
                  <div className="text-center text-gray-400 py-8">
                    <FileText className="w-6 h-6 mx-auto mb-2" />
                    Nenhum log encontrado
                  </div>
                ) : (
                  <div className="space-y-1 font-mono text-sm">
                    {logs.map((line, index) => (
                      <div 
                        key={index} 
                        className={`p-2 rounded flex items-start space-x-2 ${getLogColorClass(line)}`}
                      >
                        {getLogIcon(line)}
                        <span className="flex-1 whitespace-pre-wrap break-all">
                          {line}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Estatísticas dos logs */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-success flex items-center space-x-2">
                  <CheckCircle className="w-5 h-5" />
                  <span>INFO</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {logs.filter(line => line.includes('[INFO]')).length}
                </p>
                <p className="text-sm text-gray-600">Operações bem-sucedidas</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-danger flex items-center space-x-2">
                  <XCircle className="w-5 h-5" />
                  <span>ERRO</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {logs.filter(line => line.includes('[ERROR]')).length}
                </p>
                <p className="text-sm text-gray-600">Erros encontrados</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-blue-600 flex items-center space-x-2">
                  <FileText className="w-5 h-5" />
                  <span>DEBUG</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {logs.filter(line => line.includes('[DEBUG]')).length}
                </p>
                <p className="text-sm text-gray-600">Informações de debug</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab de Painel de Status */}
        <TabsContent value="status" className="mt-6">
          <div className="space-y-6">
            
            {/* Estatísticas Gerais */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center justify-between text-sm font-medium">
                    <span>Usuários Totais</span>
                    <Users className="w-4 h-4 text-blue-600" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{statusStats.totalUsers}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {statusStats.activeUsers} ativos
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center justify-between text-sm font-medium">
                    <span>Papéis (Roles)</span>
                    <Shield className="w-4 h-4 text-purple-600" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{statusStats.totalRoles}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {statusStats.systemRoles} do sistema
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center justify-between text-sm font-medium">
                    <span>Permissões</span>
                    <Key className="w-4 h-4 text-green-600" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{statusStats.totalPermissions}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    configuradas
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center justify-between text-sm font-medium">
                    <span>Status Sistema</span>
                    <TrendingUp className="w-4 h-4 text-emerald-600" />
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center space-x-2">
                    <SemanticBadge
                      status="active"
                      customLabel="Operacional"
                      size="sm"
                    />
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    RBAC funcional
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Atividade Recente */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Clock className="w-5 h-5" />
                  <span>Atividade Recente RBAC</span>
                </CardTitle>
                <CardDescription>
                  Últimas alterações no sistema de controle de acesso
                </CardDescription>
              </CardHeader>
              <CardContent>
                {statusStats.recentActivity.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>Nenhuma atividade recente</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {statusStats.recentActivity.map((activity, index) => (
                      <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <span className="text-lg">{activity.icon}</span>
                        <div className="flex-1">
                          <p className="text-sm font-medium">{activity.message}</p>
                          <p className="text-xs text-gray-500">
                            {formatTimestamp(activity.timestamp)}
                          </p>
                        </div>
                        <CustomSemanticBadge
                          variant="info"
                          label={activity.type === 'role_created' ? 'Papel' : 'Permissão'}
                          icon={activity.type === 'role_created' ? '👑' : '🔑'}
                          size="sm"
                        />
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Resumo do Sistema */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Database className="w-5 h-5" />
                  <span>Resumo do Sistema RBAC</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center space-x-2">
                      <Shield className="w-4 h-4" />
                      <span>Papéis Ativos</span>
                    </h4>
                    <div className="space-y-2">
                      {(roles || []).slice(0, 5).map((role) => (
                        <div key={role.id} className="flex items-center justify-between text-sm">
                          <span>{role.name}</span>
                          <div className="flex items-center space-x-2">
                            <CustomSemanticBadge
                              variant={getRoleVariant(role)}
                              label={role.is_system ? 'Sistema' : 'Custom'}
                              icon={role.is_system ? '🛡' : '⚙'}
                              size="sm"
                            />
                            <span className="text-xs text-gray-500">
                              {role.permissions.length} perms
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center space-x-2">
                      <Users className="w-4 h-4" />
                      <span>Usuários Ativos</span>
                    </h4>
                    <div className="space-y-2">
                      {(users || []).slice(0, 5).map((user) => (
                        <div key={user.id} className="flex items-center justify-between text-sm">
                          <span>{user.name}</span>
                          <div className="flex items-center space-x-2">
                            <SemanticBadge
                              status={user.is_active ? 'active' : 'inactive'}
                              size="sm"
                            />
                            <span className="text-xs text-gray-500 capitalize">
                              {user.role || 'user'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

          </div>
        </TabsContent>

        {/* Tab de RBAC */}
        <TabsContent value="rbac" className="mt-6">
          <div className="space-y-6">
            
            {/* Seção de Papéis (Roles) */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Users className="w-5 h-5" />
                    <span>Gerenciamento de Papéis</span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button 
                      onClick={fetchRbacData} 
                      variant="outline" 
                      disabled={rbacLoading}
                      className="mb-4"
                    >
                      {rbacLoading ? (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          Carregando...
                        </>
                      ) : (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2" />
                          Atualizar Dados RBAC
                        </>
                      )}
                    </Button>
                    
                    <Button 
                      onClick={testRbacDirect} 
                      variant="destructive" 
                      size="sm"
                      className="mb-4 ml-2"
                    >
                      🔍 Diagnosticar RBAC
                    </Button>
                    
                    <Dialog open={roleDialogOpen} onOpenChange={setRoleDialogOpen}>
                      <DialogTrigger asChild>
                        <Button size="sm">
                          <Plus className="w-4 h-4 mr-2" />
                          Novo Papel
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Criar Novo Papel</DialogTitle>
                          <DialogDescription>
                            Defina um novo papel com suas permissões específicas.
                          </DialogDescription>
                        </DialogHeader>
                        
                        <div className="space-y-4">
                          <div>
                            <Label htmlFor="role-name">Nome do Papel</Label>
                            <Input
                              id="role-name"
                              value={newRole.name}
                              onChange={(e) => setNewRole({...newRole, name: e.target.value})}
                              placeholder="Ex: Editor, Supervisor"
                            />
                          </div>
                          
                          <div>
                            <Label htmlFor="role-description">Descrição</Label>
                            <Textarea
                              id="role-description"
                              value={newRole.description}
                              onChange={(e) => setNewRole({...newRole, description: e.target.value})}
                              placeholder="Descreva as responsabilidades deste papel"
                            />
                          </div>
                        </div>
                        
                        <DialogFooter>
                          <Button variant="outline" onClick={() => setRoleDialogOpen(false)}>
                            Cancelar
                          </Button>
                          <Button onClick={createRole}>
                            Criar Papel
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {rbacLoading ? (
                    <div className="text-center py-8">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                      Carregando papéis...
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {roles.map((role) => (
                        <Card key={role.id} className="border-l-4 border-l-blue-500">
                          <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                              <CardTitle className="text-lg flex items-center space-x-2">
                                <CustomSemanticBadge
                                  variant={getRoleVariant(role)}
                                  label={role.name}
                                  icon="♦"
                                  ariaLabel={`Papel: ${role.name}`}
                                  size="sm"
                                />
                              </CardTitle>
                              {!role.is_system && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => deleteRole(role.id)}
                                  className="text-danger hover:bg-danger-light"
                                >
                                  <Trash2 className="w-3 h-3" />
                                </Button>
                              )}
                            </div>
                            {role.is_system && (
                              <CustomSemanticBadge
                                variant="info"
                                label="Sistema"
                                icon="🛡"
                                ariaLabel="Papel do sistema - não editável"
                                size="sm"
                              />
                            )}
                          </CardHeader>
                          <CardContent>
                            <p className="text-sm text-gray-600 mb-3">{role.description}</p>
                            <div className="text-xs text-gray-500">
                              <span className="font-medium">{role.permissions.length}</span> permissões
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Seção de Permissões */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Key className="w-5 h-5" />
                    <span>Gerenciamento de Permissões</span>
                  </div>
                  
                  <Dialog open={permissionDialogOpen} onOpenChange={setPermissionDialogOpen}>
                    <DialogTrigger asChild>
                      <Button size="sm">
                        <Plus className="w-4 h-4 mr-2" />
                        Nova Permissão
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Criar Nova Permissão</DialogTitle>
                        <DialogDescription>
                          Defina uma nova permissão específica para recursos do sistema.
                        </DialogDescription>
                      </DialogHeader>
                      
                      <div className="space-y-4">
                        <div>
                          <Label htmlFor="perm-name">Nome da Permissão</Label>
                          <Input
                            id="perm-name"
                            value={newPermission.name}
                            onChange={(e) => setNewPermission({...newPermission, name: e.target.value})}
                            placeholder="Ex: clients.export, reports.advanced"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="perm-resource">Recurso</Label>
                          <Input
                            id="perm-resource"
                            value={newPermission.resource}
                            onChange={(e) => setNewPermission({...newPermission, resource: e.target.value})}
                            placeholder="Ex: clients, reports, licenses"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="perm-action">Ação</Label>
                          <Select value={newPermission.action} onValueChange={(value) => setNewPermission({...newPermission, action: value})}>
                            <SelectTrigger>
                              <SelectValue placeholder="Selecione uma ação" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="read">Read (Visualizar)</SelectItem>
                              <SelectItem value="create">Create (Criar)</SelectItem>
                              <SelectItem value="update">Update (Editar)</SelectItem>
                              <SelectItem value="delete">Delete (Excluir)</SelectItem>
                              <SelectItem value="manage">Manage (Gerenciar)</SelectItem>
                              <SelectItem value="export">Export (Exportar)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div>
                          <Label htmlFor="perm-description">Descrição</Label>
                          <Textarea
                            id="perm-description"
                            value={newPermission.description}
                            onChange={(e) => setNewPermission({...newPermission, description: e.target.value})}
                            placeholder="Descreva o que esta permissão permite fazer"
                          />
                        </div>
                      </div>
                      
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setPermissionDialogOpen(false)}>
                          Cancelar
                        </Button>
                        <Button onClick={createPermission}>
                          Criar Permissão
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {permissions.map((permission) => (
                    <div key={permission.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <CustomSemanticBadge
                          variant={getPermissionVariant(permission)}
                          label={permission.action}
                          icon="🔑"
                          ariaLabel={`Ação: ${permission.action}`}
                          size="sm"
                        />
                        <div>
                          <p className="font-medium text-sm">{permission.name}</p>
                          <p className="text-xs text-gray-500">{permission.description}</p>
                        </div>
                      </div>
                      <div className="text-xs text-gray-400 font-mono">
                        {permission.resource}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Seção de Atribuição de Papéis */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <UserPlus className="w-5 h-5" />
                    <span>Atribuir Papéis aos Usuários</span>
                  </div>
                  
                  <Dialog open={assignRoleDialogOpen} onOpenChange={setAssignRoleDialogOpen}>
                    <DialogTrigger asChild>
                      <Button size="sm">
                        <UserPlus className="w-4 h-4 mr-2" />
                        Atribuir Papéis
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Atribuir Papéis ao Usuário</DialogTitle>
                        <DialogDescription>
                          Selecione um usuário e os papéis que deseja atribuir.
                        </DialogDescription>
                      </DialogHeader>
                      
                      <div className="space-y-4">
                        <div>
                          <Label>Usuário</Label>
                          <Select value={selectedUser} onValueChange={setSelectedUser}>
                            <SelectTrigger>
                              <SelectValue placeholder="Selecione um usuário" />
                            </SelectTrigger>
                            <SelectContent>
                              {users.map((user) => (
                                <SelectItem key={user.id} value={user.id}>
                                  {user.name} ({user.email})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setAssignRoleDialogOpen(false)}>
                          Cancelar
                        </Button>
                        <Button onClick={assignRoles} disabled={!selectedUser}>
                          Atribuir Papéis
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {users.map((user) => (
                    <Card key={user.id} className="bg-gray-50">
                      <CardContent className="pt-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">{user.name}</p>
                            <p className="text-sm text-gray-600">{user.email}</p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <SemanticBadge
                              status={user.is_active ? 'active' : 'inactive'}
                              customLabel={user.is_active ? 'Ativo' : 'Inativo'}
                              size="sm"
                            />
                            <CustomSemanticBadge
                              variant="info"
                              label={user.role || 'user'}
                              icon="👤"
                              ariaLabel={`Papel atual: ${user.role || 'user'}`}
                              size="sm"
                            />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>

          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MaintenanceModule;