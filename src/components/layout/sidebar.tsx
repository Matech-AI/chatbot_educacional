import React, { useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/auth-store";
import { Button } from "../ui/button";
import { motion } from "framer-motion";
import {
  Home,
  MessageSquare,
  Book,
  Settings,
  LogOut,
  BarChart,
  User,
  Users,
  ChevronRight,
  X,
  LogIn,
} from "lucide-react";
import { LOGO_PATH, SITE_NAME, SITE_TAGLINE } from "../../constants/branding";

interface SidebarProps {
  onClose?: () => void;
}

const guestMenuItems = [
  {
    name: "Assistente",
    path: "/chat",
    icon: <MessageSquare size={18} />,
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ onClose }) => {
  const { user, logout, isAuthenticated } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      const currentPath = location.pathname;

      const allowedPaths = {
        student: ["/", "/chat"],
        instructor: ["/", "/chat", "/materials", "/assistant"],
        admin: [
          "/",
          "/chat",
          "/materials",
          "/assistant",
          "/settings",
          "/users",
          "/debug",
        ],
      };

      const userAllowedPaths =
        allowedPaths[user.role as keyof typeof allowedPaths] || [];

      if (
        !userAllowedPaths.some(
          (path) => currentPath === path || currentPath.startsWith(path + "/")
        )
      ) {
        navigate("/");
      }
    }
  }, [location.pathname, user, navigate]);

  const handleLogout = () => {
    logout();
    navigate("/chat");
  };

  const menuItems = [
    {
      name: "Início",
      path: "/",
      icon: <Home size={18} />,
      roles: ["admin", "instructor", "student"],
    },
    {
      name: "Assistente",
      path: "/chat",
      icon: <MessageSquare size={18} />,
      roles: ["admin", "instructor", "student"],
    },
    {
      name: "Materiais",
      path: "/materials",
      icon: <Book size={18} />,
      roles: ["admin", "instructor"],
    },
    {
      name: "Configurar Assistente",
      path: "/assistant",
      icon: <User size={18} />,
      roles: ["admin", "instructor"],
    },
    {
      name: "Configurações",
      path: "/settings",
      icon: <Settings size={18} />,
      roles: ["admin"],
    },
    {
      name: "Gerenciar Usuários",
      path: "/users",
      icon: <Users size={18} />,
      roles: ["admin"],
    },
    {
      name: "Debug",
      path: "/debug",
      icon: <BarChart size={18} />,
      roles: ["admin"],
    },
  ];

  const filteredItems = isAuthenticated
    ? menuItems.filter((item) => user && item.roles.includes(user.role))
    : guestMenuItems;

  return (
    <div className="flex flex-col h-full bg-[#0f1419] border-r border-gray-800 text-white">
      <div className="flex items-center justify-between px-5 py-5 border-b border-white/10">
        <div className="flex items-center gap-3 min-w-0">
          <img
            src={LOGO_PATH}
            alt={SITE_NAME}
            className="w-9 h-9 object-contain shrink-0"
          />
          <div className="min-w-0">
            <h1 className="text-base font-semibold tracking-tight truncate">
              {SITE_NAME}
            </h1>
            <p className="text-[11px] text-gray-500 truncate">{SITE_TAGLINE}</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="lg:hidden p-1.5 rounded-md text-gray-500 hover:text-white hover:bg-white/10 transition-colors"
          aria-label="Fechar menu"
        >
          <X size={18} />
        </button>
      </div>

      {isAuthenticated && user ? (
        <div className="px-5 py-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            {user.avatarUrl ? (
              <img
                src={user.avatarUrl}
                alt={user.name}
                className="w-9 h-9 rounded-full object-cover ring-2 ring-white/10"
              />
            ) : (
              <div className="w-9 h-9 rounded-full bg-red-600/20 ring-2 ring-red-500/30 flex items-center justify-center">
                <span className="text-red-300 text-sm font-medium">
                  {user.name?.charAt(0) || "?"}
                </span>
              </div>
            )}
            <div className="min-w-0">
              <p className="font-medium text-sm truncate">{user.name}</p>
              <p className="text-xs text-gray-500 capitalize">{user.role}</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="px-5 py-3">
          <div className="rounded-lg bg-white/5 border border-white/10 px-3 py-2.5">
            <p className="text-xs font-medium text-gray-300">Modo visitante</p>
            <p className="text-[11px] text-gray-500 mt-0.5 leading-relaxed">
              Acesso livre ao assistente
            </p>
          </div>
        </div>
      )}

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-wider text-gray-600">
          Menu
        </p>
        <ul className="space-y-0.5">
          {filteredItems.map((item) => {
            const isActive = location.pathname === item.path;

            return (
              <li key={item.path}>
                <Link to={item.path} onClick={onClose}>
                  <motion.div
                    whileTap={{ scale: 0.98 }}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                      isActive
                        ? "bg-white/10 text-white font-medium shadow-sm"
                        : "text-gray-400 hover:text-white hover:bg-white/5"
                    }`}
                  >
                    <span className={isActive ? "text-red-400" : "text-gray-500"}>
                      {item.icon}
                    </span>
                    <span>{item.name}</span>
                    {isActive && (
                      <ChevronRight size={14} className="ml-auto text-gray-500" />
                    )}
                  </motion.div>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="px-4 py-4 border-t border-white/10 space-y-3">
        {isAuthenticated ? (
          <Button
            variant="dark-ghost"
            size="sm"
            className="w-full"
            onClick={handleLogout}
          >
            <LogOut size={16} />
            <span>Sair</span>
          </Button>
        ) : (
          <Button
            variant="accent"
            size="sm"
            className="w-full"
            onClick={() => navigate("/login")}
          >
            <LogIn size={16} />
            <span>Entrar</span>
          </Button>
        )}

        <div className="text-center">
          <a
            href="https://matechai.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-gray-600 hover:text-gray-400 transition-colors"
          >
            matechai.com
          </a>
        </div>
      </div>
    </div>
  );
};
