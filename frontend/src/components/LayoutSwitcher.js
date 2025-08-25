import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import Navbar from './Navbar';
import ModernSidebar from './ModernSidebar';
import FloatingNav from './FloatingNav';
import CascadeNav from './CascadeNav';

const LayoutSwitcher = ({ children }) => {
  const { user } = useAuth();
  // Always start with original layout as default
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
    try {
      const savedLayout = localStorage.getItem('preferredLayout');
      // Force original layout as default if no valid saved layout
      if (savedLayout && layouts.find(l => l.id === savedLayout)) {
        setCurrentLayout(savedLayout);
      } else {
        // Always default to original layout
        setCurrentLayout('original');
        localStorage.setItem('preferredLayout', 'original');
      }
    } catch (error) {
      // Fallback to original if localStorage fails
      setCurrentLayout('original');
    }
  }, []);

  // Save layout preference
  const changeLayout = (layoutId) => {
    try {
      // Validate layout ID
      if (!layoutId || !layouts.find(l => l.id === layoutId)) {
        console.warn('Invalid layout ID:', layoutId);
        return;
      }
      
      setCurrentLayout(layoutId);
      localStorage.setItem('preferredLayout', layoutId);
      
      // Force page refresh for layout changes to take effect properly
      setTimeout(() => {
        window.location.reload();
      }, 100);
    } catch (error) {
      console.error('Error changing layout:', error);
      // Fallback to original layout
      setCurrentLayout('original');
    }
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