import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
import axios from 'axios';
import { Button } from './ui/button';
import TenantSelector from './TenantSelector';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from './ui/dropdown-menu';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Badge } from './ui/badge';
import { 
  Shield, 
  User, 
  Settings, 
  LogOut, 
  Home, 
  FileText,
  UserCog,
  Tag,
  Users,
  RotateCcw,
  TrendingUp,
  Building,
  ChevronDown,
  BarChart3,
  Activity,
  Eye,
  Package
} from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [activeDropdown, setActiveDropdown] = useState(null);
  const [licenseCount, setLicenseCount] = useState(0);
  const [loading, setLoading] = useState(true);

  // Fetch license count on component mount
  useEffect(() => {
    const fetchLicenseCount = async () => {
      try {
        const response = await axios.get('/licenses');
        setLicenseCount(response.data.length);
      } catch (error) {
        console.error('Error fetching license count:', error);
        setLicenseCount(0); // Fallback to 0 if error
      } finally {
        setLoading(false);
      }
    };

    fetchLicenseCount();
  }, []);

  const getInitials = (name) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const isActive = (path) => location.pathname === path;

  const navigationGroups = [
    {
      id: 'overview',
      label: 'Visão Geral',
      icon: Home,
      color: 'text-blue-600',
      items: [
        { label: 'Dashboard', path: '/dashboard', icon: BarChart3, description: 'Painel principal' },
        { label: 'Métricas', path: '/vendas', icon: TrendingUp, description: 'Vendas e relatórios' }
      ]
    },
    {
      id: 'licenses',
      label: 'Licenças',
      icon: FileText,
      color: 'text-green-600', 
      badge: '6',
      items: [
        { label: 'Minhas Licenças', path: '/licenses', icon: FileText, description: 'Licenças do usuário' },
        { label: 'Dashboard Vendas', path: '/vendas', icon: TrendingUp, description: 'Vendas e conversões' }
      ]
    }
  ];

  const adminGroups = (user?.role === 'admin' || user?.role === 'super_admin') ? [
    {
      id: 'management',
      label: 'Administração',
      icon: UserCog,
      color: 'text-orange-600',
      items: [
        { label: 'Painel Admin', path: '/admin', icon: UserCog, description: 'Gestão de usuários' },
        { label: 'Clientes', path: '/clientes', icon: Users, description: 'PF e PJ' },
        { label: 'Cadastros', path: '/cadastros', icon: Tag, description: 'Categorias e produtos' },
        { label: 'Manutenção', path: '/manutencao', icon: Activity, description: 'Logs do sistema' },
        // Super Admin exclusive items integrated in the same group
        ...(user?.role === 'super_admin' ? [
          { 
            label: 'Multi-Tenant SaaS', 
            path: '/tenants', 
            icon: Building, 
            description: 'Gestão de tenants',
            special: true 
          }
        ] : [])
      ]
    }
  ] : [];

  const allGroups = [...navigationGroups, ...adminGroups];

  const toggleDropdown = (groupId) => {
    setActiveDropdown(activeDropdown === groupId ? null : groupId);
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          
          {/* Logo */}
          <div className="flex items-center space-x-3 flex-shrink-0">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900 hidden sm:block">
                License Manager
              </span>
            </Link>
          </div>

          {/* Navigation Groups */}
          <div className="hidden md:flex items-center space-x-1 flex-1 justify-center">
            {allGroups.map((group) => (
              <div key={group.id} className="relative">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      className={`flex items-center space-x-2 px-3 py-2 ${
                        group.special ? 'bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200' : ''
                      } ${group.id === 'management' && user?.role === 'super_admin' ? 'relative' : ''}`}
                    >
                      <group.icon className={`w-4 h-4 ${group.color}`} />
                      <span className="text-sm font-medium">{group.label}</span>
                      {group.badge && (
                        <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded-full">
                          {group.badge}
                        </span>
                      )}
                      {/* Super Admin indicator for Administration group */}
                      {group.id === 'management' && user?.role === 'super_admin' && (
                        <span className="bg-purple-100 text-purple-800 text-xs font-medium px-2 py-1 rounded-full">
                          SA+
                        </span>
                      )}
                      <ChevronDown className="w-3 h-3 text-gray-400" />
                    </Button>
                  </DropdownMenuTrigger>
                  
                  <DropdownMenuContent align="center" className="w-64">
                    <DropdownMenuLabel className="flex items-center space-x-2">
                      <group.icon className={`w-4 h-4 ${group.color}`} />
                      <span>{group.label}</span>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    
                    {group.items.map((item) => (
                      <Link key={item.path} to={item.path}>
                        <DropdownMenuItem className={`flex items-start space-x-3 py-3 ${
                          isActive(item.path) ? 'bg-blue-50 text-blue-700' : ''
                        } ${item.special ? 'bg-gradient-to-r from-purple-50 to-indigo-50 border-l-4 border-purple-400' : ''}`}>
                          <item.icon className={`w-4 h-4 mt-0.5 ${
                            item.special ? 'text-purple-600' : 'text-gray-500'
                          }`} />
                          <div className="flex-1">
                            <div className={`font-medium text-sm flex items-center ${
                              item.special ? 'text-purple-900' : ''
                            }`}>
                              {item.label}
                              {item.special && (
                                <span className="ml-2 bg-purple-100 text-purple-800 text-xs font-medium px-2 py-0.5 rounded-full">
                                  SaaS
                                </span>
                              )}
                            </div>
                            <div className={`text-xs ${
                              item.special ? 'text-purple-700' : 'text-gray-500'
                            }`}>
                              {item.description}
                            </div>
                          </div>
                          {isActive(item.path) && (
                            <div className={`w-2 h-2 rounded-full mt-1 ${
                              item.special ? 'bg-purple-600' : 'bg-blue-600'
                            }`}></div>
                          )}
                        </DropdownMenuItem>
                      </Link>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ))}
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-3 flex-shrink-0">
            
            {/* Tenant Selector */}
            {user?.role === 'super_admin' && (
              <div className="hidden lg:block">
                <TenantSelector currentUser={user} />
              </div>
            )}

            {/* User Role Badge */}
            <Badge 
              variant={user?.role === 'admin' ? 'default' : user?.role === 'super_admin' ? 'destructive' : 'secondary'}
              className="text-xs px-2 py-1"
            >
              {user?.role === 'super_admin' ? 'SA' : user?.role === 'admin' ? 'Admin' : 'User'}
            </Badge>

            {/* User Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-blue-500 text-white text-sm">
                      {user?.name ? getInitials(user.name) : 'U'}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">
                      {user?.name}
                    </p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {user?.email}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                
                {/* Mobile Navigation Items */}
                <div className="md:hidden">
                  {allGroups.map((group) => (
                    <div key={group.id}>
                      <DropdownMenuLabel className="text-xs text-gray-500 uppercase tracking-wider">
                        {group.label}
                      </DropdownMenuLabel>
                      {group.items.map((item) => (
                        <Link key={item.path} to={item.path}>
                          <DropdownMenuItem>
                            <item.icon className="mr-2 h-4 w-4" />
                            <span>{item.label}</span>
                          </DropdownMenuItem>
                        </Link>
                      ))}
                      <DropdownMenuSeparator />
                    </div>
                  ))}
                </div>
                
                <DropdownMenuItem>
                  <User className="mr-2 h-4 w-4" />
                  <span>Perfil</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-2 h-4 w-4" />
                  <span>Configurações</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Sair</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;