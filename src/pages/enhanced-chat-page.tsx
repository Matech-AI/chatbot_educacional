import React, { useEffect, useCallback, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  useChatSessions,
  useChatActions,
  useSessionMessages,
} from "../store/chat-store";
import { EducationalMessageBubble } from "../components/chat/educational-message-bubble";
import { EnhancedChatInput } from "../components/chat/enhanced-chat-input";
import { LearningPathExplorer } from "../components/chat/learning-path-explorer";
import { Button } from "../components/ui/button";
import { BackButton } from "../components/ui/back-button";
import { 
  PlusCircle, 
  Trash2, 
  BookOpen, 
  Target, 
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  Settings,
  Brain
} from "lucide-react";
import { api } from "../lib/api";

interface EducationalMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  sources?: any[];
  follow_up_questions?: string[];
  learning_suggestions?: string[];
  related_topics?: string[];
  video_suggestions?: any[];
  educational_metadata?: any;
  isLoading?: boolean;
}

interface LearningPreferences {
  user_level: 'beginner' | 'intermediate' | 'advanced';
  learning_style: 'visual' | 'auditory' | 'kinesthetic' | 'mixed';
  current_topic?: string;
  learning_objectives: string[];
}

const EnhancedChatPage: React.FC = () => {
  // Chat state
  const { sessions, activeSessionId, isProcessing } = useChatSessions();
  const { createSession, setActiveSession, deleteSession, sendMessage } = useChatActions();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Enhanced chat state
  const [educationalMessages, setEducationalMessages] = useState<EducationalMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionContext, setSessionContext] = useState<any>(null);
  const [showLearningPath, setShowLearningPath] = useState(false);
  const [currentExplorationTopic, setCurrentExplorationTopic] = useState<string>("");
  const [userLevel, setUserLevel] = useState<'beginner' | 'intermediate' | 'advanced'>('intermediate');

  // References
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isUpdatingRef = useRef(false);

  // URL session management
  const urlSessionId = searchParams.get("session");

  // Initialize session
  useEffect(() => {
    if (sessions.length === 0) {
      const newSessionId = createSession("Conversa educacional");
      setSearchParams({ session: newSessionId }, { replace: true });
    } else if (urlSessionId && urlSessionId !== activeSessionId) {
      const sessionExists = sessions.some(s => s.id === urlSessionId);
      if (sessionExists) {
        setActiveSession(urlSessionId);
      } else {
        setSearchParams({}, { replace: true });
      }
    }
  }, [urlSessionId, activeSessionId, sessions, setActiveSession, setSearchParams, createSession]);

  // Load session context
  useEffect(() => {
    if (activeSessionId) {
      loadSessionContext();
    }
  }, [activeSessionId]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [educationalMessages]);

  const loadSessionContext = async () => {
    if (!activeSessionId) return;
    
    try {
      const context = await api.getSessionContext(activeSessionId);
      setSessionContext(context);
    } catch (error) {
      console.error('Error loading session context:', error);
    }
  };

  const handleSendMessage = async (content: string, preferences?: LearningPreferences) => {
    if (!content.trim() || isLoading) return;

    const userMessage: EducationalMessage = {
      id: `user_${Date.now()}`,
      content,
      role: 'user',
      timestamp: new Date()
    };

    setEducationalMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Add loading message
    const loadingMessage: EducationalMessage = {
      id: `assistant_${Date.now()}`,
      content: "Analisando sua pergunta e buscando as melhores fontes...",
      role: 'assistant',
      timestamp: new Date(),
      isLoading: true
    };

    setEducationalMessages(prev => [...prev, loadingMessage]);

    try {
      const response = await api.educationalChat({
        content,
        user_level: preferences?.user_level || userLevel,
        learning_style: preferences?.learning_style || 'mixed',
        session_id: activeSessionId,
        current_topic: preferences?.current_topic,
        learning_objectives: preferences?.learning_objectives || []
      });

      // Replace loading message with actual response
      setEducationalMessages(prev => 
        prev.map(msg => 
          msg.id === loadingMessage.id 
            ? {
                ...msg,
                content: response.response,
                sources: response.sources,
                follow_up_questions: response.follow_up_questions,
                learning_suggestions: response.learning_suggestions,
                related_topics: response.related_topics,
                video_suggestions: response.video_suggestions,
                educational_metadata: response.educational_metadata,
                isLoading: false
              }
            : msg
        )
      );

      // Update session context
      await loadSessionContext();

      // Auto-set exploration topic if mentioned
      if (response.related_topics && response.related_topics.length > 0) {
        setCurrentExplorationTopic(response.related_topics[0]);
      }

    } catch (error) {
      console.error('Error in educational chat:', error);
      
      // Replace loading message with error
      setEducationalMessages(prev => 
        prev.map(msg => 
          msg.id === loadingMessage.id 
            ? {
                ...msg,
                content: "Desculpe, ocorreu um erro. Pode tentar novamente?",
                isLoading: false
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleFollowUpClick = (question: string) => {
    handleSendMessage(question);
  };

  const handleTopicExplore = async (topic: string) => {
    setCurrentExplorationTopic(topic);
    setShowLearningPath(true);
    
    // Also send an exploration message
    const explorationPrompt = `Quero explorar mais profundamente o tópico: ${topic}`;
    handleSendMessage(explorationPrompt);
  };

  const handleSourceClick = (source: any) => {
    // Open source in a modal or new tab
    console.log('Source clicked:', source);
  };

  const handleVideoPlay = (video: any) => {
    // Handle video play request
    console.log('Video play requested:', video);
    // Could open in modal, navigate to video page, or handle differently
  };

  const handleNewSession = useCallback(() => {
    if (isUpdatingRef.current) return;
    isUpdatingRef.current = true;

    const newSessionId = createSession("Nova conversa educacional");
    setEducationalMessages([]);
    setSessionContext(null);
    setCurrentExplorationTopic("");
    setShowLearningPath(false);
    setSearchParams({ session: newSessionId }, { replace: true });

    setTimeout(() => {
      isUpdatingRef.current = false;
    }, 100);
  }, [createSession, setSearchParams]);

  const handleDeleteSession = useCallback(
    (sessionId: string) => {
      if (sessions.length <= 1) return;

      deleteSession(sessionId);
      if (sessionId === activeSessionId) {
        const remainingSessions = sessions.filter(s => s.id !== sessionId);
        if (remainingSessions.length > 0) {
          setActiveSession(remainingSessions[0].id);
          setSearchParams({ session: remainingSessions[0].id }, { replace: true });
        }
      }
    },
    [sessions, activeSessionId, deleteSession, setActiveSession, setSearchParams]
  );

  const currentSession = sessions.find(s => s.id === activeSessionId);

  return (
    <div className="h-full flex">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 p-4 flex-shrink-0">
          <div className="flex items-center justify-between mb-4">
            <div>
              <BackButton />
              <h1 className="text-xl font-semibold text-gray-900 mt-2 flex items-center space-x-2">
                <Brain className="text-red-600" size={24} />
                <span>Assistente Educacional</span>
              </h1>
              {sessionContext?.current_focus && (
                <p className="text-sm text-gray-600 mt-1">
                  Foco atual: {sessionContext.current_focus}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Button
                onClick={() => setShowLearningPath(!showLearningPath)}
                variant={showLearningPath ? "default" : "outline"}
                size="sm"
                className="flex items-center gap-1"
              >
                <BookOpen size={16} />
                <span>Trilha de Aprendizado</span>
              </Button>
              
              <Button
                onClick={handleNewSession}
                variant="outline"
                className="flex items-center gap-1"
                disabled={isProcessing}
              >
                <PlusCircle size={16} />
                <span>Nova conversa</span>
              </Button>
            </div>
          </div>

          {/* Session Tabs */}
          {sessions.length > 1 && (
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {sessions.map((session) => (
                <motion.div
                  key={session.id}
                  className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm whitespace-nowrap cursor-pointer transition-colors ${
                    session.id === activeSessionId
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                  onClick={() => {
                    setActiveSession(session.id);
                    setSearchParams({ session: session.id }, { replace: true });
                  }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span>{session.title}</span>
                  {sessions.length > 1 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSession(session.id);
                      }}
                      className="text-gray-400 hover:text-red-500 ml-1"
                    >
                      <Trash2 size={12} />
                    </button>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <AnimatePresence>
            {educationalMessages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-12"
              >
                <Brain size={48} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Bem-vindo ao Assistente Educacional!
                </h3>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  Faça perguntas sobre treinamento físico e receba respostas detalhadas 
                  com fontes, sugestões de aprofundamento e trilhas de aprendizado personalizadas.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <Target className="text-blue-600 mb-2" size={24} />
                    <h4 className="font-medium text-blue-900">Personalizado</h4>
                    <p className="text-sm text-blue-700">
                      Adapta o nível de complexidade ao seu conhecimento
                    </p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <BookOpen className="text-green-600 mb-2" size={24} />
                    <h4 className="font-medium text-green-900">Fontes Confiáveis</h4>
                    <p className="text-sm text-green-700">
                      Respostas baseadas em materiais científicos e práticos
                    </p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <TrendingUp className="text-purple-600 mb-2" size={24} />
                    <h4 className="font-medium text-purple-900">Aprendizado Progressivo</h4>
                    <p className="text-sm text-purple-700">
                      Trilhas estruturadas para aprofundar conhecimentos
                    </p>
                  </div>
                </div>
              </motion.div>
            ) : (
              educationalMessages.map((message) => (
                <EducationalMessageBubble
                  key={message.id}
                  message={message}
                  onFollowUpClick={handleFollowUpClick}
                  onTopicExplore={handleTopicExplore}
                  onSourceClick={handleSourceClick}
                  onVideoPlay={handleVideoPlay}
                />
              ))
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Enhanced Input */}
        <EnhancedChatInput
          onSendMessage={handleSendMessage}
          onTopicExplore={handleTopicExplore}
          isLoading={isLoading}
          sessionContext={sessionContext?.summary}
        />
      </div>

      {/* Learning Path Sidebar */}
      <AnimatePresence>
        {showLearningPath && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 400, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="border-l border-gray-200 bg-gray-50 overflow-hidden"
          >
            <div className="p-4 h-full overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Trilha de Aprendizado</h3>
                <button
                  onClick={() => setShowLearningPath(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <ChevronRight size={20} />
                </button>
              </div>

              {currentExplorationTopic ? (
                <LearningPathExplorer
                  topic={currentExplorationTopic}
                  userLevel={userLevel}
                  onStepExplore={(step) => {
                    handleSendMessage(`Explique mais sobre: ${step.title}`);
                  }}
                  onTopicExplore={handleTopicExplore}
                />
              ) : (
                <div className="text-center py-12">
                  <BookOpen size={48} className="mx-auto text-gray-400 mb-4" />
                  <p className="text-gray-600">
                    Selecione um tópico na conversa para ver a trilha de aprendizado
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default EnhancedChatPage;