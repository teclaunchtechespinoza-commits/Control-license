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
  MoreHorizontal,
  Zap,
  Star,
  Bell,
  Search,
  Plus,
  Grid3x3,
  LogOut
} from 'lucide-react';
import TenantSelector from './TenantSelector';

const FloatingNav = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [activeMenu, setActiveMenu] = useState(null);
  const [showNotifications, setShowNotifications] = useState(false);

  const primaryActions = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: Home,
      path: '/dashboard',
      color: 'bg-blue-600 hover:bg-blue-700',
      shortcut: '⌘D'
    },
    {
      id: 'licenses',
      label: 'Licenças',
      icon: FileText,
      path: '/licenses',
      color: 'bg-green-600 hover:bg-green-700',
      badge: '6',
      shortcut: '⌘L'
    },
    {
      id: 'sales',
      label: 'Vendas',
      icon: TrendingUp,
      path: '/vendas',
      color: 'bg-purple-600 hover:bg-purple-700',
      premium: true,
      shortcut: '⌘V'
    }
  ];

  const secondaryActions = [
    ...(user?.role === 'admin' || user?.role === 'super_admin' ? [
      {
        id: 'admin',
        label: 'Admin',
        icon: UserCog,
        path: '/admin',
        color: 'bg-orange-600 hover:bg-orange-700'
      },
      {
        id: 'clients',
        label: 'Clientes',
        icon: Users,
        path: '/clientes',
        color: 'bg-indigo-600 hover:bg-indigo-700'
      },
      {
        id: 'registry',
        label: 'Cadastros',
        icon: Tag,
        path: '/cadastros',
        color: 'bg-pink-600 hover:bg-pink-700'
      }
    ] : []),
    ...(user?.role === 'super_admin' ? [
      {
        id: 'tenants',
        label: 'Multi-Tenant',
        icon: Building,
        path: '/tenants',
        color: 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700',
        special: true
      }
    ] : [])
  ];

  const quickActions = [
    {
      label: 'Nova Licença',
      icon: Plus,
      action: () => console.log('Nova licença'),
      color: 'bg-emerald-500 hover:bg-emerald-600'
    },
    {
      label: 'Buscar',
      icon: Search,
      action: () => console.log('Buscar'),
      color: 'bg-amber-500 hover:bg-amber-600'
    }
  ];

  const isActive = (path) => location.pathname === path;

  const toggleMenu = (menuId) => {
    setActiveMenu(activeMenu === menuId ? null : menuId);
  };

  return (
    <>
      {/* Compact Top Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-200/50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14">
            
            {/* Logo + Breadcrumb */}
            <div className="flex items-center space-x-4">
              <Link to="/dashboard" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                  <Shield className="w-5 h-5 text-white" />
                </div>
                <span className="font-bold text-gray-900 hidden sm:block">License Manager</span>
              </Link>
              
              <div className="hidden md:flex items-center space-x-2 text-sm text-gray-500">
                <span>/</span>
                <span className="font-medium text-gray-900">Dashboard</span>
              </div>
            </div>

            {/* Search Bar */}
            <div className="hidden lg:flex flex-1 max-w-lg mx-8">
              <div className="relative w-full">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Buscar licenças, clientes..."
                  className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Right Actions */}
            <div className="flex items-center space-x-3">
              
              {/* Notifications */}
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Bell className="w-5 h-5" />
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
              </button>

              {/* Tenant Selector - Compact */}
              {user?.role === 'super_admin' && (
                <div className="hidden xl:block">
                  <TenantSelector currentUser={user} />
                </div>
              )}

              {/* User Menu */}
              <div className="relative">
                <button
                  onClick={() => toggleMenu('user')}
                  className="flex items-center space-x-2 p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-xs">
                      {user?.name?.split(' ').map(n => n[0]).join('') || 'U'}
                    </span>
                  </div>
                  <div className="hidden sm:block text-left">
                    <div className="text-sm font-medium text-gray-900">{user?.name}</div>
                    <div className="text-xs text-gray-500">
                      {user?.role === 'super_admin' ? 'Super Admin' : 
                       user?.role === 'admin' ? 'Admin' : 'Usuário'}
                    </div>
                  </div>
                </button>

                {/* User Dropdown */}
                {activeMenu === 'user' && (
                  <div className="absolute right-0 top-full mt-2 w-64 bg-white rounded-xl shadow-2xl border border-gray-200 py-2 z-50">
                    <div className="px-4 py-3 border-b border-gray-100">
                      <div className="font-medium text-gray-900">{user?.name}</div>
                      <div className="text-sm text-gray-500">{user?.email}</div>
                    </div>
                    
                    <Link to="/profile" className="flex items-center px-4 py-3 hover:bg-gray-50 transition-colors">
                      <Settings className="w-4 h-4 mr-3 text-gray-400" />
                      <span>Configurações</span>
                    </Link>
                    
                    <button
                      onClick={logout}
                      className="w-full flex items-center px-4 py-3 hover:bg-gray-50 transition-colors text-red-600"
                    >
                      <LogOut className="w-4 h-4 mr-3" />
                      <span>Sair</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Floating Action Hub */}
      <div className="fixed bottom-8 right-8 z-50">
        
        {/* Quick Actions */}
        <div className="mb-4 space-y-3">
          {quickActions.map((action, index) => (
            <button
              key={index}
              onClick={action.action}
              className={`${action.color} text-white p-3 rounded-full shadow-2xl transition-all hover:scale-110 transform`}
              title={action.label}
            >
              <action.icon className="w-5 h-5" />
            </button>
          ))}
        </div>

        {/* Main Menu Button */}
        <button
          onClick={() => toggleMenu('main')}
          className={`bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white p-4 rounded-full shadow-2xl transition-all hover:scale-105 transform ${
            activeMenu === 'main' ? 'rotate-45' : ''
          }`}
        >
          <Grid3x3 className="w-6 h-6" />
        </button>

        {/* Floating Menu */}
        {activeMenu === 'main' && (
          <div className="absolute bottom-full right-0 mb-4 bg-white rounded-2xl shadow-2xl border border-gray-200 p-4 min-w-80">
            
            {/* Primary Actions */}
            <div className="mb-6">
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
                Navegação Principal
              </h3>
              <div className="grid grid-cols-3 gap-3">
                {primaryActions.map((action) => (
                  <Link
                    key={action.id}
                    to={action.path}
                    className={`relative group ${action.color} text-white p-4 rounded-xl transition-all hover:scale-105 transform ${
                      isActive(action.path) ? 'ring-2 ring-offset-2 ring-blue-500' : ''
                    }`}
                    onClick={() => setActiveMenu(null)}
                  >
                    <action.icon className="w-6 h-6 mb-2" />
                    <div className="text-sm font-medium">{action.label}</div>
                    {action.shortcut && (
                      <div className="text-xs opacity-75 mt-1">{action.shortcut}</div>
                    )}
                    
                    {/* Badges */}
                    {action.badge && (
                      <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                        {action.badge}
                      </span>
                    )}
                    
                    {action.premium && (
                      <Star className="absolute top-2 right-2 w-4 h-4 text-yellow-300" />
                    )}
                  </Link>
                ))}
              </div>
            </div>

            {/* Secondary Actions */}
            {secondaryActions.length > 0 && (
              <div>
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
                  Administração
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {secondaryActions.map((action) => (
                    <Link
                      key={action.id}
                      to={action.path}
                      className={`${action.color} ${action.special ? 'text-white' : 'text-white'} p-3 rounded-xl transition-all hover:scale-105 transform text-center ${
                        isActive(action.path) ? 'ring-2 ring-offset-2 ring-blue-500' : ''
                      }`}
                      onClick={() => setActiveMenu(null)}
                    >
                      <action.icon className="w-5 h-5 mx-auto mb-1" />
                      <div className="text-sm font-medium">{action.label}</div>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Notifications Panel */}
      {showNotifications && (
        <div className="fixed top-16 right-8 w-80 bg-white rounded-xl shadow-2xl border border-gray-200 z-50">
          <div className="p-4 border-b border-gray-100">
            <h3 className="font-medium text-gray-900">Notificações</h3>
          </div>
          <div className="p-4 space-y-3">
            <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
              <Bell className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <div className="text-sm font-medium text-gray-900">
                  Nova licença criada
                </div>
                <div className="text-xs text-gray-500">há 5 minutos</div>
              </div>
            </div>
            <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
              <Zap className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div>
                <div className="text-sm font-medium text-gray-900">
                  Licença expirando em 3 dias
                </div>
                <div className="text-xs text-gray-500">há 1 hora</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Overlay */}
      {(activeMenu || showNotifications) && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => {
            setActiveMenu(null);
            setShowNotifications(false);
          }}
        />
      )}

      {/* Main content spacer */}
      <div className="pt-14">
        {/* This ensures content doesn't hide behind the header */}
      </div>
    </>
  );
};

export default FloatingNav;