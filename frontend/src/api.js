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

// Request interceptor - cookies handled automatically, add tenant header
api.interceptors.request.use(
  (config) => {
    // 🔐 SECURITY UPGRADE: Cookies are sent automatically (HttpOnly)
    // No need to manually add Authorization header - cookies handle this
    
    // 🚨 CRITICAL FIX: Always ensure X-Tenant-ID is sent
    let tenantId = localStorage.getItem('tenant_id');
    
    // Fallback: try to get tenant from user data if tenant_id is missing
    if (!tenantId) {
      try {
        const userData = localStorage.getItem('user');
        if (userData) {
          const user = JSON.parse(userData);
          tenantId = user.tenant_id || 'default';
          // Save it for next time
          localStorage.setItem('tenant_id', tenantId);
        }
      } catch (e) {
        console.warn('Failed to parse user data for tenant_id:', e);
      }
    }
    
    // Always add tenant header (fallback to 'default' if still missing)
    const finalTenantId = tenantId || 'default';
    config.headers['X-Tenant-ID'] = finalTenantId;
    
    // Ensure cookies are included in requests
    config.withCredentials = true;
    
    // Debug: log missing tenant scenarios
    if (!tenantId) {
      console.warn('⚠️ X-Tenant-ID not found in localStorage, using fallback:', finalTenantId);
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
  async (error) => {
    const { response, config } = error;
    
    if (response?.status === 401) {
      // 🔄 SECURITY UPGRADE: Try to refresh token but prevent infinite loops
      console.warn('Access token expired...');
      
      // 🚫 CRITICAL: Prevent infinite loops - don't retry refresh endpoints
      if (config.url?.includes('/auth/refresh') || config.url?.includes('/auth/me')) {
        console.warn('❌ Auth endpoint failed, redirecting to login...');
      } else {
        console.warn('Attempting token refresh...');
        
        try {
          // Try to refresh the token
          const refreshResponse = await api.post('/auth/refresh');
          if (refreshResponse.status === 200) {
            console.log('✅ Token refreshed successfully, retrying original request');
            // Retry the original request
            return api.request(config);
          }
        } catch (refreshError) {
          console.warn('❌ Token refresh failed:', refreshError.response?.status);
        }
      }
      
      // If refresh failed or was skipped, clear auth data and redirect
      console.warn('Authentication failed, redirecting to login...');
      
      // Clear remaining auth-related data (cookies cleared by server)
      localStorage.removeItem('user');
      localStorage.removeItem('tenant_id');
      
      // Redirect to login (avoid infinite loops)
      if (!window.location.pathname.includes('/login')) {
        if (window.toast) {
          window.toast.error('Sessão expirada. Redirecionando para login...');
        }
        
        // Redirect after a brief delay
        setTimeout(() => {
          window.location.href = '/login';
        }, 1500);
      }
    } else if (response?.status === 400) {
      // 🚨 CRITICAL: Handle missing tenant header specifically
      const errorDetail = response?.data?.detail || '';
      if (errorDetail.includes('X-Tenant-ID') || errorDetail.includes('tenant')) {
        console.error('❌ X-Tenant-ID header missing or invalid');
        if (window.toast) {
          window.toast.error('Erro de configuração: Selecione um tenant para continuar');
        }
        // Try to reload tenant_id from user data
        try {
          const userData = localStorage.getItem('user');
          if (userData) {
            const user = JSON.parse(userData);
            if (user.tenant_id) {
              localStorage.setItem('tenant_id', user.tenant_id);
              console.log('🔄 Tenant ID restored from user data:', user.tenant_id);
              // Could retry the request here if needed
            }
          }
        } catch (e) {
          console.error('Failed to restore tenant_id:', e);
        }
      } else {
        console.warn('Bad Request (400):', errorDetail);
        if (window.toast) {
          window.toast.error('Requisição inválida: ' + errorDetail);
        }
      }
    } else if (response?.status === 403) {
      // Forbidden - insufficient permissions (user is authenticated but lacks permission)
      console.warn('Access denied (403) - authenticated but insufficient permissions');
      if (window.toast) {
        window.toast.error('Acesso negado: Você não tem permissão para esta ação.');
      }
    } else if (response?.status === 404) {
      // Not Found - possibly wrong URL (classic /api/api problem)
      console.warn('Not Found (404) - check if URL is correct');
      const requestUrl = config?.url || 'unknown';
      if (requestUrl.includes('/api/api')) {
        console.error('🚨 DETECTED /api/api double prefix in URL:', requestUrl);
        if (window.toast) {
          window.toast.error('Erro de configuração: URL duplicada detectada');
        }
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
      
      // 🔐 SECURITY UPGRADE: Tokens now stored in HttpOnly cookies
      // Only store user data and tenant_id for app functionality
      if (response.data.user) {
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
      // 🔐 SECURITY UPGRADE: Call logout endpoint to revoke refresh token
      await api.post('/auth/logout');
      
      // Clear local data (cookies cleared by server)
      localStorage.removeItem('user');
      localStorage.removeItem('tenant_id');
      
      return true;
    } catch (error) {
      console.error('Logout error:', error);
      // Force clear even if API call fails
      localStorage.removeItem('user');
      localStorage.removeItem('tenant_id');
      return false;
    }
  },
  
  // Check if user is authenticated
  isAuthenticated: () => {
    // 🔐 SECURITY UPGRADE: Check if user data exists (cookies handled automatically)
    const user = localStorage.getItem('user');
    return !!user;
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
  },
  
  // Register new user
  register: async (userData) => {
    try {
      const response = await api.post('/auth/register', userData);
      return response.data;
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  }
};

// ---------- Sprint 2: Convites ----------
// Get backend URL for public API calls
const BACKEND_URL_FOR_INVITES = process.env.REACT_APP_BACKEND_URL || import.meta.env.VITE_API_URL || 'http://localhost:8001';

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
        baseURL: `${BACKEND_URL_FOR_INVITES}/api`,
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