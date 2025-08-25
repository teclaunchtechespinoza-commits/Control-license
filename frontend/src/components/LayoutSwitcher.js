import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import Navbar from './Navbar';
import ModernSidebar from './ModernSidebar';
import FloatingNav from './FloatingNav';
import CascadeNav from './CascadeNav';
import { 
  Layout, 
  Menu, 
  Layers, 
  Grid3x3, 
  Settings,
  Eye
} from 'lucide-react';

const LayoutSwitcher = ({ children }) => {
  const { user } = useAuth();
  const [currentLayout, setCurrentLayout] = useState('original');
  const [showSwitcher, setShowSwitcher] = useState(false);

  const layouts = [
    {
      id: 'original',
      name: 'Layout Original',
      description: 'Navbar horizontal clássica',
      icon: Layout,
      color: 'bg-blue-600',
      component: Navbar
    },
    {
      id: 'sidebar',
      name: 'Sidebar Moderna',
      description: 'Menu lateral colapsável com contexto',
      icon: Menu,
      color: 'bg-green-600',
      component: ModernSidebar
    },
    {
      id: 'floating',
      name: 'Navegação Flutuante',
      description: 'Header compacto + menu flutuante',
      icon: Layers,
      color: 'bg-purple-600',
      component: FloatingNav
    },
    {
      id: 'cascade',
      name: 'Navegação em Cascata',
      description: 'Cards hierárquicos em níveis',
      icon: Grid3x3,
      color: 'bg-indigo-600',
      component: CascadeNav
    }
  ];

  // Load saved layout preference
  useEffect(() => {
    const savedLayout = localStorage.getItem('preferredLayout');
    if (savedLayout && layouts.find(l => l.id === savedLayout)) {
      setCurrentLayout(savedLayout);
    }
  }, []);

  // Save layout preference
  const changeLayout = (layoutId) => {
    setCurrentLayout(layoutId);
    localStorage.setItem('preferredLayout', layoutId);
    setShowSwitcher(false);
  };

  const getCurrentLayout = () => {
    return layouts.find(l => l.id === currentLayout) || layouts[0];
  };

  const LayoutComponent = getCurrentLayout().component;

  // Special handling for cascade layout (full page)
  if (currentLayout === 'cascade') {
    return (
      <>
        <CascadeNav />
        
        {/* Layout Switcher Button */}
        <div className="fixed top-4 right-4 z-50">
          <div className="relative">
            <button
              onClick={() => setShowSwitcher(!showSwitcher)}
              className="bg-white/90 backdrop-blur-md text-gray-700 p-3 rounded-full shadow-2xl hover:bg-white transition-all border border-gray-200/50"
              title="Trocar Layout"
            >
              <Eye className="w-5 h-5" />
            </button>

            {showSwitcher && <LayoutSwitcherMenu />}
          </div>
        </div>
      </>
    );
  }

  // Regular layouts with navigation + content
  const LayoutSwitcherMenu = () => (
    <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-2xl border border-gray-200 z-50 overflow-hidden">
      <div className="p-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <h3 className="font-bold text-lg mb-1">Escolher Layout</h3>
        <p className="text-sm opacity-90">Personalize sua experiência</p>
      </div>
      
      <div className="p-2">
        {layouts.map((layout) => (
          <button
            key={layout.id}
            onClick={() => changeLayout(layout.id)}
            className={`w-full flex items-center p-3 rounded-lg hover:bg-gray-50 transition-colors text-left ${
              currentLayout === layout.id ? 'bg-blue-50 border border-blue-200' : ''
            }`}
          >
            <div className={`w-10 h-10 ${layout.color} rounded-lg flex items-center justify-center mr-3`}>
              <layout.icon className="w-5 h-5 text-white" />
            </div>
            
            <div className="flex-1">
              <div className={`font-medium ${currentLayout === layout.id ? 'text-blue-900' : 'text-gray-900'}`}>
                {layout.name}
              </div>
              <div className={`text-sm ${currentLayout === layout.id ? 'text-blue-700' : 'text-gray-500'}`}>
                {layout.description}
              </div>
            </div>
            
            {currentLayout === layout.id && (
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
            )}
          </button>
        ))}
      </div>
      
      <div className="p-4 bg-gray-50 border-t">
        <p className="text-xs text-gray-500 text-center">
          Sua preferência será salva automaticamente
        </p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Component */}
      <LayoutComponent />

      {/* Main Content */}
      <div className={`${currentLayout === 'sidebar' ? '' : 'pt-16'} ${currentLayout === 'floating' ? 'pb-24' : ''}`}>
        {children}
      </div>

      {/* Layout Switcher Button - Primary (Bottom Left) */}
      <div className="fixed bottom-20 left-4 z-50">
        <div className="relative">
          <button
            onClick={() => setShowSwitcher(!showSwitcher)}
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-3 rounded-full shadow-2xl hover:from-blue-700 hover:to-purple-700 transition-all hover:scale-110 transform"
            title="Trocar Layout"
          >
            <Settings className="w-5 h-5" />
          </button>

          {showSwitcher && <LayoutSwitcherMenu />}
        </div>
      </div>

      {/* Layout Switcher Button - Alternative (Top Right) */}
      <div className="fixed top-20 right-4 z-50">
        <div className="relative">
          <button
            onClick={() => setShowSwitcher(!showSwitcher)}
            className="bg-white/90 backdrop-blur-md text-gray-700 p-2 rounded-lg shadow-lg hover:bg-white transition-all border border-gray-200/50"
            title="Layouts Disponíveis"
          >
            <Eye className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Overlay */}
      {showSwitcher && (
        <div 
          className="fixed inset-0 z-40"
          onClick={() => setShowSwitcher(false)}
        />
      )}
    </div>
  );
};

export default LayoutSwitcher;