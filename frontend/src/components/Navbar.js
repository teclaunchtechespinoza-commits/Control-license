import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
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
  Layout,
  Menu,
  Layers,
  Grid3x3
} from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const getInitials = (name) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-6">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Brand */}
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

          {/* Navigation Links - Compacted */}
          <div className="hidden lg:flex items-center space-x-1 flex-1 justify-center max-w-3xl">
            <Link to="/dashboard">
              <Button
                variant={isActive('/dashboard') ? 'default' : 'ghost'}
                size="sm"
                className="flex items-center space-x-1 px-2"
              >
                <Home className="w-4 h-4" />
                <span className="text-xs">Dashboard</span>
              </Button>
            </Link>
            
            <Link to="/licenses">
              <Button
                variant={isActive('/licenses') ? 'default' : 'ghost'}
                size="sm"
                className="flex items-center space-x-1 px-2"
              >
                <FileText className="w-4 h-4" />
                <span className="text-xs">Licenças</span>
              </Button>
            </Link>

            <Link to="/vendas">
              <Button
                variant={isActive('/vendas') ? 'default' : 'ghost'}
                size="sm"
                className="flex items-center space-x-1 px-2"
              >
                <TrendingUp className="w-4 h-4" />
                <span className="text-xs">Vendas</span>
              </Button>
            </Link>
            
            {user?.role === 'admin' && (
              <>
                <Link to="/admin">
                  <Button
                    variant={isActive('/admin') ? 'default' : 'ghost'}
                    size="sm"
                    className="flex items-center space-x-1 px-2"
                  >
                    <UserCog className="w-4 h-4" />
                    <span className="text-xs">Admin</span>
                  </Button>
                </Link>
                
                <Link to="/clientes">
                  <Button
                    variant={isActive('/clientes') ? 'default' : 'ghost'}
                    size="sm"
                    className="flex items-center space-x-1 px-2"
                  >
                    <Users className="w-4 h-4" />
                    <span className="text-xs">Clientes</span>
                  </Button>
                </Link>
                
                <Link to="/cadastros">
                  <Button
                    variant={isActive('/cadastros') ? 'default' : 'ghost'}
                    size="sm"
                    className="flex items-center space-x-1 px-2"
                  >
                    <Tag className="w-4 h-4" />
                    <span className="text-xs">Cadastros</span>
                  </Button>
                </Link>
                
                <Link to="/manutencao">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="flex items-center space-x-1 px-2"
                  >
                    <FileText className="w-4 h-4" />
                    <span className="text-xs">Manutenção</span>
                  </Button>
                </Link>
              </>
            )}
            
            {user?.role === 'super_admin' && (
              <Link to="/tenants">
                <Button
                  variant={isActive('/tenants') ? 'default' : 'ghost'}
                  size="sm"
                  className="flex items-center space-x-1 px-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700"
                >
                  <Building className="w-4 h-4" />
                  <span className="text-xs">Multi-Tenant</span>
                </Button>
              </Link>
            )}
            
            {/* Global Refresh Button */}
            <Button
              onClick={() => {
                console.log('Global refresh triggered');
                window.location.reload();
              }}
              variant="ghost"
              size="sm"
              className="flex items-center space-x-1 px-2"
              title="Atualizar Página"
            >
              <RotateCcw className="w-4 h-4" />
              <span className="text-xs hidden xl:inline">Atualizar</span>
            </Button>
          </div>

          {/* User Menu - Compact */}
          <div className="flex items-center space-x-3 flex-shrink-0">
            
            {/* Tenant Selector - Only for large screens */}
            <div className="hidden xl:block">
              <TenantSelector currentUser={user} />
            </div>

            {/* User Role Badge - Compact */}
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
                <div className="lg:hidden">
                  <Link to="/dashboard">
                    <DropdownMenuItem>
                      <Home className="mr-2 h-4 w-4" />
                      <span>Dashboard</span>
                    </DropdownMenuItem>
                  </Link>
                  <Link to="/licenses">
                    <DropdownMenuItem>
                      <FileText className="mr-2 h-4 w-4" />
                      <span>Minhas Licenças</span>
                    </DropdownMenuItem>
                  </Link>
                  <Link to="/vendas">
                    <DropdownMenuItem>
                      <TrendingUp className="mr-2 h-4 w-4" />
                      <span>Dashboard Vendas</span>
                    </DropdownMenuItem>
                  </Link>
                  {user?.role === 'admin' && (
                    <>
                      <Link to="/admin">
                        <DropdownMenuItem>
                          <UserCog className="mr-2 h-4 w-4" />
                          <span>Admin</span>
                        </DropdownMenuItem>
                      </Link>
                      <Link to="/clientes">
                        <DropdownMenuItem>
                          <Users className="mr-2 h-4 w-4" />
                          <span>Clientes</span>
                        </DropdownMenuItem>
                      </Link>
                      <Link to="/cadastros">
                        <DropdownMenuItem>
                          <Tag className="mr-2 h-4 w-4" />
                          <span>Cadastros</span>
                        </DropdownMenuItem>
                      </Link>
                      <Link to="/manutencao">
                        <DropdownMenuItem>
                          <FileText className="mr-2 h-4 w-4" />
                          <span>Manutenção</span>
                        </DropdownMenuItem>
                      </Link>
                    </>
                  )}
                  {user?.role === 'super_admin' && (
                    <Link to="/tenants">
                      <DropdownMenuItem>
                        <Building className="mr-2 h-4 w-4" />
                        <span>Multi-Tenant</span>
                      </DropdownMenuItem>
                    </Link>
                  )}
                  <DropdownMenuSeparator />
                </div>

                {/* Tenant Selector for Mobile/Tablet */}
                <div className="xl:hidden mb-2">
                  {user?.role === 'super_admin' && (
                    <>
                      <DropdownMenuLabel>Tenant Atual</DropdownMenuLabel>
                      <div className="px-2 py-1">
                        <TenantSelector currentUser={user} />
                      </div>
                      <DropdownMenuSeparator />
                    </>
                  )}
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