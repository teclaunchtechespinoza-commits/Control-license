import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../../App';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { toast } from 'sonner';
import {
  Upload,
  Image,
  FileText,
  ListOrdered,
  Save,
  RotateCcw,
  Plus,
  Trash2,
  GripVertical,
  Eye,
  Download,
  Settings,
  ChevronUp,
  ChevronDown,
  X
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function CertificateSettingsPage() {
  const { user, tenantId } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState(null);
  const [activeTab, setActiveTab] = useState('logo');
  const fileInputRef = useRef(null);
  const stepImageInputRef = useRef(null);
  const [editingStepId, setEditingStepId] = useState(null);

  const fetchSettings = useCallback(async () => {
    try {
      const response = await fetch(`${API}/api/certificate-settings`, {
        credentials: 'include',
        headers: {
          'X-Tenant-ID': tenantId || 'default'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSettings(data.settings);
      } else {
        toast.error('Erro ao carregar configurações');
      }
    } catch (error) {
      console.error('Erro:', error);
      toast.error('Erro de conexão');
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  // Upload de Logo
  const handleLogoUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validar tipo
    if (!file.type.match(/image\/(png|jpeg|jpg|svg\+xml)/)) {
      toast.error('Formato inválido. Use PNG, JPG ou SVG.');
      return;
    }

    // Validar tamanho (5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Arquivo muito grande. Máximo 5MB.');
      return;
    }

    setSaving(true);
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64 = e.target?.result;
        
        const response = await fetch(`${API}/api/certificate-settings/logo`, {
          method: 'PUT',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'X-Tenant-ID': tenantId || 'default'
          },
          body: JSON.stringify({
            logo_base64: base64,
            logo_filename: file.name,
            company_name: settings?.company_name
          })
        });

        if (response.ok) {
          toast.success('Logo atualizado com sucesso!');
          fetchSettings();
        } else {
          toast.error('Erro ao atualizar logo');
        }
        setSaving(false);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Erro:', error);
      toast.error('Erro ao fazer upload');
      setSaving(false);
    }
  };

  const handleRemoveLogo = async () => {
    if (!window.confirm('Remover logo customizado?')) return;
    
    setSaving(true);
    try {
      const response = await fetch(`${API}/api/certificate-settings/logo`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'X-Tenant-ID': tenantId || 'default'
        }
      });

      if (response.ok) {
        toast.success('Logo removido');
        fetchSettings();
      }
    } catch (error) {
      toast.error('Erro ao remover logo');
    } finally {
      setSaving(false);
    }
  };

  // Atualizar Termos
  const handleSaveTerms = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API}/api/certificate-settings/terms`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-ID': tenantId || 'default'
        },
        body: JSON.stringify({
          introduction: settings.terms?.introduction,
          sections: settings.terms?.sections
        })
      });

      if (response.ok) {
        toast.success('Termos salvos com sucesso!');
      } else {
        toast.error('Erro ao salvar termos');
      }
    } catch (error) {
      toast.error('Erro de conexão');
    } finally {
      setSaving(false);
    }
  };

  const handleResetTerms = async () => {
    if (!window.confirm('Restaurar termos padrão? Isso substituirá os termos atuais.')) return;
    
    setSaving(true);
    try {
      const response = await fetch(`${API}/api/certificate-settings/terms/reset`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'X-Tenant-ID': tenantId || 'default'
        }
      });

      if (response.ok) {
        toast.success('Termos restaurados ao padrão');
        fetchSettings();
      }
    } catch (error) {
      toast.error('Erro ao restaurar termos');
    } finally {
      setSaving(false);
    }
  };

  // Procedimento Steps
  const handleAddStep = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API}/api/certificate-settings/procedure-steps`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-ID': tenantId || 'default'
        },
        body: JSON.stringify({
          title: 'Novo Passo',
          description: 'Descreva as instruções deste passo...'
        })
      });

      if (response.ok) {
        toast.success('Passo adicionado');
        fetchSettings();
      }
    } catch (error) {
      toast.error('Erro ao adicionar passo');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateStep = async (stepId, data) => {
    try {
      const response = await fetch(`${API}/api/certificate-settings/procedure-steps/${stepId}`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-ID': tenantId || 'default'
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        toast.success('Passo atualizado');
        fetchSettings();
      }
    } catch (error) {
      toast.error('Erro ao atualizar passo');
    }
  };

  const handleDeleteStep = async (stepId) => {
    if (!window.confirm('Remover este passo?')) return;
    
    try {
      const response = await fetch(`${API}/api/certificate-settings/procedure-steps/${stepId}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'X-Tenant-ID': tenantId || 'default'
        }
      });

      if (response.ok) {
        toast.success('Passo removido');
        fetchSettings();
      }
    } catch (error) {
      toast.error('Erro ao remover passo');
    }
  };

  const handleStepImageUpload = async (stepId, event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.match(/image\/(png|jpeg|jpg)/)) {
      toast.error('Use PNG ou JPG para screenshots');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      toast.error('Máximo 2MB por screenshot');
      return;
    }

    const reader = new FileReader();
    reader.onload = async (e) => {
      await handleUpdateStep(stepId, {
        screenshot_base64: e.target?.result,
        screenshot_filename: file.name
      });
    };
    reader.readAsDataURL(file);
  };

  const handleMoveStep = async (stepId, direction) => {
    const steps = settings?.procedure_steps || [];
    const index = steps.findIndex(s => s.id === stepId);
    if (index === -1) return;
    
    const newOrder = direction === 'up' ? steps[index].order - 1 : steps[index].order + 1;
    if (newOrder < 1 || newOrder > steps.length) return;
    
    await handleUpdateStep(stepId, { order: newOrder });
  };

  const handleResetSteps = async () => {
    if (!window.confirm('Restaurar passos padrão? Isso substituirá os passos atuais.')) return;
    
    setSaving(true);
    try {
      const response = await fetch(`${API}/api/certificate-settings/procedure-steps/reset`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'X-Tenant-ID': tenantId || 'default'
        }
      });

      if (response.ok) {
        toast.success('Passos restaurados ao padrão');
        fetchSettings();
      }
    } catch (error) {
      toast.error('Erro ao restaurar passos');
    } finally {
      setSaving(false);
    }
  };

  // Informações Importantes
  const handleSaveImportantInfo = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API}/api/certificate-settings/important-info`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-ID': tenantId || 'default'
        },
        body: JSON.stringify({
          items: settings.important_info || []
        })
      });

      if (response.ok) {
        toast.success('Informações salvas!');
      }
    } catch (error) {
      toast.error('Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  // Helpers para edição local
  const updateLocalSettings = (path, value) => {
    setSettings(prev => {
      const newSettings = { ...prev };
      const keys = path.split('.');
      let obj = newSettings;
      for (let i = 0; i < keys.length - 1; i++) {
        obj = obj[keys[i]];
      }
      obj[keys[keys.length - 1]] = value;
      return newSettings;
    });
  };

  const updateTermSection = (index, field, value) => {
    setSettings(prev => {
      const newSettings = { ...prev };
      if (!newSettings.terms) newSettings.terms = { sections: [] };
      if (!newSettings.terms.sections) newSettings.terms.sections = [];
      if (!newSettings.terms.sections[index]) newSettings.terms.sections[index] = {};
      newSettings.terms.sections[index][field] = value;
      return newSettings;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto" data-testid="certificate-settings-page">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6 text-green-500" />
          Configurações de Certificado
        </h1>
        <p className="text-gray-400 mt-1">
          Personalize o layout, termos e procedimento dos seus certificados digitais
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-gray-800 mb-6">
          <TabsTrigger value="logo" className="data-[state=active]:bg-green-600">
            <Image className="w-4 h-4 mr-2" />
            Logo & Marca
          </TabsTrigger>
          <TabsTrigger value="terms" className="data-[state=active]:bg-green-600">
            <FileText className="w-4 h-4 mr-2" />
            Termos
          </TabsTrigger>
          <TabsTrigger value="procedure" className="data-[state=active]:bg-green-600">
            <ListOrdered className="w-4 h-4 mr-2" />
            Procedimento
          </TabsTrigger>
        </TabsList>

        {/* TAB: Logo & Marca */}
        <TabsContent value="logo">
          <Card className="bg-gray-900 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Logo da Empresa</CardTitle>
              <CardDescription>
                O logo aparecerá no cabeçalho de todos os certificados gerados
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Preview do Logo */}
              <div className="flex items-center gap-6">
                <div className="w-40 h-24 bg-gray-800 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-600">
                  {settings?.logo_base64 ? (
                    <img 
                      src={settings.logo_base64} 
                      alt="Logo" 
                      className="max-w-full max-h-full object-contain"
                    />
                  ) : (
                    <div className="text-center">
                      <Image className="w-8 h-8 text-gray-500 mx-auto mb-2" />
                      <span className="text-xs text-gray-500">Sem logo</span>
                    </div>
                  )}
                </div>
                
                <div className="flex flex-col gap-2">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleLogoUpload}
                    accept="image/png,image/jpeg,image/svg+xml"
                    className="hidden"
                  />
                  <Button 
                    onClick={() => fileInputRef.current?.click()}
                    disabled={saving}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    {settings?.logo_base64 ? 'Trocar Logo' : 'Fazer Upload'}
                  </Button>
                  {settings?.logo_base64 && (
                    <Button 
                      variant="outline"
                      onClick={handleRemoveLogo}
                      disabled={saving}
                      className="border-red-500 text-red-500 hover:bg-red-500/10"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Remover
                    </Button>
                  )}
                </div>
              </div>

              <div className="text-xs text-gray-500">
                Formatos: PNG, JPG, SVG • Tamanho máximo: 5MB • Recomendado: fundo transparente
              </div>

              {/* Nome da Empresa */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-700">
                <div>
                  <Label className="text-gray-300">Nome da Empresa</Label>
                  <Input
                    value={settings?.company_name || ''}
                    onChange={(e) => updateLocalSettings('company_name', e.target.value)}
                    placeholder="Nome exibido no certificado"
                    className="bg-gray-800 border-gray-600 mt-2"
                  />
                </div>
                <div>
                  <Label className="text-gray-300">Subtítulo (opcional)</Label>
                  <Input
                    value={settings?.company_subtitle || ''}
                    onChange={(e) => updateLocalSettings('company_subtitle', e.target.value)}
                    placeholder="Ex: SECURITY GATEWAY"
                    className="bg-gray-800 border-gray-600 mt-2"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* TAB: Termos */}
        <TabsContent value="terms">
          <Card className="bg-gray-900 border-gray-700">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-white">Termo de Compromisso</CardTitle>
                <CardDescription>
                  Edite as cláusulas do termo que aparece no certificado
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleResetTerms}
                  disabled={saving}
                  className="border-gray-600"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Restaurar Padrão
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveTerms}
                  disabled={saving}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Save className="w-4 h-4 mr-2" />
                  Salvar Termos
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Introdução */}
              <div>
                <Label className="text-gray-300">Introdução</Label>
                <Textarea
                  value={settings?.terms?.introduction || ''}
                  onChange={(e) => updateLocalSettings('terms.introduction', e.target.value)}
                  placeholder="Texto introdutório do termo..."
                  className="bg-gray-800 border-gray-600 mt-2 min-h-[80px]"
                />
              </div>

              {/* Seções do Termo */}
              <div className="space-y-4">
                <Label className="text-gray-300">Cláusulas do Termo</Label>
                {settings?.terms?.sections?.map((section, index) => (
                  <div key={index} className="bg-gray-800 rounded-lg p-4 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="bg-green-600 text-white w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold">
                        {section.number || index + 1}
                      </span>
                      <Input
                        value={section.title || ''}
                        onChange={(e) => updateTermSection(index, 'title', e.target.value)}
                        placeholder="Título da cláusula"
                        className="bg-gray-700 border-gray-600 flex-1"
                      />
                    </div>
                    <Textarea
                      value={section.content || ''}
                      onChange={(e) => updateTermSection(index, 'content', e.target.value)}
                      placeholder="Conteúdo da cláusula..."
                      className="bg-gray-700 border-gray-600 min-h-[60px]"
                    />
                    {section.items?.length > 0 && (
                      <div className="pl-4 space-y-1">
                        <span className="text-xs text-gray-500">Itens:</span>
                        {section.items.map((item, i) => (
                          <div key={i} className="text-sm text-gray-400">• {item}</div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* TAB: Procedimento */}
        <TabsContent value="procedure">
          <Card className="bg-gray-900 border-gray-700">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-white">Passos do Procedimento</CardTitle>
                <CardDescription>
                  Configure os passos e screenshots do guia de ativação
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleResetSteps}
                  disabled={saving}
                  className="border-gray-600"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Restaurar Padrão
                </Button>
                <Button
                  size="sm"
                  onClick={handleAddStep}
                  disabled={saving}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Novo Passo
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {settings?.procedure_steps?.sort((a, b) => a.order - b.order).map((step, index) => (
                  <div 
                    key={step.id} 
                    className="bg-gray-800 rounded-lg p-4 border border-gray-700"
                  >
                    <div className="flex items-start gap-4">
                      {/* Controles de ordem */}
                      <div className="flex flex-col gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleMoveStep(step.id, 'up')}
                          disabled={index === 0}
                          className="p-1 h-6"
                        >
                          <ChevronUp className="w-4 h-4" />
                        </Button>
                        <div className="bg-green-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
                          {step.order}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleMoveStep(step.id, 'down')}
                          disabled={index === settings.procedure_steps.length - 1}
                          className="p-1 h-6"
                        >
                          <ChevronDown className="w-4 h-4" />
                        </Button>
                      </div>

                      {/* Conteúdo */}
                      <div className="flex-1 space-y-3">
                        <Input
                          value={step.title || ''}
                          onChange={(e) => {
                            const newSteps = [...settings.procedure_steps];
                            newSteps[index].title = e.target.value;
                            updateLocalSettings('procedure_steps', newSteps);
                          }}
                          onBlur={() => handleUpdateStep(step.id, { title: step.title })}
                          placeholder="Título do passo"
                          className="bg-gray-700 border-gray-600 font-semibold"
                        />
                        <Textarea
                          value={step.description || ''}
                          onChange={(e) => {
                            const newSteps = [...settings.procedure_steps];
                            newSteps[index].description = e.target.value;
                            updateLocalSettings('procedure_steps', newSteps);
                          }}
                          onBlur={() => handleUpdateStep(step.id, { description: step.description })}
                          placeholder="Descrição/instruções..."
                          className="bg-gray-700 border-gray-600 min-h-[60px]"
                        />
                        
                        {/* Screenshot */}
                        <div className="flex items-center gap-4">
                          {step.screenshot_base64 ? (
                            <div className="relative">
                              <img 
                                src={step.screenshot_base64}
                                alt={`Screenshot ${step.order}`}
                                className="h-20 rounded border border-gray-600"
                              />
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleUpdateStep(step.id, { screenshot_base64: null })}
                                className="absolute -top-2 -right-2 p-1 h-6 w-6 bg-red-500 hover:bg-red-600 rounded-full"
                              >
                                <X className="w-3 h-3" />
                              </Button>
                            </div>
                          ) : (
                            <div className="h-20 w-32 bg-gray-700 rounded border-2 border-dashed border-gray-600 flex items-center justify-center">
                              <span className="text-xs text-gray-500">Sem imagem</span>
                            </div>
                          )}
                          <div>
                            <input
                              type="file"
                              id={`step-image-${step.id}`}
                              onChange={(e) => handleStepImageUpload(step.id, e)}
                              accept="image/png,image/jpeg"
                              className="hidden"
                            />
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => document.getElementById(`step-image-${step.id}`)?.click()}
                              className="border-gray-600"
                            >
                              <Upload className="w-4 h-4 mr-2" />
                              {step.screenshot_base64 ? 'Trocar' : 'Upload Screenshot'}
                            </Button>
                          </div>
                        </div>
                      </div>

                      {/* Ações */}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteStep(step.id)}
                        className="text-red-500 hover:text-red-400 hover:bg-red-500/10"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}

                {(!settings?.procedure_steps || settings.procedure_steps.length === 0) && (
                  <div className="text-center py-8 text-gray-500">
                    <ListOrdered className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Nenhum passo configurado</p>
                    <p className="text-sm">Clique em "Novo Passo" ou "Restaurar Padrão"</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Informações Importantes */}
          <Card className="bg-gray-900 border-gray-700 mt-6">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-white">Informações Importantes</CardTitle>
                <CardDescription>
                  Exibidas na página de certificação (uma por linha)
                </CardDescription>
              </div>
              <Button
                size="sm"
                onClick={handleSaveImportantInfo}
                disabled={saving}
                className="bg-green-600 hover:bg-green-700"
              >
                <Save className="w-4 h-4 mr-2" />
                Salvar
              </Button>
            </CardHeader>
            <CardContent>
              <Textarea
                value={settings?.important_info?.join('\n') || ''}
                onChange={(e) => updateLocalSettings('important_info', e.target.value.split('\n'))}
                placeholder="Uma informação por linha..."
                className="bg-gray-800 border-gray-600 min-h-[150px]"
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
