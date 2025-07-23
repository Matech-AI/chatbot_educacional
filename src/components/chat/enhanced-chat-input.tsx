import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Settings,
  BookOpen,
  Target,
  TrendingUp,
  Brain,
  Eye,
  Volume2,
  Hand,
  RotateCcw,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';

interface LearningPreferences {
  user_level: 'beginner' | 'intermediate' | 'advanced';
  learning_style: 'visual' | 'auditory' | 'kinesthetic' | 'mixed';
  current_topic?: string;
  learning_objectives: string[];
}

interface EnhancedChatInputProps {
  onSendMessage: (message: string, preferences?: LearningPreferences) => void;
  onTopicExplore?: (topic: string) => void;
  isLoading?: boolean;
  sessionContext?: {
    current_focus?: string;
    difficulty_level?: string;
    topics_covered?: string[];
  };
}

export const EnhancedChatInput: React.FC<EnhancedChatInputProps> = ({
  onSendMessage,
  onTopicExplore,
  isLoading = false,
  sessionContext
}) => {
  const [message, setMessage] = useState('');
  const [showPreferences, setShowPreferences] = useState(false);
  const [preferences, setPreferences] = useState<LearningPreferences>({
    user_level: 'intermediate',
    learning_style: 'mixed',
    learning_objectives: []
  });
  const [newObjective, setNewObjective] = useState('');
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  // Update preferences based on session context
  useEffect(() => {
    if (sessionContext?.current_focus && sessionContext.current_focus !== preferences.current_topic) {
      setPreferences(prev => ({
        ...prev,
        current_topic: sessionContext.current_focus
      }));
    }
    if (sessionContext?.difficulty_level) {
      setPreferences(prev => ({
        ...prev,
        user_level: sessionContext.difficulty_level as any
      }));
    }
  }, [sessionContext]);

  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim(), preferences);
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const addLearningObjective = () => {
    if (newObjective.trim() && preferences.learning_objectives.length < 5) {
      setPreferences(prev => ({
        ...prev,
        learning_objectives: [...prev.learning_objectives, newObjective.trim()]
      }));
      setNewObjective('');
    }
  };

  const removeLearningObjective = (index: number) => {
    setPreferences(prev => ({
      ...prev,
      learning_objectives: prev.learning_objectives.filter((_, i) => i !== index)
    }));
  };

  const suggestedQuestions = [
    "Como melhorar minha técnica?",
    "Qual a diferença entre hipertrofia e força?",
    "Como montar um programa de treino?",
    "Quais são os princípios da periodização?",
    "Como prevenir lesões durante o treino?"
  ];

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'beginner': return <BookOpen size={16} />;
      case 'intermediate': return <Target size={16} />;
      case 'advanced': return <TrendingUp size={16} />;
      default: return <Target size={16} />;
    }
  };

  const getStyleIcon = (style: string) => {
    switch (style) {
      case 'visual': return <Eye size={16} />;
      case 'auditory': return <Volume2 size={16} />;
      case 'kinesthetic': return <Hand size={16} />;
      case 'mixed': return <Brain size={16} />;
      default: return <Brain size={16} />;
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      {/* Session Context Display */}
      {sessionContext?.current_focus && (
        <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Target size={16} className="text-blue-600" />
              <span className="text-sm font-medium text-blue-800">
                Foco atual: {sessionContext.current_focus}
              </span>
            </div>
            {sessionContext.topics_covered && sessionContext.topics_covered.length > 0 && (
              <div className="text-xs text-blue-600">
                {sessionContext.topics_covered.length} tópicos explorados
              </div>
            )}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="mb-3 flex flex-wrap gap-2">
        {suggestedQuestions.map((question, index) => (
          <button
            key={index}
            onClick={() => setMessage(question)}
            className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full px-3 py-1 transition-colors"
          >
            {question}
          </button>
        ))}
      </div>

      {/* Learning Preferences Panel */}
      <AnimatePresence>
        {showPreferences && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4 p-4 bg-gray-50 border border-gray-200 rounded-lg overflow-hidden"
          >
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-gray-900 flex items-center space-x-2">
                <Settings size={16} />
                <span>Preferências de Aprendizado</span>
              </h4>

              {/* Level Selection */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-2">
                  Nível de Conhecimento
                </label>
                <div className="flex space-x-2">
                  {['beginner', 'intermediate', 'advanced'].map((level) => (
                    <button
                      key={level}
                      onClick={() => setPreferences(prev => ({ ...prev, user_level: level as any }))}
                      className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                        preferences.user_level === level
                          ? 'bg-red-100 text-red-700 border border-red-300'
                          : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {getLevelIcon(level)}
                      <span className="capitalize">
                        {level === 'beginner' ? 'Iniciante' : 
                         level === 'intermediate' ? 'Intermediário' : 'Avançado'}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Learning Style */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-2">
                  Estilo de Aprendizado
                </label>
                <div className="flex space-x-2">
                  {[
                    { key: 'visual', label: 'Visual' },
                    { key: 'auditory', label: 'Auditivo' },
                    { key: 'kinesthetic', label: 'Cinestésico' },
                    { key: 'mixed', label: 'Misto' }
                  ].map(({ key, label }) => (
                    <button
                      key={key}
                      onClick={() => setPreferences(prev => ({ ...prev, learning_style: key as any }))}
                      className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                        preferences.learning_style === key
                          ? 'bg-blue-100 text-blue-700 border border-blue-300'
                          : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {getStyleIcon(key)}
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Current Topic */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-2">
                  Tópico Atual (opcional)
                </label>
                <Input
                  value={preferences.current_topic || ''}
                  onChange={(e) => setPreferences(prev => ({ ...prev, current_topic: e.target.value }))}
                  placeholder="Ex: hipertrofia, força, resistência..."
                  className="text-sm"
                />
              </div>

              {/* Learning Objectives */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-2">
                  Objetivos de Aprendizado (máx. 5)
                </label>
                
                {preferences.learning_objectives.length > 0 && (
                  <div className="mb-2 space-y-1">
                    {preferences.learning_objectives.map((objective, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between bg-white border border-gray-200 rounded px-3 py-2"
                      >
                        <span className="text-sm text-gray-700">{objective}</span>
                        <button
                          onClick={() => removeLearningObjective(index)}
                          className="text-red-500 hover:text-red-700 ml-2"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {preferences.learning_objectives.length < 5 && (
                  <div className="flex space-x-2">
                    <Input
                      value={newObjective}
                      onChange={(e) => setNewObjective(e.target.value)}
                      placeholder="Adicionar objetivo..."
                      className="text-sm"
                      onKeyPress={(e) => e.key === 'Enter' && addLearningObjective()}
                    />
                    <Button
                      onClick={addLearningObjective}
                      variant="outline"
                      size="sm"
                      disabled={!newObjective.trim()}
                    >
                      +
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Input Area */}
      <div className="flex space-x-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Digite sua pergunta sobre treinamento..."
            className="w-full min-h-[44px] max-h-32 px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all"
            disabled={isLoading}
          />
        </div>

        <div className="flex flex-col space-y-2">
          <Button
            onClick={() => setShowPreferences(!showPreferences)}
            variant="outline"
            size="sm"
            className="p-2"
          >
            {showPreferences ? <ChevronUp size={18} /> : <Settings size={18} />}
          </Button>

          <Button
            onClick={handleSend}
            disabled={!message.trim() || isLoading}
            className="bg-red-600 hover:bg-red-700 p-2"
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <Send size={18} />
            )}
          </Button>
        </div>
      </div>

      {/* Quick Topic Exploration */}
      {sessionContext?.topics_covered && sessionContext.topics_covered.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-600">Explorar tópicos relacionados:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {sessionContext.topics_covered.slice(-3).map((topic, index) => (
              <button
                key={index}
                onClick={() => onTopicExplore?.(topic)}
                className="text-xs bg-green-100 text-green-700 hover:bg-green-200 rounded-full px-3 py-1 transition-colors"
              >
                {topic}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};