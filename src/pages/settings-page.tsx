import React, { useState } from "react";
import { useAuthStore } from "../store/auth-store";
import { MaintenancePanel } from "../maintenance/maintenance-panel";
import { BackButton } from "../components/ui/back-button";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { motion, AnimatePresence } from "framer-motion";
import {
  Settings,
  Database,
  Shield,
  Users,
  Bell,
  Palette,
  Globe,
  HardDrive,
  Wrench,
  Info,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";

const SettingsPage: React.FC = () => {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<
    "general" | "maintenance" | "security" | "about"
  >("general");
  const [isDirty, setIsDirty] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // Mock settings state
  const [settings, setSettings] = useState({
    general: {
      siteName: "DNA da Força",
      description: "Sistema Educacional de Treinamento Físico",
      language: "pt-BR",
      timezone: "America/Sao_Paulo",
      maxFileSize: 50,
      allowedFileTypes: ".pdf,.docx,.txt,.mp4,.avi,.mov,.pptx,.webm",
    },
    security: {
      sessionTimeout: 180,
      maxLoginAttempts: 3,
      requirePasswordChange: false,
      enableTwoFactor: false,
    },
    notifications: {
      emailNotifications: true,
      pushNotifications: false,
      maintenanceAlerts: true,
      systemUpdates: true,
    },
  });

  const handleSettingChange = (category: string, key: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      [category]: {
        ...prev[category as keyof typeof prev],
        [key]: value,
      },
    }));
    setIsDirty(true);
  };

  const saveSettings = async () => {
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setMessage({
        type: "success",
        text: "Configurações salvas com sucesso!",
      });
      setIsDirty(false);

      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: "error", text: "Erro ao salvar configurações." });
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    {
      id: "general" as const,
      label: "🎛️ Geral",
      icon: Settings,
      description: "Configurações básicas do sistema",
    },
    {
      id: "maintenance" as const,
      label: "🔧 Manutenção",
      icon: Wrench,
      description: "Ferramentas de limpeza e otimização",
    },
    {
      id: "security" as const,
      label: "🔒 Segurança",
      icon: Shield,
      description: "Configurações de segurança e autenticação",
    },
    {
      id: "about" as const,
      label: "ℹ️ Sobre",
      icon: Info,
      description: "Informações do sistema e versão",
    },
  ];

  const isAdmin = user?.role === "admin";

  if (!isAdmin) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <BackButton />
        <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <AlertTriangle size={48} className="text-yellow-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Acesso Restrito
          </h2>
          <p className="text-gray-600">
            Apenas administradores podem acessar as configurações do sistema.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <header className="mb-6">
        <BackButton />
        <div className="mt-2 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Settings size={24} />
              Configurações do Sistema
            </h1>
            <p className="text-gray-600 mt-1">
              Gerencie configurações, manutenção e otimizações do DNA da Força
            </p>
          </div>

          {isDirty && activeTab !== "maintenance" && activeTab !== "about" && (
            <Button
              onClick={saveSettings}
              isLoading={isLoading}
              className="flex items-center gap-2"
            >
              <CheckCircle size={16} />
              Salvar Alterações
            </Button>
          )}
        </div>
      </header>

      {/* Message Display */}
      <AnimatePresence>
        {message && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`mb-6 p-4 rounded-lg border ${
              message.type === "success"
                ? "bg-green-50 border-green-200 text-green-700"
                : "bg-red-50 border-red-200 text-red-700"
            }`}
          >
            <div className="flex items-center gap-2">
              {message.type === "success" ? (
                <CheckCircle size={16} />
              ) : (
                <AlertTriangle size={16} />
              )}
              {message.text}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tab Navigation */}
      <div className="mb-8">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? "border-red-500 text-red-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <div className="flex items-center gap-2">
                  <tab.icon size={16} />
                  {tab.label}
                </div>
              </button>
            ))}
          </nav>
        </div>

        {/* Tab descriptions */}
        <div className="mt-4">
          <p className="text-sm text-gray-600">
            {tabs.find((tab) => tab.id === activeTab)?.description}
          </p>
        </div>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === "general" && (
          <motion.div
            key="general"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Site Information */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Globe size={20} />
                Informações do Site
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome do Sistema
                  </label>
                  <Input
                    value={settings.general.siteName}
                    onChange={(e) =>
                      handleSettingChange("general", "siteName", e.target.value)
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Idioma
                  </label>
                  <select
                    value={settings.general.language}
                    onChange={(e) =>
                      handleSettingChange("general", "language", e.target.value)
                    }
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="pt-BR">Português (Brasil)</option>
                  </select>
                </div>
              </div>
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrição
                </label>
                <Input
                  value={settings.general.description}
                  onChange={(e) =>
                    handleSettingChange(
                      "general",
                      "description",
                      e.target.value
                    )
                  }
                />
              </div>
            </div>

            {/* File Upload Settings */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <HardDrive size={20} />
                Configurações de Upload
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tamanho Máximo (MB)
                  </label>
                  <Input
                    type="number"
                    value={settings.general.maxFileSize}
                    onChange={(e) =>
                      handleSettingChange(
                        "general",
                        "maxFileSize",
                        parseInt(e.target.value)
                      )
                    }
                    min={1}
                    max={500}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipos de Arquivo Permitidos
                  </label>
                  <Input
                    value={settings.general.allowedFileTypes}
                    onChange={(e) =>
                      handleSettingChange(
                        "general",
                        "allowedFileTypes",
                        e.target.value
                      )
                    }
                    placeholder=".pdf,.docx,.txt,.mp4"
                  />
                </div>
              </div>
            </div>

            {/* Notification Settings */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Bell size={20} />
                Notificações
              </h3>
              <div className="space-y-4">
                {Object.entries(settings.notifications).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-gray-700">
                        {key === "emailNotifications" &&
                          "Notificações por Email"}
                        {key === "pushNotifications" && "Notificações Push"}
                        {key === "maintenanceAlerts" && "Alertas de Manutenção"}
                        {key === "systemUpdates" && "Atualizações do Sistema"}
                      </label>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={value}
                        onChange={(e) =>
                          handleSettingChange(
                            "notifications",
                            key,
                            e.target.checked
                          )
                        }
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === "maintenance" && (
          <motion.div
            key="maintenance"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <MaintenancePanel onRefresh={() => {}} />
          </motion.div>
        )}

        {activeTab === "security" && (
          <motion.div
            key="security"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Authentication Settings */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Shield size={20} />
                Configurações de Autenticação
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Timeout da Sessão (minutos)
                  </label>
                  <Input
                    type="number"
                    value={settings.security.sessionTimeout}
                    onChange={(e) =>
                      handleSettingChange(
                        "security",
                        "sessionTimeout",
                        parseInt(e.target.value)
                      )
                    }
                    min={15}
                    max={1440}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Máximo de Tentativas de Login
                  </label>
                  <Input
                    type="number"
                    value={settings.security.maxLoginAttempts}
                    onChange={(e) =>
                      handleSettingChange(
                        "security",
                        "maxLoginAttempts",
                        parseInt(e.target.value)
                      )
                    }
                    min={1}
                    max={10}
                  />
                </div>
              </div>

              <div className="mt-4 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Exigir Troca de Senha no Primeiro Login
                    </label>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.security.requirePasswordChange}
                      onChange={(e) =>
                        handleSettingChange(
                          "security",
                          "requirePasswordChange",
                          e.target.checked
                        )
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">
                      Habilitar Autenticação de Dois Fatores
                    </label>
                    <p className="text-xs text-gray-500">Em desenvolvimento</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.security.enableTwoFactor}
                      onChange={(e) =>
                        handleSettingChange(
                          "security",
                          "enableTwoFactor",
                          e.target.checked
                        )
                      }
                      className="sr-only peer"
                      disabled
                    />
                    <div className="w-11 h-6 bg-gray-200 rounded-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 opacity-50"></div>
                  </label>
                </div>
              </div>
            </div>

            {/* User Management */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Users size={20} />
                Gerenciamento de Usuários
              </h3>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">1</div>
                    <div className="text-sm text-blue-800">Administradores</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">2</div>
                    <div className="text-sm text-green-800">Instrutores</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">∞</div>
                    <div className="text-sm text-purple-800">Alunos</div>
                  </div>
                </div>

                <div className="text-center">
                  <Button
                    variant="outline"
                    className="flex items-center gap-2 mx-auto"
                  >
                    <Users size={16} />
                    Gerenciar Usuários
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                      Em breve
                    </span>
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === "about" && (
          <motion.div
            key="about"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* System Information */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Info size={20} />
                Informações do Sistema
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Versão:</span>
                    <span className="font-medium">1.4.0 - Recursivo</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Última Atualização:</span>
                    <span className="font-medium">Junho 2025</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Licença:</span>
                    <span className="font-medium">Proprietária</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Desenvolvedor:</span>
                    <span className="font-medium">Matech AI</span>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Backend:</span>
                    <span className="font-medium">FastAPI + Python</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Frontend:</span>
                    <span className="font-medium">React + TypeScript</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Banco Vetorial:</span>
                    <span className="font-medium">ChromaDB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">IA:</span>
                    <span className="font-medium">OpenAI GPT-4</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Features */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4">
                Funcionalidades v1.4.0
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-600" />
                    <span className="text-sm">
                      Download Recursivo do Google Drive
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-600" />
                    <span className="text-sm">
                      Detecção Automática de Duplicatas
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-600" />
                    <span className="text-sm">
                      Preservação de Estrutura Hierárquica
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-600" />
                    <span className="text-sm">Assistente IA com RAG</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-600" />
                    <span className="text-sm">Sistema de Autenticação JWT</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-600" />
                    <span className="text-sm">
                      Painel de Manutenção Avançado
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-600" />
                    <span className="text-sm">Relatórios Detalhados</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-600" />
                    <span className="text-sm">Interface Responsiva</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Support */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">
                Suporte e Documentação
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button
                  variant="outline"
                  className="flex items-center gap-2 justify-center"
                >
                  <Database size={16} />
                  Documentação da API
                </Button>
                <Button
                  variant="outline"
                  className="flex items-center gap-2 justify-center"
                >
                  <Wrench size={16} />
                  Guia de Manutenção
                </Button>
                <Button
                  variant="outline"
                  className="flex items-center gap-2 justify-center"
                >
                  <Shield size={16} />
                  Manual de Segurança
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Export default para funcionar com lazy loading
export default SettingsPage;
