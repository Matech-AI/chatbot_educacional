import { create } from 'zustand';
import { useCallback } from 'react';
import { ChatSession, Message, Source } from '../types';
import { generateUniqueId } from '../lib/utils';
import { api } from '../lib/api';

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isProcessing: boolean;
  createSession: () => string;
  renameSession: (sessionId: string, title: string) => void;
  deleteSession: (sessionId: string) => void;
  setActiveSession: (sessionId: string) => void;
  addMessage: (sessionId: string, content: string, role: 'user' | 'assistant' | 'system', sources?: Source[]) => void;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: (sessionId: string) => void;
}

// Function to send message to AI backend
const sendToAI = async (message: string): Promise<{ content: string, sources: Source[] }> => {
  try {
    console.log('🤖 Sending message to AI:', message.substring(0, 50) + '...');
    const response = await api.chat(message);
    
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

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  isProcessing: false,
  
  createSession: () => {
    const id = generateUniqueId();
    const currentSessions = get().sessions;
    const newSession: ChatSession = {
      id,
      title: `Nova conversa ${currentSessions.length + 1}`,
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    console.log('💬 Creating new chat session:', id);
    
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
        newActiveId = filteredSessions.length > 0 ? filteredSessions[0].id : null;
      }
      
      return {
        sessions: filteredSessions,
        activeSessionId: newActiveId
      };
    });
  },
  
  setActiveSession: (sessionId) => {
    console.log('🎯 Setting active session:', sessionId);
    set({ activeSessionId: sessionId });
  },
  
  addMessage: (sessionId, content, role, sources = []) => {
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
    
    // Create a session if none exists
    if (!sessionId) {
      console.log('📝 No active session, creating new one...');
      sessionId = get().createSession();
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
}));

// Hook personalizado para evitar re-renders desnecessários
export const useChatActions = () => {
  const store = useChatStore();
  
  return {
    createSession: useCallback(store.createSession, []),
    renameSession: useCallback(store.renameSession, []),
    deleteSession: useCallback(store.deleteSession, []),
    setActiveSession: useCallback(store.setActiveSession, []),
    addMessage: useCallback(store.addMessage, []),
    sendMessage: useCallback(store.sendMessage, []),
    clearMessages: useCallback(store.clearMessages, []),
  };
};