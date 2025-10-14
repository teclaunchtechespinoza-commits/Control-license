import React, { useState, useEffect } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../App';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Loader2, Shield, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

const LoginPage = () => {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

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

  // If user is already logged in, redirect to dashboard
  if (user) {
    console.log('User is logged in, redirecting to dashboard:', user);
    return <Navigate to="/dashboard" />;
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
      const result = await login(loginData.email, loginData.password);
      
      if (result.success) {
        toast.success('Login realizado com sucesso!');
        navigate('/dashboard');
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
        
        // Update auth context
        await login(userData.email || userData.serial_number, userLoginData.password, userData);
        
        toast.success('Login realizado com sucesso!');
        navigate('/minhas-licencas'); // Redirecionar para página específica do usuário
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
      toast.error('Passwords do not match');
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Sistema de Controle de Licenças</h1>
          <p className="text-gray-600 mt-2">Faça login para acessar o sistema</p>
        </div>

        <Card className="shadow-lg">
          <Tabs defaultValue="login" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Entrar</TabsTrigger>
              <TabsTrigger value="register">Registrar</TabsTrigger>
            </TabsList>
            
            <TabsContent value="login">
              <form onSubmit={handleLogin}>
                <CardHeader>
                  <CardTitle>Fazer Login</CardTitle>
                  <CardDescription>
                    Digite suas credenciais para acessar o sistema
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="seu@email.com"
                      value={loginData.email}
                      onChange={(e) => setLoginData({...loginData, email: e.target.value})}
                      required
                      disabled={isLoading}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="password">Senha</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Sua senha"
                        value={loginData.password}
                        onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                        required
                        disabled={isLoading}
                        className="pr-10"
                      />
                      <button
                        type="button"
                        className="absolute right-3 top-1/2 transform -translate-y-1/2"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Entrar
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
                    <Input
                      id="register-password"
                      type="password"
                      placeholder="Mínimo 8 caracteres"
                      value={registerData.password}
                      onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                      required
                      disabled={isLoading}
                      minLength={8}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="confirm-password">Confirmar Senha</Label>
                    <Input
                      id="confirm-password"
                      type="password"
                      placeholder="Confirme sua senha"
                      value={registerData.confirmPassword}
                      onChange={(e) => setRegisterData({...registerData, confirmPassword: e.target.value})}
                      required
                      disabled={isLoading}
                    />
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