import React, { useState, useCallback } from 'react';
import { api } from '../api';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { 
  Upload, 
  FileSpreadsheet, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  RefreshCw,
  Download,
  Eye,
  Loader2,
  Info,
  ArrowRight,
  FileWarning
} from 'lucide-react';
import { toast } from 'sonner';

const DataImport = () => {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [importResult, setImportResult] = useState(null);
  const [showConflictsDialog, setShowConflictsDialog] = useState(false);
  const [importConflicts, setImportConflicts] = useState(false);

  // Drag and drop handlers
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.name.endsWith('.csv') || droppedFile.name.endsWith('.xlsx'))) {
      setFile(droppedFile);
      handlePreview(droppedFile);
    } else {
      toast.error('Por favor, selecione um arquivo CSV ou Excel (.xlsx)');
    }
  }, []);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      handlePreview(selectedFile);
    }
  };

  const handlePreview = async (fileToPreview) => {
    setIsUploading(true);
    setPreviewData(null);
    setImportResult(null);
    
    try {
      const formData = new FormData();
      formData.append('file', fileToPreview);
      
      const response = await api.post('/import/preview', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setPreviewData(response.data);
      
      if (response.data.conflicts > 0) {
        toast.warning(`${response.data.conflicts} conflitos detectados!`);
      } else {
        toast.success(`${response.data.new_records} registros prontos para importar`);
      }
    } catch (error) {
      console.error('Erro ao processar arquivo:', error);
      toast.error(error.response?.data?.detail || 'Erro ao processar arquivo');
    } finally {
      setIsUploading(false);
    }
  };

  const handleImport = async () => {
    if (!previewData) return;
    
    setIsImporting(true);
    
    try {
      // Preparar registros para importação
      const recordsToImport = [
        ...previewData.preview.new,
        ...(importConflicts ? previewData.preview.conflicts.map(c => c.new_data) : [])
      ];
      
      const response = await api.post('/import/execute', {
        records: recordsToImport,
        import_conflicts: importConflicts
      });
      
      setImportResult(response.data);
      toast.success(`Importação concluída! ${response.data.summary.imported} registros importados.`);
      
      // Limpar estado
      setPreviewData(null);
      setFile(null);
      
    } catch (error) {
      console.error('Erro na importação:', error);
      toast.error(error.response?.data?.detail || 'Erro ao importar dados');
    } finally {
      setIsImporting(false);
    }
  };

  const resetImport = () => {
    setFile(null);
    setPreviewData(null);
    setImportResult(null);
    setImportConflicts(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Importação de Dados</h1>
          <p className="text-gray-500">Importe licenças a partir de arquivos CSV ou Excel</p>
        </div>
        {(previewData || importResult) && (
          <Button variant="outline" onClick={resetImport}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Nova Importação
          </Button>
        )}
      </div>

      {/* Resultado da Importação */}
      {importResult && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-800">
              <CheckCircle className="w-5 h-5" />
              Importação Concluída
            </CardTitle>
            <CardDescription>Lote: {importResult.batch_id}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center p-4 bg-white rounded-lg">
                <div className="text-3xl font-bold text-blue-600">{importResult.summary.total}</div>
                <div className="text-sm text-gray-500">Total</div>
              </div>
              <div className="text-center p-4 bg-white rounded-lg">
                <div className="text-3xl font-bold text-green-600">{importResult.summary.imported}</div>
                <div className="text-sm text-gray-500">Importados</div>
              </div>
              <div className="text-center p-4 bg-white rounded-lg">
                <div className="text-3xl font-bold text-amber-600">{importResult.summary.updated}</div>
                <div className="text-sm text-gray-500">Atualizados</div>
              </div>
              <div className="text-center p-4 bg-white rounded-lg">
                <div className="text-3xl font-bold text-gray-600">{importResult.summary.skipped}</div>
                <div className="text-sm text-gray-500">Ignorados</div>
              </div>
            </div>
            
            {importResult.summary.errors > 0 && (
              <div className="mt-4 p-3 bg-red-100 rounded-lg">
                <div className="flex items-center gap-2 text-red-700">
                  <XCircle className="w-4 h-4" />
                  <span>{importResult.summary.errors} erros durante a importação</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Upload Area */}
      {!previewData && !importResult && (
        <Card>
          <CardContent className="pt-6">
            <div
              className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                isDragging 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {isUploading ? (
                <div className="flex flex-col items-center">
                  <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
                  <p className="text-gray-600">Processando arquivo...</p>
                </div>
              ) : (
                <>
                  <FileSpreadsheet className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Arraste seu arquivo aqui
                  </h3>
                  <p className="text-gray-500 mb-4">ou clique para selecionar</p>
                  <input
                    type="file"
                    accept=".csv,.xlsx"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload">
                    <Button asChild>
                      <span>
                        <Upload className="w-4 h-4 mr-2" />
                        Selecionar Arquivo
                      </span>
                    </Button>
                  </label>
                  <p className="text-xs text-gray-400 mt-4">
                    Formatos aceitos: CSV, Excel (.xlsx)
                  </p>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Preview dos Dados */}
      {previewData && !importResult && (
        <div className="space-y-4">
          {/* Resumo */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-blue-600" />
                Pré-visualização: {previewData.filename}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-3xl font-bold text-gray-900">{previewData.total_records}</div>
                  <div className="text-sm text-gray-500">Total de registros</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-3xl font-bold text-green-600">{previewData.new_records}</div>
                  <div className="text-sm text-gray-500">Novos registros</div>
                </div>
                <div className="text-center p-4 bg-amber-50 rounded-lg">
                  <div className="text-3xl font-bold text-amber-600">{previewData.conflicts}</div>
                  <div className="text-sm text-gray-500">Conflitos</div>
                </div>
              </div>

              {/* Barra de progresso visual */}
              <div className="mb-6">
                <div className="flex justify-between text-sm text-gray-500 mb-1">
                  <span>Novos ({previewData.new_records})</span>
                  <span>Conflitos ({previewData.conflicts})</span>
                </div>
                <div className="h-3 bg-gray-200 rounded-full overflow-hidden flex">
                  <div 
                    className="bg-green-500 transition-all"
                    style={{ width: `${(previewData.new_records / previewData.total_records) * 100}%` }}
                  />
                  <div 
                    className="bg-amber-500 transition-all"
                    style={{ width: `${(previewData.conflicts / previewData.total_records) * 100}%` }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tabela de Novos Registros */}
          {previewData.preview.new.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-700">
                  <CheckCircle className="w-5 h-5" />
                  Novos Registros ({previewData.new_records})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 px-3">Serial</th>
                        <th className="text-left py-2 px-3">Fabricante</th>
                        <th className="text-left py-2 px-3">Modelo</th>
                        <th className="text-left py-2 px-3">Data</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.preview.new.slice(0, 10).map((record, idx) => (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="py-2 px-3 font-mono">{record.serial}</td>
                          <td className="py-2 px-3">{record.manufacturer}</td>
                          <td className="py-2 px-3">{record.model}</td>
                          <td className="py-2 px-3">{record.added_date || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {previewData.new_records > 10 && (
                    <p className="text-center text-gray-500 py-2">
                      ... e mais {previewData.new_records - 10} registros
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Conflitos */}
          {previewData.preview.conflicts.length > 0 && (
            <Card className="border-amber-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-amber-700">
                  <AlertTriangle className="w-5 h-5" />
                  Conflitos Detectados ({previewData.conflicts})
                </CardTitle>
                <CardDescription>
                  Estes registros já existem no sistema. Revise antes de importar.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {previewData.preview.conflicts.slice(0, 5).map((conflict, idx) => (
                    <div key={idx} className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-mono font-medium text-amber-800">
                            Serial: {conflict.serial}
                          </div>
                          <div className="grid grid-cols-2 gap-4 mt-2 text-sm">
                            <div>
                              <div className="text-gray-500">Dados Existentes:</div>
                              <div>Fabricante: {conflict.existing_data.manufacturer || '-'}</div>
                              <div>Modelo: {conflict.existing_data.model || '-'}</div>
                            </div>
                            <div>
                              <div className="text-gray-500">Novos Dados:</div>
                              <div>Fabricante: {conflict.new_data.manufacturer || '-'}</div>
                              <div>Modelo: {conflict.new_data.model || '-'}</div>
                            </div>
                          </div>
                        </div>
                        <Badge variant="outline" className="bg-amber-100 text-amber-700">
                          <FileWarning className="w-3 h-3 mr-1" />
                          Conflito
                        </Badge>
                      </div>
                    </div>
                  ))}
                  {previewData.conflicts > 5 && (
                    <Button 
                      variant="outline" 
                      className="w-full"
                      onClick={() => setShowConflictsDialog(true)}
                    >
                      Ver todos os {previewData.conflicts} conflitos
                    </Button>
                  )}
                </div>

                {/* Opção de importar conflitos */}
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={importConflicts}
                      onChange={(e) => setImportConflicts(e.target.checked)}
                      className="w-4 h-4 rounded border-gray-300"
                    />
                    <div>
                      <div className="font-medium">Atualizar registros existentes</div>
                      <div className="text-sm text-gray-500">
                        Sobrescrever dados existentes com os novos valores
                      </div>
                    </div>
                  </label>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Botões de Ação */}
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={resetImport}>
              Cancelar
            </Button>
            <Button 
              onClick={handleImport}
              disabled={isImporting || (previewData.new_records === 0 && !importConflicts)}
              className="bg-green-600 hover:bg-green-700"
            >
              {isImporting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Importando...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Importar {importConflicts ? previewData.total_records : previewData.new_records} Registros
                </>
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Informações */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-2">Formato esperado do arquivo:</p>
              <ul className="list-disc list-inside space-y-1 text-blue-700">
                <li><strong>Manufacturer</strong> - Fabricante do equipamento</li>
                <li><strong>Model</strong> - Modelo do equipamento</li>
                <li><strong>Serial</strong> - Número de série (identificador único)</li>
                <li><strong>Added</strong> - Data de ativação (opcional)</li>
              </ul>
              <p className="mt-2 text-blue-600">
                O campo Serial é usado como chave única para detectar registros duplicados.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DataImport;
