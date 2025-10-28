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
  withCredentials: true, // 🔐 CRITICAL: Enable cookies for cross-origin requests
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

// Flag para evitar loops infinitos de refresh
let isRefreshing = false;

// Response interceptor para tratamento de erros avançado
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response, config } = error;
    
    // 🚀 FASE 1 - TRATAMENTO DE ERROS CONSISTENTE
    // Enhanced error handling with structured error codes
    
    if (response?.data) {
      const errorData = response.data;
      const errorCode = errorData.error_code;
      const suggestion = errorData.suggestion;
      const errorId = errorData.error_id;
      
      console.group('🚨 Enhanced Error Handling');
      console.log('Status:', response.status);
      console.log('Error Code:', errorCode);
      console.log('Message:', errorData.detail);
      console.log('Suggestion:', suggestion);
      if (errorId) console.log('Error ID:', errorId);
      console.groupEnd();
      
      // Handle specific error codes with enhanced UX
      switch (errorCode) {
        case 'AUTHENTICATION_REQUIRED':
          return handleAuthenticationError(error, config);
          
        case 'TENANT_ID_REQUIRED':
          return handleTenantError(errorData);
          
        case 'INSUFFICIENT_PERMISSIONS':
          return handlePermissionError(errorData);
          
        case 'VALIDATION_ERROR':
        case 'VALIDATION_FAILED':
          return handleValidationError(errorData);
          
        case 'TENANT_NOT_FOUND':
        case 'TENANT_INACTIVE':
          return handleTenantStatusError(errorData);
          
        case 'INTERNAL_SERVER_ERROR':
          return handleInternalError(errorData);
          
        default:
          // Handle legacy 401 errors and fallback cases
          if (response?.status === 401) {
            return handleAuthenticationError(error, config);
          }
      }
    }
    
    // Legacy error handling for old-style errors
    if (response?.status === 401) {
      return handleAuthenticationError(error, config);
    }
    
    return Promise.reject(error);
  }
);

// 🔐 Enhanced Authentication Error Handler
async function handleAuthenticationError(error, config) {
  console.warn('🔐 Authentication Error - Enhanced Handler');
  
  // 🚫 CRITICAL: Prevent infinite loops - don't retry refresh endpoints
  if (config.url?.includes('/auth/refresh') || config.url?.includes('/auth/me')) {
    console.warn('❌ Auth endpoint failed, redirecting to login...');
    redirectToLogin('Sessão expirada. Faça login novamente.');
    return Promise.reject(error);
  }
  
  // 🚫 CRITICAL: Prevent multiple concurrent refresh attempts
  if (isRefreshing) {
    console.warn('❌ Already refreshing token, rejecting request...');
    redirectToLogin('Múltiplas tentativas de refresh detectadas. Faça login novamente.');
    return Promise.reject(error);
  }
  
  console.warn('🔄 Attempting token refresh...');
  isRefreshing = true;
  
  try {
    // Try to refresh the token
    const refreshResponse = await api.post('/auth/refresh');
    if (refreshResponse.status === 200) {
      console.log('✅ Token refreshed successfully, retrying original request');
      isRefreshing = false;
      // Retry the original request
      return api.request(config);
    }
  } catch (refreshError) {
    console.warn('❌ Token refresh failed:', refreshError.response?.status);
    
    // Se é erro 500 ou problema de conexão, pode ser Redis
    if (refreshError.response?.status >= 500 || !refreshError.response) {
      console.warn('🚨 Server error detected - may be Redis connection issue');
      console.warn('Clearing auth state and redirecting to login...');
    }
  } finally {
    isRefreshing = false;
  }
  
  // If refresh failed, show enhanced message and redirect
  redirectToLogin('Sua sessão expirou. Você será redirecionado para fazer login.');
  return Promise.reject(error);
}

