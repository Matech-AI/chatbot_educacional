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
  ChevronRight,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import {
  LOGO_PATH,
  SITE_NAME,
  SITE_TAGLINE,
  BRAND_BG,
} from "../../constants/branding";
import { ChatSidebarSessions } from "./chat-sidebar-sessions";

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

const roleLabels: Record<string, string> = {
  student: "Aluno",
  instructor: "Instrutor",
  admin: "Administrador",
};

export const Sidebar: React.FC<SidebarProps> = ({ onClose }) => {
  const { user, logout, isAuthenticated } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();
  const isChatRoute =
    location.pathname === "/chat" ||
    location.pathname.startsWith("/chat/");

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
    {
      name: "Início",
      path: "/",
      icon: Home,
      roles: ["admin", "instructor", "student"],
    },
    {
      name: "Assistente",
      path: "/chat",
      icon: MessageSquare,
      roles: ["admin", "instructor", "student"],
    },
    {
      name: "Materiais",
      path: "/materials",
      icon: Book,
      roles: ["admin", "instructor"],
    },
    {
      name: "Configurar Assistente",
      path: "/assistant",
      icon: User,
      roles: ["admin", "instructor"],
    },
    {
      name: "Configurações",
      path: "/settings",
      icon: Settings,
      roles: ["admin"],
    },
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
    icon: LucideIcon;
  }) => {
    const isActive =
      location.pathname === path ||
      (path === "/chat" && location.pathname.startsWith("/chat"));
    return (
      <Link to={path} onClick={onClose} className="block">
        <span
          className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
            isActive
              ? "bg-red-500/15 text-white font-medium ring-1 ring-red-500/25"
              : "text-slate-400 hover:bg-white/5 hover:text-slate-100"
          }`}
        >
          <Icon
            size={18}
            className={isActive ? "text-red-400" : "text-slate-500"}
          />
          <span className="flex-1 truncate">{name}</span>
          {isActive && (
            <ChevronRight size={14} className="text-red-400/80 shrink-0" />
          )}
        </span>
      </Link>
    );
  };

  return (
    <aside
      className="flex flex-col h-full w-full text-slate-200 border-r border-white/[0.06] shadow-xl shadow-black/20"
      style={{ backgroundColor: BRAND_BG }}
    >
      {/* Brand */}
      <div className="relative shrink-0 px-4 pt-5 pb-4">
        <div
          className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-red-600/10 to-transparent pointer-events-none"
          aria-hidden
        />
        <div className="relative flex items-start justify-between gap-2">
          <a
            href="https://matechai.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 min-w-0 group"
          >
            <div className="w-11 h-11 rounded-2xl bg-white/10 ring-1 ring-white/10 flex items-center justify-center p-2.5 shrink-0 group-hover:bg-white/15 transition-colors">
              <img
                src={LOGO_PATH}
                alt={SITE_NAME}
                className="w-full h-full object-contain"
              />
            </div>
            <div className="min-w-0 pt-0.5">
              <p className="text-[15px] font-semibold text-white truncate leading-tight tracking-tight">
                {SITE_NAME}
              </p>
              <p className="text-[11px] text-slate-500 truncate mt-0.5">
                {SITE_TAGLINE}
              </p>
            </div>
          </a>
          <button
            type="button"
            onClick={onClose}
            className="lg:hidden p-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/10"
            aria-label="Fechar menu"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* User (authenticated) */}
      {isAuthenticated && user && (
        <div className="px-4 pb-3 shrink-0">
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-white/[0.04] ring-1 ring-white/[0.06]">
            {user.avatarUrl ? (
              <img
                src={user.avatarUrl}
                alt={user.name}
                className="w-9 h-9 rounded-full object-cover ring-2 ring-white/10"
              />
            ) : (
              <div className="w-9 h-9 rounded-full bg-red-500/20 text-red-300 flex items-center justify-center text-sm font-semibold ring-1 ring-red-500/30">
                {user.name?.charAt(0) || "?"}
              </div>
            )}
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-white truncate">
                {user.name}
              </p>
              <p className="text-[11px] text-slate-500">
                {roleLabels[user.role] || user.role}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Guest hint */}
      {!isAuthenticated && (
        <div className="px-4 pb-3 shrink-0">
          <div className="flex gap-2.5 px-3 py-3 rounded-xl bg-white/[0.04] ring-1 ring-white/[0.06]">
            <div className="w-8 h-8 rounded-lg bg-red-500/15 flex items-center justify-center shrink-0">
              <Sparkles size={16} className="text-red-400" />
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Acesso público ao assistente. Faça login para recursos
              administrativos.
            </p>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav
        className={`shrink-0 px-3 ${isChatRoute ? "pb-2" : "pb-4 flex-1"}`}
      >
        <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-600">
          Menu
        </p>
        <ul className="space-y-0.5">
          {filteredItems.map((item) => (
            <li key={item.path}>
              <NavLink path={item.path} name={item.name} icon={item.icon} />
            </li>
          ))}
        </ul>
      </nav>

      {/* Chat sessions (only on /chat) */}
      {isChatRoute && <ChatSidebarSessions onClose={onClose} />}

      {/* Footer */}
      <div className="shrink-0 px-4 py-4 mt-auto border-t border-white/[0.06] space-y-3 bg-black/20">
        {isAuthenticated ? (
          <button
            type="button"
            onClick={() => {
              logout();
              navigate("/chat");
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-slate-300 ring-1 ring-white/10 hover:bg-white/5 hover:text-white transition-colors"
          >
            <LogOut size={16} />
            Sair
          </button>
        ) : (
          <button
            type="button"
            onClick={() => navigate("/login")}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-[#0f1419] bg-white hover:bg-slate-100 shadow-lg shadow-black/20 transition-colors"
          >
            <LogIn size={16} />
            Entrar
          </button>
        )}

        <a
          href="https://matechai.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-1.5 text-[11px] text-slate-600 hover:text-red-400 transition-colors"
        >
          <span>{SITE_NAME}</span>
          <span className="text-slate-700">·</span>
          <span>matechai.com</span>
          <ExternalLink size={11} />
        </a>
      </div>
    </aside>
  );
};
