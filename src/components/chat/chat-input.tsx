import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../ui/button';
import { Send } from 'lucide-react';
import { motion } from 'framer-motion';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isDisabled?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  isDisabled = false,
  placeholder = 'Digite sua pergunta...'
}) => {
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (message.trim() && !isDisabled) {
      setIsSending(true);
      await onSendMessage(message.trim());
      setMessage('');
      setIsSending(false);
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Submit with Enter (without shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  // Auto-resize textarea
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 150);
      textarea.style.height = `${newHeight}px`;
    }
  };
  
  useEffect(() => {
    adjustTextareaHeight();
  }, [message]);
  
  const suggestedQuestions = [
    "Como melhorar minha técnica?",
    "Qual a diferença entre hipertrofia e força?",
    "Como montar um programa de treino?",
    "Quais são os princípios da periodização?",
    "Como prevenir lesões durante o treino?",
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-gray-200 rounded-lg shadow-sm p-3 relative"
    >
      <div className="mb-3 flex flex-wrap gap-2">
        {suggestedQuestions.map((question, index) => (
          <button
            key={index}
            onClick={() => setMessage(question)}
            className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full px-3 py-1 transition-colors"
          >
            {question}
          </button>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isDisabled}
          rows={1}
          className="flex-1 resize-none py-2 px-3 text-sm border-0 focus:ring-0 focus:outline-none"
          style={{ minHeight: "44px", maxHeight: "150px" }}
        />

        <Button
          type="submit"
          disabled={!message.trim() || isDisabled || isSending}
          size="icon"
          className="rounded-full transition-all duration-200"
        >
          {isSending ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
          ) : (
            <Send size={18} />
          )}
        </Button>
      </form>

      <div className="text-xs text-gray-500 text-center mt-2">
        Pressione Enter para enviar, Shift+Enter para nova linha
      </div>
    </motion.div>
  );
};