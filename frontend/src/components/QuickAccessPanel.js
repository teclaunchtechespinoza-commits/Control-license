import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
import { 
  Home, 
  FileText, 
  TrendingUp, 
  Users, 
  UserCog, 
  Tag, 
  Building, 
  Settings,
  Plus,
  ChevronRight,
  ChevronLeft,
  Zap
} from 'lucide-react';

const QuickAccessPanel = () => {
  const { user } = useAuth();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const quickActions = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: Home,
      path: '/dashboard',
      color: 'text-blue-600',
      bgColor: 'hover:bg-blue-50'
    },
    {
      id: 'licenses',
      label: 'Licenças',
      icon: FileText,
      path: '/licenses',
      color: 'text-green-600',
      bgColor: 'hover:bg-green-50',
      badge: '6'
    },
    {
      id: 'sales',
      label: 'Vendas',
      icon: TrendingUp,
      path: '/vendas',
      color: 'text-purple-600',
      bgColor: 'hover:bg-purple-50'
    }
  ];

  const adminActions = user?.role === 'admin' || user?.role === 'super_admin' ? [
    {
      id: 'admin',
      label: 'Admin',
      icon: UserCog,
      path: '/admin',
      color: 'text-orange-600',
      bgColor: 'hover:bg-orange-50'
    },
    {
      id: 'clients',
      label: 'Clientes',
      icon: Users,
      path: '/clientes',
      color: 'text-indigo-600',
      bgColor: 'hover:bg-indigo-50'
    },
    {
      id: 'registry',
      label: 'Cadastros',
      icon: Tag,
      path: '/cadastros',
      color: 'text-pink-600',
      bgColor: 'hover:bg-pink-50'
    }
  ] : [];

  const superAdminActions = user?.role === 'super_admin' ? [
    {
      id: 'tenants',
      label: 'Multi-Tenant',
      icon: Building,
      path: '/tenants',
      color: 'text-violet-600',
      bgColor: 'hover:bg-violet-50',
      special: true
    }
  ] : [];

  const allActions = [...quickActions, ...adminActions, ...superAdminActions];

  const isActive = (path) => location.pathname === path;

  return (
    <div className={`fixed left-0 top-20 bottom-0 z-40 bg-white border-r border-gray-200 shadow-sm transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-64'
    }`}>
      
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-100">
        {!isCollapsed && (
          <div>
            <h3 className="font-semibold text-gray-900">Acesso Rápido</h3>
            <p className="text-xs text-gray-500">Navegação principal</p>
          </div>
        )}
        
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          {isCollapsed ? 
            <ChevronRight className="w-4 h-4 text-gray-500" /> : 
            <ChevronLeft className="w-4 h-4 text-gray-500" />
          }
        </button>
      </div>

      {/* Quick Actions */}
      <div className="p-2 space-y-1">
        {allActions.map((action) => (
          <Link
            key={action.id}
            to={action.path}
            className={`
              group flex items-center p-3 rounded-lg transition-all duration-200
              ${isActive(action.path) ? 
                'bg-blue-50 border-l-4 border-blue-500 text-blue-700' : 
                `text-gray-700 ${action.bgColor} border-l-4 border-transparent`
              }
              ${action.special ? 'bg-gradient-to-r from-violet-50 to-purple-50' : ''}
            `}
            title={isCollapsed ? action.label : ''}
          >
            {/* Icon */}
            <div className={`flex-shrink-0 ${action.color}`}>
              <action.icon className="w-5 h-5" />
            </div>

            {/* Content */}
            {!isCollapsed && (
              <div className="ml-3 flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{action.label}</span>
                  
                  {/* Badge */}
                  {action.badge && (
                    <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded-full">
                      {action.badge}
                    </span>
                  )}
                  
                  {/* Special indicator */}
                  {action.special && (
                    <Zap className="w-3 h-3 text-yellow-500" />
                  )}
                </div>
              </div>
            )}

            {/* Active indicator */}
            {isActive(action.path) && !isCollapsed && (
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            )}
          </Link>
        ))}
      </div>

      {/* Add New Section */}
      {!isCollapsed && (
        <div className="absolute bottom-4 left-4 right-4">
          <button className="w-full flex items-center justify-center p-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all">
            <Plus className="w-4 h-4 mr-2" />
            <span className="text-sm font-medium">Nova Licença</span>
          </button>
        </div>
      )}

      {/* Collapsed Add Button */}
      {isCollapsed && (
        <div className="absolute bottom-4 left-2 right-2">
          <button className="w-full flex items-center justify-center p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all">
            <Plus className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};

export default QuickAccessPanel;