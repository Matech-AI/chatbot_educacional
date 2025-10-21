import React, {
  useEffect,
  useCallback,
  useMemo,
  useRef,
  useState,
} from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  useUserChatSessions,
  useChatActions,
  useSessionMessages,
  useChatStore,
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
  Brain,
} from "lucide-react";
import { api } from "../lib/api";

interface EducationalMessage {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
  sources?: any[];
  follow_up_questions?: string[];
  learning_suggestions?: string[];
  related_topics?: string[];
  video_suggestions?: any[];
  educational_metadata?: any;
  isLoading?: boolean;
  isHidden?: boolean; // ✅ NOVA PROPRIEDADE: para mensagens invisíveis na UI
}

interface LearningPreferences {
  user_level: "beginner" | "intermediate" | "advanced";
  learning_style: "visual" | "auditory" | "kinesthetic" | "mixed";
  current_topic?: string;
  learning_objectives: string[];
}

const EnhancedChatPage: React.FC = () => {
  // Chat state
  const { sessions, activeSessionId, isProcessing, currentUserId } =
    useUserChatSessions();
  const {
    createSession,
    setActiveSession,
    deleteSession,
    sendMessage,
    addMessage,
  } = useChatActions();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Enhanced chat state
  const [educationalMessages, setEducationalMessages] = useState<
    EducationalMessage[]
  >([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionContext, setSessionContext] = useState<any>(null);
  const [showLearningPath, setShowLearningPath] = useState(false);
  const [currentExplorationTopic, setCurrentExplorationTopic] =
    useState<string>("");
  const [userLevel, setUserLevel] = useState<
    "beginner" | "intermediate" | "advanced"
  >("intermediate");

  // References
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isUpdatingRef = useRef(false);

  // URL session management
  const urlSessionId = searchParams.get("session");

  // Load session context function - moved before useEffect
  const loadSessionContext = useCallback(async () => {
    if (!activeSessionId) return;

    try {
      const context = await api.getSessionContext(activeSessionId);
      setSessionContext(context);
    } catch (error) {
      console.error("Error loading session context:", error);
    }
  }, [activeSessionId]);

  // Initialize session
  useEffect(() => {
    // Verificar se há um usuário logado
    if (!currentUserId) {
      console.log("⚠️ No user logged in, cannot create sessions");
      return;
    }

    if (sessions.length === 0) {
      try {
        const newSessionId = createSession();
        setSearchParams({ session: newSessionId }, { replace: true });
      } catch (error) {
        console.error("❌ Failed to create session:", error);
      }
    } else if (urlSessionId && urlSessionId !== activeSessionId) {
      const sessionExists = sessions.some((s) => s.id === urlSessionId);
      if (sessionExists) {
        setActiveSession(urlSessionId);
      } else {
        setSearchParams({}, { replace: true });
      }
    }
  }, [
    urlSessionId,
    activeSessionId,
    sessions.length,
    setActiveSession,
    setSearchParams,
    createSession,
    currentUserId,
  ]);

  // Load session context
  useEffect(() => {
    if (activeSessionId) {
      loadSessionContext();
    }
  }, [activeSessionId, loadSessionContext]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (educationalMessages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [educationalMessages.length]);

  const handleSendMessage = async (
    content: string,
    preferences?: LearningPreferences
  ) => {
    if (!content.trim() || isLoading) return;

    const userMessage: EducationalMessage = {
      id: `user_${Date.now()}`,
      content,
      role: "user",
      timestamp: new Date(),
    };

    // Adicionar à UI
    setEducationalMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Adicionar ao store persistente
    if (activeSessionId) {
      addMessage(activeSessionId, content, "user");
    }

    // ✅ ADICIONAR MENSAGEM DE CARREGAMENTO SIMPLES na UI principal
    const loadingMessage: EducationalMessage = {
      id: `loading_${Date.now()}`,
      content: "⏳ Processando sua pergunta...",
      role: "assistant",
      timestamp: new Date(),
      isLoading: true, // ✅ É uma mensagem de loading (true)
      isHidden: false, // ✅ VISÍVEL na UI
    };

    // ✅ MOSTRAR AMBAS as mensagens na UI
    setEducationalMessages((prev) => [...prev, loadingMessage]);

    // ✅ ADICIONAR mensagem detalhada ao store para exportação
    if (activeSessionId) {
      addMessage(activeSessionId, loadingMessage.content, "assistant");
    }

    try {
      const response = await api.educationalChat({
        content,
        user_level: preferences?.user_level || userLevel,
        learning_style: preferences?.learning_style || "mixed",
        session_id: activeSessionId || undefined,
        current_topic: preferences?.current_topic,
        learning_objectives: preferences?.learning_objectives || [],
      });

      // ✅ REMOVER AMBAS as mensagens de loading e adicionar resposta real
      setEducationalMessages((prev) => [
        ...prev.filter((msg) => msg.id !== loadingMessage.id), // Remove ambas as mensagens
        {
          id: `assistant_${Date.now()}`,
          content: response.response,
          role: "assistant",
          timestamp: new Date(),
          sources: response.sources,
          follow_up_questions: response.follow_up_questions,
          learning_suggestions: response.learning_suggestions,
          related_topics: response.related_topics,
          video_suggestions: response.video_suggestions,
          educational_metadata: response.educational_metadata,
          isLoading: false,
        },
      ]);

      // Adicionar resposta do assistente ao store persistente
      if (activeSessionId) {
        addMessage(
          activeSessionId,
          response.response,
          "assistant",
          response.sources
        );
      }

      // Update session context
      await loadSessionContext();

      // Auto-set exploration topic if mentioned
      if (response.related_topics && response.related_topics.length > 0) {
        setCurrentExplorationTopic(response.related_topics[0]);
      }
    } catch (error) {
      console.error("Error in educational chat:", error);

      // ✅ REMOVER AMBAS as mensagens de loading e adicionar mensagem de erro
      setEducationalMessages((prev) => [
        ...prev.filter((msg) => msg.id !== loadingMessage.id), // Remove ambas as mensagens
        {
          id: `assistant_${Date.now()}`,
          content: `❌ **ERRO AO PROCESSAR PERGUNTA**

Desculpe, ocorreu um erro ao processar sua pergunta. 

**Possíveis causas:**
- Problemas temporários de conexão
- Sistema sobrecarregado
- Erro interno do servidor

**Sugestões:**
1. Tente novamente em alguns minutos
2. Verifique sua conexão com a internet
3. Se o problema persistir, entre em contato com o suporte

**Tempo estimado para resolução:** 5-15 minutos`,
          role: "assistant",
          timestamp: new Date(),
          isLoading: false,
        },
      ]);
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
    console.log("Source clicked:", source);
  };

  const handleVideoPlay = (video: any) => {
    // Handle video play request
    console.log("Video play requested:", video);
    // Could open in modal, navigate to video page, or handle differently
  };

  const handleNewSession = useCallback(() => {
    if (isUpdatingRef.current) return;
    isUpdatingRef.current = true;

    try {
      const newSessionId = createSession();
      setEducationalMessages([]);
      setSessionContext(null);
      setCurrentExplorationTopic("");
      setShowLearningPath(false);
      setSearchParams({ session: newSessionId }, { replace: true });
    } catch (error) {
      console.error("❌ Failed to create new session:", error);
      alert("Erro ao criar nova conversa. Verifique se você está logado.");
    }

    setTimeout(() => {
      isUpdatingRef.current = false;
    }, 100);
  }, [createSession, setSearchParams]);

  const handleDeleteSession = useCallback(
    (sessionId: string) => {
      if (sessions.length <= 1) return;

      deleteSession(sessionId);
      if (sessionId === activeSessionId) {
        const remainingSessions = sessions.filter((s) => s.id !== sessionId);
        if (remainingSessions.length > 0) {
          setActiveSession(remainingSessions[0].id);
          setSearchParams(
            { session: remainingSessions[0].id },
            { replace: true }
          );
        }
      }
    },
    [
      sessions,
      activeSessionId,
      deleteSession,
      setActiveSession,
      setSearchParams,
    ]
  );

  const currentSession = sessions.find((s) => s.id === activeSessionId);

  // Hook para pegar mensagens da sessão ativa
  const sessionMessages = useSessionMessages(activeSessionId);

  // Sincronizar mensagens do store com o estado local
  useEffect(() => {
    if (activeSessionId) {
      if (sessionMessages.length > 0) {
        const convertedMessages = sessionMessages.map((msg) => ({
          id: msg.id,
          content: msg.content,
          role: msg.role as "user" | "assistant",
          timestamp: new Date(msg.timestamp),
          sources: msg.sources,
          isLoading: false,
        }));

        setEducationalMessages(convertedMessages);
      } else {
        setEducationalMessages([]);
      }
    }
  }, [activeSessionId, sessionMessages.length]);

  // Verificar se há usuário logado
  if (!currentUserId) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-red-600"
            >
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="m22 2-7 20-4-9-9-4 20-7z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold mb-2">Usuário não logado</h3>
          <p className="text-gray-600 mb-4">
            Você precisa estar logado para acessar o assistente educacional.
          </p>
          <Button onClick={() => navigate("/login")}>Fazer Login</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col lg:flex-row">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 p-3 lg:p-4 flex-shrink-0">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-3 lg:mb-4 space-y-2 lg:space-y-0">
            <div className="flex-1">
              <BackButton />
              <h1 className="text-lg lg:text-xl font-semibold text-gray-900 mt-2 flex items-center space-x-2">
                <Brain className="text-red-600" size={20} />
                <span className="truncate">Assistente Educacional</span>
              </h1>
              {sessionContext?.current_focus && (
                <p className="text-xs lg:text-sm text-gray-600 mt-1 truncate">
                  Foco atual: {sessionContext.current_focus}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <Button
                onClick={() => setShowLearningPath(!showLearningPath)}
                variant={showLearningPath ? "default" : "outline"}
                size="sm"
                className="flex items-center gap-1 text-xs lg:text-sm"
              >
                <BookOpen size={14} />
                <span className="hidden sm:inline">Trilha de Aprendizado</span>
                <span className="sm:hidden">Trilha</span>
              </Button>

              <Button
                onClick={handleNewSession}
                variant="outline"
                size="sm"
                className="flex items-center gap-1 text-xs lg:text-sm"
                disabled={isProcessing}
              >
                <PlusCircle size={14} />
                <span className="hidden sm:inline">Nova conversa</span>
                <span className="sm:hidden">Nova</span>
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
        <div className="flex-1 overflow-y-auto p-3 lg:p-4 space-y-3 lg:space-y-4">
          <AnimatePresence>
            {educationalMessages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-8 lg:py-12"
              >
                <Brain
                  size={40}
                  className="mx-auto text-gray-400 mb-4 lg:hidden"
                />
                <Brain
                  size={48}
                  className="mx-auto text-gray-400 mb-4 hidden lg:block"
                />
                <h3 className="text-base lg:text-lg font-medium text-gray-900 mb-2">
                  Bem-vindo ao Assistente Educacional!
                </h3>
                <p className="text-sm lg:text-base text-gray-600 mb-4 lg:mb-6 max-w-md mx-auto px-4">
                  Faça perguntas sobre treinamento físico e receba respostas
                  detalhadas com fontes, sugestões de aprofundamento e trilhas
                  de aprendizado personalizadas.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 lg:gap-4 max-w-3xl mx-auto px-4">
                  <div className="bg-blue-50 p-3 lg:p-4 rounded-lg">
                    <Target className="text-blue-600 mb-2" size={20} />
                    <h4 className="font-medium text-blue-900 text-sm lg:text-base">
                      Personalizado
                    </h4>
                    <p className="text-xs lg:text-sm text-blue-700">
                      Adapta o nível de complexidade ao seu conhecimento
                    </p>
                  </div>
                  <div className="bg-green-50 p-3 lg:p-4 rounded-lg">
                    <BookOpen className="text-green-600 mb-2" size={20} />
                    <h4 className="font-medium text-green-900 text-sm lg:text-base">
                      Fontes Confiáveis
                    </h4>
                    <p className="text-xs lg:text-sm text-green-700">
                      Respostas baseadas em materiais científicos e práticos
                    </p>
                  </div>
                  <div className="bg-purple-50 p-3 lg:p-4 rounded-lg sm:col-span-2 lg:col-span-1">
                    <TrendingUp className="text-purple-600 mb-2" size={20} />
                    <h4 className="font-medium text-purple-900 text-sm lg:text-base">
                      Aprendizado Progressivo
                    </h4>
                    <p className="text-xs lg:text-sm text-purple-700">
                      Trilhas estruturadas para aprofundar conhecimentos
                    </p>
                  </div>
                </div>
              </motion.div>
            ) : (
              educationalMessages
                .filter((message) => !message.isHidden) // ✅ FILTRAR mensagens ocultas
                .map((message) => (
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
            animate={{ width: "100%", opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            className="border-l border-gray-200 bg-gray-50 overflow-hidden lg:w-96"
          >
            <div className="p-3 lg:p-4 h-full overflow-y-auto">
              <div className="flex items-center justify-between mb-3 lg:mb-4">
                <h3 className="text-base lg:text-lg font-semibold text-gray-900">
                  Trilha de Aprendizado
                </h3>
                <button
                  onClick={() => setShowLearningPath(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <ChevronRight size={18} />
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
                <div className="text-center py-8 lg:py-12">
                  <BookOpen
                    size={40}
                    className="mx-auto text-gray-400 mb-4 lg:hidden"
                  />
                  <BookOpen
                    size={48}
                    className="mx-auto text-gray-400 mb-4 hidden lg:block"
                  />
                  <p className="text-sm lg:text-base text-gray-600 px-4">
                    Selecione um tópico na conversa para ver a trilha de
                    aprendizado
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
