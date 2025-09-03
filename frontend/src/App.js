import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { initializePreloader } from './utils/preloader';
import { FooterVersion } from './components/VersionControl';
import { toast, Toaster } from 'sonner';

// Sprint 2 - Pages
import AcceptInvitePage from './pages/AcceptInvitePage';
import AdminInvitePage from './pages/AdminInvitePage';

// Components
import LoginPage from './components/LoginPage';
import Dashboard from './components/Dashboard';
import AdminPanel from './components/AdminPanel';
import UserLicenses from './components/UserLicenses';
import RegistryModule from './components/RegistryModule';
import ClientsModule from './components/ClientsModule';
import MaintenanceModule from './components/MaintenanceModule';
import SalesDashboard from './components/SalesDashboard';
import TenantAdmin from './components/TenantAdmin';
import Navbar from './components/Navbar';
import QuickAccessPanel from './components/QuickAccessPanel';
import LoadingSpinner from './components/LoadingSpinner';
import { HelpProvider } from './components/help/HelpProvider';

// API Configuration
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Set default axios headers
axios.defaults.baseURL = API;

// Note: Axios interceptors are configured in api.js to avoid duplication

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
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    console.log('Token encontrado:', token ? 'SIM' : 'NÃO');
    
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      console.log('Configurando axios com token e chamando fetchUser...');
      fetchUser();
    } else {
      console.log('Nenhum token encontrado, definindo loading como false');
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      console.log('Tentando buscar dados do usuário...');
      console.log('Axios baseURL:', axios.defaults.baseURL);
      console.log('Authorization header:', axios.defaults.headers.common['Authorization']);
      
      const response = await axios.get('/auth/me');
      console.log('Resposta fetchUser:', response.data);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      console.error('Error response:', error.response);
      
      // Clear auth data
      localStorage.removeItem('token');
      localStorage.removeItem('access_token');
      delete axios.defaults.headers.common['Authorization'];
      
      // Only show session expired message if user was previously logged in
      // (don't show it on initial page load with expired tokens)
      if (error.response?.status === 401 && user !== null) {
        toast.error('Session expired. Please login again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials) => {
    try {
      console.log('Fazendo login com credenciais:', credentials.email);
      const response = await axios.post('/auth/login', credentials);
      console.log('Resposta do servidor:', response.data);
      
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      
      // Initialize preloader after successful login
      initializePreloader();
      
      toast.success(`Welcome back, ${userData.name}!`);
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
      await axios.post('/auth/register', userData);
      toast.success('Account created successfully! Please login.');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    toast.success('Logged out successfully');
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
                    <ProtectedRoute>
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
                
                <Route path="/" element={<Navigate to="/dashboard" />} />
              </Routes>
            </div>
            
            {/* Rodapé com Controle de Versão */}
            <footer className="bg-white border-t border-gray-200 py-3 px-4 mt-auto">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  © 2025 License Manager. Todos os direitos reservados.
                </div>
                <FooterVersion />
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