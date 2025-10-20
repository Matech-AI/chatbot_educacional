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
  Dumbbell,
} from "lucide-react";

interface SidebarProps {
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onClose }) => {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();

  // Efeito para redirecionar usuários que tentam acessar páginas não autorizadas
  useEffect(() => {
    if (user) {
      const currentPath = location.pathname;

      // Definir rotas permitidas por perfil
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

      // Se o caminho atual não estiver na lista de permitidos para o perfil do usuário
      if (
        !userAllowedPaths.some(
          (path) => currentPath === path || currentPath.startsWith(path + "/")
        )
      ) {
        // Redirecionar para a página inicial
        navigate("/");
      }
    }
  }, [location.pathname, user, navigate]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const menuItems = [
    {
      name: "Início",
      path: "/",
      icon: <Home size={20} />,
      roles: ["admin", "instructor", "student"],
    },
    {
      name: "Assistente de Treino",
      path: "/chat",
      icon: <MessageSquare size={20} />,
      roles: ["admin", "instructor", "student"],
    },
    {
      name: "Materiais de Treino",
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

  const filteredItems = menuItems.filter(
    (item) => user && item.roles.includes(user.role)
  );

  return (
    <div className="flex flex-col h-full bg-white border-r border-gray-200 shadow-sm">
      {/* Header with logo and close button */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <div className="w-12 h-12 bg-white rounded-md flex items-center justify-center shadow-sm">
            <img
              src="/logo_dna_forca_1.jpg"
              alt="DNA da Força"
              className="w-10 h-10 object-contain"
            />
          </div>
          <h1 className="text-xl font-bold">DNA da Força</h1>
        </div>

        <button
          onClick={onClose}
          className="lg:hidden text-gray-500 hover:text-gray-700"
        >
          <X size={20} />
        </button>
      </div>

      {/* User info */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          {user?.avatarUrl ? (
            <img
              src={user.avatarUrl}
              alt={user.name}
              className="w-10 h-10 rounded-full object-cover"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
              <span className="text-red-600 font-medium">
                {user?.name?.charAt(0) || "?"}
              </span>
            </div>
          )}
          <div>
            <p className="font-medium text-sm">{user?.name}</p>
            <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
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
                        ? "bg-red-50 text-red-600 font-medium"
                        : "text-gray-700 hover:bg-gray-100"
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

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <Button
          variant="outline"
          className="w-full flex items-center justify-center gap-2"
          onClick={handleLogout}
        >
          <LogOut size={16} />
          <span>Sair</span>
        </Button>

        <div className="mt-4 text-center text-xs text-gray-500">
          <p>DNA da Força v1.7</p>
          <p className="mt-1">Desenvolvido pela Matech AI</p>
        </div>
      </div>
    </div>
  );
};
