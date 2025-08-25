import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import Navbar from './Navbar';
import ModernSidebar from './ModernSidebar';
import FloatingNav from './FloatingNav';
import CascadeNav from './CascadeNav';

const LayoutSwitcher = ({ children }) => {
  const { user } = useAuth();
  const [currentLayout, setCurrentLayout] = useState('original');

  const layouts = [
    {
      id: 'original',
      name: 'Clássico',
      component: Navbar
    },
    {
      id: 'sidebar',
      name: 'Sidebar',
      component: ModernSidebar
    },
    {
      id: 'floating',
      name: 'Flutuante',
      component: FloatingNav
    },
    {
      id: 'cascade',
      name: 'Cascata',
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
  };

  const getCurrentLayout = () => {
    return layouts.find(l => l.id === currentLayout) || layouts[0];
  };

  const LayoutComponent = getCurrentLayout().component;

  // Special handling for cascade layout (full page)
  if (currentLayout === 'cascade') {
    return <CascadeNav />;
  }

  // Regular layouts with navigation + content
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Pass layout controls to the navbar */}
      <LayoutComponent 
        currentLayout={currentLayout}
        layouts={layouts}
        onLayoutChange={changeLayout}
      />

      {/* Main Content */}
      <div className={`${currentLayout === 'sidebar' ? '' : 'pt-16'} ${currentLayout === 'floating' ? 'pb-24' : ''}`}>
        {children}
      </div>
    </div>
  );
};

export default LayoutSwitcher;