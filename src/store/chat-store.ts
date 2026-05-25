import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ChatSession, Message, Source } from '../types';
import { generateUniqueId } from '../lib/utils';
import { api } from '../lib/api';

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isProcessing: boolean;
  currentUserId: string | null; // ID do usuário atual
  createSession: () => string;
  renameSession: (sessionId: string, title: string) => void;
  deleteSession: (sessionId: string) => void;
  setActiveSession: (sessionId: string) => void;
  addMessage: (sessionId: string, content: string, role: 'user' | 'assistant' | 'system', sources?: Source[]) => void;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: (sessionId: string) => void;
  setCurrentUser: (userId: string) => void; // Função para definir o usuário atual
  clearUserData: () => void; // Função para limpar dados quando usuário faz logout
}

// Function to send message to AI backend
const sendToAI = async (message: string): Promise<{ content: string, sources: Source[] }> => {
  try {
    console.log('🤖 Sending message to AI:', message.substring(0, 50) + '...');
    const response = await api.chatAuth(message);
    
    console.log('✅ AI response received');
    return {
      content: response.answer || "Desculpe, não consegui processar sua mensagem.",
      sources: response.sources ? response.sources.map((source: any) => ({
        title: source.title || 'Documento',
        source: source.source || '',
        page: source.page,
        chunk: source.chunk || ''
      })) : []
    };
  } catch (error) {
    console.error('❌ Error sending message to AI:', error);
    
    // Return error message
    return {
      content: "Ocorreu um erro ao processar sua mensagem. Verifique se o sistema está inicializado e tente novamente.",
      sources: []
    };
  }
};

