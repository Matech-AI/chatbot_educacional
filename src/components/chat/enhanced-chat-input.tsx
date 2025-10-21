import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  BookOpen,
  Target,
  TrendingUp,
  Brain,
  Eye,
  Volume2,
  Hand,
} from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";

interface LearningPreferences {
  user_level: "beginner" | "intermediate" | "advanced";
  learning_style: "visual" | "auditory" | "kinesthetic" | "mixed";
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
  sessionContext,
}) => {
  const [message, setMessage] = useState("");
  const [preferences, setPreferences] = useState<LearningPreferences>({
    user_level: "intermediate",
    learning_style: "mixed",
    learning_objectives: [],
  });
  const [newObjective, setNewObjective] = useState("");

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  // Update preferences based on session context
  useEffect(() => {
    if (
      sessionContext?.current_focus &&
      sessionContext.current_focus !== preferences.current_topic
    ) {
      setPreferences((prev) => ({
        ...prev,
        current_topic: sessionContext.current_focus,
      }));
    }
    if (sessionContext?.difficulty_level) {
      setPreferences((prev) => ({
        ...prev,
        user_level: sessionContext.difficulty_level as any,
      }));
    }
  }, [sessionContext]);

  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim(), preferences);
      setMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Preferências removidas da UI; mantemos apenas defaults internos

  const suggestedQuestions = [
    "Como melhorar minha técnica?",
    "Qual a diferença entre hipertrofia e força?",
    "Como montar um programa de treino?",
    "Quais são os princípios da periodização?",
    "Como prevenir lesões durante o treino?",
  ];

  const getLevelIcon = (level: string) => {
    switch (level) {
      case "beginner":
        return <BookOpen size={16} />;
      case "intermediate":
        return <Target size={16} />;
      case "advanced":
        return <TrendingUp size={16} />;
      default:
        return <Target size={16} />;
    }
  };

  const getStyleIcon = (style: string) => {
    switch (style) {
      case "visual":
        return <Eye size={16} />;
      case "auditory":
        return <Volume2 size={16} />;
      case "kinesthetic":
        return <Hand size={16} />;
      case "mixed":
        return <Brain size={16} />;
      default:
        return <Brain size={16} />;
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-3 lg:p-4">
      {/* Session Context Display */}
      {sessionContext?.current_focus && (
        <div className="mb-3 p-2 lg:p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Target size={14} className="text-blue-600" />
              <span className="text-xs lg:text-sm font-medium text-blue-800 truncate">
                Foco atual: {sessionContext.current_focus}
              </span>
            </div>
            {sessionContext.topics_covered &&
              Array.isArray(sessionContext.topics_covered) &&
              sessionContext.topics_covered.length > 0 && (
                <div className="text-xs text-blue-600">
                  {sessionContext.topics_covered.length} tópicos
                </div>
              )}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="mb-3 flex flex-wrap gap-1 lg:gap-2">
        {suggestedQuestions.map((question, index) => (
          <button
            key={index}
            onClick={() => setMessage(question)}
            className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full px-2 lg:px-3 py-1 transition-colors"
          >
            {question}
          </button>
        ))}
      </div>

      {/* Preferências removidas da UI por solicitação */}

      {/* Main Input Area */}
      <div className="flex space-x-2 lg:space-x-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Digite sua pergunta sobre treinamento..."
            className="w-full min-h-[40px] lg:min-h-[44px] max-h-24 lg:max-h-32 px-3 lg:px-4 py-2 lg:py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all text-sm lg:text-base"
            disabled={isLoading}
          />
        </div>

        <div className="flex flex-col space-y-2">
          <Button
            onClick={handleSend}
            disabled={!message.trim() || isLoading}
            className="bg-red-600 hover:bg-red-700 p-2 lg:p-2"
            size="sm"
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <Send size={16} />
            )}
          </Button>
        </div>
      </div>

      {/* Quick Topic Exploration */}
      {(() => {
        const topics = Array.isArray(sessionContext?.topics_covered)
          ? (sessionContext!.topics_covered as string[])
          : [];
        if (topics.length === 0) return null;
        return (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-gray-600">
                Explorar tópicos relacionados:
              </span>
            </div>
            <div className="flex flex-wrap gap-1 lg:gap-2">
              {topics.slice(-3).map((topic, index) => (
                <button
                  key={index}
                  onClick={() => onTopicExplore?.(topic)}
                  className="text-xs bg-green-100 text-green-700 hover:bg-green-200 rounded-full px-2 lg:px-3 py-1 transition-colors"
                >
                  {topic}
                </button>
              ))}
            </div>
          </div>
        );
      })()}
    </div>
  );
};
