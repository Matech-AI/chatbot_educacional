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
    icon: <MessageSquare size={20} />,
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
      icon: <Home size={20} />,
      roles: ["admin", "instructor", "student"],
    },
    {
      name: "Assistente",
      path: "/chat",
      icon: <MessageSquare size={20} />,
      roles: ["admin", "instructor", "student"],
    },
    {
      name: "Materiais",
      path: "/materials",
      icon: <Book size={20} />,
      roles: ["admin", "instructor"],
    },
    {
      name: "Configurar Assistente",
      path: "/assistant",
      icon: <User size={20} />,
      roles: ["admin", "instructor"],
    },
    {
      name: "Configurações",
      path: "/settings",
      icon: <Settings size={20} />,
      roles: ["admin"],
    },
    {
      name: "Gerenciar Usuários",
      path: "/users",
      icon: <Users size={20} />,
      roles: ["admin"],
    },
    {
      name: "Debug",
      path: "/debug",
      icon: <BarChart size={20} />,
      roles: ["admin"],
    },
  ];

  const filteredItems = isAuthenticated
    ? menuItems.filter((item) => user && item.roles.includes(user.role))
    : guestMenuItems;

  return (
    <div className="flex flex-col h-full bg-gray-900 border-r border-gray-800 shadow-sm text-white">
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-12 h-12 rounded-md flex items-center justify-center">
            <img
              src={LOGO_PATH}
              alt={SITE_NAME}
              className="w-10 h-10 object-contain"
            />
          </div>
          <div>
            <h1 className="text-lg font-bold leading-tight">{SITE_NAME}</h1>
            <p className="text-xs text-gray-400">{SITE_TAGLINE}</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="lg:hidden text-gray-400 hover:text-white"
        >
          <X size={20} />
        </button>
      </div>

      {isAuthenticated && user ? (
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            {user.avatarUrl ? (
              <img
                src={user.avatarUrl}
                alt={user.name}
                className="w-10 h-10 rounded-full object-cover"
              />
            ) : (
              <div className="w-10 h-10 rounded-full bg-red-900/50 flex items-center justify-center">
                <span className="text-red-300 font-medium">
                  {user.name?.charAt(0) || "?"}
                </span>
              </div>
            )}
            <div>
              <p className="font-medium text-sm">{user.name}</p>
              <p className="text-xs text-gray-400 capitalize">{user.role}</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-4 border-b border-gray-800">
          <p className="text-sm text-gray-300">Acesso público ao assistente</p>
          <p className="text-xs text-gray-500 mt-1">
            Faça login para recursos administrativos
          </p>
        </div>
      )}

      <nav className="flex-1 overflow-y-auto p-3">
        <ul className="space-y-1">
          {filteredItems.map((item) => {
            const isActive = location.pathname === item.path;

            return (
              <li key={item.path}>
                <Link to={item.path} onClick={onClose}>
                  <motion.div
                    whileHover={{ x: 5 }}
                    whileTap={{ scale: 0.98 }}
                    className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                      isActive
                        ? "bg-red-900/40 text-red-300 font-medium"
                        : "text-gray-300 hover:bg-gray-800"
                    }`}
                  >
                    {item.icon}
                    <span>{item.name}</span>
                    {isActive && <ChevronRight size={16} className="ml-auto" />}
                  </motion.div>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-gray-800">
        {isAuthenticated ? (
          <Button
            variant="outline"
            className="w-full flex items-center justify-center gap-2 border-gray-700 text-gray-200 hover:bg-gray-800"
            onClick={handleLogout}
          >
            <LogOut size={16} />
            <span>Sair</span>
          </Button>
        ) : (
          <Button
            variant="outline"
            className="w-full flex items-center justify-center gap-2 border-gray-700 text-gray-200 hover:bg-gray-800"
            onClick={() => navigate("/login")}
          >
            <LogIn size={16} />
            <span>Entrar</span>
          </Button>
        )}

        <div className="mt-4 text-center text-xs text-gray-500">
          <p>{SITE_NAME}</p>
          <p className="mt-1">
            <a
              href="https://matechai.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-gray-300"
            >
              matechai.com
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};
