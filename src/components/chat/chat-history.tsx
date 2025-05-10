import React, { useRef, useEffect } from 'react';
import { Message } from '../../types';
import { MessageBubble } from './message-bubble';
import { motion } from 'framer-motion';

interface ChatHistoryProps {
  messages: Message[];
  isProcessing: boolean;
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ 
  messages,
  isProcessing
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  if (messages.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md mx-auto p-6"
        >
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-600">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold mb-2">Comece uma conversa</h3>
          <p className="text-gray-600 mb-4">
            Faça perguntas sobre o material do curso. O assistente irá
            responder com base no conteúdo dos documentos.
          </p>
          <div className="space-y-2 text-sm text-gray-500">
            <p>Exemplo de perguntas:</p>
            <ul className="list-disc text-left pl-5 space-y-1">
              <li>Quais são os benefícios do treinamento de força?</li>
              <li>Como funciona a periodização no treinamento?</li>
              <li>Explique o conceito de supercompensação.</li>
            </ul>
          </div>
        </motion.div>
      </div>
    );
  }
  
  return (
    <div className="h-full overflow-y-auto px-4 py-6">
      {messages.map(message => (
        <MessageBubble 
          key={message.id} 
          message={message} 
        />
      ))}
      
      {/* Auto-scroll anchor */}
      <div ref={bottomRef} />
    </div>
  );
};