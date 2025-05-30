import React from "react";
import { useAssistantStore } from "../store/assistant-store";
import { ConfigForm } from "../components/assistant/config-form";
import { TemplateSelector } from "../components/assistant/template-selector";
import { BackButton } from "../components/ui/back-button";
import { motion } from "framer-motion";

const AssistantPage: React.FC = () => {
  const {
    config,
    templates,
    isLoading,
    updateConfig,
    saveAsTemplate,
    loadTemplate,
  } = useAssistantStore();

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <header className="mb-6">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <BackButton />
          <h1 className="text-2xl font-bold text-gray-900 mt-2">
            Configuração do Assistente
          </h1>
          <p className="text-gray-600 mt-1">
            Personalize o comportamento do assistente de treino
          </p>
        </motion.div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Template selector */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <TemplateSelector
            templates={templates}
            onSelectTemplate={loadTemplate}
            isLoading={isLoading}
          />
        </motion.div>

        {/* Config form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2"
        >
          <ConfigForm
            config={config}
            onSave={updateConfig}
            onSaveAsTemplate={saveAsTemplate}
            isLoading={isLoading}
          />
        </motion.div>
      </div>
    </div>
  );
};

// Export default para funcionar com lazy loading
export default AssistantPage;
