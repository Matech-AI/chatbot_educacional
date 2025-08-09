import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  User, 
  Bot, 
  ChevronDown, 
  ChevronUp, 
  BookOpen, 
  ExternalLink,
  HelpCircle,
  Lightbulb,
  ArrowRight,
  Target,
  Clock,
  PlayCircle,
  Video,
  Download
} from 'lucide-react';
import { Button } from '../ui/button';
import { SecureVideoPlayer } from '../video/secure-video-player';
import ReactMarkdown from 'react-markdown';
import jsPDF from 'jspdf';

interface EducationalSource {
  title: string;
  source: string;
  chunk: string;
  page?: number | null;
  response?: string;
}

interface VideoSuggestion {
  topic: string;
  video_path: string;
  video_title: string;
  start_timestamp: number;
  duration?: number;
  difficulty_level: string;
  description: string;
}

interface EducationalMessageBubbleProps {
  message: {
    id: string;
    content: string;
    role: 'user' | 'assistant' | 'system';
    timestamp: Date;
    sources?: EducationalSource[];
    follow_up_questions?: string[];
    learning_suggestions?: string[];
    related_topics?: string[];
    video_suggestions?: VideoSuggestion[];
    educational_metadata?: {
      estimated_reading_time?: number;
      complexity_score?: number;
      topics_mentioned?: string[];
    };
    isLoading?: boolean;
  };
  onFollowUpClick?: (question: string) => void;
  onTopicExplore?: (topic: string) => void;
  onSourceClick?: (source: EducationalSource) => void;
  onVideoPlay?: (video: VideoSuggestion) => void;
}