// 🏢 Tenant Error Handler
function handleTenantError(errorData) {
  if (window.toast) {
    window.toast.error('Problema de organização detectado', {
      description: 'Tente fazer logout e login novamente',
      action: {
        label: 'Logout',
        onClick: () => {
          // Trigger logout
          localStorage.removeItem('user');
          localStorage.removeItem('tenant_id');
          window.location.href = '/login';
        }
      }
    });
  }
  return Promise.reject(new Error(errorData.detail));
}

// 🚫 Permission Error Handler  
function handlePermissionError(errorData) {
  if (window.toast) {
    window.toast.error('Acesso negado', {
      description: errorData.detail,
      action: {
        label: 'Falar com Admin',
        onClick: () => {
          // Could open contact modal or redirect to help
          console.log('User requested admin contact');
        }
      }
    });
  }
  return Promise.reject(new Error(errorData.detail));
}

// 📝 Validation Error Handler
function handleValidationError(errorData) {
  console.group('📝 Validation Error Details');
  
  if (errorData.errors && Array.isArray(errorData.errors)) {
    // Enhanced validation with field-specific errors
    errorData.errors.forEach(err => {
      console.log(`Field: ${err.field} - ${err.message}`);
    });
    
    const fieldCount = errorData.errors.length;
    const mainMessage = `${fieldCount} campo${fieldCount > 1 ? 's' : ''} ${fieldCount > 1 ? 'precisam' : 'precisa'} de correção`;
    
    if (window.toast) {
      window.toast.error('Erro de validação', {
        description: mainMessage,
        duration: 5000 // Longer duration for validation errors
      });
    }
  } else {
    // Generic validation error
    if (window.toast) {
      window.toast.error('Dados inválidos', {
        description: errorData.suggestion || 'Verifique os campos e tente novamente'
      });
    }
  }
  
  console.groupEnd();
  return Promise.reject(new Error(errorData.detail));
}

// 🏢 Tenant Status Error Handler
function handleTenantStatusError(errorData) {
  const isInactive = errorData.error_code === 'TENANT_INACTIVE';
  const title = isInactive ? 'Organização Suspensa' : 'Organização Não Encontrada';
  
  if (window.toast) {
    window.toast.error(title, {
      description: errorData.detail,
      action: {
        label: 'Contatar Suporte',
        onClick: () => {
          // Could open support modal or redirect to help
          console.log('User requested support contact');
        }
      }
    });
  }
  
  // For tenant issues, might need to redirect or clear session
  if (isInactive) {
    setTimeout(() => {
      localStorage.removeItem('user');
      localStorage.removeItem('tenant_id');
      window.location.href = '/login';
    }, 3000);
  }
  
  return Promise.reject(new Error(errorData.detail));
}

// 💥 Internal Error Handler
function handleInternalError(errorData) {
  const errorId = errorData.error_id || 'N/A';
  
  if (window.toast) {
    window.toast.error('Erro interno do servidor', {
      description: `Erro ID: ${errorId}. Se persistir, contate o suporte.`,
      duration: 8000, // Longer duration for server errors
      action: {
        label: 'Copiar ID',
        onClick: () => {
          navigator.clipboard.writeText(errorId);
          window.toast.success('ID do erro copiado!');
        }
      }
    });
  }
  
  return Promise.reject(new Error(errorData.detail));
}

// 🔄 Enhanced Redirect to Login
function redirectToLogin(message) {
  // Clear remaining auth-related data (cookies cleared by server)
  localStorage.removeItem('user');
  localStorage.removeItem('tenant_id');
  
  // Show enhanced toast message
  if (window.toast) {
    window.toast.error(message, {
      action: {
        label: 'Ir para Login',
        onClick: () => window.location.href = '/login'
      }
    });
  }
  
  // Redirect after a brief delay (avoid infinite loops)
  if (!window.location.pathname.includes('/login')) {
    setTimeout(() => {
      window.location.href = '/login';
    }, 2000);
  }
}

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

  // Excluir convite (Admin)
  deleteInvitation: async (token) => {
    try {
      const response = await api.delete(`/admin/invitations/${token}`);
      return response.data;
    } catch (error) {
      console.error('Failed to delete invitation:', error);
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