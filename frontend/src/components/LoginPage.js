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
import { Loader2, Shield, Eye, EyeOff, KeyRound, ArrowLeft, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

const LoginPage = () => {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  // Estado do modal de recuperação de senha
  const [showRecoveryModal, setShowRecoveryModal] = useState(false);
  const [recoveryStep, setRecoveryStep] = useState(1); // 1: email, 2: código, 3: sucesso
  const [recoveryEmail, setRecoveryEmail] = useState('');
  const [recoveryCode, setRecoveryCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [recoveryLoading, setRecoveryLoading] = useState(false);

  // Login form state
  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  });

  // User login form state (serial + password)
  const [userLoginData, setUserLoginData] = useState({
    serial_number: '',
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
    console.log('User is logged in, redirecting based on role:', user.role);
    // Users vão para suas licenças, admins vão para dashboard
    const targetPath = user.role === 'user' ? '/minhas-licencas' : '/dashboard';
    return <Navigate to={targetPath} />;
  }

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      // Validação básica
      if (!loginData.email || !loginData.password) {
        toast.error('Por favor, preencha email e senha');
        return;
      }

      console.log('Tentando login admin com:', loginData.email);
      const result = await login({ email: loginData.email, password: loginData.password });
      
      if (result.success) {
        toast.success('Login realizado com sucesso!');
        // Redirecionar baseado no role do usuário
        const userRole = result.user?.role;
        const targetPath = userRole === 'user' ? '/minhas-licencas' : '/dashboard';
        navigate(targetPath);
      } else {
        toast.error(result.error || 'Erro no login');
      }
    } catch (error) {
      console.error('Erro no login:', error);
      toast.error('Erro no login. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUserLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      // Validação básica
      if (!userLoginData.serial_number || !userLoginData.password) {
        toast.error('Por favor, preencha número de série e senha');
        return;
      }

      console.log('Tentando login usuário com serial:', userLoginData.serial_number);
      
      // Fazer login usando endpoint específico para usuários por serial
      const response = await api.post('/auth/login-serial', {
        serial_number: userLoginData.serial_number,
        password: userLoginData.password
      });
      
      if (response.data && response.data.user) {
        // Atualizar contexto de autenticação
        const userData = response.data.user;
        
        // Store user data
        localStorage.setItem('user', JSON.stringify(userData));
        if (userData.tenant_id) {  
          localStorage.setItem('tenant_id', userData.tenant_id);
        }
        
        // Redirecionamento inteligente baseado no role
        const targetPage = userData.role === 'admin' ? '/dashboard' : '/minhas-licencas';
        window.location.href = targetPage;
        
        toast.success(`Login realizado com sucesso! Redirecionando para ${userData.role === 'admin' ? 'painel admin' : 'suas licenças'}...`);
      } else {
        toast.error('Credenciais inválidas');
      }
    } catch (error) {
      console.error('Erro no login por serial:', error);
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
      toast.error('Password must be at least 8 characters long');
      return;
    }

    setIsLoading(true);
    
    const result = await register({
      email: registerData.email,
      password: registerData.password,
      name: registerData.name
    });

    if (result.success) {
      setRegisterData({ email: '', password: '', name: '', confirmPassword: '' });
    }
    
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="w-full max-w-md px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
              <Shield className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Sistema de Controle de Licenças</h1>
          <p className="text-gray-600">Faça login para acessar o sistema</p>
        </div>

        <Card className="shadow-lg">
          <Tabs defaultValue="user" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="user">Usuário</TabsTrigger>
              <TabsTrigger value="admin">Admin</TabsTrigger>
              <TabsTrigger value="register">Registrar</TabsTrigger>
            </TabsList>
            
            {/* Aba de Login Usuário */}
            <TabsContent value="user">
              <form onSubmit={handleUserLogin}>
                <CardHeader>
                  <CardTitle>Acesso do Usuário</CardTitle>
                  <CardDescription>
                    Somente para usuarios Cadastrados
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="user-code">Código de Identificação</Label>
                    <Input
                      id="user-code"
                      type="text"
                      placeholder="Digite aqui..."
                      value={userLoginData.serial_number || ''}
                      onChange={(e) => {
                        const value = e.target.value.trim();
                        setUserLoginData({...userLoginData, serial_number: value});
                      }}
                      required
                      disabled={isLoading}
                      className="font-mono"
                    />
                    <div className="text-xs text-gray-500">
                    
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="user-password">Senha</Label>
                    <div className="relative">
                      <Input
                        id="user-password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Digite aqui..."
                        value={userLoginData.password}
                        onChange={(e) => setUserLoginData({...userLoginData, password: e.target.value})}
                        required
                        disabled={isLoading}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={isLoading}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4 text-gray-500" />
                        ) : (
                          <Eye className="h-4 w-4 text-gray-500" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button
                    type="submit"
                    className="w-full bg-blue-600 hover:bg-blue-700"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Fazendo login...
                      </>
                    ) : (
                      'Acessar Minhas Licenças'
                    )}
                  </Button>
                </CardFooter>
              </form>
            </TabsContent>
            
            {/* Aba de Login Admin/Email */}
            <TabsContent value="admin">
              <form onSubmit={handleLogin}>
                <CardHeader>
                  <CardTitle>Acesso Administrativo</CardTitle>
                  <CardDescription>
                    Para administradores e super admins
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="admin-email">Email</Label>
                    <Input
                      id="admin-email"
                      type="email"
                      placeholder="admin@exemplo.com"
                      value={loginData.email}
                      onChange={(e) => setLoginData({...loginData, email: e.target.value})}
                      required
                      disabled={isLoading}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="admin-password">Senha</Label>
                    <div className="relative">
                      <Input
                        id="admin-password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Digite sua senha..."
                        value={loginData.password}
                        onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                        required
                        disabled={isLoading}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={isLoading}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4 text-gray-500" />
                        ) : (
                          <Eye className="h-4 w-4 text-gray-500" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button
                    type="submit"
                    className="w-full bg-indigo-600 hover:bg-indigo-700"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Entrando...
                      </>
                    ) : (
                      'Entrar como Admin'
                    )}
                  </Button>
                </CardFooter>
              </form>
            </TabsContent>
            
            <TabsContent value="register">
              <form onSubmit={handleRegister}>
                <CardHeader>
                  <CardTitle>Criar Conta</CardTitle>
                  <CardDescription>
                    Crie uma nova conta no sistema
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
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={isLoading}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4 text-gray-500" /> : <Eye className="h-4 w-4 text-gray-500" />}
                      </Button>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="confirm-password">Confirmar Senha</Label>
                    <div className="relative">
                      <Input
                        id="confirm-password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Confirme sua senha"
                        value={registerData.confirmPassword}
                        onChange={(e) => setRegisterData({...registerData, confirmPassword: e.target.value})}
                        required
                        disabled={isLoading}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={isLoading}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4 text-gray-500" /> : <Eye className="h-4 w-4 text-gray-500" />}
                      </Button>
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Criar Conta
                  </Button>
                </CardFooter>
              </form>
            </TabsContent>
          </Tabs>
        </Card>

        <div className="text-center mt-6">
          <p className="text-sm text-gray-500">
            Sistema seguro e confiável para controle de licenças
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;