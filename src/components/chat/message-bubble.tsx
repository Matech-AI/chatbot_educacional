import React, { useState } from 'react';
import { Message, Source } from '../../types';
import { formatDate } from '../../lib/utils';
import { motion } from 'framer-motion';
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div 
        className={`max-w-3xl ${
          isUser 
            ? 'bg-blue-600 text-white rounded-t-lg rounded-bl-lg' 
            : 'bg-white border border-gray-200 rounded-t-lg rounded-br-lg shadow-sm'
        } px-4 py-3`}
      >
        {message.isLoading ? (
          <div className="flex justify-center py-2">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        ) : (
          <>
            <div className="text-sm mb-1 flex justify-between items-center gap-3">
              <span className="font-medium">{isUser ? 'Você' : 'Assistente'}</span>
              <span className="text-xs opacity-70">{formatDate(message.timestamp)}</span>
            </div>
            
            <div className={`prose ${isUser ? 'prose-invert' : ''} max-w-none text-sm`}>
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
            
            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 pt-2 border-t border-gray-200">
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="text-xs flex items-center gap-1 text-blue-500 hover:text-blue-700"
                >
                  {showSources ? (
                    <>
                      <ChevronUp size={14} />
                      <span>Ocultar fontes</span>
                    </>
                  ) : (
                    <>
                      <ChevronDown size={14} />
                      <span>Mostrar {message.sources.length} fontes</span>
                    </>
                  )}
                </button>
                
                {showSources && (
                  <div className="mt-2 space-y-2">
                    {message.sources.map((source, index) => (
                      <SourceItem key={index} source={source} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </motion.div>
  );
};

interface SourceItemProps {
  source: Source;
}

const SourceItem: React.FC<SourceItemProps> = ({ source }) => {
  return (
    <div className="bg-gray-50 rounded p-2 text-xs">
      <div className="flex justify-between items-center">
        <h4 className="font-medium text-gray-900">{source.title}</h4>
        {source.page && <span className="text-gray-500">Pág. {source.page}</span>}
      </div>
      
      <p className="mt-1 text-gray-600">{source.chunk}</p>
      
      <a 
        href={source.source} 
        className="mt-1 text-blue-500 hover:text-blue-700 inline-flex items-center gap-1"
        target="_blank" 
        rel="noopener noreferrer"
      >
        <ExternalLink size={12} />
        <span>Ver documento</span>
      </a>
    </div>
  );
};