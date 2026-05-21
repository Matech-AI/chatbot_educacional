import React, { useState, useRef, useEffect } from "react";
import { Send, Target } from "lucide-react";
import { Button } from "../ui/button";

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

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

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
        user_level: sessionContext.difficulty_level as LearningPreferences["user_level"],
      }));
    }
  }, [sessionContext, preferences.current_topic]);

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

  const suggestedQuestions = [
    "Como melhorar minha técnica?",
    "Qual a diferença entre hipertrofia e força?",
    "Como montar um programa de treino?",
    "Quais são os princípios da periodização?",
    "Como prevenir lesões durante o treino?",
  ];

  return (
    <div className="border-t border-slate-200 bg-white px-4 lg:px-6 py-4">
      {sessionContext?.current_focus && (
        <div className="mb-3 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <Target size={14} className="text-slate-500 shrink-0" />
              <span className="text-xs font-medium text-slate-700 truncate">
                Foco: {sessionContext.current_focus}
              </span>
            </div>
            {sessionContext.topics_covered &&
              Array.isArray(sessionContext.topics_covered) &&
              sessionContext.topics_covered.length > 0 && (
                <span className="text-xs text-slate-500 shrink-0">
                  {sessionContext.topics_covered.length} tópicos
                </span>
              )}
          </div>
        </div>
      )}

      <div className="mb-3 flex flex-wrap gap-2">
        {suggestedQuestions.map((question, index) => (
          <button
            key={index}
            type="button"
            onClick={() => setMessage(question)}
            className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-full px-3 py-1.5 transition-colors border border-transparent hover:border-slate-200"
          >
            {question}
          </button>
        ))}
      </div>

      <div className="flex gap-2 items-end">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Digite sua pergunta sobre treinamento..."
            className="w-full min-h-[44px] max-h-32 px-4 py-3 border border-slate-200 rounded-xl resize-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all text-sm text-slate-900 placeholder:text-slate-400 bg-slate-50 focus:bg-white"
            disabled={isLoading}
          />
        </div>

        <Button
          onClick={handleSend}
          disabled={!message.trim() || isLoading}
          variant="accent"
          size="icon"
          className="shrink-0 rounded-xl h-11 w-11"
          aria-label="Enviar mensagem"
        >
          {isLoading ? (
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
          ) : (
            <Send size={18} />
          )}
        </Button>
      </div>

      {(() => {
        const topics = Array.isArray(sessionContext?.topics_covered)
          ? (sessionContext!.topics_covered as string[])
          : [];
        if (topics.length === 0) return null;
        return (
          <div className="mt-3 pt-3 border-t border-slate-100">
            <span className="text-xs font-medium text-slate-500 block mb-2">
              Explorar tópicos
            </span>
            <div className="flex flex-wrap gap-2">
              {topics.slice(-3).map((topic, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => onTopicExplore?.(topic)}
                  className="text-xs bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-full px-3 py-1 transition-colors"
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
