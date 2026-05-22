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
  BookOpen,
  Target,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  Settings,
} from "lucide-react";
import { api } from "../lib/api";
import { LOGO_PATH, SITE_NAME } from "../constants/branding";
import { useAuthStore } from "../store/auth-store";

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
    sendMessage,
    addMessage,
  } = useChatActions();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { isAuthenticated } = useAuthStore();

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

  return (
    <div className="h-full flex flex-col lg:flex-row bg-slate-50">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-4 lg:px-6 py-4 flex-shrink-0">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
            <div className="flex-1 min-w-0">
              <BackButton />
              <div className="flex items-center gap-3 mt-1">
                <div className="w-9 h-9 rounded-lg bg-[#0f1419] flex items-center justify-center shrink-0 p-1.5">
                  <img
                    src={LOGO_PATH}
                    alt={SITE_NAME}
                    className="w-full h-full object-contain"
                  />
                </div>
                <div className="min-w-0">
                  <h1 className="text-lg font-semibold text-slate-900 tracking-tight truncate">
                    Assistente Educacional
                  </h1>
                  {sessionContext?.current_focus ? (
                    <p className="text-xs text-slate-500 mt-0.5 truncate">
                      Foco: {sessionContext.current_focus}
                    </p>
                  ) : (
                    <p className="text-xs text-slate-500 mt-0.5">
                      {isAuthenticated
                        ? "Treinamento com IA"
                        : "Acesso público · Matech.AI"}
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap shrink-0">
              <Button
                onClick={() => setShowLearningPath(!showLearningPath)}
                variant={showLearningPath ? "accent" : "outline"}
                size="sm"
                className={`flex items-center gap-1.5 text-xs ${
                  !showLearningPath
                    ? "border-slate-200 text-slate-700 hover:bg-slate-50"
                    : ""
                }`}
              >
                <BookOpen size={14} />
                <span className="hidden sm:inline">Trilha</span>
              </Button>

              <Button
                onClick={handleNewSession}
                variant="outline"
                size="sm"
                className="flex items-center gap-1.5 text-xs border-slate-200 text-slate-700 hover:bg-slate-50"
                disabled={isProcessing}
              >
                <PlusCircle size={14} />
                <span className="hidden sm:inline">Nova conversa</span>
                <span className="sm:hidden">Nova</span>
              </Button>
            </div>
          </div>

        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 lg:px-6 py-4 space-y-4">
          <AnimatePresence>
            {educationalMessages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-2xl mx-auto text-center py-10 lg:py-16"
              >
                <div className="w-14 h-14 mx-auto mb-5 rounded-2xl bg-[#0f1419] flex items-center justify-center p-3">
                  <img
                    src={LOGO_PATH}
                    alt={SITE_NAME}
                    className="w-full h-full object-contain"
                  />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">
                  Como posso ajudar?
                </h3>
                <p className="text-sm text-slate-500 mb-8 leading-relaxed max-w-md mx-auto">
                  Pergunte sobre treinamento físico e receba respostas com
                  fontes e sugestões de aprofundamento.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-left">
                  {[
                    {
                      icon: <Target size={18} className="text-red-500" />,
                      title: "Personalizado",
                      desc: "Adaptado ao seu nível",
                    },
                    {
                      icon: <BookOpen size={18} className="text-red-500" />,
                      title: "Com fontes",
                      desc: "Base científica e prática",
                    },
                    {
                      icon: <TrendingUp size={18} className="text-red-500" />,
                      title: "Progressivo",
                      desc: "Trilhas de aprendizado",
                    },
                  ].map((card) => (
                    <div
                      key={card.title}
                      className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm"
                    >
                      <div className="mb-2">{card.icon}</div>
                      <h4 className="font-medium text-slate-900 text-sm">
                        {card.title}
                      </h4>
                      <p className="text-xs text-slate-500 mt-1">{card.desc}</p>
                    </div>
                  ))}
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
            className="border-l border-slate-200 bg-white overflow-hidden lg:w-96"
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
