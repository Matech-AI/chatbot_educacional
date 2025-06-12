import React, { useState } from 'react';
import { Button } from '../ui/button';
import { motion } from 'framer-motion';
import { CheckCircle, BookOpen, Apple, Zap } from 'lucide-react';

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
  const [loadingTemplate, setLoadingTemplate] = useState<string | null>(null);
  const [lastLoadedTemplate, setLastLoadedTemplate] = useState<string | null>(null);

  const handleTemplateSelect = async (template: string) => {
    setLoadingTemplate(template);
    await onSelectTemplate(template);
    setLoadingTemplate(null);
    setLastLoadedTemplate(template);
    
    // Clear the success indicator after 3 seconds
    setTimeout(() => {
      setLastLoadedTemplate(null);
    }, 3000);
  };

  const getTemplateIcon = (template: string) => {
    switch (template) {
      case 'Educação Física':
        return <Zap size={20} className="text-blue-600" />;
      case 'Nutrição Esportiva':
        return <Apple size={20} className="text-green-600" />;
      case 'Anatomia Humana':
        return <BookOpen size={20} className="text-purple-600" />;
      default:
        return <BookOpen size={20} className="text-gray-600" />;
    }
  };

  const getTemplateColor = (template: string) => {
    switch (template) {
      case 'Educação Física':
        return 'hover:border-blue-400 hover:bg-blue-50 focus:ring-blue-500';
      case 'Nutrição Esportiva':
        return 'hover:border-green-400 hover:bg-green-50 focus:ring-green-500';
      case 'Anatomia Humana':
        return 'hover:border-purple-400 hover:bg-purple-50 focus:ring-purple-500';
      default:
        return 'hover:border-gray-400 hover:bg-gray-50 focus:ring-gray-500';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Templates Disponíveis</h2>
      
      <div className="space-y-3">
        {templates.map((template, index) => {
          const isLoadingThis = loadingTemplate === template;
          const wasJustLoaded = lastLoadedTemplate === template;
          
          return (
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
                onClick={() => handleTemplateSelect(template)}
                disabled={isLoading || isLoadingThis}
                className={`w-full text-left p-4 rounded-md border transition-all duration-200 focus:outline-none focus:ring-2 ${
                  wasJustLoaded 
                    ? 'border-green-400 bg-green-50' 
                    : isLoadingThis 
                    ? 'border-blue-400 bg-blue-50'
                    : `border-gray-200 ${getTemplateColor(template)}`
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    {isLoadingThis ? (
                      <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                    ) : wasJustLoaded ? (
                      <CheckCircle size={20} className="text-green-600" />
                    ) : (
                      getTemplateIcon(template)
                    )}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 mb-1">
                      {template}
                      {wasJustLoaded && (
                        <span className="ml-2 text-sm text-green-600 font-normal">
                          ✓ Carregado
                        </span>
                      )}
                    </h3>
                    <p className="text-xs text-gray-500">
                      {isLoadingThis 
                        ? 'Carregando configurações...'
                        : `Template para assistente especializado em ${template}`
                      }
                    </p>
                  </div>
                </div>
              </button>
            </motion.div>
          );
        })}
      </div>
      
      <div className="mt-4 text-center text-sm text-gray-500">
        <p>Selecione um template para carregar configurações pré-definidas</p>
        <p className="mt-1">Você poderá personalizar as configurações após o carregamento</p>
      </div>
    </div>
  );
};
