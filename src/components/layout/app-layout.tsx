import React, { useState, useEffect } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./sidebar";
import { useAuthStore } from "../../store/auth-store";
import { motion, AnimatePresence } from "framer-motion";
import { Menu } from "lucide-react";
import TemporaryPasswordCheck from "./temporary-password-check";

const AppLayout: React.FC = () => {
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
    window.addEventListener("resize", checkMobile);

    // Cleanup
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Load sidebar state from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem("sidebarOpen");
    if (savedState !== null && !isMobile) {
      setSidebarOpen(savedState === "true");
    }
  }, [isMobile]);

  const toggleSidebar = () => {
    const newState = !sidebarOpen;
    setSidebarOpen(newState);
    // Only save state if not mobile
    if (!isMobile) {
      localStorage.setItem("sidebarOpen", String(newState));
    }
  };

  return (
    <div className="h-screen w-full bg-slate-50 text-slate-900 overflow-hidden flex">
      {/* Verificação de senha temporária */}
      <TemporaryPasswordCheck />
      
      {/* Mobile toggle button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          type="button"
          onClick={toggleSidebar}
          className="p-2.5 bg-[#0f1419] text-white border border-white/10 shadow-lg rounded-xl hover:bg-[#161d2b] transition-colors"
          aria-label="Abrir menu"
        >
          <Menu size={20} />
        </button>
      </div>

      {/* Sidebar - Always rendered but transforms based on state */}
      <div
        className={`fixed lg:relative z-40 h-full transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
        style={{ width: isMobile ? "min(100vw, 300px)" : "280px" }}
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

// Export default para funcionar com lazy loading
export default AppLayout;
