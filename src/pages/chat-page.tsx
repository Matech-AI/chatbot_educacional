import React, { useEffect, useCallback, useMemo, useRef } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import {
  useUserChatSessions,
  useChatActions,
  useSessionMessages,
} from "../store/chat-store";
import { ChatInput } from "../components/chat/chat-input";
import { ChatHistory } from "../components/chat/chat-history";
import { Button } from "../components/ui/button";
import { BackButton } from "../components/ui/back-button";
import { PlusCircle, Trash2 } from "lucide-react";
import { motion } from "framer-motion";

const ChatPage: React.FC = () => {
  // Usar hooks especializados para evitar re-renders desnecessários
  const { sessions, activeSessionId, isProcessing, currentUserId } =
    useUserChatSessions();
  const { createSession, setActiveSession, deleteSession, sendMessage } =
    useChatActions();

  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Pegar o sessionId da URL de forma controlada
  const urlSessionId = searchParams.get("session");

  // Flag para prevenir loops infinitos
  const isUpdatingRef = useRef(false);

  // Pegar mensagens da sessão ativa
  const messages = useSessionMessages(activeSessionId);

  // ========================================
  // EFEITOS CONTROLADOS - CORRIGIDO PARA EVITAR LOOPS
  // ========================================

  // 1. Sincronizar URL com sessão ativa - COM PROTEÇÃO CONTRA LOOPS
  useEffect(() => {
    // Se há uma sessão na URL diferente da ativa, ativá-la
    if (urlSessionId && urlSessionId !== activeSessionId) {
      const sessionExists = sessions.some((s) => s.id === urlSessionId);
      if (sessionExists) {
        console.log("🎯 Activating session from URL:", urlSessionId);
        setActiveSession(urlSessionId);
      } else {
        console.log(
          "⚠️ Session from URL doesn't exist, clearing URL:",
          urlSessionId
        );
        setSearchParams({}, { replace: true });
      }
    }
  }, [
    urlSessionId,
    activeSessionId,
    sessions,
    setActiveSession,
    setSearchParams,
  ]);

  // 2. NÃO atualizar URL automaticamente quando sessão ativa muda
  // A URL só deve ser atualizada por ações explícitas do usuário

  // 3. Log para debug (sem limpeza automática para evitar confusão)
  useEffect(() => {
    console.log(
      "📊 Current state - Sessions:",
      sessions.length,
      "Active:",
      activeSessionId,
      "URL:",
      urlSessionId
    );
  }, [sessions.length, activeSessionId, urlSessionId]);

  // 4. Criar primeira sessão automaticamente quando acessar a página de chat
  useEffect(() => {
    // Verificar se há um usuário logado
    if (!currentUserId) {
      console.log("⚠️ No user logged in, cannot create sessions");
      return;
    }

    // ✅ Sempre criar uma sessão se não houver nenhuma
    if (sessions.length === 0) {
      console.log(
        "📝 ChatPage: No sessions exist, creating first session automatically"
      );
      try {
        const newSessionId = createSession();
        // Navegar imediatamente para a nova sessão
        setSearchParams({ session: newSessionId }, { replace: true });
      } catch (error) {
        console.error("❌ Failed to create session:", error);
      }
    }
    // Se há sessões mas nenhuma ativa e nenhuma na URL, ativar a primeira
    else if (!activeSessionId && !urlSessionId && sessions.length > 0) {
      console.log(
        "📝 ChatPage: Sessions exist but none active, activating first one"
      );
      const firstSession = sessions[0];
      setSearchParams({ session: firstSession.id }, { replace: true });
    }
  }, [
    sessions.length,
    activeSessionId,
    urlSessionId,
    createSession,
    setSearchParams,
    currentUserId,
  ]); // ✅ Incluir dependências para evitar criações desnecessárias

  // ========================================
  // CALLBACKS MEMOIZADOS
  // ========================================

  const handleSendMessage = useCallback(
    (message: string) => {
      console.log("📤 Sending message from ChatPage");
      sendMessage(message);
    },
    [sendMessage]
  );

  const handleNewSession = useCallback(() => {
    console.log("➕ Creating SINGLE new session from button");
    try {
      const newSessionId = createSession();
      // Forçar navegação imediata para a nova sessão
      setSearchParams({ session: newSessionId }, { replace: true });
    } catch (error) {
      console.error("❌ Failed to create new session:", error);
      // Mostrar mensagem de erro para o usuário
      alert("Erro ao criar nova conversa. Verifique se você está logado.");
    }
  }, [createSession, setSearchParams]);

  // Função temporária para resetar todas as sessões
  const handleResetSessions = useCallback(() => {
    if (
      window.confirm("Deseja limpar todas as conversas e resetar o sistema?")
    ) {
      localStorage.removeItem("chat-storage");
      window.location.reload();
    }
  }, []);

  const handleDeleteSession = useCallback(
    (sessionId: string) => {
      if (sessions.length <= 1) {
        console.log("⚠️ Cannot delete last session");
        return;
      }

      console.log("🗑️ Deleting session:", sessionId);

      // Get remaining sessions after deletion
      const remainingSessions = sessions.filter((s) => s.id !== sessionId);

      // Delete the session
      deleteSession(sessionId);

      // Handle URL and active session update
      if (sessionId === activeSessionId) {
        if (remainingSessions.length > 0) {
          // Navigate to the first remaining session
          const firstRemaining = remainingSessions[0];
          console.log(
            "🎯 Navigating to first remaining session:",
            firstRemaining.id
          );
          setSearchParams({ session: firstRemaining.id }, { replace: true });
        } else {
          // No sessions left, clear URL
          console.log("🧹 No sessions left, clearing URL");
          setSearchParams({}, { replace: true });
        }
      } else if (sessionId === urlSessionId) {
        // If we deleted the session from URL but it wasn't active, clear URL
        console.log("🧹 Deleted session was in URL, clearing URL");
        setSearchParams({}, { replace: true });
      }
    },
    [sessions, deleteSession, activeSessionId, urlSessionId, setSearchParams]
  );

  const handleSelectSession = useCallback(
    (sessionId: string) => {
      console.log("👆 Selecting session:", sessionId);
      // Só atualizar se for diferente da sessão atual
      if (sessionId !== activeSessionId) {
        setActiveSession(sessionId);
        setSearchParams({ session: sessionId }, { replace: true });
      }
    },
    [setSearchParams, setActiveSession, activeSessionId]
  );

  // ========================================
  // VALORES MEMOIZADOS
  // ========================================

  const canDelete = useMemo(() => sessions.length > 1, [sessions.length]);

  // ========================================
  // RENDER
  // ========================================

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
            Você precisa estar logado para acessar o assistente de treino.
          </p>
          <Button onClick={() => navigate("/login")}>Fazer Login</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full min-h-dvh flex flex-col">
      {/* Header com sessões */}
      <header className="bg-white border-b border-gray-200 p-4 flex-shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div>
            <BackButton />
            <h1 className="text-xl font-semibold text-gray-900 mt-2">
              💬 Assistente de Treino
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <Button
              onClick={handleResetSessions}
              variant="ghost"
              size="sm"
              className="text-xs text-red-500 hover:text-red-700"
              title="Resetar todas as conversas"
            >
              Reset
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

        {/* Abas de sessões */}
        {sessions.length > 0 && (
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {sessions.map((session) => (
              <SessionTab
                key={session.id}
                session={session}
                isActive={session.id === activeSessionId}
                canDelete={canDelete}
                onSelect={handleSelectSession}
                onDelete={handleDeleteSession}
              />
            ))}
          </div>
        )}
      </header>

      {/* Área do chat */}
      <div className="flex-1 overflow-hidden flex flex-col min-h-0">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="flex-1 overflow-y-auto"
        >
          <ChatHistory messages={messages} isProcessing={isProcessing} />
        </motion.div>

        {/* Área de input */}
        <div className="p-4 bg-gray-50 border-t border-gray-200 flex-shrink-0 sticky bottom-0 z-10 pb-[calc(1rem+env(safe-area-inset-bottom))]">
          <ChatInput
            onSendMessage={handleSendMessage}
            isDisabled={isProcessing || !activeSessionId}
            placeholder="Digite sua pergunta sobre o material do curso..."
          />
        </div>
      </div>
    </div>
  );
};

