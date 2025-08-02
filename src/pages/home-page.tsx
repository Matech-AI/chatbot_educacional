import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuthStore } from "../store/auth-store";
import { useMaterialsStore } from "../store/materials-store";
import { motion } from "framer-motion";
import {
  MessageSquare,
  Book,
  User,
  Settings,
  TrendingUp,
  Clock,
  BookOpen,
  Dumbbell,
} from "lucide-react";

const HomePage: React.FC = () => {
  const { user } = useAuthStore();
  const { materials, fetchMaterials } = useMaterialsStore();
  const [backendStatus, setBackendStatus] = useState<string>("Verificando...");
  const [isOnline, setIsOnline] = useState(false);

  useEffect(() => {
    fetchMaterials();
    checkBackendHealth();
  }, [fetchMaterials]);

  const checkBackendHealth = async () => {
    try {
      // Usar a mesma URL base que é usada para outras requisições API
      const apiBase = process.env.NODE_ENV === 'production' 
        ? (import.meta.env.VITE_API_BASE_URL || 'https://dna-forca-api-server.onrender.com')
        : '/api';
      
      const response = await fetch(`${apiBase}/health`);
      if (response.ok) {
        const data = await response.json();
        setBackendStatus(`✅ ${data.message || "Backend online"}`);
        setIsOnline(true);
      } else {
        setBackendStatus("❌ Backend com problemas");
        setIsOnline(false);
      }
    } catch (error) {
      setBackendStatus("❌ Backend offline");
      setIsOnline(false);
    }
  };

  const canManage = user?.role === "admin" || user?.role === "instructor";

  const quickActions = [
    {
      title: "Assistente de Treino",
      description: "Converse com o assistente especializado",
      icon: <MessageSquare size={24} />,
      href: "/chat",
      color: "bg-blue-500",
      available: true,
    },
    {
      title: "Materiais de Treino",
      description: "Gerencie documentos e recursos",
      icon: <Book size={24} />,
      href: "/materials",
      color: "bg-green-500",
      available: canManage,
    },
    {
      title: "Configurar Assistente",
      description: "Personalize o comportamento do AI",
      icon: <User size={24} />,
      href: "/assistant",
      color: "bg-purple-500",
      available: canManage,
    },
    {
      title: "Configurações",
      description: "Configurações do sistema",
      icon: <Settings size={24} />,
      href: "/settings",
      color: "bg-gray-500",
      available: user?.role === "admin",
    },
  ];

  const stats = [
    {
      label: "Materiais Disponíveis",
      value: materials.length,
      icon: <BookOpen size={20} />,
      color: "text-blue-600",
    },
    {
      label: "Status do Sistema",
      value: isOnline ? "Online" : "Offline",
      icon: <TrendingUp size={20} />,
      color: isOnline ? "text-green-600" : "text-red-600",
    },
    {
      label: "Último Login",
      value: "Agora",
      icon: <Clock size={20} />,
      color: "text-purple-600",
    },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-red-600 rounded-lg flex items-center justify-center">
            <Dumbbell size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Bem-vindo, {user?.name}!
            </h1>
            <p className="text-gray-600">
              Sistema DNA da Força -{" "}
              {user?.role === "admin"
                ? "Administrador"
                : user?.role === "instructor"
                ? "Instrutor"
                : "Aluno"}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Status Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
      >
        {stats.map((stat, index) => (
          <div
            key={index}
            className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  {stat.label}
                </p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {stat.value}
                </p>
              </div>
              <div className={`${stat.color}`}>{stat.icon}</div>
            </div>
          </div>
        ))}
      </motion.div>

      {/* Backend Status */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-lg border border-gray-200 p-4 mb-8 shadow-sm"
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-medium text-gray-900">Status do Backend</h3>
            <p className="text-sm text-gray-600">{backendStatus}</p>
          </div>
          <button
            onClick={checkBackendHealth}
            className="text-blue-600 text-sm hover:text-blue-800 font-medium"
          >
            Verificar novamente
          </button>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          Ações Rápidas
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickActions
            .filter((action) => action.available)
            .map((action, index) => (
              <Link key={index} to={action.href} className="group block">
                <motion.div
                  whileHover={{ y: -5, scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-all duration-200"
                >
                  <div
                    className={`w-12 h-12 ${action.color} rounded-lg flex items-center justify-center mb-4 text-white group-hover:scale-110 transition-transform duration-200`}
                  >
                    {action.icon}
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                    {action.title}
                  </h3>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {action.description}
                  </p>
                  <div className="mt-4 text-blue-600 text-sm font-medium group-hover:translate-x-1 transition-transform duration-200 inline-block">
                    Acessar →
                  </div>
                </motion.div>
              </Link>
            ))}
        </div>
      </motion.div>

      {/* Recent Materials Preview */}
      {materials.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">
              Materiais Recentes
            </h2>
            {canManage && (
              <Link
                to="/materials"
                className="text-blue-600 text-sm font-medium hover:text-blue-800"
              >
                Ver todos →
              </Link>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {materials.slice(0, 3).map((material) => (
              <div
                key={material.id}
                className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow duration-200"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 truncate">
                      {material.title}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {material.type.toUpperCase()}
                    </p>
                  </div>
                </div>
                {material.description && (
                  <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                    {material.description}
                  </p>
                )}
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>
                    {new Date(material.uploadedAt).toLocaleDateString("pt-BR")}
                  </span>
                  {canManage && (
                    <Link
                      to="/materials"
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Gerenciar
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Footer Info */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-12 text-center text-sm text-gray-500"
      >
        <p>DNA da Força v1.4 - Sistema de Assistente Educacional</p>
        <p className="mt-1">Desenvolvido por Matech AI</p>
      </motion.div>
    </div>
  );
};

// Export default para funcionar com lazy loading
export default HomePage;
