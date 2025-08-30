/**
 * Route Guard Component for Protected Routes
 * Implements modern React Router v6 patterns with <Outlet /> and <Navigate />
 */
import React, { useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { apiHelpers } from '../api';
import LoadingSpinner from './LoadingSpinner';

const RequireAuth = ({ allowedRoles = [], redirectTo = '/login' }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    checkAuthentication();
  }, []);

  const checkAuthentication = async () => {
    try {
      setIsLoading(true);
      
      // Check if token exists
      if (!apiHelpers.isAuthenticated()) {
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }

      // Get user data
      const userData = apiHelpers.getUser();
      if (!userData) {
        // Try to fetch user data from API
        const currentUser = await apiHelpers.getCurrentUser();
        if (currentUser) {
          setUser(currentUser);
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
        }
      } else {
        setUser(userData);
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('Authentication check failed:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  // Not authenticated - redirect to login
  if (!isAuthenticated) {
    // Save the attempted location for redirect after login
    return (
      <Navigate 
        to={redirectTo} 
        state={{ from: location.pathname }} 
        replace 
      />
    );
  }

  // Check role-based access if roles are specified
  if (allowedRoles.length > 0 && user) {
    const hasRequiredRole = allowedRoles.includes(user.role);
    if (!hasRequiredRole) {
      console.warn(`Access denied. Required roles: ${allowedRoles.join(', ')}, User role: ${user.role}`);
      return (
        <Navigate 
          to="/unauthorized" 
          state={{ requiredRoles: allowedRoles, userRole: user.role }} 
          replace 
        />
      );
    }
  }

  // User is authenticated and authorized - render child routes
  return <Outlet />;
};

// Specific guards for different user roles
export const RequireAdmin = () => (
  <RequireAuth allowedRoles={['admin', 'super_admin']} />
);

export const RequireSuperAdmin = () => (
  <RequireAuth allowedRoles={['super_admin']} />
);

export const RequireUser = () => (
  <RequireAuth allowedRoles={['user', 'admin', 'super_admin']} />
);

// Public route component (for routes that should not be accessible when logged in)
export const RequireGuest = ({ redirectTo = '/dashboard' }) => {
  const isAuthenticated = apiHelpers.isAuthenticated();
  
  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }
  
  return <Outlet />;
};

// Unauthorized page component
export const UnauthorizedPage = () => {
  const location = useLocation();
  const { requiredRoles, userRole } = location.state || {};

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 text-red-600">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Acesso Negado
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Você não tem permissão para acessar esta página.
          </p>
          {requiredRoles && (
            <p className="mt-2 text-xs text-gray-500">
              Roles necessárias: {requiredRoles.join(', ')}<br />
              Sua role: {userRole}
            </p>
          )}
          <div className="mt-6">
            <button
              onClick={() => window.history.back()}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Voltar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RequireAuth;