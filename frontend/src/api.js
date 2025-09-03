/**
 * Centralized API Configuration
 * Provides unified axios instance with automatic token injection and error handling
 */
import axios from 'axios';

// Get backend URL from environment
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.VITE_API_URL || 'http://localhost:8001';

// Create centralized axios instance
export const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - automatically inject authorization token
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage (multiple possible keys for compatibility)
    const token = localStorage.getItem('access_token') || 
                  localStorage.getItem('token') || 
                  sessionStorage.getItem('access_token');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add tenant header if available
    const tenantId = localStorage.getItem('tenant_id');
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId;
    }
    
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor - handle authentication errors and common responses
api.interceptors.response.use(
  (response) => {
    // Successful response
    return response;
  },
  (error) => {
    const { response } = error;
    
    if (response?.status === 401) {
      // Unauthorized - clear auth data and redirect to login
      console.warn('Authentication expired, redirecting to login...');
      
      // Clear all auth-related data
      localStorage.removeItem('access_token');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('tenant_id');
      sessionStorage.removeItem('access_token');
      
      // Clear axios default headers
      delete api.defaults.headers.common['Authorization'];
      
      // Redirect to login (avoid infinite loops)
      if (!window.location.pathname.includes('/login')) {
        // Show user-friendly message
        if (window.toast) {
          window.toast.error('Sessão expirada. Redirecionando para login...');
        }
        
        // Redirect after a brief delay
        setTimeout(() => {
          window.location.href = '/login';
        }, 1500);
      }
    } else if (response?.status === 403) {
      // Forbidden - show access denied message
      console.warn('Access denied:', response.data?.detail || 'Insufficient permissions');
      
      if (window.toast) {
        window.toast.error('Acesso negado: Você não tem permissão para esta ação.');
      }
    } else if (response?.status >= 500) {
      // Server error
      console.error('Server error:', response.data);
      
      if (window.toast) {
        window.toast.error('Erro do servidor. Tente novamente em alguns instantes.');
      }
    } else if (!response) {
      // Network error
      console.error('Network error:', error.message);
      
      if (window.toast) {
        window.toast.error('Erro de conexão. Verifique sua internet.');
      }
    }
    
    return Promise.reject(error);
  }
);

// Helper functions for common API operations
export const apiHelpers = {
  // Get current user info
  getCurrentUser: async () => {
    try {
      const response = await api.get('/auth/me');
      return response.data;
    } catch (error) {
      console.error('Failed to get current user:', error);
      return null;
    }
  },
  
  // Login
  login: async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      
      // Store auth data
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        if (response.data.user.tenant_id) {
          localStorage.setItem('tenant_id', response.data.user.tenant_id);
        }
      }
      
      return response.data;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  },
  
  // Logout
  logout: async () => {
    try {
      // Clear local data
      localStorage.removeItem('access_token');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('tenant_id');
      sessionStorage.removeItem('access_token');
      
      // Clear axios headers
      delete api.defaults.headers.common['Authorization'];
      delete api.defaults.headers.common['X-Tenant-ID'];
      
      // Optional: call logout endpoint if available
      // await api.post('/auth/logout');
      
      return true;
    } catch (error) {
      console.error('Logout error:', error);
      return false;
    }
  },
  
  // Check if user is authenticated
  isAuthenticated: () => {
    const token = localStorage.getItem('access_token') || 
                  localStorage.getItem('token');
    return !!token;
  },
  
  // Get stored user data
  getUser: () => {
    try {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('Failed to parse user data:', error);
      return null;
    }
  }
};

// ---------- Sprint 2: Convites ----------
export const inviteHelpers = {
  // Criar convite (Admin)
  createInvitation: async (email) => {
    try {
      const response = await api.post('/admin/invitations', { email });
      return response.data;
    } catch (error) {
      console.error('Failed to create invitation:', error);
      throw error;
    }
  },

  // Aceitar convite (público - sem auth)
  acceptInvite: async (token, password = null) => {
    try {
      // Criar instância sem interceptors de auth para esta chamada
      const publicApi = axios.create({
        baseURL: `${BACKEND_URL}/api`,
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const body = { token };
      if (password) body.password = password;
      
      const response = await publicApi.post('/auth/accept-invite', body);
      return response.data;
    } catch (error) {
      console.error('Failed to accept invitation:', error);
      throw error;
    }
  },

  // Revogar convite (Admin)
  revokeInvitation: async (token) => {
    try {
      const response = await api.post('/admin/invitations/revoke', { token });
      return response.data;
    } catch (error) {
      console.error('Failed to revoke invitation:', error);
      throw error;
    }
  },

  // Listar convites (Admin)
  listInvitations: async () => {
    try {
      const response = await api.get('/admin/invitations');
      return response.data;
    } catch (error) {
      console.error('Failed to list invitations:', error);
      throw error;
    }
  }
};

// Export default api instance
export default api;