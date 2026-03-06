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

  const fetchSettings = useCallback(async () => {
    try {
      const response = await fetch(`${API}/api/certificate-settings`, {
        credentials: 'include',
        headers: { 'X-Tenant-ID': tenantId || 'default' }
      });
      if (response.ok) {
        const data = await response.json();
        setSettings(data.settings);
      } else {
        toast.error('Erro ao carregar configurações');
      }
    } catch (error) {
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
    if (!file.type.match(/image\/(png|jpeg|jpg|svg\+xml)/)) {
      toast.error('Formato inválido. Use PNG, JPG ou SVG.');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Arquivo muito grande. Máximo 5MB.');
      return;
    }

    setSaving(true);
    const reader = new FileReader();
    reader.onload = async (e) => {
      const response = await fetch(`${API}/api/certificate-settings/logo`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-Tenant-ID': tenantId || 'default' },
        body: JSON.stringify({ logo_base64: e.target?.result, logo_filename: file.name })
      });
      if (response.ok) {
        toast.success('Logo atualizado!');
        fetchSettings();
      } else {
        toast.error('Erro ao atualizar logo');
      }
      setSaving(false);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveLogo = async () => {
    if (!window.confirm('Remover logo?')) return;
    setSaving(true);
    const response = await fetch(`${API}/api/certificate-settings/logo`, {
      method: 'DELETE',
      credentials: 'include',
      headers: { 'X-Tenant-ID': tenantId || 'default' }
    });
    if (response.ok) {
      toast.success('Logo removido');
      fetchSettings();
    }
    setSaving(false);
  };

  // Termos
  const handleSaveTerms = async () => {
    setSaving(true);
    const response = await fetch(`${API}/api/certificate-settings/terms`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Tenant-ID': tenantId || 'default' },
      body: JSON.stringify({ introduction: settings.terms?.introduction, sections: settings.terms?.sections })
    });
    if (response.ok) toast.success('Termos salvos!');
    else toast.error('Erro ao salvar termos');
    setSaving(false);
  };

  const handleResetTerms = async () => {
    if (!window.confirm('Restaurar termos padrão?')) return;
    setSaving(true);
    const response = await fetch(`${API}/api/certificate-settings/terms/reset`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'X-Tenant-ID': tenantId || 'default' }
    });
    if (response.ok) {
      toast.success('Termos restaurados');
      fetchSettings();
    }
    setSaving(false);
  };

  // Procedimento
  const handleAddStep = async () => {
    setSaving(true);
    const response = await fetch(`${API}/api/certificate-settings/procedure-steps`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Tenant-ID': tenantId || 'default' },
      body: JSON.stringify({ title: 'Novo Passo', description: 'Descreva as instruções...' })
    });
    if (response.ok) {
      toast.success('Passo adicionado');
      fetchSettings();
    }
    setSaving(false);
  };

  const handleUpdateStep = async (stepId, data) => {
    const response = await fetch(`${API}/api/certificate-settings/procedure-steps/${stepId}`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Tenant-ID': tenantId || 'default' },
      body: JSON.stringify(data)
    });
    if (response.ok) {
      toast.success('Passo atualizado');
      fetchSettings();
    }
  };

  const handleDeleteStep = async (stepId) => {
    if (!window.confirm('Remover este passo?')) return;
    const response = await fetch(`${API}/api/certificate-settings/procedure-steps/${stepId}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: { 'X-Tenant-ID': tenantId || 'default' }
    });
    if (response.ok) {
      toast.success('Passo removido');
      fetchSettings();
    }
  };

  const handleStepImageUpload = async (stepId, event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.match(/image\/(png|jpeg|jpg)/)) {
      toast.error('Use PNG ou JPG');
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      toast.error('Máximo 2MB');
      return;
    }
    const reader = new FileReader();
    reader.onload = async (e) => {
      await handleUpdateStep(stepId, { screenshot_base64: e.target?.result, screenshot_filename: file.name });
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
    if (!window.confirm('Restaurar passos padrão?')) return;
    setSaving(true);
    const response = await fetch(`${API}/api/certificate-settings/procedure-steps/reset`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'X-Tenant-ID': tenantId || 'default' }
    });
    if (response.ok) {
      toast.success('Passos restaurados');
      fetchSettings();
    }
    setSaving(false);
  };

  const handleSaveImportantInfo = async () => {
    setSaving(true);
    const response = await fetch(`${API}/api/certificate-settings/important-info`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Tenant-ID': tenantId || 'default' },
      body: JSON.stringify({ items: settings.important_info || [] })
    });
    if (response.ok) toast.success('Informações salvas!');
    setSaving(false);
  };

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
      <div className="flex items-center justify-center h-64 bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6" data-testid="certificate-settings-page">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <Settings className="w-6 h-6 text-emerald-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-800">Configurações de Certificado</h1>
          </div>
          <p className="text-gray-600 ml-12">
            Personalize o layout, termos e procedimento dos seus certificados digitais
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-white border border-gray-200 shadow-sm mb-6 p-1 rounded-xl">
            <TabsTrigger 
              value="logo" 
              className="data-[state=active]:bg-emerald-500 data-[state=active]:text-white rounded-lg px-4 py-2 text-gray-600"
            >
              <Image className="w-4 h-4 mr-2" />
              Logo & Marca
            </TabsTrigger>
            <TabsTrigger 
              value="terms" 
              className="data-[state=active]:bg-emerald-500 data-[state=active]:text-white rounded-lg px-4 py-2 text-gray-600"
            >
              <FileText className="w-4 h-4 mr-2" />
              Termos
            </TabsTrigger>
            <TabsTrigger 
              value="procedure" 
              className="data-[state=active]:bg-emerald-500 data-[state=active]:text-white rounded-lg px-4 py-2 text-gray-600"
            >
              <ListOrdered className="w-4 h-4 mr-2" />
              Procedimento
            </TabsTrigger>
          </TabsList>

          {/* TAB: Logo & Marca */}
          <TabsContent value="logo">
            <Card className="bg-white border border-gray-200 shadow-sm rounded-xl">
              <CardHeader className="border-b border-gray-100 bg-gray-50/50 rounded-t-xl">
                <CardTitle className="text-gray-800 text-lg">Logo da Empresa</CardTitle>
                <CardDescription className="text-gray-500">
                  O logo aparecerá no cabeçalho de todos os certificados
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6 space-y-6">
                <div className="flex items-center gap-6">
                  <div className="w-44 h-28 bg-gray-100 rounded-xl flex items-center justify-center border-2 border-dashed border-gray-300 hover:border-emerald-400 transition-colors">
                    {settings?.logo_base64 ? (
                      <img src={settings.logo_base64} alt="Logo" className="max-w-full max-h-full object-contain p-2" />
                    ) : (
                      <div className="text-center">
                        <Image className="w-10 h-10 text-gray-400 mx-auto mb-2" />
                        <span className="text-sm text-gray-400">Sem logo</span>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col gap-3">
                    <input type="file" ref={fileInputRef} onChange={handleLogoUpload} accept="image/*" className="hidden" />
                    <Button onClick={() => fileInputRef.current?.click()} disabled={saving} className="bg-emerald-500 hover:bg-emerald-600 text-white shadow-sm">
                      <Upload className="w-4 h-4 mr-2" />
                      {settings?.logo_base64 ? 'Trocar Logo' : 'Fazer Upload'}
                    </Button>
                    {settings?.logo_base64 && (
                      <Button variant="outline" onClick={handleRemoveLogo} disabled={saving} className="border-red-300 text-red-600 hover:bg-red-50">
                        <Trash2 className="w-4 h-4 mr-2" />
                        Remover
                      </Button>
                    )}
                  </div>
                </div>
                <p className="text-sm text-gray-500 bg-gray-50 p-3 rounded-lg">
                  📎 Formatos: PNG, JPG, SVG • Tamanho máximo: 5MB • Recomendado: fundo transparente
                </p>

                <div className="grid grid-cols-2 gap-6 pt-4 border-t border-gray-100">
                  <div>
                    <Label className="text-gray-700 font-medium">Nome da Empresa</Label>
                    <Input
                      value={settings?.company_name || ''}
                      onChange={(e) => updateLocalSettings('company_name', e.target.value)}
                      placeholder="Nome exibido no certificado"
                      className="mt-2 bg-white border-gray-300 text-gray-800 placeholder:text-gray-400 focus:border-emerald-500 focus:ring-emerald-500"
                    />
                  </div>
                  <div>
                    <Label className="text-gray-700 font-medium">Subtítulo (opcional)</Label>
                    <Input
                      value={settings?.company_subtitle || ''}
                      onChange={(e) => updateLocalSettings('company_subtitle', e.target.value)}
                      placeholder="Ex: SECURITY GATEWAY"
                      className="mt-2 bg-white border-gray-300 text-gray-800 placeholder:text-gray-400 focus:border-emerald-500 focus:ring-emerald-500"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* TAB: Termos */}
          <TabsContent value="terms">
            <Card className="bg-white border border-gray-200 shadow-sm rounded-xl">
              <CardHeader className="border-b border-gray-100 bg-gray-50/50 rounded-t-xl flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-gray-800 text-lg">Termo de Compromisso</CardTitle>
                  <CardDescription className="text-gray-500">
                    Edite as cláusulas que aparecem no certificado
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={handleResetTerms} disabled={saving} className="border-gray-300 text-gray-600 hover:bg-gray-100">
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Restaurar
                  </Button>
                  <Button size="sm" onClick={handleSaveTerms} disabled={saving} className="bg-emerald-500 hover:bg-emerald-600 text-white">
                    <Save className="w-4 h-4 mr-2" />
                    Salvar
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-6 space-y-6">
                <div>
                  <Label className="text-gray-700 font-medium">Introdução</Label>
                  <Textarea
                    value={settings?.terms?.introduction || ''}
                    onChange={(e) => updateLocalSettings('terms.introduction', e.target.value)}
                    placeholder="Texto introdutório do termo..."
                    className="mt-2 bg-white border-gray-300 text-gray-800 placeholder:text-gray-400 min-h-[100px] focus:border-emerald-500 focus:ring-emerald-500"
                  />
                </div>

                <div className="space-y-4">
                  <Label className="text-gray-700 font-medium">Cláusulas do Termo</Label>
                  {settings?.terms?.sections?.map((section, index) => (
                    <div key={index} className="bg-gray-50 rounded-xl p-5 border border-gray-200 space-y-3">
                      <div className="flex items-center gap-3">
                        <span className="bg-emerald-500 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shadow-sm">
                          {section.number || index + 1}
                        </span>
                        <Input
                          value={section.title || ''}
                          onChange={(e) => updateTermSection(index, 'title', e.target.value)}
                          placeholder="Título da cláusula"
                          className="flex-1 bg-white border-gray-300 text-gray-800 font-medium focus:border-emerald-500"
                        />
                      </div>
                      <Textarea
                        value={section.content || ''}
                        onChange={(e) => updateTermSection(index, 'content', e.target.value)}
                        placeholder="Conteúdo da cláusula..."
                        className="bg-white border-gray-300 text-gray-700 min-h-[80px] focus:border-emerald-500"
                      />
                      {section.items?.length > 0 && (
                        <div className="bg-white rounded-lg p-3 border border-gray-200">
                          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Itens:</span>
                          <ul className="mt-2 space-y-1">
                            {section.items.map((item, i) => (
                              <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                                <span className="text-emerald-500 mt-0.5">•</span>
                                {item}
                              </li>
                            ))}
                          </ul>
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
            <Card className="bg-white border border-gray-200 shadow-sm rounded-xl">
              <CardHeader className="border-b border-gray-100 bg-gray-50/50 rounded-t-xl flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-gray-800 text-lg">Passos do Procedimento</CardTitle>
                  <CardDescription className="text-gray-500">
                    Configure os passos e screenshots do guia de ativação
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={handleResetSteps} disabled={saving} className="border-gray-300 text-gray-600 hover:bg-gray-100">
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Restaurar
                  </Button>
                  <Button size="sm" onClick={handleAddStep} disabled={saving} className="bg-emerald-500 hover:bg-emerald-600 text-white">
                    <Plus className="w-4 h-4 mr-2" />
                    Novo Passo
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-4">
                  {settings?.procedure_steps?.sort((a, b) => a.order - b.order).map((step, index) => (
                    <div key={step.id} className="bg-gray-50 rounded-xl p-5 border border-gray-200 hover:border-emerald-300 transition-colors">
                      <div className="flex items-start gap-4">
                        <div className="flex flex-col gap-1 items-center">
                          <Button variant="ghost" size="sm" onClick={() => handleMoveStep(step.id, 'up')} disabled={index === 0} className="p-1 h-7 text-gray-400 hover:text-gray-600">
                            <ChevronUp className="w-4 h-4" />
                          </Button>
                          <div className="bg-emerald-500 text-white w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shadow-sm">
                            {step.order}
                          </div>
                          <Button variant="ghost" size="sm" onClick={() => handleMoveStep(step.id, 'down')} disabled={index === settings.procedure_steps.length - 1} className="p-1 h-7 text-gray-400 hover:text-gray-600">
                            <ChevronDown className="w-4 h-4" />
                          </Button>
                        </div>

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
                            className="bg-white border-gray-300 text-gray-800 font-semibold focus:border-emerald-500"
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
                            className="bg-white border-gray-300 text-gray-700 min-h-[80px] focus:border-emerald-500"
                          />

                          <div className="flex items-center gap-4 pt-2">
                            {step.screenshot_base64 ? (
                              <div className="relative group">
                                <img src={step.screenshot_base64} alt={`Screenshot ${step.order}`} className="h-24 rounded-lg border border-gray-300 shadow-sm" />
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleUpdateStep(step.id, { screenshot_base64: null })}
                                  className="absolute -top-2 -right-2 p-1 h-6 w-6 bg-red-500 hover:bg-red-600 rounded-full text-white shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
                                >
                                  <X className="w-3 h-3" />
                                </Button>
                              </div>
                            ) : (
                              <div className="h-24 w-36 bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
                                <span className="text-xs text-gray-400">Sem imagem</span>
                              </div>
                            )}
                            <div>
                              <input type="file" id={`step-image-${step.id}`} onChange={(e) => handleStepImageUpload(step.id, e)} accept="image/png,image/jpeg" className="hidden" />
                              <Button variant="outline" size="sm" onClick={() => document.getElementById(`step-image-${step.id}`)?.click()} className="border-gray-300 text-gray-600 hover:bg-gray-100">
                                <Upload className="w-4 h-4 mr-2" />
                                {step.screenshot_base64 ? 'Trocar' : 'Upload Screenshot'}
                              </Button>
                            </div>
                          </div>
                        </div>

                        <Button variant="ghost" size="sm" onClick={() => handleDeleteStep(step.id)} className="text-red-500 hover:text-red-600 hover:bg-red-50">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}

                  {(!settings?.procedure_steps || settings.procedure_steps.length === 0) && (
                    <div className="text-center py-12 bg-gray-50 rounded-xl border-2 border-dashed border-gray-300">
                      <ListOrdered className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p className="text-gray-500 font-medium">Nenhum passo configurado</p>
                      <p className="text-sm text-gray-400">Clique em "Novo Passo" ou "Restaurar"</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Informações Importantes */}
            <Card className="bg-white border border-gray-200 shadow-sm rounded-xl mt-6">
              <CardHeader className="border-b border-gray-100 bg-gray-50/50 rounded-t-xl flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-gray-800 text-lg">Informações Importantes</CardTitle>
                  <CardDescription className="text-gray-500">
                    Exibidas na página de certificação (uma por linha)
                  </CardDescription>
                </div>
                <Button size="sm" onClick={handleSaveImportantInfo} disabled={saving} className="bg-emerald-500 hover:bg-emerald-600 text-white">
                  <Save className="w-4 h-4 mr-2" />
                  Salvar
                </Button>
              </CardHeader>
              <CardContent className="p-6">
                <Textarea
                  value={settings?.important_info?.join('\n') || ''}
                  onChange={(e) => updateLocalSettings('important_info', e.target.value.split('\n'))}
                  placeholder="Uma informação por linha..."
                  className="bg-white border-gray-300 text-gray-700 min-h-[150px] focus:border-emerald-500 focus:ring-emerald-500"
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
