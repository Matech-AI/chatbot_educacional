import React from "react";
import { Link } from "react-router-dom";
import { useAuthStore } from "../store/auth-store";
import { useMaterialsStore } from "../store/materials-store";
import { useChatStore } from "../store/chat-store";
import { Button } from "../components/ui/button";
import { MessageSquare, Book, User, BarChart } from "lucide-react";
import { motion } from "framer-motion";

export const HomePage: React.FC = () => {
  const { user } = useAuthStore();
  // const { materials } = useMaterialsStore();
  const { sessions, createSession } = useChatStore();

  const startNewChat = () => {
    const sessionId = createSession();
    return `/chat?session=${sessionId}`;
  };

  // Stats for dashboard
  const stats = [
    {
      label: "Materiais Disponíveis",
      value: materials.length,
      icon: <Book size={20} />,
      color: "bg-blue-100 text-blue-600",
      link: "/materials",
      roles: ["admin", "instructor", "student"],
    },
    {
      label: "Conversas",
      value: sessions.length,
      icon: <MessageSquare size={20} />,
      color: "bg-green-100 text-green-600",
      link: "/chat",
      roles: ["admin", "instructor", "student"],
    },
    {
      label: "Templates de Assistente",
      value: 3, // Mock value
      icon: <User size={20} />,
      color: "bg-purple-100 text-purple-600",
      link: "/assistant",
      roles: ["admin", "instructor"],
    },
    {
      label: "Estatísticas",
      value: "24h",
      icon: <BarChart size={20} />,
      color: "bg-orange-100 text-orange-600",
      link: "/debug",
      roles: ["admin"],
    },
  ];

  // Filter stats based on user role
  const filteredStats = stats.filter(
    (stat) => user && stat.roles.includes(user.role)
  );

  // Featured content
  const featuredMaterials = materials.slice(0, 3);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Welcome header */}
      <header className="mb-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-3xl font-bold text-gray-900">
            Olá, {user?.name}!
          </h1>
          <p className="text-gray-600 mt-1">
            Bem-vindo ao seu Assistente Educacional de Educação Física
          </p>
        </motion.div>
      </header>

      {/* Stats */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        {filteredStats.map((stat, i) => (
          <Link to={stat.link} key={i}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{
                opacity: 1,
                y: 0,
                transition: { delay: 0.1 * i },
              }}
              whileHover={{ y: -5, transition: { duration: 0.2 } }}
              className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm hover:shadow-md transition-all duration-200"
            >
              <div className="flex items-center">
                <div
                  className={`w-10 h-10 rounded-full ${stat.color} flex items-center justify-center mr-4`}
                >
                  {stat.icon}
                </div>
                <div>
                  <p className="text-gray-500 text-sm">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stat.value}
                  </p>
                </div>
              </div>
            </motion.div>
          </Link>
        ))}
      </motion.div>

      {/* Quick actions */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm mb-8"
      >
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Ações Rápidas
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link to={startNewChat()}>
            <motion.div
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              className="bg-blue-600 text-white p-4 rounded-lg flex items-center justify-center gap-3"
            >
              <MessageSquare size={20} />
              <span className="font-medium">Nova Conversa</span>
            </motion.div>
          </Link>

          {user?.role !== "student" && (
            <Link to="/materials">
              <motion.div
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.98 }}
                className="bg-green-600 text-white p-4 rounded-lg flex items-center justify-center gap-3"
              >
                <Book size={20} />
                <span className="font-medium">Gerenciar Materiais</span>
              </motion.div>
            </Link>
          )}

          {user?.role !== "student" && (
            <Link to="/assistant">
              <motion.div
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.98 }}
                className="bg-purple-600 text-white p-4 rounded-lg flex items-center justify-center gap-3"
              >
                <User size={20} />
                <span className="font-medium">Configurar Assistente</span>
              </motion.div>
            </Link>
          )}
        </div>
      </motion.div>

      {/* Featured content */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Materiais em Destaque
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {featuredMaterials.map((material, i) => (
            <motion.div
              key={material.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{
                opacity: 1,
                y: 0,
                transition: { delay: 0.1 * i + 0.3 },
              }}
              className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-all duration-200"
            >
              <h3 className="font-medium text-gray-900 mb-1">
                {material.title}
              </h3>
              {material.description && (
                <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                  {material.description}
                </p>
              )}

              <div className="flex justify-end">
                <Link to={`/materials?id=${material.id}`}>
                  <Button variant="link" size="sm">
                    Ver material
                  </Button>
                </Link>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};
