import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
import { 
  Shield, 
  Home, 
  FileText, 
  TrendingUp, 
  Users, 
  UserCog, 
  Tag, 
  Building, 
  Settings,
  Menu,
  X,
  ChevronRight,
  Zap,
  BarChart3,
  Database,
  Bell,
  Search,
  Plus
} from 'lucide-react';
import TenantSelector from './TenantSelector';

const ModernSidebar = () => {
  const { user } = useAuth();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [activeSubmenu, setActiveSubmenu] = useState(null);

  const navigationItems = [
    {
      id: 'overview',
      label: 'Visão Geral',
      icon: Home,
      path: '/dashboard',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      description: 'Dashboard principal'
    },
    {
      id: 'licenses',
      label: 'Licenças',
      icon: FileText,
      path: '/licenses',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      description: 'Gerenciar licenças',
      badge: '6'
    },
    {
      id: 'sales',
      label: 'Vendas',
      icon: TrendingUp,
      path: '/vendas',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      description: 'Dashboard de vendas',
      premium: true
    }
  ];

  const adminItems = [
    {
      id: 'management',
      label: 'Gestão',
      icon: UserCog,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      description: 'Administração do sistema',
      children: [
        { label: 'Painel Admin', path: '/admin', icon: UserCog },
        { label: 'Clientes', path: '/clientes', icon: Users },
        { label: 'Cadastros', path: '/cadastros', icon: Tag },
        { label: 'Manutenção', path: '/manutencao', icon: Settings }
      ]
    }
  ];

  const superAdminItems = [
    {
      id: 'tenants',
      label: 'Multi-Tenant',
      icon: Building,
      path: '/tenants',
      color: 'text-indigo-600',
      bgColor: 'bg-gradient-to-r from-purple-50 to-indigo-50',
      description: 'Gestão SaaS',
      special: true,
      badge: 'SA'
    }
  ];

  const quickActions = [
    {
      label: 'Nova Licença',
      icon: Plus,
      action: () => console.log('Nova licença'),
      color: 'bg-blue-600 hover:bg-blue-700'
    },
    {
      label: 'Relatório',
      icon: BarChart3,
      action: () => console.log('Gerar relatório'),
      color: 'bg-green-600 hover:bg-green-700'
    },
    {
      label: 'Buscar',
      icon: Search,
      action: () => console.log('Buscar'),
      color: 'bg-purple-600 hover:bg-purple-700'
    }
  ];

  const isActive = (path) => location.pathname === path;

  const allItems = [
    ...navigationItems,
    ...(user?.role === 'admin' || user?.role === 'super_admin' ? adminItems : []),
    ...(user?.role === 'super_admin' ? superAdminItems : [])
  ];

  const toggleSubmenu = (itemId) => {
    setActiveSubmenu(activeSubmenu === itemId ? null : itemId);
  };

  return (
    <>
      {/* Overlay for mobile */}
      {!isCollapsed && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setIsCollapsed(true)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed left-0 top-0 h-full bg-white shadow-2xl z-50 transition-all duration-300 ${
        isCollapsed ? 'w-16' : 'w-80'
      }`}>
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className={`flex items-center space-x-3 ${isCollapsed ? 'justify-center' : ''}`}>
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            {!isCollapsed && (
              <div>
                <h1 className="text-lg font-bold text-gray-900">License Manager</h1>
                <p className="text-xs text-gray-500">Sistema Multi-Tenant</p>
              </div>
            )}
          </div>
          
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {isCollapsed ? <Menu className="w-5 h-5" /> : <X className="w-5 h-5" />}
          </button>
        </div>

        {/* Tenant Selector */}
        {!isCollapsed && user?.role === 'super_admin' && (
          <div className="p-4 border-b border-gray-200">
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 block">
              Tenant Atual
            </label>
            <TenantSelector currentUser={user} />
          </div>
        )}

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto py-4">
          {/* Quick Actions */}
          {!isCollapsed && (
            <div className="px-4 mb-6">
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
                Ações Rápidas
              </h3>
              <div className="grid grid-cols-3 gap-2">
                {quickActions.map((action, index) => (
                  <button
                    key={index}
                    onClick={action.action}
                    className={`${action.color} text-white p-3 rounded-lg transition-all hover:scale-105 flex flex-col items-center space-y-1`}
                    title={action.label}
                  >
                    <action.icon className="w-4 h-4" />
                    <span className="text-xs font-medium">{action.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Navigation Items */}
          <nav className="px-2">
            {allItems.map((item) => (
              <div key={item.id} className="mb-2">
                {/* Main Item */}
                {item.children ? (
                  <button
                    onClick={() => toggleSubmenu(item.id)}
                    className={`w-full flex items-center p-3 rounded-xl transition-all hover:bg-gray-50 group ${
                      activeSubmenu === item.id ? 'bg-gray-50' : ''
                    }`}
                  >
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${item.bgColor} mr-3`}>
                      <item.icon className={`w-5 h-5 ${item.color}`} />
                    </div>
                    
                    {!isCollapsed && (
                      <>
                        <div className="flex-1 text-left">
                          <div className="font-medium text-gray-900">{item.label}</div>
                          <div className="text-xs text-gray-500">{item.description}</div>
                        </div>
                        
                        <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${
                          activeSubmenu === item.id ? 'rotate-90' : ''
                        }`} />
                      </>
                    )}
                  </button>
                ) : (
                  <Link
                    to={item.path}
                    className={`flex items-center p-3 rounded-xl transition-all hover:bg-gray-50 group ${
                      isActive(item.path) ? `${item.bgColor} shadow-md` : ''
                    } ${item.special ? 'bg-gradient-to-r from-purple-50 to-indigo-50 border-2 border-purple-200' : ''}`}
                  >
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      isActive(item.path) ? 'bg-white shadow-sm' : item.bgColor
                    } mr-3`}>
                      <item.icon className={`w-5 h-5 ${
                        isActive(item.path) ? item.color : item.color
                      }`} />
                    </div>
                    
                    {!isCollapsed && (
                      <div className="flex-1">
                        <div className={`font-medium ${
                          isActive(item.path) ? 'text-gray-900' : 'text-gray-700'
                        }`}>
                          {item.label}
                        </div>
                        <div className="text-xs text-gray-500">{item.description}</div>
                      </div>
                    )}
                    
                    {/* Badges */}
                    {!isCollapsed && item.badge && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        item.special ? 'bg-purple-600 text-white' : 'bg-blue-100 text-blue-800'
                      }`}>
                        {item.badge}
                      </span>
                    )}
                    
                    {!isCollapsed && item.premium && (
                      <Zap className="w-4 h-4 text-yellow-500" />
                    )}
                  </Link>
                )}

                {/* Submenu */}
                {item.children && activeSubmenu === item.id && !isCollapsed && (
                  <div className="ml-6 mt-2 space-y-1">
                    {item.children.map((child) => (
                      <Link
                        key={child.path}
                        to={child.path}
                        className={`flex items-center p-2 rounded-lg hover:bg-gray-50 transition-colors ${
                          isActive(child.path) ? 'bg-blue-50 text-blue-700' : 'text-gray-600'
                        }`}
                      >
                        <child.icon className="w-4 h-4 mr-3" />
                        <span className="text-sm font-medium">{child.label}</span>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>
        </div>

        {/* User Profile */}
        <div className="p-4 border-t border-gray-200">
          <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'space-x-3'}`}>
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">
                {user?.name?.split(' ').map(n => n[0]).join('') || 'U'}
              </span>
            </div>
            
            {!isCollapsed && (
              <div className="flex-1">
                <div className="font-medium text-gray-900 text-sm">{user?.name}</div>
                <div className="text-xs text-gray-500">{user?.email}</div>
                <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mt-1 ${
                  user?.role === 'super_admin' ? 'bg-purple-100 text-purple-800' :
                  user?.role === 'admin' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {user?.role === 'super_admin' ? 'Super Admin' : 
                   user?.role === 'admin' ? 'Administrador' : 'Usuário'}
                </div>
              </div>
            )}
            
            {!isCollapsed && (
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <Settings className="w-4 h-4 text-gray-400" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Spacer */}
      <div className={`transition-all duration-300 ${isCollapsed ? 'ml-16' : 'ml-80'}`}>
        {/* This div pushes the main content to the right of the sidebar */}
      </div>
    </>
  );
};

export default ModernSidebar;