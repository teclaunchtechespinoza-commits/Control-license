import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { 
  RefreshCw, 
  Trash2, 
  FileText, 
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const MaintenanceModule = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [totalLines, setTotalLines] = useState(0);
  const [showingLines, setShowingLines] = useState(0);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/maintenance/logs?lines=100');
      setLogs(response.data.logs);
      setTotalLines(response.data.total_lines);
      setShowingLines(response.data.showing);
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
      await axios.post('/maintenance/clear-logs');
      toast.success('Logs limpos com sucesso');
      await fetchLogs();
    } catch (error) {
      console.error('Failed to clear logs:', error);
      toast.error('Erro ao limpar logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const getLogIcon = (line) => {
    if (line.includes('[ERROR]')) return <XCircle className="w-4 h-4 text-red-500" />;
    if (line.includes('[INFO]')) return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (line.includes('[DEBUG]')) return <FileText className="w-4 h-4 text-blue-500" />;
    return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
  };

  const getLogColorClass = (line) => {
    if (line.includes('[ERROR]')) return 'text-red-600 bg-red-50';
    if (line.includes('[INFO]')) return 'text-green-600 bg-green-50';
    if (line.includes('[DEBUG]')) return 'text-blue-600 bg-blue-50';
    return 'text-gray-600 bg-gray-50';
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
          <FileText className="w-8 h-8 text-blue-600" />
          <span>Módulo de Manutenção</span>
        </h1>
        <p className="text-gray-600 mt-2">
          Monitor de logs do sistema para identificar falhas e problemas
        </p>
      </div>

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
                className="text-red-600 hover:bg-red-50"
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

      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-green-600 flex items-center space-x-2">
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
            <CardTitle className="text-red-600 flex items-center space-x-2">
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
    </div>
  );
};

export default MaintenanceModule;