// 3. Cimport React, { useEffect, useCallback, useMemo } from 'react';
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import {
  useChatSessions,
  useChatActions,
  useSessionMessages,
} from "../store/chat-store";
import { ChatInput } from "../components/chat/chat-input";
import { ChatHistory } from "../components/chat/chat-history";
import { Button } from "../components/ui/button";
import { BackButton } from "../components/ui/back-button";
import { PlusCircle, Trash2 } from "lucide-react";
import { motion } from "framer-motion";

export const ChatPage: React.FC = () => {
  // Usar hooks especializados para evitar re-renders desnecessários
  const { sessions, activeSessionId, isProcessing } = useChatSessions();
  const { createSession, setActiveSession, deleteSession, sendMessage } =
    useChatActions();

  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Pegar o sessionId da URL de forma controlada
  const urlSessionId = searchParams.get("session");

  // Pegar mensagens da sessão ativa
  const messages = useSessionMessages(activeSessionId);

  // ========================================
  // EFEITOS CONTROLADOS
  // ========================================

  // 1. Sincronizar URL com sessão ativa (apenas quando necessário)
  useEffect(() => {
    if (urlSessionId && urlSessionId !== activeSessionId) {
      const sessionExists = sessions.some(
        (session) => session.id === urlSessionId
      );

      if (sessionExists) {
        console.log("🎯 Setting active session from URL:", urlSessionId);
        setActiveSession(urlSessionId);
      } else {
        console.log("⚠️ Session from URL does not exist, removing from URL");
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

  // 2. Atualizar URL quando sessão ativa muda (apenas quando necessário)
  useEffect(() => {
    if (activeSessionId && activeSessionId !== urlSessionId) {
      console.log("🔗 Updating URL with active session:", activeSessionId);
      setSearchParams({ session: activeSessionId }, { replace: true });
    }
  }, [activeSessionId, urlSessionId, setSearchParams]);

  // 3. Criar primeira sessão apenas se necessário
  useEffect(() => {
    if (sessions.length === 0 && !activeSessionId) {
      console.log("📝 No sessions exist, creating first session");
      const newSessionId = createSession();
      // A URL será atualizada pelo useEffect acima
    }
  }, [sessions.length, activeSessionId, createSession]);

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
    console.log("➕ Creating new session from button");
    const newSessionId = createSession();
    // A navegação será feita pelos useEffects
  }, [createSession]);

  const handleDeleteSession = useCallback(
    (sessionId: string) => {
      if (sessions.length <= 1) {
        console.log("⚠️ Cannot delete last session");
        return;
      }

      console.log("🗑️ Deleting session:", sessionId);
      deleteSession(sessionId);

      // Se deletou a sessão ativa e não há mais na URL, limpar URL
      if (sessionId === activeSessionId && sessionId === urlSessionId) {
        setSearchParams({}, { replace: true });
      }
    },
    [
      sessions.length,
      deleteSession,
      activeSessionId,
      urlSessionId,
      setSearchParams,
    ]
  );

  const handleSelectSession = useCallback(
    (sessionId: string) => {
      console.log("👆 Selecting session:", sessionId);
      setSearchParams({ session: sessionId }, { replace: true });
    },
    [setSearchParams]
  );

  // ========================================
  // VALORES MEMOIZADOS
  // ========================================

  const canDelete = useMemo(() => sessions.length > 1, [sessions.length]);

  // ========================================
  // RENDER
  // ========================================

  return (
    <div className="h-full flex flex-col">
      {/* Header com sessões */}
      <header className="bg-white border-b border-gray-200 p-4 flex-shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div>
            <BackButton />
            <h1 className="text-xl font-semibold text-gray-900 mt-2">
              💬 Assistente de Treino
            </h1>
          </div>

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
          className="flex-1 overflow-hidden"
        >
          <ChatHistory messages={messages} isProcessing={isProcessing} />
        </motion.div>

        {/* Área de input */}
        <div className="p-4 bg-gray-50 border-t border-gray-200 flex-shrink-0">
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
