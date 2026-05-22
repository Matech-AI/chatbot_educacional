import React from "react";
import { useSearchParams } from "react-router-dom";
import { Plus, MessageSquare, Trash2 } from "lucide-react";
import {
  useUserChatSessions,
  useChatActions,
} from "../../store/chat-store";

interface ChatSidebarSessionsProps {
  onClose?: () => void;
}

export const ChatSidebarSessions: React.FC<ChatSidebarSessionsProps> = ({
  onClose,
}) => {
  const { sessions, activeSessionId } = useUserChatSessions();
  const { createSession, setActiveSession, deleteSession } = useChatActions();
  const [, setSearchParams] = useSearchParams();

  const handleNewSession = () => {
    try {
      const newSessionId = createSession();
      setActiveSession(newSessionId);
      setSearchParams({ session: newSessionId }, { replace: true });
      onClose?.();
    } catch {
      // usuário sem sessão válida — ignorar silenciosamente
    }
  };

  const handleSelectSession = (sessionId: string) => {
    setActiveSession(sessionId);
    setSearchParams({ session: sessionId }, { replace: true });
    onClose?.();
  };

  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (sessions.length <= 1) return;
    deleteSession(sessionId);
    if (sessionId === activeSessionId) {
      const remaining = sessions.filter((s) => s.id !== sessionId);
      if (remaining.length > 0) {
        setActiveSession(remaining[0].id);
        setSearchParams({ session: remaining[0].id }, { replace: true });
      }
    }
  };

  return (
    <div className="flex flex-col min-h-0 flex-1 px-3 pb-2">
      <div className="flex items-center justify-between px-1 mb-2">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Conversas
        </span>
        <button
          type="button"
          onClick={handleNewSession}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          title="Nova conversa"
          aria-label="Nova conversa"
        >
          <Plus size={16} />
        </button>
      </div>

      <ul className="space-y-0.5 overflow-y-auto flex-1 min-h-0 sidebar-dark-scroll pr-0.5">
        {sessions.length === 0 ? (
          <li className="px-2 py-3 text-xs text-slate-500 leading-relaxed">
            Nenhuma conversa ainda. Use o botão + para começar.
          </li>
        ) : (
          sessions.map((session) => {
            const isActive = session.id === activeSessionId;
            return (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => handleSelectSession(session.id)}
                  className={`group w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left text-sm transition-colors ${
                    isActive
                      ? "bg-white/10 text-white"
                      : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                  }`}
                >
                  <MessageSquare
                    size={15}
                    className={`shrink-0 ${
                      isActive ? "text-red-400" : "text-slate-500"
                    }`}
                  />
                  <span className="truncate flex-1">{session.title}</span>
                  {sessions.length > 1 && (
                    <span
                      role="button"
                      tabIndex={0}
                      onClick={(e) => handleDeleteSession(e, session.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          handleDeleteSession(
                            e as unknown as React.MouseEvent,
                            session.id
                          );
                        }
                      }}
                      className="opacity-0 group-hover:opacity-100 p-0.5 rounded text-slate-500 hover:text-red-400 transition-all shrink-0"
                      aria-label="Excluir conversa"
                    >
                      <Trash2 size={13} />
                    </span>
                  )}
                </button>
              </li>
            );
          })
        )}
      </ul>
    </div>
  );
};
