import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { SemanticBadge } from './ui/semantic-badge';
import { AlertTriangle, MessageCircle, Phone, Mail, TrendingUp, TrendingDown, Users, DollarSign, Calendar, Send, Loader2, RefreshCw } from 'lucide-react';

const SalesDashboard = () => {
    // Estados principais
    const [summary, setSummary] = useState(null);
    const [expiringLicenses, setExpiringLicenses] = useState([]);
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [refreshing, setRefreshing] = useState(false);
    
    // Estados para ações
    const [sendingWhatsApp, setSendingWhatsApp] = useState(new Set());
    const [selectedAlerts, setSelectedAlerts] = useState(new Set());

    // Configuração do backend
    const backendUrl = import.meta.env?.VITE_REACT_APP_BACKEND_URL || 
                      process.env?.REACT_APP_BACKEND_URL || 
                      'http://localhost:8001';

    // Função para buscar dados
    const fetchDashboardData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Usar API central que injeta Authorization + X-Tenant-ID automaticamente
            // Buscar resumo executivo
            const summaryResponse = await api.get('/sales-dashboard/summary');
            setSummary(summaryResponse.data);

            // Buscar licenças expirando (expandido para 90 dias para incluir mais licenças)
            const licensesResponse = await api.get('/sales-dashboard/expiring-licenses', { params: { days_ahead: 90 } });
            setExpiringLicenses(licensesResponse.data);

            // Buscar analytics
            const analyticsResponse = await api.get('/sales-dashboard/analytics', { params: { period_days: 30 } });
            setAnalytics(analyticsResponse.data);

        } catch (error) {
            console.error('Erro ao buscar dados do dashboard:', error);
            
            // Handle specific error cases
            if (error.response?.status === 403) {
                setError('Acesso negado: Você não tem permissão para acessar o dashboard de vendas. Entre em contato com o administrador.');
            } else if (error.response?.status === 401) {
                setError('Sessão expirada: Faça login novamente para acessar o dashboard.');
            } else {
                setError('Erro ao carregar dados do dashboard de vendas');
            }
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    // Carregar dados na inicialização
    useEffect(() => {
        fetchDashboardData();
    }, []);

    // Função para atualizar dados
    const handleRefresh = async () => {
        setRefreshing(true);
        await fetchDashboardData();
    };

    // Função para enviar WhatsApp individual
    const sendWhatsAppMessage = async (alertId) => {
        try {
            setSendingWhatsApp(prev => new Set(prev).add(alertId));

            const response = await api.post(`/sales-dashboard/send-whatsapp/${alertId}`, {});

            if (response.data) {
                // Mostrar sucesso
                alert(`WhatsApp enviado com sucesso!\nStatus: ${response.data.whatsapp_status}\nTipo: ${response.data.alert_type}`);
                
                // Atualizar lista de licenças
                await fetchDashboardData();
            }

        } catch (error) {
            console.error('Erro ao enviar WhatsApp:', error);
            alert('Erro ao enviar mensagem WhatsApp: ' + (error.response?.data?.detail || error.message));
        } finally {
            setSendingWhatsApp(prev => {
                const newSet = new Set(prev);
                newSet.delete(alertId);
                return newSet;
            });
        }
    };

    // Função para envio em lote
    const sendBulkWhatsApp = async () => {
        if (selectedAlerts.size === 0) {
            alert('Selecione ao menos um alerta para envio em lote');
            return;
        }

        try {
            setSendingWhatsApp(prev => new Set([...prev, 'bulk']));

            const response = await api.post('/sales-dashboard/bulk-whatsapp', { alert_ids: Array.from(selectedAlerts) });

            if (response.data) {
                alert(`Campanha concluída!\n${response.data.sent} enviadas\n${response.data.failed} falharam`);
                setSelectedAlerts(new Set());
                await fetchDashboardData();
            }

        } catch (error) {
            console.error('Erro no envio em lote:', error);
            alert('Erro no envio em lote: ' + (error.response?.data?.detail || error.message));
        } finally {
            setSendingWhatsApp(prev => {
                const newSet = new Set(prev);
                newSet.delete('bulk');
                return newSet;
            });
        }
    };

    // Função para alternar seleção de alertas
    const toggleAlertSelection = (alertId) => {
        setSelectedAlerts(prev => {
            const newSet = new Set(prev);
            if (newSet.has(alertId)) {
                newSet.delete(alertId);
            } else {
                newSet.add(alertId);
            }
            return newSet;
        });
    };

    // Função para obter cor da prioridade
    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'high': return 'bg-red-100 text-red-800';
            case 'medium': return 'bg-yellow-100 text-yellow-800';
            case 'low': return 'bg-green-100 text-green-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    // Função para obter cor dos dias restantes
    const getDaysColor = (days) => {
        if (days < 0) return 'text-red-600 font-bold';
        if (days <= 1) return 'text-red-500 font-bold';
        if (days <= 7) return 'text-orange-500 font-semibold';
        if (days <= 30) return 'text-yellow-600';
        return 'text-green-600';
    };

    if (loading && !refreshing) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                    <p className="text-gray-600">Carregando Dashboard de Vendas...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-red-600 mb-2">Erro ao Carregar Dashboard</h2>
                    <p className="text-gray-600 mb-4">{error}</p>
                    <button
                        onClick={fetchDashboardData}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        Tentar Novamente
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Dashboard de Vendas</h1>
                    <p className="text-gray-600 mt-1">Transforme alertas técnicos em oportunidades de vendas</p>
                </div>
                
                <div className="flex gap-3">
                    <button
                        onClick={handleRefresh}
                        disabled={refreshing}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50"
                    >
                        <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                        Atualizar
                    </button>
                    
                    {selectedAlerts.size > 0 && (
                        <button
                            onClick={sendBulkWhatsApp}
                            disabled={sendingWhatsApp.has('bulk')}
                            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                        >
                            <Send className="h-4 w-4" />
                            {sendingWhatsApp.has('bulk') ? 'Enviando...' : `Enviar WhatsApp (${selectedAlerts.size})`}
                        </button>
                    )}
                </div>
            </div>

            {/* Métricas Principais */}
            {summary?.metrics && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Licenças Expirando</CardTitle>
                            <AlertTriangle className="h-4 w-4 text-orange-500" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{summary.metrics.total_expiring_licenses || 0}</div>
                            <div className="flex gap-2 mt-2 text-sm text-gray-600">
                                <span>30d: {summary.metrics.licenses_expiring_30_days || 0}</span>
                                <span>7d: {summary.metrics.licenses_expiring_7_days || 0}</span>
                                <span>1d: {summary.metrics.licenses_expiring_1_day || 0}</span>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Taxa de Conversão</CardTitle>
                            <TrendingUp className="h-4 w-4 text-green-500" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{(summary.metrics.conversion_rate || 0).toFixed(1)}%</div>
                            <p className="text-xs text-gray-600 mt-1">
                                {summary.metrics.renewed_licenses || 0} renovações de {summary.metrics.contacted_leads || 0} contatos
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Receita Potencial</CardTitle>
                            <DollarSign className="h-4 w-4 text-blue-500" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">
                                R$ {(summary.metrics.potential_revenue || 0).toLocaleString('pt-BR')}
                            </div>
                            <p className="text-xs text-gray-600 mt-1">
                                Confirmado: R$ {(summary.metrics.confirmed_revenue || 0).toLocaleString('pt-BR')}
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Contatos WhatsApp</CardTitle>
                            <MessageCircle className="h-4 w-4 text-green-500" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{summary.metrics.whatsapp_contacts || 0}</div>
                            <div className="flex gap-2 mt-2 text-sm text-gray-600">
                                <span>📧 {summary.metrics.email_contacts || 0}</span>
                                <span>📞 {summary.metrics.phone_contacts || 0}</span>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Lista de Licenças Expirando */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Calendar className="h-5 w-5" />
                        Licenças Expirando - Oportunidades de Renovação
                    </CardTitle>
                    <CardDescription>
                        Licenças que precisam de atenção imediata dos vendedores
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {expiringLicenses.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
                            <p>Nenhuma licença expirando encontrada</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {expiringLicenses.slice(0, 20).map((license) => (
                                <div key={license.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                                    <div className="flex items-center gap-4">
                                        <input
                                            type="checkbox"
                                            checked={selectedAlerts.has(license.id)}
                                            onChange={() => toggleAlertSelection(license.id)}
                                            className="w-4 h-4 text-blue-600"
                                        />
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="font-semibold">{license.client_name}</span>
                                                <Badge className={getPriorityColor(license.priority)}>
                                                    {license.priority?.toUpperCase() || 'NORMAL'}
                                                </Badge>
                                                <SemanticBadge 
                                                    type={license.status === 'expired' ? 'error' : 'warning'}
                                                    label={license.alert_type || license.status}
                                                />
                                            </div>
                                            <p className="text-sm text-gray-600">{license.license_name}</p>
                                            <div className="flex items-center gap-4 mt-2 text-sm">
                                                <span className={getDaysColor(license.days_to_expire)}>
                                                    {license.days_to_expire < 0 
                                                        ? `Venceu há ${Math.abs(license.days_to_expire)} dias`
                                                        : license.days_to_expire === 0 
                                                        ? 'Vence hoje!'
                                                        : `${license.days_to_expire} dias restantes`}
                                                </span>
                                                {license.contact_phone && (
                                                    <span className="text-gray-500 flex items-center gap-1">
                                                        <MessageCircle className="h-3 w-3" />
                                                        {license.contact_phone}
                                                    </span>
                                                )}
                                                {license.renewal_opportunity_value && (
                                                    <span className="text-green-600 font-medium">
                                                        R$ {license.renewal_opportunity_value.toLocaleString('pt-BR')}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div className="flex items-center gap-2">
                                        {license.contact_attempts > 0 && (
                                            <Badge variant="outline">
                                                {license.contact_attempts} contatos
                                            </Badge>
                                        )}
                                        
                                        <button
                                            onClick={() => sendWhatsAppMessage(license.id)}
                                            disabled={sendingWhatsApp.has(license.id) || !license.contact_phone}
                                            className="flex items-center gap-2 px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                            title={!license.contact_phone ? 'Cliente sem WhatsApp cadastrado' : 'Enviar mensagem de renovação'}
                                        >
                                            {sendingWhatsApp.has(license.id) ? (
                                                <Loader2 className="h-3 w-3 animate-spin" />
                                            ) : (
                                                <MessageCircle className="h-3 w-3" />
                                            )}
                                            WhatsApp
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Analytics por Canal */}
            {analytics?.channel_metrics && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <MessageCircle className="h-5 w-5 text-green-500" />
                                WhatsApp
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                <div className="flex justify-between">
                                    <span className="text-sm text-gray-600">Contatos:</span>
                                    <span className="font-medium">{analytics.channel_metrics.whatsapp.contacts}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-gray-600">Respostas:</span>
                                    <span className="font-medium">{analytics.channel_metrics.whatsapp.responses}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-gray-600">Taxa de Resposta:</span>
                                    <span className="font-medium text-green-600">{analytics.channel_metrics.whatsapp.response_rate}%</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-gray-600">Conversões:</span>
                                    <span className="font-medium text-blue-600">{analytics.channel_metrics.whatsapp.conversions}</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Phone className="h-5 w-5 text-blue-500" />
                                Telefone
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                <div className="flex justify-between">
                                    <span className="text-sm text-gray-600">Contatos:</span>
                                    <span className="font-medium">{analytics.channel_metrics.phone.contacts}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-gray-600">Respostas:</span>
                                    <span className="font-medium">{analytics.channel_metrics.phone.responses}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-gray-600">Taxa de Resposta:</span>
                                    <span className="font-medium text-green-600">{analytics.channel_metrics.phone.response_rate}%</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-gray-600">Conversões:</span>
                                    <span className="font-medium text-blue-600">{analytics.channel_metrics.phone.conversions}</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Mail className="h-5 w-5 text-purple-500" />
                                Email
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                <div className="flex justify-between">
                                    <span className="text-sm text-gray-600">Contatos:</span>
                                    <span className="font-medium">{analytics.channel_metrics.email.contacts}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-gray-600">Respostas:</span>
                                    <span className="font-medium">{analytics.channel_metrics.email.responses}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-gray-600">Taxa de Resposta:</span>
                                    <span className="font-medium text-green-600">{analytics.channel_metrics.email.response_rate}%</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-sm text-gray-600">Conversões:</span>
                                    <span className="font-medium text-blue-600">{analytics.channel_metrics.email.conversions}</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Atividades Recentes */}
            {summary?.recent_activities && summary.recent_activities.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle>Atividades Recentes</CardTitle>
                        <CardDescription>Últimas ações da equipe de vendas</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {summary.recent_activities.map((activity, index) => (
                                <div key={activity.id || index} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                                    <div className="flex-shrink-0">
                                        {activity.type === 'whatsapp_sent' && <MessageCircle className="h-4 w-4 text-green-500" />}
                                        {activity.type === 'renewal_closed' && <DollarSign className="h-4 w-4 text-blue-500" />}
                                        {activity.type === 'follow_up' && <Phone className="h-4 w-4 text-orange-500" />}
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium">{activity.description}</p>
                                        <p className="text-xs text-gray-500">{activity.user} - {new Date(activity.timestamp).toLocaleString('pt-BR')}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};

export default SalesDashboard;