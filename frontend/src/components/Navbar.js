import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
import { Button } from './ui/button';
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
  Building
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-4">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900 hidden sm:block">
                License Manager
              </span>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            <Link to="/dashboard">
              <Button
                variant={isActive('/dashboard') ? 'default' : 'ghost'}
                size="sm"
                className="flex items-center space-x-2"
              >
                <Home className="w-4 h-4" />
                <span>Dashboard</span>
              </Button>
            </Link>
            
            <Link to="/licenses">
              <Button
                variant={isActive('/licenses') ? 'default' : 'ghost'}
                size="sm"
                className="flex items-center space-x-2"
              >
                <FileText className="w-4 h-4" />
                <span>Minhas Licenças</span>
              </Button>
            </Link>

            <Link to="/vendas">
              <Button
                variant={isActive('/vendas') ? 'default' : 'ghost'}
                size="sm"
                className="flex items-center space-x-2"
              >
                <TrendingUp className="w-4 h-4" />
                <span>Dashboard Vendas</span>
              </Button>
            </Link>
            
            {user?.role === 'admin' && (
              <>
                <Link to="/admin">
                  <Button
                    variant={isActive('/admin') ? 'default' : 'ghost'}
                    size="sm"
                    className="flex items-center space-x-2"
                  >
                    <UserCog className="w-4 h-4" />
                    <span>Admin</span>
                  </Button>
                </Link>
                
                <Link to="/clientes">
                  <Button
                    variant={isActive('/clientes') ? 'default' : 'ghost'}
                    size="sm"
                    className="flex items-center space-x-2"
                  >
                    <Users className="w-4 h-4" />
                    <span>Clientes</span>
                  </Button>
                </Link>
                
                <Link to="/cadastros">
                  <Button
                    variant={isActive('/cadastros') ? 'default' : 'ghost'}
                    size="sm"
                    className="flex items-center space-x-2"
                  >
                    <Tag className="w-4 h-4" />
                    <span>Cadastros</span>
                  </Button>
                </Link>
                
                <Link to="/manutencao">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="flex items-center space-x-2"
                  >
                    <FileText className="w-4 h-4" />
                    <span>Manutenção</span>
                  </Button>
                </Link>
              </>
            )}
            
            {/* Global Refresh Button */}
            <Button
              onClick={() => {
                console.log('Global refresh triggered');
                window.location.reload();
              }}
              variant="ghost"
              size="sm"
              className="flex items-center space-x-2 text-blue-600 hover:bg-blue-50"
              title="Atualizar página e dados"
            >
              <RotateCcw className="w-4 h-4" />
              <span className="hidden sm:inline">Atualizar</span>
            </Button>
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {/* User Role Badge */}
            <Badge variant={user?.role === 'admin' ? 'default' : 'secondary'}>
              {user?.role === 'admin' ? 'Admin' : 'Usuário'}
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
                  {user?.role === 'admin' && (
                    <>
                      <Link to="/admin">
                        <DropdownMenuItem>
                          <UserCog className="mr-2 h-4 w-4" />
                          <span>Admin Panel</span>
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
                    </>
                  )}
                  <DropdownMenuSeparator />
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
                <DropdownMenuItem 
                  onClick={logout}
                  className="text-red-600 focus:text-red-600"
                >
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