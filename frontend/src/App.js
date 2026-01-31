import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { api, apiHelpers } from './api';
import { initializePreloader } from './utils/preloader';
import { toast, Toaster } from 'sonner';

// Sprint 2 - Pages
import AcceptInvitePage from './pages/AcceptInvitePage';
import AdminInvitePage from './pages/AdminInvitePage';

// Components
import LoginPage from './components/LoginPage';
import Dashboard from './components/Dashboard';
import AdminPanel from './components/AdminPanel';
import UserLicenses from './components/UserLicenses';
import UserDashboard from './components/UserDashboard';
import UserLicenseView from './components/UserLicenseView';
import RegistryModule from './components/RegistryModule';
import ClientsModule from './components/ClientsModule';
import MaintenanceModule from './components/MaintenanceModule';
import SalesDashboard from './components/SalesDashboard';
import TenantAdmin from './components/TenantAdmin';
import DataImport from './components/DataImport';
import LicenseManagement from './components/LicenseManagement';
import Navbar from './components/Navbar';
import QuickAccessPanel from './components/QuickAccessPanel';
import LoadingSpinner from './components/LoadingSpinner';
import { HelpProvider } from './components/help/HelpProvider';

// Note: API configuration and interceptors are handled in api.js

// Auth Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Provider Component
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    console.log('App useEffect executando...');
    
    // 🚫 CRITICAL: Prevent infinite loops - only fetch if not already loading
    if (!loading) {
      return;
    }
    
    // 🔐 SECURITY UPGRADE: With HttpOnly cookies, try to fetch user
    // But add fallback to check localStorage first to avoid unnecessary API calls
    const existingUser = localStorage.getItem('user');
    if (existingUser) {
      try {
        const userData = JSON.parse(existingUser);
        console.log('✅ Usuario encontrado no localStorage:', userData.email);
        setUser(userData);
        setLoading(false);
        return;
      } catch (e) {
        console.log('❌ Erro ao parsear usuário do localStorage, tentando API...');
      }
    }
    
    console.log('Tentando buscar usuário da API com cookies...');
    fetchUser();
  }, []); // Empty dependency array - run only once

  const fetchUser = async () => {
    // 🚫 CRITICAL: Prevent multiple concurrent calls
    if (!loading) {
      console.log('⚠️ fetchUser chamado mas loading=false, ignorando...');
      return;
    }
    
    try {
      console.log('Tentando buscar dados do usuário com cookies...');
      
      const userData = await apiHelpers.getCurrentUser();
      if (userData) {
        console.log('✅ Usuário autenticado:', userData.email);
        setUser(userData);
        
        // Store user data and tenant_id for compatibility
        localStorage.setItem('user', JSON.stringify(userData));
        if (userData.tenant_id) {  
          localStorage.setItem('tenant_id', userData.tenant_id);
        }
      } else {
        console.log('❌ Nenhum dado de usuário retornado');
        setUser(null);
      }
    } catch (error) {
      console.log('❌ Erro ao buscar usuário:', error.response?.status || error.message);
      
      // Clear auth data
      localStorage.removeItem('user');
      localStorage.removeItem('tenant_id');
      setUser(null);
      
      // Only show session expired message if user was previously logged in
      // (don't show it on initial page load with expired tokens)
      if (error.response?.status === 401 && user !== null) {
        toast.error('Session expired. Please login again.');
      }
      
      // 🚨 CRITICAL: If Redis is down or server error, stop trying to refresh
      if (error.response?.status >= 500 || !error.response) {
        console.warn('🚨 Server error detected - stopping auth attempts');
        // Don't show repeated error messages for server issues
      }
    } finally {
      // 🚫 CRITICAL: Always set loading to false to prevent infinite loading
      setLoading(false);
    }
  };

  const login = async (credentials) => {
    try {
      console.log('Fazendo login com credenciais:', credentials.email);
      const loginResult = await apiHelpers.login(credentials.email, credentials.password);
      console.log('Resposta do servidor:', loginResult);
      
      const userData = loginResult.user;
      setUser(userData);
      
      // Initialize preloader after successful login
      initializePreloader();
      
      // Welcome message moved to Dashboard.js to avoid duplication
      console.log('Login completado com sucesso');
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      console.error('Resposta de erro:', error.response);
      
      const message = error.response?.data?.detail || error.message || 'Login failed';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const register = async (userData) => {
    try {
      const response = await apiHelpers.register(userData);
      
      // Verificar se é resposta de aprovação pendente
      if (response.approval_status === 'pending') {
        toast.success('Registro realizado! Aguardando aprovação do administrador.', {
          duration: 6000
        });
        return { 
          success: true, 
          pending_approval: true,
          message: response.message 
        };
      }
      
      toast.success('Conta criada com sucesso! Faça login para continuar.');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Falha no registro';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const logout = async () => {
    try {
      await apiHelpers.logout();
      setUser(null);
      toast.success('Logged out successfully');
    } catch (error) {
      console.error('Logout error:', error);
      // Force logout even if API call fails
      setUser(null);
      localStorage.removeItem('token');
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      localStorage.removeItem('tenant_id');
      toast.success('Logged out successfully');
    }
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Redirecionamento baseado no role do usuário
const RoleBasedRedirect = () => {
  const { user } = useAuth();
  
  if (!user) {
    return <Navigate to="/login" />;
  }
  
  // Usuários normais vão para suas licenças
  if (user.role === 'user') {
    return <Navigate to="/minhas-licencas" />;
  }
  
  // Admins e super_admins vão para dashboard
  return <Navigate to="/dashboard" />;
};

// Protected Route Component
const ProtectedRoute = ({ children, adminOnly = false, superAdminOnly = false }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (superAdminOnly && user.role !== 'super_admin') {
    return <Navigate to="/dashboard" />;
  }

  if (adminOnly && user.role !== 'admin' && user.role !== 'super_admin') {
    return <Navigate to="/dashboard" />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="pt-16">
        {children}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <div className="App">
      <Router>
        <AuthProvider>
          <HelpProvider>
            <div className="min-h-screen">
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route 
                  path="/dashboard" 
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/licenses" 
                  element={
                    <ProtectedRoute>
                      <UserLicenses />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/minhas-licencas" 
                  element={
                    <ProtectedRoute>
                      <UserDashboard />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/admin" 
                  element={
                    <ProtectedRoute adminOnly>
                      <AdminPanel />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/clientes" 
                  element={
                    <ProtectedRoute adminOnly>
                      <ClientsModule />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/cadastros" 
                  element={
                    <ProtectedRoute adminOnly>
                      <RegistryModule />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/manutencao" 
                  element={
                    <ProtectedRoute adminOnly>
                      <MaintenanceModule />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/vendas" 
                  element={
                    <ProtectedRoute adminOnly>
                      <SalesDashboard />
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/tenants" 
                  element={
                    <ProtectedRoute superAdminOnly>
                      <TenantAdmin />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Importação de Dados */}
                <Route 
                  path="/import" 
                  element={
                    <ProtectedRoute adminOnly>
                      <DataImport />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Sprint 2 - Convites */}
                <Route path="/accept-invite" element={<AcceptInvitePage />} />
                <Route 
                  path="/admin/convites" 
                  element={
                    <ProtectedRoute adminOnly>
                      <AdminInvitePage />
                    </ProtectedRoute>
                  } 
                />
                
                <Route path="/" element={<RoleBasedRedirect />} />
              </Routes>
            </div>
            
            {/* Rodapé simples e harmonioso */}
            <footer className="bg-gray-50 py-4 px-4 mt-auto">
              <div className="text-center">
                <div className="text-sm text-gray-500">
                  © 2025 License Manager. Todos os direitos reservados.
                </div>
              </div>
            </footer>
            
            <Toaster position="top-right" richColors />
          </HelpProvider>
        </AuthProvider>
      </Router>
    </div>
  );
}

export default App;