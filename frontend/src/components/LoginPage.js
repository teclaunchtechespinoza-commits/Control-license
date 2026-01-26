import React, { useState, useEffect } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../App';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Loader2, Shield, Eye, EyeOff, KeyRound, ArrowLeft, CheckCircle, LogIn, UserPlus, Clock, Mail } from 'lucide-react';
import { toast } from 'sonner';

const LoginPage = () => {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [activeTab, setActiveTab] = useState('login');
  const [registrationPending, setRegistrationPending] = useState(false);
  const [pendingEmail, setPendingEmail] = useState('');
  
  // Estado do modal de recuperação de senha
  const [showRecoveryModal, setShowRecoveryModal] = useState(false);
  const [recoveryStep, setRecoveryStep] = useState(1);
  const [recoveryEmail, setRecoveryEmail] = useState('');
  const [recoveryCode, setRecoveryCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [recoveryLoading, setRecoveryLoading] = useState(false);

  // Login unificado - aceita email ou código
  const [loginData, setLoginData] = useState({
    identifier: '', // Email ou código de acesso
    password: ''
  });

  // Register form state
  const [registerData, setRegisterData] = useState({
    email: '',
    password: '',
    name: '',
    confirmPassword: ''
  });

  useEffect(() => {
    // Component initialization if needed
  }, []);

  // If user is already logged in, redirect based on role
  if (user) {
    const targetPath = user.role === 'user' ? '/minhas-licencas' : '/dashboard';
    return <Navigate to={targetPath} />;
  }

  // Detecta se é email ou código
  const isEmail = (value) => value.includes('@');

  // Login unificado - detecta automaticamente email ou código
  const handleUnifiedLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const { identifier, password } = loginData;
      
      if (!identifier || !password) {
        toast.error('Por favor, preencha todos os campos');
        setIsLoading(false);
        return;
      }

      // Detecta se é email ou código de acesso
      if (isEmail(identifier)) {
        // Login por email
        const result = await login({ email: identifier, password });
        
        if (result.success) {
          toast.success('Login realizado com sucesso!');
          const userRole = result.user?.role;
          const targetPath = userRole === 'user' ? '/minhas-licencas' : '/dashboard';
          navigate(targetPath);
        } else {
          toast.error(result.error || 'Email ou senha incorretos');
        }
      } else {
        // Login por código de acesso (serial)
        const response = await api.post('/auth/login-serial', {
          serial_number: identifier,
          password: password
        });
        
        if (response.data && response.data.user) {
          const userData = response.data.user;
          localStorage.setItem('user', JSON.stringify(userData));
          if (userData.tenant_id) {  
            localStorage.setItem('tenant_id', userData.tenant_id);
          }
          
          toast.success('Login realizado com sucesso!');
          const targetPage = userData.role === 'admin' ? '/dashboard' : '/minhas-licencas';
          window.location.href = targetPage;
        } else {
          toast.error('Credenciais inválidas');
        }
      }
    } catch (error) {
      console.error('Erro no login:', error);
      const errorMessage = error.response?.data?.detail || 'Erro no login. Verifique suas credenciais.';
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    if (registerData.password !== registerData.confirmPassword) {
      toast.error('As senhas não coincidem');
      return;
    }

    if (registerData.password.length < 8) {
      toast.error('A senha deve ter pelo menos 8 caracteres');
      return;
    }

    setIsLoading(true);
    
    const result = await register({
      email: registerData.email,
      password: registerData.password,
      name: registerData.name
    });

    if (result.success) {
      if (result.pending_approval) {
        // Mostrar tela de aprovação pendente
        setPendingEmail(registerData.email);
        setRegistrationPending(true);
      }
      setRegisterData({ email: '', password: '', name: '', confirmPassword: '' });
    }
    
    setIsLoading(false);
  };

  // Funções de Recuperação de Senha
  const handleRequestRecovery = async () => {
    if (!recoveryEmail.trim()) {
      toast.error('Digite seu email');
      return;
    }
    
    if (!isEmail(recoveryEmail)) {
      toast.error('Digite um email válido');
      return;
    }
    
    setRecoveryLoading(true);
    try {
      const response = await api.post('/auth/forgot-password', { email: recoveryEmail });
      if (response.data.success) {
        toast.success('Solicitação enviada! Entre em contato com o administrador para obter seu código.');
        setRecoveryStep(2);
      }
    } catch (error) {
      toast.error('Erro ao solicitar recuperação');
    } finally {
      setRecoveryLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!recoveryCode.trim() || recoveryCode.length !== 6) {
      toast.error('Digite o código de 6 dígitos');
      return;
    }
    if (!newPassword || newPassword.length < 6) {
      toast.error('A senha deve ter pelo menos 6 caracteres');
      return;
    }
    if (newPassword !== confirmNewPassword) {
      toast.error('As senhas não coincidem');
      return;
    }
    
    setRecoveryLoading(true);
    try {
      const response = await api.post('/auth/verify-recovery-code', {
        email: recoveryEmail,
        code: recoveryCode,
        new_password: newPassword
      });
      if (response.data.success) {
        setRecoveryStep(3);
        toast.success('Senha redefinida com sucesso!');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Código inválido ou expirado');
    } finally {
      setRecoveryLoading(false);
    }
  };

  const resetRecoveryModal = () => {
    setShowRecoveryModal(false);
    setRecoveryStep(1);
    setRecoveryEmail('');
    setRecoveryCode('');
    setNewPassword('');
    setConfirmNewPassword('');
  };

  // Verifica se o campo tem email para mostrar opção de recuperação
  const showForgotPassword = isEmail(loginData.identifier);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg">
              <Shield className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Sistema de Controle de Licenças</h1>
          <p className="text-gray-500 text-sm">Acesse sua conta para continuar</p>
        </div>

        {/* Card Principal */}
        <Card className="shadow-xl border-0">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            {/* Abas com diferenciação de cor */}
            <TabsList className="grid w-full grid-cols-2 p-1 bg-gray-100 rounded-t-lg">
              <TabsTrigger 
                value="login" 
                className="flex items-center gap-2 data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-md rounded-md transition-all duration-200"
                data-testid="tab-login"
              >
                <LogIn className="w-4 h-4" />
                Entrar
              </TabsTrigger>
              <TabsTrigger 
                value="register"
                className="flex items-center gap-2 data-[state=active]:bg-emerald-600 data-[state=active]:text-white data-[state=active]:shadow-md rounded-md transition-all duration-200"
                data-testid="tab-register"
              >
                <UserPlus className="w-4 h-4" />
                Registrar
              </TabsTrigger>
            </TabsList>
            
            {/* Aba de Login Unificado */}
            <TabsContent value="login" className="mt-0">
              <form onSubmit={handleUnifiedLogin}>
                <CardHeader className="pb-4">
                  <CardTitle className="text-lg">Bem-vindo</CardTitle>
                  <CardDescription>
                    Entre com seu email ou código de acesso
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="identifier">Identificação</Label>
                    <Input
                      id="identifier"
                      type="text"
                      placeholder="Email ou código de acesso"
                      value={loginData.identifier}
                      onChange={(e) => setLoginData({...loginData, identifier: e.target.value.trim()})}
                      required
                      disabled={isLoading}
                      className="h-11"
                      data-testid="login-identifier-input"
                    />
                    <p className="text-xs text-gray-400">
                      {loginData.identifier && (isEmail(loginData.identifier) 
                        ? '📧 Entrando com email' 
                        : '🔑 Entrando com código de acesso')}
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="password">Senha</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Digite sua senha"
                        value={loginData.password}
                        onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                        required
                        disabled={isLoading}
                        className="h-11 pr-10"
                        data-testid="login-password-input"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={isLoading}
                        tabIndex={-1}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4 text-gray-400" />
                        ) : (
                          <Eye className="h-4 w-4 text-gray-400" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="flex flex-col gap-3 pt-2">
                  <Button
                    type="submit"
                    className="w-full h-11 bg-blue-600 hover:bg-blue-700 text-white font-medium"
                    disabled={isLoading}
                    data-testid="login-submit-btn"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Entrando...
                      </>
                    ) : (
                      <>
                        <LogIn className="mr-2 h-4 w-4" />
                        Entrar no Sistema
                      </>
                    )}
                  </Button>
                  
                  {/* Link de recuperação - só aparece quando é email */}
                  {showForgotPassword && (
                    <button
                      type="button"
                      onClick={() => {
                        setRecoveryEmail(loginData.identifier);
                        setShowRecoveryModal(true);
                      }}
                      className="text-sm text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                      data-testid="forgot-password-link"
                    >
                      Esqueci minha senha
                    </button>
                  )}
                </CardFooter>
              </form>
            </TabsContent>
            
            {/* Aba de Registro */}
            <TabsContent value="register" className="mt-0">
              <form onSubmit={handleRegister}>
                <CardHeader className="pb-4">
                  <CardTitle className="text-lg">Criar nova conta</CardTitle>
                  <CardDescription>
                    Preencha os dados para se registrar
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Nome Completo</Label>
                    <Input
                      id="name"
                      type="text"
                      placeholder="Seu nome completo"
                      value={registerData.name}
                      onChange={(e) => setRegisterData({...registerData, name: e.target.value})}
                      required
                      disabled={isLoading}
                      className="h-11"
                      data-testid="register-name-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="register-email">Email</Label>
                    <Input
                      id="register-email"
                      type="email"
                      placeholder="seu@email.com"
                      value={registerData.email}
                      onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
                      required
                      disabled={isLoading}
                      className="h-11"
                      data-testid="register-email-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="register-password">Senha</Label>
                    <div className="relative">
                      <Input
                        id="register-password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Mínimo 8 caracteres"
                        value={registerData.password}
                        onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                        required
                        disabled={isLoading}
                        minLength={8}
                        className="h-11 pr-10"
                        data-testid="register-password-input"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={isLoading}
                        tabIndex={-1}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4 text-gray-400" /> : <Eye className="h-4 w-4 text-gray-400" />}
                      </Button>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="confirm-password">Confirmar Senha</Label>
                    <div className="relative">
                      <Input
                        id="confirm-password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Repita a senha"
                        value={registerData.confirmPassword}
                        onChange={(e) => setRegisterData({...registerData, confirmPassword: e.target.value})}
                        required
                        disabled={isLoading}
                        className="h-11 pr-10"
                        data-testid="register-confirm-password-input"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={isLoading}
                        tabIndex={-1}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4 text-gray-400" /> : <Eye className="h-4 w-4 text-gray-400" />}
                      </Button>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="pt-2">
                  <Button 
                    type="submit" 
                    className="w-full h-11 bg-emerald-600 hover:bg-emerald-700 text-white font-medium" 
                    disabled={isLoading}
                    data-testid="register-submit-btn"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Criando conta...
                      </>
                    ) : (
                      <>
                        <UserPlus className="mr-2 h-4 w-4" />
                        Criar Conta
                      </>
                    )}
                  </Button>
                </CardFooter>
              </form>
            </TabsContent>
          </Tabs>
        </Card>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-xs text-gray-400">
            Sistema seguro e confiável para controle de licenças
          </p>
        </div>
      </div>

      {/* Modal de Recuperação de Senha */}
      <Dialog open={showRecoveryModal} onOpenChange={(open) => !open && resetRecoveryModal()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-blue-600" />
              {recoveryStep === 1 && 'Recuperar Senha'}
              {recoveryStep === 2 && 'Verificar Código'}
              {recoveryStep === 3 && 'Senha Redefinida!'}
            </DialogTitle>
            <DialogDescription>
              {recoveryStep === 1 && 'Digite seu email para receber um código de recuperação.'}
              {recoveryStep === 2 && 'Digite o código de 6 dígitos e sua nova senha.'}
              {recoveryStep === 3 && 'Sua senha foi alterada com sucesso.'}
            </DialogDescription>
          </DialogHeader>

          {/* Step 1: Email */}
          {recoveryStep === 1 && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="recovery-email">Email</Label>
                <Input
                  id="recovery-email"
                  type="email"
                  placeholder="seu@email.com"
                  value={recoveryEmail}
                  onChange={(e) => setRecoveryEmail(e.target.value)}
                  disabled={recoveryLoading}
                  data-testid="recovery-email-input"
                />
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-700">
                  <strong>Nota:</strong> Um código de 6 dígitos será gerado. 
                  Para esta versão de demonstração, verifique os logs do servidor 
                  ou contate o administrador para obter o código.
                </p>
              </div>
            </div>
          )}

          {/* Step 2: Code + New Password */}
          {recoveryStep === 2 && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="recovery-code">Código de Verificação</Label>
                <Input
                  id="recovery-code"
                  type="text"
                  placeholder="000000"
                  maxLength={6}
                  value={recoveryCode}
                  onChange={(e) => setRecoveryCode(e.target.value.replace(/\D/g, ''))}
                  disabled={recoveryLoading}
                  className="text-center text-2xl tracking-widest font-mono"
                  data-testid="recovery-code-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-password">Nova Senha</Label>
                <div className="relative">
                  <Input
                    id="new-password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Mínimo 6 caracteres"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    disabled={recoveryLoading}
                    data-testid="new-password-input"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4 text-gray-500" /> : <Eye className="h-4 w-4 text-gray-500" />}
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm-new-password">Confirmar Nova Senha</Label>
                <div className="relative">
                  <Input
                    id="confirm-new-password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Repita a senha"
                    value={confirmNewPassword}
                    onChange={(e) => setConfirmNewPassword(e.target.value)}
                    disabled={recoveryLoading}
                    data-testid="confirm-new-password-input"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4 text-gray-500" /> : <Eye className="h-4 w-4 text-gray-500" />}
                  </Button>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setRecoveryStep(1)}
                className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
              >
                <ArrowLeft className="h-3 w-3" /> Voltar
              </button>
            </div>
          )}

          {/* Step 3: Success */}
          {recoveryStep === 3 && (
            <div className="py-6 text-center space-y-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <p className="text-gray-600">
                Sua senha foi alterada com sucesso. Agora você pode fazer login com sua nova senha.
              </p>
            </div>
          )}

          <DialogFooter>
            {recoveryStep === 1 && (
              <Button 
                onClick={handleRequestRecovery} 
                disabled={recoveryLoading || !recoveryEmail}
                className="w-full"
                data-testid="request-recovery-btn"
              >
                {recoveryLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Enviando...
                  </>
                ) : (
                  'Solicitar Código'
                )}
              </Button>
            )}
            {recoveryStep === 2 && (
              <Button 
                onClick={handleVerifyCode} 
                disabled={recoveryLoading || recoveryCode.length !== 6 || !newPassword}
                className="w-full"
                data-testid="verify-code-btn"
              >
                {recoveryLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Verificando...
                  </>
                ) : (
                  'Redefinir Senha'
                )}
              </Button>
            )}
            {recoveryStep === 3 && (
              <Button 
                onClick={resetRecoveryModal}
                className="w-full"
                data-testid="close-recovery-btn"
              >
                Fechar e Fazer Login
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default LoginPage;
