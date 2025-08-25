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
  ChevronDown,
  Zap,
  Star,
  Activity,
  BarChart3,
  Database,
  Eye,
  MousePointer
} from 'lucide-react';
import TenantSelector from './TenantSelector';

const CascadeNav = ({ currentLayout, layouts, onLayoutChange }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [hoveredCard, setHoveredCard] = useState(null);
  const [activeLevel, setActiveLevel] = useState(1);

  const navigationLevels = {
    1: { // Primary Level
      title: 'Área Principal',
      cards: [
        {
          id: 'overview',
          title: 'Visão Geral',
          subtitle: 'Dashboard e métricas',
          icon: Home,
          path: '/dashboard',
          color: 'from-blue-500 to-cyan-500',
          stats: '6 alertas',
          level: 1
        },
        {
          id: 'business',
          title: 'Negócios',
          subtitle: 'Vendas e licenças',
          icon: TrendingUp,
          color: 'from-emerald-500 to-green-500',
          stats: 'R$ 25.8k',
          hasSubmenu: true,
          level: 1
        }
      ]
    },
    2: { // Business Submenu
      title: 'Gestão de Negócios',
      parent: 'business',
      cards: [
        {
          id: 'licenses',
          title: 'Licenças',
          subtitle: 'Gerenciar licenças',
          icon: FileText,
          path: '/licenses',
          color: 'from-green-500 to-emerald-500',
          stats: '142 ativas',
          level: 2
        },
        {
          id: 'sales',
          title: 'Vendas',
          subtitle: 'Dashboard comercial',
          icon: BarChart3,
          path: '/vendas',
          color: 'from-purple-500 to-pink-500',
          stats: '89% meta',
          level: 2
        }
      ]
    },
    3: { // Admin Level
      title: 'Administração',
      condition: () => user?.role === 'admin' || user?.role === 'super_admin',
      cards: [
        {
          id: 'management',
          title: 'Gestão',
          subtitle: 'Usuários e sistema',
          icon: UserCog,
          color: 'from-orange-500 to-red-500',
          stats: '24 usuários',
          hasSubmenu: true,
          level: 3
        },
        {
          id: 'data',
          title: 'Dados',
          subtitle: 'Clientes e cadastros',
          icon: Database,
          color: 'from-indigo-500 to-purple-500',
          stats: '1.2k registros',
          hasSubmenu: true,
          level: 3
        }
      ]
    },
    4: { // Management Submenu
      title: 'Gestão do Sistema',
      parent: 'management',
      cards: [
        {
          id: 'admin',
          title: 'Painel Admin',
          subtitle: 'Configurações gerais',
          icon: Settings,
          path: '/admin',
          color: 'from-orange-500 to-red-500',
          level: 4
        },
        {
          id: 'maintenance',
          title: 'Manutenção',
          subtitle: 'Logs e sistema',
          icon: Activity,
          path: '/manutencao',
          color: 'from-gray-500 to-gray-600',
          level: 4
        }
      ]
    },
    5: { // Data Submenu
      title: 'Gestão de Dados',
      parent: 'data',
      cards: [
        {
          id: 'clients',
          title: 'Clientes',
          subtitle: 'PF e PJ',
          icon: Users,
          path: '/clientes',
          color: 'from-indigo-500 to-blue-500',
          stats: '458 clientes',
          level: 5
        },
        {
          id: 'registry',
          title: 'Cadastros',
          subtitle: 'Categorias e produtos',
          icon: Tag,
          path: '/cadastros',
          color: 'from-purple-500 to-indigo-500',
          stats: '89 itens',
          level: 5
        }
      ]
    },
    6: { // Super Admin Level
      title: 'Multi-Tenancy',
      condition: () => user?.role === 'super_admin',
      cards: [
        {
          id: 'tenants',
          title: 'Tenants SaaS',
          subtitle: 'Gestão multi-inquilino',
          icon: Building,
          path: '/tenants',
          color: 'from-purple-600 to-indigo-600',
          stats: '12 tenants',
          special: true,
          level: 6
        }
      ]
    }
  };

  const isActive = (path) => location.pathname === path;

  const handleCardClick = (card) => {
    if (card.hasSubmenu) {
      // Find the next level that has this card as parent
      const nextLevel = Object.entries(navigationLevels).find(([level, data]) => 
        data.parent === card.id
      );
      if (nextLevel) {
        setActiveLevel(parseInt(nextLevel[0]));
      }
    } else if (card.path) {
      // Navigate to the path
      // This will be handled by the Link component
    }
  };

  const goToLevel = (level) => {
    setActiveLevel(level);
  };

  const getCurrentLevel = () => {
    const level = navigationLevels[activeLevel];
    if (level?.condition && !level.condition()) {
      // Skip to next available level
      const nextLevel = Object.entries(navigationLevels)
        .find(([lvl, data]) => parseInt(lvl) > activeLevel && (!data.condition || data.condition()));
      if (nextLevel) {
        setActiveLevel(parseInt(nextLevel[0]));
        return navigationLevels[parseInt(nextLevel[0])];
      }
    }
    return level;
  };

  const currentLevel = getCurrentLevel();

  const getBreadcrumb = () => {
    const breadcrumb = [];
    let level = activeLevel;
    
    while (level > 1 && navigationLevels[level]?.parent) {
      const currentLevelData = navigationLevels[level];
      breadcrumb.unshift(currentLevelData.title);
      
      // Find parent level
      const parentId = currentLevelData.parent;
      let parentLevel = null;
      for (const [lvl, data] of Object.entries(navigationLevels)) {
        if (data.cards?.some(card => card.id === parentId)) {
          parentLevel = parseInt(lvl);
          break;
        }
      }
      level = parentLevel || 1;
    }
    
    return breadcrumb;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-100">
      
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            
            {/* Logo + Breadcrumb */}
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">License Manager</h1>
                  <p className="text-sm text-gray-500">Sistema Multi-Tenant SaaS</p>
                </div>
              </div>
              
              {/* Breadcrumb */}
              <div className="hidden md:flex items-center space-x-2 text-sm">
                <button
                  onClick={() => goToLevel(1)}
                  className="text-blue-600 hover:text-blue-800 transition-colors"
                >
                  Início
                </button>
                {getBreadcrumb().map((crumb, index) => (
                  <React.Fragment key={index}>
                    <span className="text-gray-400">/</span>
                    <span className="text-gray-600">{crumb}</span>
                  </React.Fragment>
                ))}
              </div>
            </div>

            {/* User Info + Tenant + Layout Switcher */}
            <div className="flex items-center space-x-4">
              
              {/* Layout Switcher */}
              {layouts && onLayoutChange && (
                <select 
                  value={currentLayout}
                  onChange={(e) => onLayoutChange(e.target.value)}
                  className="bg-white/80 border border-gray-200 rounded-lg px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {layouts.map((layout) => (
                    <option key={layout.id} value={layout.id}>
                      {layout.name}
                    </option>
                  ))}
                </select>
              )}
              
              {user?.role === 'super_admin' && (
                <div className="hidden lg:block">
                  <TenantSelector currentUser={user} />
                </div>
              )}
              
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold text-sm">
                    {user?.name?.split(' ').map(n => n[0]).join('') || 'U'}
                  </span>
                </div>
                <div className="hidden sm:block">
                  <div className="text-sm font-medium text-gray-900">{user?.name}</div>
                  <div className="text-xs text-gray-500">
                    {user?.role === 'super_admin' ? 'Super Administrador' : 
                     user?.role === 'admin' ? 'Administrador' : 'Usuário'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Level Navigation */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        
        {/* Level Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                {currentLevel?.title || 'Navegação'}
              </h2>
              <p className="text-gray-600">
                Selecione uma opção para continuar
              </p>
            </div>
            
            {activeLevel > 1 && (
              <button
                onClick={() => goToLevel(activeLevel - 1)}
                className="flex items-center px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-white transition-all"
              >
                ← Voltar
              </button>
            )}
          </div>
          
          {/* Level Indicator */}
          <div className="flex items-center space-x-2 mt-4">
            {[1, 2, 3, 4, 5, 6].filter(level => navigationLevels[level]).map((level) => (
              <button
                key={level}
                onClick={() => goToLevel(level)}
                className={`w-3 h-3 rounded-full transition-all ${
                  level === activeLevel ? 'bg-blue-600' :
                  level < activeLevel ? 'bg-blue-300' : 'bg-gray-300'
                }`}
                title={navigationLevels[level]?.title}
              />
            ))}
          </div>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {currentLevel?.cards?.map((card) => (
            <div
              key={card.id}
              className="group relative"
              onMouseEnter={() => setHoveredCard(card.id)}
              onMouseLeave={() => setHoveredCard(null)}
            >
              {card.path ? (
                <Link to={card.path} onClick={() => handleCardClick(card)}>
                  <CardContent card={card} isHovered={hoveredCard === card.id} isActive={isActive(card.path)} />
                </Link>
              ) : (
                <button onClick={() => handleCardClick(card)} className="w-full text-left">
                  <CardContent card={card} isHovered={hoveredCard === card.id} />
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Quick Stats */}
        <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="bg-white/70 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">142</div>
                <div className="text-sm text-gray-500">Licenças Ativas</div>
              </div>
              <FileText className="w-8 h-8 text-green-600" />
            </div>
          </div>
          
          <div className="bg-white/70 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">89%</div>
                <div className="text-sm text-gray-500">Meta Vendas</div>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-600" />
            </div>
          </div>
          
          <div className="bg-white/70 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">458</div>
                <div className="text-sm text-gray-500">Clientes</div>
              </div>
              <Users className="w-8 h-8 text-indigo-600" />
            </div>
          </div>
          
          <div className="bg-white/70 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {user?.role === 'super_admin' ? '12' : '1'}
                </div>
                <div className="text-sm text-gray-500">
                  {user?.role === 'super_admin' ? 'Tenants' : 'Sistema'}
                </div>
              </div>
              <Building className="w-8 h-8 text-blue-600" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Card Content Component
const CardContent = ({ card, isHovered, isActive }) => (
  <div className={`
    bg-white/80 backdrop-blur-sm rounded-2xl p-6 border border-gray-200/50 
    transition-all duration-300 hover:scale-105 hover:shadow-2xl
    ${isActive ? 'ring-2 ring-blue-500 bg-blue-50/80' : ''}
    ${isHovered ? 'bg-white shadow-xl transform -translate-y-1' : ''}
    ${card.special ? 'bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200' : ''}
  `}>
    
    {/* Icon and Status */}
    <div className="flex items-start justify-between mb-4">
      <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${card.color} flex items-center justify-center shadow-lg`}>
        <card.icon className="w-6 h-6 text-white" />
      </div>
      
      <div className="flex flex-col items-end space-y-2">
        {card.hasSubmenu && (
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${
            isHovered ? 'rotate-180' : ''
          }`} />
        )}
        
        {card.special && (
          <div className="flex items-center space-x-1">
            <Star className="w-4 h-4 text-yellow-500" />
            <span className="text-xs text-purple-600 font-medium">SAAS</span>
          </div>
        )}
      </div>
    </div>

    {/* Content */}
    <div className="mb-4">
      <h3 className="text-lg font-bold text-gray-900 mb-1">
        {card.title}
      </h3>
      <p className="text-sm text-gray-600">
        {card.subtitle}
      </p>
    </div>

    {/* Stats */}
    {card.stats && (
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-500">
          {card.stats}
        </span>
        <Activity className="w-4 h-4 text-gray-400" />
      </div>
    )}

    {/* Hover Effect */}
    {isHovered && (
      <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-purple-600/10 rounded-2xl pointer-events-none" />
    )}
  </div>
);

export default CascadeNav;