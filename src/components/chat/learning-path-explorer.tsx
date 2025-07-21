import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen,
  ChevronRight,
  ChevronDown,
  Target,
  Clock,
  CheckCircle,
  Circle,
  ArrowRight,
  Lightbulb,
  TrendingUp,
  Users,
  Award
} from 'lucide-react';
import { Button } from '../ui/button';
import { api } from '../../lib/api';

interface LearningStep {
  step: number;
  title: string;
  description: string;
  estimated_time?: string;
  completed?: boolean;
  difficulty?: 'easy' | 'medium' | 'hard';
}

interface LearningPath {
  topic: string;
  user_level: string;
  learning_path: LearningStep[];
  estimated_time: string;
  prerequisites: string[];
  resources_available: boolean;
}

interface LearningPathExplorerProps {
  topic: string;
  userLevel: string;
  onStepExplore?: (step: LearningStep) => void;
  onTopicExplore?: (topic: string) => void;
  className?: string;
}

export const LearningPathExplorer: React.FC<LearningPathExplorerProps> = ({
  topic,
  userLevel,
  onStepExplore,
  onTopicExplore,
  className = ''
}) => {
  const [learningPath, setLearningPath] = useState<LearningPath | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadLearningPath();
  }, [topic, userLevel]);

  const loadLearningPath = async () => {
    setLoading(true);
    setError(null);
    try {
      const path = await api.getLearningPath(topic, userLevel);
      setLearningPath(path);
    } catch (err) {
      setError('Erro ao carregar caminho de aprendizado');
      console.error('Error loading learning path:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleStepExpansion = (stepNumber: number) => {
    setExpandedSteps(prev => {
      const newSet = new Set(prev);
      if (newSet.has(stepNumber)) {
        newSet.delete(stepNumber);
      } else {
        newSet.add(stepNumber);
      }
      return newSet;
    });
  };

  const toggleStepCompletion = (stepNumber: number) => {
    setCompletedSteps(prev => {
      const newSet = new Set(prev);
      if (newSet.has(stepNumber)) {
        newSet.delete(stepNumber);
      } else {
        newSet.add(stepNumber);
      }
      return newSet;
    });
  };

  const getDifficultyColor = (difficulty?: string) => {
    switch (difficulty) {
      case 'easy': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'hard': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getDifficultyLabel = (difficulty?: string) => {
    switch (difficulty) {
      case 'easy': return 'Fácil';
      case 'medium': return 'Médio';
      case 'hard': return 'Difícil';
      default: return 'Médio';
    }
  };

  const calculateProgress = () => {
    if (!learningPath) return 0;
    return (completedSteps.size / learningPath.learning_path.length) * 100;
  };

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-3 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️</div>
          <p className="text-sm text-gray-600">{error}</p>
          <Button 
            onClick={loadLearningPath}
            variant="outline" 
            size="sm" 
            className="mt-3"
          >
            Tentar novamente
          </Button>
        </div>
      </div>
    );
  }

  if (!learningPath) return null;

  const progress = calculateProgress();

  return (
    <div className={`bg-white border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-red-500 to-red-600 text-white p-6">
        <div className="flex items-center space-x-3 mb-3">
          <BookOpen size={24} />
          <div>
            <h3 className="text-lg font-semibold">Caminho de Aprendizado</h3>
            <p className="text-red-100 text-sm">
              {topic} • Nível {learningPath.user_level === 'beginner' ? 'Iniciante' : 
                              learningPath.user_level === 'intermediate' ? 'Intermediário' : 'Avançado'}
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-sm mb-1">
            <span>Progresso</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-red-400 rounded-full h-2">
            <motion.div
              className="bg-white rounded-full h-2"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Meta Information */}
        <div className="flex items-center space-x-4 text-sm text-red-100">
          <div className="flex items-center space-x-1">
            <Clock size={14} />
            <span>{learningPath.estimated_time}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Target size={14} />
            <span>{learningPath.learning_path.length} etapas</span>
          </div>
          {learningPath.resources_available && (
            <div className="flex items-center space-x-1">
              <CheckCircle size={14} />
              <span>Recursos disponíveis</span>
            </div>
          )}
        </div>
      </div>

      {/* Prerequisites */}
      {learningPath.prerequisites && learningPath.prerequisites.length > 0 && (
        <div className="p-4 bg-yellow-50 border-b border-gray-200">
          <h4 className="text-sm font-medium text-yellow-800 mb-2 flex items-center space-x-2">
            <Lightbulb size={14} />
            <span>Pré-requisitos</span>
          </h4>
          <div className="flex flex-wrap gap-2">
            {learningPath.prerequisites.map((prereq, index) => (
              <span
                key={index}
                className="text-xs bg-yellow-200 text-yellow-800 rounded-full px-2 py-1"
              >
                {prereq}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Learning Steps */}
      <div className="p-6">
        <div className="space-y-4">
          {learningPath.learning_path.map((step, index) => {
            const isExpanded = expandedSteps.has(step.step);
            const isCompleted = completedSteps.has(step.step);

            return (
              <motion.div
                key={step.step}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`border rounded-lg transition-all ${
                  isCompleted ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3 flex-1">
                      <button
                        onClick={() => toggleStepCompletion(step.step)}
                        className="flex-shrink-0"
                      >
                        {isCompleted ? (
                          <CheckCircle size={20} className="text-green-600" />
                        ) : (
                          <Circle size={20} className="text-gray-400 hover:text-gray-600" />
                        )}
                      </button>

                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded">
                            Etapa {step.step}
                          </span>
                          {step.difficulty && (
                            <span className={`text-xs font-medium px-2 py-1 rounded ${getDifficultyColor(step.difficulty)}`}>
                              {getDifficultyLabel(step.difficulty)}
                            </span>
                          )}
                        </div>
                        <h4 className={`font-medium mt-1 ${isCompleted ? 'text-green-800' : 'text-gray-900'}`}>
                          {step.title}
                        </h4>
                        <p className={`text-sm mt-1 ${isCompleted ? 'text-green-700' : 'text-gray-600'}`}>
                          {step.description}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Button
                        onClick={() => onStepExplore?.(step)}
                        variant="outline"
                        size="sm"
                        className="text-xs"
                      >
                        Explorar
                      </Button>
                      <button
                        onClick={() => toggleStepExpansion(step.step)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                      </button>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-4 pt-4 border-t border-gray-200 overflow-hidden"
                      >
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h5 className="text-sm font-medium text-gray-900 mb-2">O que você aprenderá:</h5>
                            <ul className="text-sm text-gray-600 space-y-1">
                              <li>• Conceitos fundamentais</li>
                              <li>• Aplicações práticas</li>
                              <li>• Técnicas avançadas</li>
                            </ul>
                          </div>
                          <div>
                            <h5 className="text-sm font-medium text-gray-900 mb-2">Recursos disponíveis:</h5>
                            <div className="space-y-1">
                              <div className="flex items-center space-x-2 text-sm text-gray-600">
                                <BookOpen size={12} />
                                <span>Material teórico</span>
                              </div>
                              <div className="flex items-center space-x-2 text-sm text-gray-600">
                                <Users size={12} />
                                <span>Exemplos práticos</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="mt-4 flex items-center space-x-2">
                          <Button
                            onClick={() => onTopicExplore?.(step.title)}
                            variant="outline"
                            size="sm"
                            className="text-xs"
                          >
                            <ArrowRight size={12} className="mr-1" />
                            Explorar profundamente
                          </Button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Completion Certificate */}
        {progress === 100 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-6 p-6 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg text-center"
          >
            <Award size={48} className="mx-auto mb-3" />
            <h3 className="text-lg font-semibold mb-2">Parabéns!</h3>
            <p className="text-green-100">
              Você completou o caminho de aprendizado para {topic}!
            </p>
            <Button
              onClick={() => onTopicExplore?.(`${topic} avançado`)}
              variant="outline"
              className="mt-4 bg-white text-green-600 hover:bg-green-50"
            >
              <TrendingUp size={16} className="mr-2" />
              Explorar tópicos avançados
            </Button>
          </motion.div>
        )}
      </div>
    </div>
  );
};