export const useChatStore = create<ChatState>()(persist((set, get) => ({
  sessions: [],
  activeSessionId: null,
  isProcessing: false,
  currentUserId: null,
  
  setCurrentUser: (userId: string) => {
    console.log('👤 Setting current user for chat sessions:', userId);
    set({ currentUserId: userId });
  },
  
  clearUserData: () => {
    console.log('🧹 Clearing user chat data');
    set({
      activeSessionId: null,
      currentUserId: null
    });
  },
  
  createSession: () => {
    const state = get();
    
    // Verificar se há um usuário logado
    if (!state.currentUserId) {
      console.error('❌ No user logged in. Cannot create session.');
      throw new Error('Usuário não está logado');
    }
    
    // ✅ Verificar se já há uma sessão sendo criada recentemente (últimos 100ms)
    const now = Date.now();
    const recentSession = state.sessions.find(session => 
      session.userId === state.currentUserId &&
      now - new Date(session.createdAt).getTime() < 100
    );
    
    if (recentSession) {
      console.log('⚠️ Session recently created, returning existing:', recentSession.id);
      return recentSession.id;
    }
    
    // ✅ Gerar ID único com timestamp para garantir unicidade
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2);
    const id = `${timestamp}_${random}`;
    
    // ✅ Calcular próximo número baseado no maior número existente para este usuário
    const userSessions = state.sessions.filter(session => session.userId === state.currentUserId);
    const existingNumbers = userSessions
      .map(session => {
        const match = session.title.match(/Nova conversa (\d+)/);
        return match ? parseInt(match[1], 10) : 0;
      })
      .filter(num => num > 0);
    
    const conversationNumber = existingNumbers.length > 0 
      ? Math.max(...existingNumbers) + 1 
      : 1;
    
    const newSession: ChatSession = {
      id,
      title: `Nova conversa ${conversationNumber}`,
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      userId: state.currentUserId
    };
    
    console.log('💬 Creating new chat session for user:', state.currentUserId, 'session ID:', id, 'number:', conversationNumber);
    
    // ✅ ADICIONAR nova sessão (não substituir)
    set(state => ({
      sessions: [...state.sessions, newSession],
      activeSessionId: id
    }));
    
    return id;
  },
  
  renameSession: (sessionId, title) => {
    console.log('✏️ Renaming session:', sessionId, 'to:', title);
    
    set(state => ({
      sessions: state.sessions.map(session => 
        session.id === sessionId 
          ? { ...session, title, updatedAt: new Date() } 
          : session
      )
    }));
  },
  
  deleteSession: (sessionId) => {
    console.log('🗑️ Deleting session:', sessionId);
    
    set(state => {
      const filteredSessions = state.sessions.filter(session => session.id !== sessionId);
      let newActiveId = state.activeSessionId;
      
      // If we deleted the active session, select another one if available
      if (state.activeSessionId === sessionId) {
        // Buscar próxima sessão do mesmo usuário
        const userSessions = filteredSessions.filter(session => session.userId === state.currentUserId);
        newActiveId = userSessions.length > 0 ? userSessions[0].id : null;
        console.log('💡 Active session deleted, new active:', newActiveId);
      }
      
      return {
        sessions: filteredSessions,
        activeSessionId: newActiveId
      };
    });
  },
  
  setActiveSession: (sessionId) => {
    const state = get();
    
    // Verificar se a sessão existe e pertence ao usuário atual
    const sessionExists = state.sessions.some(session => 
      session.id === sessionId && session.userId === state.currentUserId
    );
    
    if (!sessionExists) {
      console.warn('⚠️ Trying to set active session that does not exist or does not belong to current user:', sessionId);
      return;
    }
    
    // Evitar mudanças desnecessárias
    if (state.activeSessionId === sessionId) {
      console.log('📌 Session already active, skipping:', sessionId);
      return;
    }
    
    console.log('🎯 Setting active session:', sessionId);
    set({ activeSessionId: sessionId });
  },
  
  addMessage: (sessionId, content, role, sources = []) => {
    const state = get();
    
    // Verificar se a sessão pertence ao usuário atual
    const session = state.sessions.find(s => s.id === sessionId && s.userId === state.currentUserId);
    if (!session) {
      console.error('❌ Session does not exist or does not belong to current user:', sessionId);
      return;
    }
    
    const message: Message = {
      id: generateUniqueId(),
      content,
      role,
      timestamp: new Date(),
      sources
    };
    
    set(state => ({
      sessions: state.sessions.map(session => 
        session.id === sessionId 
          ? { 
              ...session, 
              messages: [...session.messages, message],
              updatedAt: new Date()
            } 
          : session
      )
    }));
  },
  
  sendMessage: async (content) => {
    const state = get();
    let sessionId = state.activeSessionId;
    
    // ✅ NÃO criar sessão automaticamente - exigir que exista
    if (!sessionId) {
      console.error('❌ No active session for sending message. Create a session first.');
      return;
    }
    
    // ✅ Verificar se a sessão ativa realmente existe e pertence ao usuário atual
    const sessionExists = state.sessions.some(session => 
      session.id === sessionId && session.userId === state.currentUserId
    );
    if (!sessionExists) {
      console.error('❌ Active session does not exist or does not belong to current user:', sessionId);
      set({ activeSessionId: null });
      return;
    }
    
    console.log('📤 Sending message in session:', sessionId);
    
    // Add user message
    get().addMessage(sessionId, content, 'user');
    
    // Set loading state
    set({ isProcessing: true });
    
    // Add temporary assistant message with loading state
    const tempId = generateUniqueId();
    const tempMessage: Message = {
      id: tempId,
      content: '',
      role: 'assistant',
      timestamp: new Date(),
      isLoading: true
    };
    
    set(state => ({
      sessions: state.sessions.map(session => 
        session.id === sessionId 
          ? { 
              ...session, 
              messages: [...session.messages, tempMessage],
              updatedAt: new Date()
            } 
          : session
      )
    }));
    
    try {
      // Get AI response
      const response = await sendToAI(content);
      
      // Replace the temporary message with the actual response
      set(state => ({
        sessions: state.sessions.map(session => 
          session.id === sessionId 
            ? { 
                ...session, 
                messages: session.messages.map(msg => 
                  msg.id === tempId 
                    ? {
                        ...msg,
                        content: response.content,
                        sources: response.sources,
                        isLoading: false
                      } 
                    : msg
                ),
                updatedAt: new Date()
              } 
            : session
        ),
        isProcessing: false
      }));
      
      // Auto-rename session based on first message
      const updatedState = get();
      const session = updatedState.sessions.find(s => s.id === sessionId);
      if (session && session.messages.length === 2) { // User + AI response
        const title = content.length > 30 ? content.substring(0, 30) + '...' : content;
        get().renameSession(sessionId, title);
      }
      
    } catch (error) {
      console.error('❌ Error in sendMessage:', error);
      
      // Update with error message
      set(state => ({
        sessions: state.sessions.map(session => 
          session.id === sessionId 
            ? { 
                ...session, 
                messages: session.messages.map(msg => 
                  msg.id === tempId 
                    ? {
                        ...msg,
                        content: "Ocorreu um erro ao processar sua mensagem. Por favor, verifique se o sistema está inicializado e tente novamente.",
                        isLoading: false
                      } 
                    : msg
                ),
                updatedAt: new Date()
              } 
            : session
        ),
        isProcessing: false
      }));
    }
  },
  
  clearMessages: (sessionId) => {
    console.log('🧹 Clearing messages for session:', sessionId);
    
    set(state => ({
      sessions: state.sessions.map(session => 
        session.id === sessionId 
          ? { 
              ...session, 
              messages: [],
              updatedAt: new Date()
            } 
          : session
      )
    }));
  }
}), {
  name: 'chat-storage',
  version: 2, // Incrementar versão para forçar migração
  // Don't persist isProcessing state
  partialize: (state) => ({
    sessions: state.sessions,
    activeSessionId: state.activeSessionId,
    currentUserId: state.currentUserId
  }),
  
  // Migração para adicionar userId às sessões existentes
  migrate: (persistedState: any, version: number) => {
    if (version < 2) {
      // Migrar sessões existentes para incluir userId
      const migratedSessions = persistedState.sessions?.map((session: any) => ({
        ...session,
        userId: 'anonymous' // Usuário anônimo para sessões antigas
      })) || [];
      
      return {
        ...persistedState,
        sessions: migratedSessions,
        currentUserId: null
      };
    }
    return persistedState;
  }
}));
// ========================================
// HOOKS ESPECIALIZADOS PARA EVITAR RE-RENDERS
// ========================================

