import React, { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useChatStore } from '../store/chat-store';
import { ChatInput } from '../components/chat/chat-input';
import { ChatHistory } from '../components/chat/chat-history';
import { Button } from '../components/ui/button';
import { BackButton } from '../components/ui/back-button';
import { PlusCircle, Trash2 } from 'lucide-react';
import { motion } from 'framer-motion';

export const ChatPage: React.FC = () => {
  const { 
    sessions,
    activeSessionId,
    isProcessing,
    createSession,
    setActiveSession,
    deleteSession,
    sendMessage
  } = useChatStore();
  
  const location = useLocation();
  const navigate = useNavigate();
  
  // Get session ID from URL query parameter
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sessionId = params.get('session');
    
    if (sessionId) {
      // Check if the session exists
      const sessionExists = sessions.some(session => session.id === sessionId);
      
      if (sessionExists) {
        setActiveSession(sessionId);
      } else {
        // Remove invalid session from URL
        navigate('/chat', { replace: true });
      }
    } else if (sessions.length > 0 && !activeSessionId) {
      // Set the first session as active if none is selected
      setActiveSession(sessions[0].id);
    }
  }, [location.search, sessions, activeSessionId, setActiveSession, navigate]);
  
  // Create a new session if none exists
  useEffect(() => {
    if (sessions.length === 0) {
      const newSessionId = createSession();
      navigate(`/chat?session=${newSessionId}`, { replace: true });
    }
  }, [sessions, createSession, navigate]);
  
  const handleSendMessage = (message: string) => {
    if (activeSessionId) {
      sendMessage(message);
    }
  };
  
  const handleNewSession = () => {
    const newSessionId = createSession();
    navigate(`/chat?session=${newSessionId}`);
  };
  
  const handleDeleteSession = (sessionId: string) => {
    deleteSession(sessionId);
  };
  
  const handleSelectSession = (sessionId: string) => {
    navigate(`/chat?session=${sessionId}`);
  };
  
  // Get the active session messages
  const activeSession = sessions.find(session => session.id === activeSessionId);
  const messages = activeSession?.messages || [];
  
  return (
    <div className="h-full flex flex-col">
      {/* Header with sessions */}
      <header className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <BackButton />
            <h1 className="text-xl font-semibold text-gray-900 mt-2">Assistente de Treino</h1>
          </div>
          
          <Button
            onClick={handleNewSession}
            variant="outline"
            className="flex items-center gap-1"
          >
            <PlusCircle size={16} />
            <span>Nova conversa</span>
          </Button>
        </div>
        
        {/* Session tabs */}
        {sessions.length > 0 && (
          <div className="mt-4 flex items-center gap-2 overflow-x-auto pb-2">
            {sessions.map(session => (
              <div
                key={session.id}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm cursor-pointer transition-colors ${
                  session.id === activeSessionId
                    ? 'bg-blue-100 text-blue-700 font-medium'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                onClick={() => handleSelectSession(session.id)}
              >
                <span className="truncate max-w-[150px]">{session.title}</span>
                
                {sessions.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSession(session.id);
                    }}
                    className="opacity-60 hover:opacity-100"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </header>
      
      {/* Chat area */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="flex-1 overflow-hidden"
        >
          {activeSession && (
            <ChatHistory 
              messages={messages} 
              isProcessing={isProcessing}
            />
          )}
        </motion.div>
        
        {/* Input area */}
        <div className="p-4 bg-gray-50 border-t border-gray-200">
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