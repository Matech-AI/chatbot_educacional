import { create } from 'zustand';
import { ChatSession, Message, Source } from '../types';
import { generateUniqueId } from '../lib/utils';

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

// Mock function to simulate sending a message to the AI
const mockSendToAI = async (message: string): Promise<{ content: string, sources: Source[] }> => {
  // Simulate response time
  await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
  
  const mockResponses = [
    {
      content: "Os exercícios de força são fundamentais para o desenvolvimento muscular. De acordo com os estudos mais recentes, treinos de alta intensidade promovem maior hipertrofia quando comparados a treinos de baixa intensidade com alto volume.",
      sources: [
        {
          title: "Princípios do Treinamento de Força.pdf",
          source: "/data/materiais/princ-treinamento.pdf",
          page: 24,
          chunk: "Os estudos demonstram que o treinamento de alta intensidade (>80% 1RM) é mais eficaz para..."
        }
      ]
    },
    {
      content: "Para maximizar os resultados no treinamento, é essencial entender os princípios da periodização. Este conceito permite variar sistematicamente o volume e a intensidade ao longo do tempo, evitando platôs e reduzindo o risco de lesões.",
      sources: [
        {
          title: "Periodização do Treinamento.pdf",
          source: "/data/materiais/periodizacao.pdf",
          page: 12,
          chunk: "A periodização é definida como a variação planejada das variáveis de treinamento..."
        },
        {
          title: "Prevenção de Lesões.docx",
          source: "/data/materiais/prevencao.docx",
          page: null,
          chunk: "Estudos indicam que a periodização adequada reduz em até 40% o risco de lesões por uso excessivo..."
        }
      ]
    },
    {
      content: "A nutrição adequada é um componente crucial no processo de ganho muscular. A ingestão de proteínas no período pós-treino (dentro da janela anabólica de aproximadamente 2 horas) maximiza a síntese proteica muscular e acelera a recuperação.",
      sources: [
        {
          title: "Nutrição Esportiva.pdf",
          source: "/data/materiais/nutricao.pdf",
          page: 56,
          chunk: "A janela anabólica representa um período de aproximadamente 2 horas após o exercício..."
        }
      ]
    }
  ];
  
  // Return a random mock response
  return mockResponses[Math.floor(Math.random() * mockResponses.length)];
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
      const response = await mockSendToAI(content);
      
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
    } catch (error) {
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
                        content: "Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
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