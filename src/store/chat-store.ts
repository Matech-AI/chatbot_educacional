import { create } from 'zustand';
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
    const response = await api.chat(message);
    
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
    console.error('Error sending message to AI:', error);
    
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
    const newSession: ChatSession = {
      id,
      title: `Nova conversa ${get().sessions.length + 1}`,
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    set(state => ({
      sessions: [...state.sessions, newSession],
      activeSessionId: id
    }));
    
    return id;
  },
  
  renameSession: (sessionId, title) => {
    set(state => ({
      sessions: state.sessions.map(session => 
        session.id === sessionId 
          ? { ...session, title, updatedAt: new Date() } 
          : session
      )
    }));
  },
  
  deleteSession: (sessionId) => {
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
    const { activeSessionId, addMessage } = get();
    
    // Create a session if none exists
    let sessionId = activeSessionId;
    if (!sessionId) {
      sessionId = get().createSession();
    }
    
    // Add user message
    addMessage(sessionId, content, 'user');
    
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
      const session = get().sessions.find(s => s.id === sessionId);
      if (session && session.messages.length === 2) { // User + AI response
        const title = content.length > 30 ? content.substring(0, 30) + '...' : content;
        get().renameSession(sessionId, title);
      }
      
    } catch (error) {
      console.error('Error in sendMessage:', error);
      
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