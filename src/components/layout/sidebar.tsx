import React, { useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/auth-store";
import {
  Home,
  MessageSquare,
  Book,
  Settings,
  LogOut,
  BarChart,
  User,
  Users,
  X,
  LogIn,
  ExternalLink,
} from "lucide-react";
import { LOGO_PATH, SITE_NAME, SITE_TAGLINE } from "../../constants/branding";

interface SidebarProps {
  onClose?: () => void;
}

const guestMenuItems = [
  {
    name: "Assistente",
    path: "/chat",
    icon: MessageSquare,
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

  const menuItems = [
    { name: "Início", path: "/", icon: Home, roles: ["admin", "instructor", "student"] },
    { name: "Assistente", path: "/chat", icon: MessageSquare, roles: ["admin", "instructor", "student"] },
    { name: "Materiais", path: "/materials", icon: Book, roles: ["admin", "instructor"] },
    { name: "Configurar Assistente", path: "/assistant", icon: User, roles: ["admin", "instructor"] },
    { name: "Configurações", path: "/settings", icon: Settings, roles: ["admin"] },
    { name: "Usuários", path: "/users", icon: Users, roles: ["admin"] },
    { name: "Debug", path: "/debug", icon: BarChart, roles: ["admin"] },
  ];

  const filteredItems = isAuthenticated
    ? menuItems.filter((item) => user && item.roles.includes(user.role))
    : guestMenuItems;

  const NavLink = ({
    path,
    name,
    icon: Icon,
  }: {
    path: string;
    name: string;
    icon: React.ComponentType<{ size?: number; className?: string }>;
  }) => {
    const isActive = location.pathname === path;
    return (
      <Link to={path} onClick={onClose} className="block">
        <span
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
            isActive
              ? "bg-red-50 text-red-700 font-medium ring-1 ring-red-100"
              : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
          }`}
        >
          <Icon
            size={18}
            className={isActive ? "text-red-600" : "text-slate-400"}
          />
          {name}
        </span>
      </Link>
    );
  };

  return (
    <aside className="flex flex-col h-full w-full bg-white border-r border-slate-200">
      {/* Brand */}
      <div className="flex items-center justify-between gap-2 px-4 h-16 border-b border-slate-100 shrink-0">
        <a
          href="https://matechai.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-3 min-w-0 group"
        >
          <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center p-2 shrink-0 group-hover:bg-slate-800 transition-colors">
            <img
              src={LOGO_PATH}
              alt={SITE_NAME}
              className="w-full h-full object-contain"
            />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-900 truncate leading-tight">
              {SITE_NAME}
            </p>
            <p className="text-[10px] text-slate-400 truncate">{SITE_TAGLINE}</p>
          </div>
        </a>
        <button
          type="button"
          onClick={onClose}
          className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
          aria-label="Fechar menu"
        >
          <X size={18} />
        </button>
      </div>

      {/* User (authenticated only) */}
      {isAuthenticated && user && (
        <div className="px-4 py-3 border-b border-slate-100 shrink-0">
          <div className="flex items-center gap-3">
            {user.avatarUrl ? (
              <img
                src={user.avatarUrl}
                alt={user.name}
                className="w-9 h-9 rounded-full object-cover"
              />
            ) : (
              <div className="w-9 h-9 rounded-full bg-red-100 text-red-700 flex items-center justify-center text-sm font-semibold">
                {user.name?.charAt(0) || "?"}
              </div>
            )}
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-900 truncate">
                {user.name}
              </p>
              <p className="text-xs text-slate-500 capitalize">{user.role}</p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {filteredItems.map((item) => (
            <li key={item.path}>
              <NavLink
                path={item.path}
                name={item.name}
                icon={item.icon}
              />
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="shrink-0 px-4 py-4 border-t border-slate-100 space-y-3">
        {!isAuthenticated && (
          <p className="text-xs text-slate-500 leading-relaxed px-1">
            Você está usando o assistente em modo público.
          </p>
        )}

        {isAuthenticated ? (
          <button
            type="button"
            onClick={() => {
              logout();
              navigate("/chat");
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-slate-600 border border-slate-200 hover:bg-slate-50 hover:text-slate-900 transition-colors"
          >
            <LogOut size={16} />
            Sair
          </button>
        ) : (
          <button
            type="button"
            onClick={() => navigate("/login")}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-white bg-red-600 hover:bg-red-500 shadow-sm transition-colors"
          >
            <LogIn size={16} />
            Entrar
          </button>
        )}

        <a
          href="https://matechai.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-1 text-xs text-slate-400 hover:text-red-600 transition-colors"
        >
          matechai.com
          <ExternalLink size={12} />
        </a>
      </div>
    </aside>
  );
};
