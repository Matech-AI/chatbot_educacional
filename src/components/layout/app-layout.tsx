import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './sidebar';
import { useAuthStore } from '../../store/auth-store';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu } from 'lucide-react';
import { Button } from '../ui/button';

export const AppLayout: React.FC = () => {
  const { user } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);

  // Check if mobile on mount and when window resizes
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
    };

    // Initial check
    checkMobile();

    // Add resize listener
    window.addEventListener('resize', checkMobile);

    // Cleanup
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Load sidebar state from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem('sidebarOpen');
    if (savedState !== null && !isMobile) {
      setSidebarOpen(savedState === 'true');
    }
  }, [isMobile]);

  const toggleSidebar = () => {
    const newState = !sidebarOpen;
    setSidebarOpen(newState);
    // Only save state if not mobile
    if (!isMobile) {
      localStorage.setItem('sidebarOpen', String(newState));
    }
  };

  return (
    <div className="h-screen w-full bg-gray-50 text-gray-900 overflow-hidden flex">
      {/* Mobile toggle button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={toggleSidebar}
          className="bg-white/80 backdrop-blur-sm shadow-md rounded-full"
        >
          <Menu size={20} />
        </Button>
      </div>

      {/* Sidebar - Always rendered but transforms based on state */}
      <div 
        className={`fixed lg:relative z-40 h-full transition-transform duration-300 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
        style={{ width: isMobile ? '280px' : '320px' }}
      >
        <Sidebar onClose={() => isMobile && setSidebarOpen(false)} />
      </div>

      {/* Main content */}
      <div className="flex-1 h-full overflow-auto transition-all duration-300">
        <main className="h-full">
          <Outlet />
        </main>
      </div>

      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && isMobile && (
          <motion.div
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-30 lg:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};