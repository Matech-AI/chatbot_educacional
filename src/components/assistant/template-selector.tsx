import React from 'react';
import { Button } from '../ui/button';
import { motion } from 'framer-motion';

interface TemplateSelectorProps {
  templates: string[];
  onSelectTemplate: (template: string) => void;
  isLoading: boolean;
}

export const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  templates,
  onSelectTemplate,
  isLoading
}) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Templates Disponíveis</h2>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {templates.map((template, index) => (
          <motion.div 
            key={template}
            initial={{ opacity: 0, y: 20 }}
            animate={{ 
              opacity: 1, 
              y: 0,
              transition: { delay: index * 0.1 }
            }}
          >
            <button
              type="button"
              onClick={() => onSelectTemplate(template)}
              disabled={isLoading}
              className="w-full text-left p-4 rounded-md border border-gray-200 hover:border-blue-400 hover:bg-blue-50 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <h3 className="font-medium text-gray-900 mb-1">{template}</h3>
              <p className="text-xs text-gray-500">Template para assistente especializado em {template}</p>
            </button>
          </motion.div>
        ))}
      </div>
      
      <div className="mt-4 text-center text-sm text-gray-500">
        <p>Selecione um template para carregar configurações pré-definidas</p>
        <p className="mt-1">Você poderá personalizar as configurações após o carregamento</p>
      </div>
    </div>
  );
};