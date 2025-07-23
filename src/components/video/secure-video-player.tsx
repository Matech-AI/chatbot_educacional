import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  SkipForward,
  SkipBack,
  Settings,
  ExternalLink,
  Clock,
  BookOpen,
  Target,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Button } from '../ui/button';

interface VideoTimestamp {
  start_time: number;
  end_time: number;
  topic: string;
  description: string;
  keywords: string[];
  confidence: number;
}

interface VideoMetadata {
  title: string;
  duration?: number;
  topics: string[];
  timestamps: VideoTimestamp[];
  summary?: string;
  difficulty_level: string;
}

interface SecureVideoPlayerProps {
  embedUrl: string;
  startTime?: number;
  metadata?: VideoMetadata;
  matchedTopic?: {
    topic: string;
    description: string;
    confidence: number;
  };
  onTimestampClick?: (timestamp: VideoTimestamp) => void;
  onTopicExplore?: (topic: string) => void;
  className?: string;
  showControls?: boolean;
  autoplay?: boolean;
}

export const SecureVideoPlayer: React.FC<SecureVideoPlayerProps> = ({
  embedUrl,
  startTime = 0,
  metadata,
  matchedTopic,
  onTimestampClick,
  onTopicExplore,
  className = '',
  showControls = true,
  autoplay = false
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [showTimestamps, setShowTimestamps] = useState(false);
  const [showMetadata, setShowMetadata] = useState(false);
  const [currentTime, setCurrentTime] = useState(startTime);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const iframeRef = useRef<HTMLIFrameElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Add security headers to iframe
    if (iframeRef.current) {
      const iframe = iframeRef.current;
      
      // Security attributes
      iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-presentation');
      iframe.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
      
      // Prevent context menu and text selection
      iframe.style.pointerEvents = 'auto';
      
      // Load event handler
      const handleLoad = () => {
        setIsLoading(false);
        
        // Try to inject custom controls disable script
        try {
          const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
          if (iframeDoc) {
            // Add custom CSS to hide download controls
            const style = iframeDoc.createElement('style');
            style.textContent = `
              .ytp-right-controls .ytp-button[data-tooltip-target-id="ytp-autonav-endscreen-upnext-button"],
              .ytp-right-controls .ytp-button[data-tooltip-target-id="ytp-fullscreen-button"],
              .ytp-chrome-bottom .ytp-chrome-controls .ytp-right-controls {
                display: none !important;
              }
              video {
                pointer-events: none;
              }
            `;
            iframeDoc.head?.appendChild(style);
          }
        } catch (e) {
          // Cross-origin restrictions - expected
          console.log('Cannot modify iframe content due to CORS policy');
        }
      };

      const handleError = () => {
        setError('Erro ao carregar vídeo. Verifique se o vídeo está acessível.');
        setIsLoading(false);
      };

      iframe.addEventListener('load', handleLoad);
      iframe.addEventListener('error', handleError);

      return () => {
        iframe.removeEventListener('load', handleLoad);
        iframe.removeEventListener('error', handleError);
      };
    }
  }, [embedUrl]);

  // Handle fullscreen
  const toggleFullscreen = () => {
    if (!containerRef.current) return;

    if (!isFullscreen) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
    setIsFullscreen(!isFullscreen);
  };

  // Format time display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Generate secured embed URL with restrictions
  const getSecureEmbedUrl = () => {
    let url = embedUrl;
    
    // Add Google Drive embed parameters for security
    if (url.includes('drive.google.com')) {
      const separator = url.includes('?') ? '&' : '?';
      url += `${separator}embedded=true&controls=1&showinfo=0&rel=0&modestbranding=1&disablekb=1`;
      
      // Add start time if specified
      if (startTime > 0) {
        const minutes = Math.floor(startTime / 60);
        const seconds = Math.floor(startTime % 60);
        url += `&start=${minutes * 60 + seconds}`;
      }
    }
    
    return url;
  };

  // Handle timestamp navigation
  const navigateToTimestamp = (timestamp: VideoTimestamp) => {
    setCurrentTime(timestamp.start_time);
    
    // Try to update iframe src with new timestamp
    if (iframeRef.current) {
      const newUrl = embedUrl.includes('drive.google.com') 
        ? getSecureEmbedUrl().replace(/&start=\d+/, `&start=${Math.floor(timestamp.start_time)}`)
        : embedUrl;
      
      iframeRef.current.src = newUrl;
    }
    
    onTimestampClick?.(timestamp);
  };

  const getDifficultyColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'beginner': return 'text-green-600 bg-green-100';
      case 'intermediate': return 'text-yellow-600 bg-yellow-100';
      case 'advanced': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getDifficultyLabel = (level: string) => {
    switch (level.toLowerCase()) {
      case 'beginner': return 'Iniciante';
      case 'intermediate': return 'Intermediário';
      case 'advanced': return 'Avançado';
      default: return 'Intermediário';
    }
  };

  if (error) {
    return (
      <div className={`bg-gray-100 rounded-lg p-8 text-center ${className}`}>
        <div className="text-red-600 mb-4">
          <ExternalLink size={48} className="mx-auto mb-2" />
          <p className="text-lg font-medium">Erro ao carregar vídeo</p>
          <p className="text-sm text-gray-600 mt-2">{error}</p>
        </div>
        <Button
          onClick={() => window.open(embedUrl, '_blank')}
          variant="outline"
          className="mt-4"
        >
          <ExternalLink size={16} className="mr-2" />
          Abrir em nova aba
        </Button>
      </div>
    );
  }

  return (
    <div ref={containerRef} className={`bg-white rounded-lg shadow-lg overflow-hidden ${className}`}>
      {/* Video Header */}
      {metadata && (
        <div className="bg-gray-50 p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-1">
                {metadata.title}
              </h3>
              {metadata.summary && (
                <p className="text-sm text-gray-600 mb-2">{metadata.summary}</p>
              )}
              <div className="flex items-center space-x-3 text-xs">
                <span className={`px-2 py-1 rounded-full font-medium ${getDifficultyColor(metadata.difficulty_level)}`}>
                  {getDifficultyLabel(metadata.difficulty_level)}
                </span>
                {metadata.duration && (
                  <span className="text-gray-500 flex items-center space-x-1">
                    <Clock size={12} />
                    <span>{formatTime(metadata.duration)}</span>
                  </span>
                )}
                <span className="text-gray-500 flex items-center space-x-1">
                  <BookOpen size={12} />
                  <span>{metadata.topics.length} tópicos</span>
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {metadata.timestamps.length > 0 && (
                <Button
                  onClick={() => setShowTimestamps(!showTimestamps)}
                  variant="outline"
                  size="sm"
                  className="text-xs"
                >
                  <Target size={14} className="mr-1" />
                  Capítulos
                </Button>
              )}
              
              <Button
                onClick={() => setShowMetadata(!showMetadata)}
                variant="outline"
                size="sm"
                className="text-xs"
              >
                <Settings size={14} className="mr-1" />
                Info
              </Button>
            </div>
          </div>

          {/* Matched Topic Highlight */}
          {matchedTopic && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-blue-900">
                    🎯 Tópico encontrado: {matchedTopic.topic}
                  </div>
                  <div className="text-xs text-blue-700 mt-1">
                    {matchedTopic.description}
                  </div>
                </div>
                <div className="text-xs text-blue-600">
                  {Math.round(matchedTopic.confidence * 100)}% relevante
                </div>
              </div>
            </motion.div>
          )}
        </div>
      )}

      {/* Video Player Container */}
      <div className="relative bg-black">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 text-white z-10">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
              <p className="text-sm">Carregando vídeo...</p>
            </div>
          </div>
        )}

        <iframe
          ref={iframeRef}
          src={getSecureEmbedUrl()}
          className="w-full aspect-video"
          frameBorder="0"
          allow="autoplay; encrypted-media"
          allowFullScreen
          title={metadata?.title || 'Vídeo educacional'}
          style={{
            minHeight: '315px',
            background: '#000'
          }}
        />

        {/* Custom Controls Overlay */}
        {showControls && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4">
            <div className="flex items-center justify-between text-white">
              <div className="flex items-center space-x-3">
                <span className="text-sm">
                  {formatTime(currentTime)}
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button
                  onClick={toggleFullscreen}
                  variant="ghost"
                  size="sm"
                  className="text-white hover:bg-white/20"
                >
                  {isFullscreen ? <Minimize size={16} /> : <Maximize size={16} />}
                </Button>
                
                <Button
                  onClick={() => window.open(embedUrl, '_blank')}
                  variant="ghost"
                  size="sm"
                  className="text-white hover:bg-white/20"
                  title="Abrir em nova aba"
                >
                  <ExternalLink size={16} />
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Timestamps Panel */}
      <AnimatePresence>
        {showTimestamps && metadata?.timestamps && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-gray-200 bg-gray-50 overflow-hidden"
          >
            <div className="p-4">
              <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                <Target size={16} className="mr-2 text-blue-600" />
                Capítulos do Vídeo
              </h4>
              
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {metadata.timestamps.map((timestamp, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200 hover:border-blue-300 cursor-pointer transition-colors"
                    onClick={() => navigateToTimestamp(timestamp)}
                  >
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full font-medium">
                          {formatTime(timestamp.start_time)}
                        </span>
                        <span className="text-xs text-gray-500">
                          Confiança: {Math.round(timestamp.confidence * 100)}%
                        </span>
                      </div>
                      <h5 className="text-sm font-medium text-gray-900">
                        {timestamp.topic}
                      </h5>
                      <p className="text-xs text-gray-600 mt-1">
                        {timestamp.description}
                      </p>
                      {timestamp.keywords.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {timestamp.keywords.slice(0, 3).map((keyword, kidx) => (
                            <span
                              key={kidx}
                              className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2 ml-3">
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          onTopicExplore?.(timestamp.topic);
                        }}
                        variant="outline"
                        size="sm"
                        className="text-xs"
                      >
                        Explorar
                      </Button>
                      <ChevronDown size={16} className="text-gray-400" />
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Metadata Panel */}
      <AnimatePresence>
        {showMetadata && metadata && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-gray-200 bg-gray-50 overflow-hidden"
          >
            <div className="p-4">
              <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                <BookOpen size={16} className="mr-2 text-green-600" />
                Informações do Vídeo
              </h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 className="text-xs font-medium text-gray-700 mb-2">Tópicos Abordados</h5>
                  <div className="flex flex-wrap gap-1">
                    {metadata.topics.map((topic, index) => (
                      <button
                        key={index}
                        onClick={() => onTopicExplore?.(topic)}
                        className="text-xs bg-green-100 text-green-700 hover:bg-green-200 px-2 py-1 rounded transition-colors"
                      >
                        {topic}
                      </button>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h5 className="text-xs font-medium text-gray-700 mb-2">Detalhes Técnicos</h5>
                  <div className="space-y-1 text-xs text-gray-600">
                    <div>Nível: {getDifficultyLabel(metadata.difficulty_level)}</div>
                    {metadata.duration && (
                      <div>Duração: {formatTime(metadata.duration)}</div>
                    )}
                    <div>Capítulos: {metadata.timestamps.length}</div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};