export const EducationalMessageBubble: React.FC<EducationalMessageBubbleProps> = ({
  message,
  onFollowUpClick,
  onTopicExplore,
  onSourceClick,
  onVideoPlay,
}) => {
  const [showEducationalFeatures, setShowEducationalFeatures] = useState(false);
  const [showVideos, setShowVideos] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<VideoSuggestion | null>(null);
  const [showExport, setShowExport] = useState(false);

  const handleExportTxt = () => {
    const blob = new Blob([message.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'response.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportPdf = () => {
    const doc = new jsPDF();
    doc.text(message.content, 10, 10);
    doc.save('response.pdf');
  };

  const isUser = message.role === 'user';
  const hasEducationalFeatures = message.follow_up_questions?.length || 
                                   message.learning_suggestions?.length || 
                                   message.related_topics?.length ||
                                   message.video_suggestions?.length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-blue-500' : 'bg-red-500'
          }`}>
            {isUser ? (
              <User size={16} className="text-white" />
            ) : (
              <Bot size={16} className="text-white" />
            )}
          </div>
        </div>

        {/* Message Content */}
        <div className="flex-1">
          {/* Main Message */}
          <div
            className={`px-4 py-3 rounded-lg shadow-sm ${
              isUser
                ? 'bg-blue-500 text-white'
                : 'bg-white border border-gray-200 text-gray-900'
            }`}
          >
            {message.isLoading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                <span className="text-sm">Pensando...</span>
              </div>
            ) : (
              <div>
                <div className="text-sm prose prose-sm max-w-none">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
                
                {/* Educational Metadata */}
                {!isUser && message.educational_metadata && (
                  <div className="mt-2 pt-2 border-t border-gray-100 flex items-center space-x-3 text-xs text-gray-500">
                    {message.educational_metadata.estimated_reading_time && (
                      <div className="flex items-center space-x-1">
                        <Clock size={12} />
                        <span>{Math.ceil(message.educational_metadata.estimated_reading_time)} min</span>
                      </div>
                    )}
                    {message.educational_metadata.complexity_score && (
                      <div className="flex items-center space-x-1">
                        <Target size={12} />
                        <span>
                          Nível: {
                            message.educational_metadata.complexity_score < 0.3 ? 'Básico' :
                            message.educational_metadata.complexity_score < 0.7 ? 'Intermediário' : 'Avançado'
                          }
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Export Section */}
          {!isUser && (
            <div className="mt-2">
              <button
                onClick={() => setShowExport(!showExport)}
                className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
              >
                <Download size={14} />
                <span>Exportar</span>
                {showExport ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
              <AnimatePresence>
                {showExport && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-2 space-y-2 overflow-hidden"
                  >
                    <Button onClick={handleExportTxt} size="sm" variant="outline">
                      Exportar como TXT
                    </Button>
                    <Button onClick={handleExportPdf} size="sm" variant="outline">
                      Exportar como PDF
                    </Button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* RAG Context Section */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-200">
              <button
                onClick={() => setShowSources(!showSources)}
                className="flex items-center space-x-2 text-sm font-semibold text-gray-700 mb-2"
              >
                <BookOpen size={14} />
                <span>Contexto do RAG ({message.sources.length})</span>
                {showSources ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
              {showSources && (
                <div className="space-y-2">
                  {message.sources.map((source, index) => (
                    <div
                      key={index}
                      className="bg-gray-50 rounded-lg p-3 border border-gray-200 cursor-pointer hover:bg-gray-100 transition-colors"
                      onClick={() => onSourceClick?.(source)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="text-xs text-gray-500 mt-1">
                            {source.page && `Página ${source.page} • `}
                            {source.source.split('/').pop()}
                          </div>
                          <div className="mt-2 pt-2 border-t border-gray-200">
                            <p className="text-xs text-gray-500 italic">
                              Resposta: {source.chunk}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Educational Features Section */}
          {!isUser && hasEducationalFeatures && (
            <div className="mt-3">
              <button
                onClick={() => setShowEducationalFeatures(!showEducationalFeatures)}
                className="flex items-center space-x-2 text-sm text-red-600 hover:text-red-700 transition-colors"
              >
                <Lightbulb size={14} />
                <span>Explorar mais</span>
                {showEducationalFeatures ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>

              <AnimatePresence>
                {showEducationalFeatures && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-3 space-y-3 overflow-hidden"
                  >
                    {/* Follow-up Questions */}
                    {message.follow_up_questions && message.follow_up_questions.length > 0 && (
                      <div>
                        <div className="flex items-center space-x-2 text-xs font-medium text-gray-700 mb-2">
                          <HelpCircle size={12} />
                          <span>Perguntas para aprofundar</span>
                        </div>
                        <div className="space-y-2">
                          {message.follow_up_questions.map((question, index) => (
                            <button
                              key={index}
                              onClick={() => onFollowUpClick?.(question)}
                              className="block w-full text-left text-sm text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 rounded-lg px-3 py-2 transition-colors"
                            >
                              <div className="flex items-center justify-between">
                                <span>{question}</span>
                                <ArrowRight size={14} className="flex-shrink-0 ml-2" />
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Learning Suggestions */}
                    {message.learning_suggestions && message.learning_suggestions.length > 0 && (
                      <div>
                        <div className="flex items-center space-x-2 text-xs font-medium text-gray-700 mb-2">
                          <Target size={12} />
                          <span>Sugestões de aprendizado</span>
                        </div>
                        <div className="space-y-1">
                          {message.learning_suggestions.map((suggestion, index) => (
                            <div
                              key={index}
                              className="text-sm text-gray-600 bg-yellow-50 rounded-lg px-3 py-2 border-l-3 border-yellow-400"
                            >
                              {suggestion}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Related Topics */}
                    {message.related_topics && message.related_topics.length > 0 && (
                      <div>
                        <div className="flex items-center space-x-2 text-xs font-medium text-gray-700 mb-2">
                          <BookOpen size={12} />
                          <span>Tópicos relacionados</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {message.related_topics.map((topic, index) => (
                            <button
                              key={index}
                              onClick={() => onTopicExplore?.(topic)}
                              className="text-xs bg-green-100 text-green-700 hover:bg-green-200 rounded-full px-3 py-1 transition-colors"
                            >
                              {topic}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Video Suggestions */}
                    {message.video_suggestions && message.video_suggestions.length > 0 && (
                      <div>
                        <div className="flex items-center space-x-2 text-xs font-medium text-gray-700 mb-2">
                          <Video size={12} />
                          <span>Vídeos relacionados ({message.video_suggestions.length})</span>
                        </div>
                        <div className="space-y-2">
                          {message.video_suggestions.map((video, index) => (
                            <div
                              key={index}
                              className="bg-gray-50 rounded-lg p-3 border border-gray-200 hover:bg-gray-100 transition-colors"
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="font-medium text-sm text-gray-900 mb-1">
                                    {video.video_title}
                                  </div>
                                  <div className="text-xs text-gray-500 mb-2">
                                    Tópico: {video.topic} • Nível: {video.difficulty_level}
                                    {video.duration && ` • ${Math.ceil(video.duration / 60)} min`}
                                  </div>
                                  <div className="text-sm text-gray-700 mb-2">
                                    {video.description}
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <button
                                      onClick={() => {
                                        setSelectedVideo(video);
                                        onVideoPlay?.(video);
                                      }}
                                      className="flex items-center space-x-1 text-xs bg-red-500 text-white hover:bg-red-600 rounded px-2 py-1 transition-colors"
                                    >
                                      <PlayCircle size={12} />
                                      <span>Assistir ({Math.floor(video.start_timestamp / 60)}:{(video.start_timestamp % 60).toString().padStart(2, '0')})</span>
                                    </button>
                                    <button
                                      onClick={() => onTopicExplore?.(video.topic)}
                                      className="text-xs text-blue-600 hover:text-blue-800 underline"
                                    >
                                      Explorar tópico
                                    </button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* Embedded Video Player */}
          {!isUser && selectedVideo && (
            <div className="mt-3">
              <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2 text-sm font-medium text-gray-700">
                    <Video size={14} />
                    <span>Vídeo: {selectedVideo.video_title}</span>
                  </div>
                  <button
                    onClick={() => setSelectedVideo(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <ChevronUp size={16} />
                  </button>
                </div>
                
                <SecureVideoPlayer
                  embedUrl={`/api/materials/${selectedVideo.video_path}`}
                  startTime={selectedVideo.start_timestamp}
                  metadata={{
                    title: selectedVideo.video_title,
                    duration: selectedVideo.duration,
                    topics: [selectedVideo.topic],
                    timestamps: [],
                    difficulty_level: selectedVideo.difficulty_level
                  }}
                  matchedTopic={{
                    topic: selectedVideo.topic,
                    description: selectedVideo.description,
                    confidence: 0.8
                  }}
                  onTimestampClick={(timestamp) => {
                    // Handle timestamp navigation
                    console.log('Navigate to timestamp:', timestamp);
                  }}
                  onTopicExplore={(topic) => onTopicExplore?.(topic)}
                  className="w-full"
                  showControls={true}
                  autoplay={false}
                />
              </div>
            </div>
          )}

          {/* Timestamp */}
          <div className={`text-xs text-gray-500 mt-2 ${isUser ? 'text-right' : 'text-left'}`}>
            {message.timestamp.toLocaleTimeString('pt-BR', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
        </div>
      </div>
    </motion.div>
  );
};