// Hook para pegar apenas os dados necessários
export const useChatSessions = () => {
  const sessions = useChatStore(state => state.sessions);
  const activeSessionId = useChatStore(state => state.activeSessionId);
  const isProcessing = useChatStore(state => state.isProcessing);
  
  return { sessions, activeSessionId, isProcessing };
};

// Hook para pegar apenas as ações
export const useChatActions = () => {
  const createSession = useChatStore(state => state.createSession);
  const renameSession = useChatStore(state => state.renameSession);
  const deleteSession = useChatStore(state => state.deleteSession);
  const setActiveSession = useChatStore(state => state.setActiveSession);
  const addMessage = useChatStore(state => state.addMessage);
  const sendMessage = useChatStore(state => state.sendMessage);
  const clearMessages = useChatStore(state => state.clearMessages);
  const setCurrentUser = useChatStore(state => state.setCurrentUser);
  const clearUserData = useChatStore(state => state.clearUserData);
  
  return {
    createSession,
    renameSession,
    deleteSession,
    setActiveSession,
    addMessage,
    sendMessage,
    clearMessages,
    setCurrentUser,
    clearUserData
  };
};

// Hook para pegar mensagens de uma sessão específica
export const useSessionMessages = (sessionId: string | null) => {
  const session = useChatStore(state => 
    sessionId ? state.sessions.find(s => s.id === sessionId) : null
  );
  
  return session?.messages || [];
};

// Hook para pegar apenas as sessões do usuário atual
export const useUserChatSessions = () => {
  const sessions = useChatStore(state => 
    state.currentUserId 
      ? state.sessions.filter(session => session.userId === state.currentUserId)
      : []
  );
  const activeSessionId = useChatStore(state => state.activeSessionId);
  const isProcessing = useChatStore(state => state.isProcessing);
  const currentUserId = useChatStore(state => state.currentUserId);
  
  return { sessions, activeSessionId, isProcessing, currentUserId };
};