// ========================================
// COMPONENTE DA ABA DE SESSÃO
// ========================================

interface SessionTabProps {
  session: { id: string; title: string };
  isActive: boolean;
  canDelete: boolean;
  onSelect: (sessionId: string) => void;
  onDelete: (sessionId: string) => void;
}

const SessionTab: React.FC<SessionTabProps> = ({
  session,
  isActive,
  canDelete,
  onSelect,
  onDelete,
}) => {
  const handleClick = useCallback(() => {
    onSelect(session.id);
  }, [onSelect, session.id]);

  const handleDelete = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (window.confirm(`Deseja excluir a conversa "${session.title}"?`)) {
        onDelete(session.id);
      }
    },
    [onDelete, session.id, session.title]
  );

  return (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm cursor-pointer transition-colors ${
        isActive
          ? "bg-blue-100 text-blue-700 font-medium"
          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
      }`}
      onClick={handleClick}
    >
      <span className="truncate max-w-[150px]">{session.title}</span>

      {canDelete && (
        <button
          onClick={handleDelete}
          className="opacity-60 hover:opacity-100 transition-opacity"
          title="Excluir conversa"
        >
          <Trash2 size={14} />
        </button>
      )}
    </div>
  );
};

// Export default para funcionar com lazy loading
export default ChatPage;
