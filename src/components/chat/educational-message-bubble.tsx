import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
  Download,
} from "lucide-react";
import { Button } from "../ui/button";
import { SecureVideoPlayer } from "../video/secure-video-player";
import ReactMarkdown from "react-markdown";
import jsPDF from "jspdf";
import remarkGfm from "remark-gfm";

interface EducationalSource {
  title: string;
  source: string;
  chunk: string;
  page?: number | null;
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
    role: "user" | "assistant" | "system";
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

export const EducationalMessageBubble: React.FC<
  EducationalMessageBubbleProps
> = ({
  message,
  onFollowUpClick,
  onTopicExplore,
  onSourceClick,
  onVideoPlay,
}) => {
  const [showEducationalFeatures, setShowEducationalFeatures] = useState(false);
  const [showVideos, setShowVideos] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<VideoSuggestion | null>(
    null
  );
  const [showExport, setShowExport] = useState(false);

  const formatContentForExport = (content: string) => {
    // Converter markdown para texto formatado
    let formattedContent = content;

    // Detectar e formatar seções específicas do chatbot
    formattedContent = formattedContent.replace(
      /^\*\*1\.\s*Resposta Principal\*\*/gim,
      "1. Resposta Principal"
    );
    formattedContent = formattedContent.replace(
      /^\*\*2\.\s*Fontes e Evidências\*\*/gim,
      "2. Fontes e Evidencias"
    );
    formattedContent = formattedContent.replace(
      /^\*\*3\.\s*Informação complementar\*\*/gim,
      "3. Informacao complementar"
    );
    formattedContent = formattedContent.replace(
      /^\*\*4\.\s*Aplicação Prática\*\*/gim,
      "4. Aplicacao Pratica"
    );
    formattedContent = formattedContent.replace(
      /^\*\*5\.\s*Perguntas para Reflexão\*\*/gim,
      "5. Perguntas para Reflexao"
    );
    formattedContent = formattedContent.replace(
      /^\*\*6\.\s*Próximos Passos\*\*/gim,
      "6. Proximos Passos"
    );

    // Converter tabelas primeiro (antes de outras conversões)
    formattedContent = formattedContent.replace(
      /\|(.+)\|/g,
      (match, content) => {
        const cells = content
          .split("|")
          .map((cell: string) => cell.trim())
          .filter((cell: string) => cell);
        return cells.join(" | ");
      }
    );

    // Converter cabeçalhos
    formattedContent = formattedContent.replace(/^### (.*$)/gim, "=== $1 ===");
    formattedContent = formattedContent.replace(/^## (.*$)/gim, "== $1 ==");
    formattedContent = formattedContent.replace(/^# (.*$)/gim, "= $1 =");

    // Converter listas
    formattedContent = formattedContent.replace(/^\* (.*$)/gim, "• $1");
    formattedContent = formattedContent.replace(/^- (.*$)/gim, "• $1");
    formattedContent = formattedContent.replace(/^\d+\. (.*$)/gim, "$&");

    // Converter código inline
    formattedContent = formattedContent.replace(/`([^`]+)`/g, "[$1]");

    // Converter blocos de código
    formattedContent = formattedContent.replace(/```[\s\S]*?```/g, (match) => {
      const code = match.replace(/```[\w]*\n?/, "").replace(/```$/, "");
      return `\n--- CÓDIGO ---\n${code}\n--- FIM CÓDIGO ---\n`;
    });

    // Converter negrito e itálico (remover completamente)
    formattedContent = formattedContent.replace(/\*\*([^*]+)\*\*/g, "$1");
    formattedContent = formattedContent.replace(/\*([^*]+)\*/g, "$1");

    // Converter links
    formattedContent = formattedContent.replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      "$1 ($2)"
    );

    // Limpar caracteres especiais e normalizar
    formattedContent = formattedContent.replace(/[^\x00-\x7F]/g, (char) => {
      const map: { [key: string]: string } = {
        ã: "a",
        á: "a",
        à: "a",
        â: "a",
        ä: "a",
        é: "e",
        è: "e",
        ê: "e",
        ë: "e",
        í: "i",
        ì: "i",
        î: "i",
        ï: "i",
        ó: "o",
        ò: "o",
        ô: "o",
        ö: "o",
        ú: "u",
        ù: "u",
        û: "u",
        ü: "u",
        ç: "c",
        ñ: "n",
        Ã: "A",
        Á: "A",
        À: "A",
        Â: "A",
        Ä: "A",
        É: "E",
        È: "E",
        Ê: "E",
        Ë: "E",
        Í: "I",
        Ì: "I",
        Î: "I",
        Ï: "I",
        Ó: "O",
        Ò: "O",
        Ô: "O",
        Ö: "O",
        Ú: "U",
        Ù: "U",
        Û: "U",
        Ü: "U",
        Ç: "C",
        Ñ: "N",
      };
      return map[char] || char;
    });

    // Adicionar quebras de linha adequadas
    formattedContent = formattedContent.replace(/\n\n/g, "\n\n");

    return formattedContent;
  };

  const handleExportTxt = () => {
    const formattedContent = formatContentForExport(message.content);
    const timestamp = new Date().toLocaleString("pt-BR");
    const header = `=== RESPOSTA DO CHATBOT ===\nData: ${timestamp}\n\n`;
    const fullContent = header + formattedContent;

    const blob = new Blob([fullContent], { type: "text/plain; charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `resposta_chatbot_${
      new Date().toISOString().split("T")[0]
    }.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportPdf = () => {
    const doc = new jsPDF();
    const timestamp = new Date().toLocaleString("pt-BR");

    // Configurar fonte e tamanho
    doc.setFont("helvetica");
    doc.setFontSize(12);

    // Adicionar cabeçalho principal
    doc.setFontSize(18);
    doc.setFont("helvetica", "bold");
    doc.text("ASSISTENTE EDUCACIONAL", 20, 25);

    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.text(`Data: ${timestamp}`, 20, 35);

    // Adicionar linha separadora
    doc.line(20, 40, 190, 40);

    // Processar conteúdo com formatação avançada
    const formattedContent = formatContentForExport(message.content);

    // Dividir em seções para melhor formatação
    const sections = formattedContent.split("\n\n");
    let currentY = 50;
    const pageHeight = 270;
    const margin = 20;
    const lineHeight = 5.5;

    sections.forEach((section, index) => {
      // Verificar se precisa de nova página
      if (currentY > pageHeight) {
        doc.addPage();
        currentY = 20;
      }

      // Processar seção
      if (section.trim()) {
        // Detectar tipo de conteúdo
        if (section.startsWith("1. Resposta Principal")) {
          // Seção principal
          doc.setFontSize(14);
          doc.setFont("helvetica", "bold");
          doc.text("1. RESPOSTA PRINCIPAL", margin, currentY);
          currentY += lineHeight * 1.5;

          // Texto da resposta
          doc.setFontSize(11);
          doc.setFont("helvetica", "normal");
          const lines = doc.splitTextToSize(
            section.replace("1. Resposta Principal", "").trim(),
            170
          );
          doc.text(lines, margin, currentY);
          currentY += lineHeight * lines.length + lineHeight;
        } else if (section.startsWith("2. Fontes e Evidencias")) {
          // Seção de fontes
          doc.setFontSize(14);
          doc.setFont("helvetica", "bold");
          doc.text("2. FONTES E EVIDENCIAS", margin, currentY);
          currentY += lineHeight * 1.5;

          doc.setFontSize(11);
          doc.setFont("helvetica", "normal");
          const lines = doc.splitTextToSize(
            section.replace("2. Fontes e Evidencias", "").trim(),
            170
          );
          doc.text(lines, margin, currentY);
          currentY += lineHeight * lines.length + lineHeight;
        } else if (section.startsWith("3. Informacao complementar")) {
          // Seção complementar
          doc.setFontSize(14);
          doc.setFont("helvetica", "bold");
          doc.text("3. INFORMACAO COMPLEMENTAR", margin, currentY);
          currentY += lineHeight * 1.5;

          // Processar subseções
          const subSections = section.split("\n").filter((line) => line.trim());
          subSections.forEach((subSection) => {
            if (subSection.includes("Programa de forca")) {
              // Título do programa
              doc.setFontSize(12);
              doc.setFont("helvetica", "bold");
              const lines = doc.splitTextToSize(subSection, 170);
              doc.text(lines, margin, currentY);
              currentY += lineHeight * lines.length + lineHeight;
            } else if (subSection.includes("Objetivo:")) {
              // Objetivo
              doc.setFontSize(11);
              doc.setFont("helvetica", "bold");
              doc.text("Objetivo:", margin, currentY);
              currentY += lineHeight;

              doc.setFont("helvetica", "normal");
              const lines = doc.splitTextToSize(
                subSection.replace("Objetivo:", "").trim(),
                170
              );
              doc.text(lines, margin, currentY);
              currentY += lineHeight * lines.length + lineHeight;
            } else if (
              subSection.includes("Dia 1") ||
              subSection.includes("Dia 2") ||
              subSection.includes("Dia 3")
            ) {
              // Divisão dos dias
              doc.setFontSize(11);
              doc.setFont("helvetica", "bold");
              const lines = doc.splitTextToSize(subSection, 170);
              doc.text(lines, margin, currentY);
              currentY += lineHeight * lines.length + lineHeight;
            } else if (subSection.includes("|")) {
              // Tabela
              doc.setFontSize(10);
              doc.setFont("helvetica", "normal");
              const lines = doc.splitTextToSize(subSection, 170);
              doc.text(lines, margin, currentY);
              currentY += lineHeight * lines.length;
            } else if (subSection.includes("Progressao semanal")) {
              // Progressão
              doc.setFontSize(11);
              doc.setFont("helvetica", "bold");
              doc.text("PROGRESSAO SEMANAL (EXEMPLO):", margin, currentY);
              currentY += lineHeight * 1.2;
            } else if (subSection.includes("Dicas de execucao")) {
              // Dicas
              doc.setFontSize(11);
              doc.setFont("helvetica", "bold");
              doc.text("DICAS DE EXECUCAO:", margin, currentY);
              currentY += lineHeight * 1.2;
            } else if (subSection.includes("•")) {
              // Lista com bullets
              doc.setFontSize(10);
              doc.setFont("helvetica", "normal");
              const lines = doc.splitTextToSize(subSection, 170);
              doc.text(lines, margin, currentY);
              currentY += lineHeight * lines.length;
            } else if (subSection.trim()) {
              // Texto normal
              doc.setFontSize(10);
              doc.setFont("helvetica", "normal");
              const lines = doc.splitTextToSize(subSection, 170);
              doc.text(lines, margin, currentY);
              currentY += lineHeight * lines.length;
            }
          });
          currentY += lineHeight;
        } else if (section.startsWith("4. Perguntas para Reflexao")) {
          // Perguntas
          doc.setFontSize(14);
          doc.setFont("helvetica", "bold");
          doc.text("4. PERGUNTAS PARA REFLEXAO", margin, currentY);
          currentY += lineHeight * 1.5;

          doc.setFontSize(11);
          doc.setFont("helvetica", "normal");
          const lines = doc.splitTextToSize(
            section.replace("4. Perguntas para Reflexao", "").trim(),
            170
          );
          doc.text(lines, margin, currentY);
          currentY += lineHeight * lines.length + lineHeight;
        } else if (section.startsWith("5. Proximos Passos")) {
          // Próximos passos
          doc.setFontSize(14);
          doc.setFont("helvetica", "bold");
          doc.text("5. PROXIMOS PASSOS", margin, currentY);
          currentY += lineHeight * 1.5;

          doc.setFontSize(11);
          doc.setFont("helvetica", "normal");
          const lines = doc.splitTextToSize(
            section.replace("5. Proximos Passos", "").trim(),
            170
          );
          doc.text(lines, margin, currentY);
          currentY += lineHeight * lines.length + lineHeight;
        } else if (section.includes("Resumo")) {
          // Resumo
          doc.setFontSize(12);
          doc.setFont("helvetica", "bold");
          doc.text("RESUMO", margin, currentY);
          currentY += lineHeight * 1.2;

          doc.setFontSize(10);
          doc.setFont("helvetica", "normal");
          const lines = doc.splitTextToSize(
            section.replace("Resumo", "").trim(),
            170
          );
          doc.text(lines, margin, currentY);
          currentY += lineHeight * lines.length + lineHeight;
        } else {
          // Texto normal
          doc.setFontSize(10);
          doc.setFont("helvetica", "normal");
          const lines = doc.splitTextToSize(section, 170);
          doc.text(lines, margin, currentY);
          currentY += lineHeight * lines.length;
        }

        currentY += lineHeight * 0.3; // Espaço entre seções
      }
    });

    // Adicionar rodapé
    const pageCount = (doc as any).getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setFont("helvetica", "normal");
      doc.text(`Página ${i} de ${pageCount}`, 20, 285);
      doc.text("DNA da Força AI - Chatbot Educacional", 120, 285);
    }

    doc.save(`resposta_chatbot_${new Date().toISOString().split("T")[0]}.pdf`);
  };

  const isUser = message.role === "user";
  const hasEducationalFeatures =
    message.follow_up_questions?.length ||
    message.learning_suggestions?.length ||
    message.related_topics?.length ||
    message.video_suggestions?.length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex mb-4 ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`flex max-w-[80%] ${
          isUser ? "flex-row-reverse" : "flex-row"
        }`}
      >
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? "ml-3" : "mr-3"}`}>
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center ${
              isUser ? "bg-blue-500" : "bg-red-500"
            }`}
          >
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
                ? "bg-blue-500 text-white"
                : "bg-white border border-gray-200 text-gray-900"
            }`}
          >
            {message.isLoading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                <span className="text-sm">Pensando...</span>
              </div>
            ) : (
              <div>
                <div
                  className={`prose ${
                    isUser ? "prose-invert" : ""
                  } max-w-none text-sm prose-table:border prose-table:border-gray-300 prose-th:bg-gray-50 prose-th:border prose-th:border-gray-300 prose-th:px-3 prose-th:py-2 prose-th:text-left prose-td:border prose-td:border-gray-300 prose-td:px-3 prose-td:py-2`}
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>

                {/* Educational Metadata */}
                {!isUser && message.educational_metadata && (
                  <div className="mt-2 pt-2 border-t border-gray-100 flex items-center space-x-3 text-xs text-gray-500">
                    {message.educational_metadata.estimated_reading_time && (
                      <div className="flex items-center space-x-1">
                        <Clock size={12} />
                        <span>
                          {Math.ceil(
                            message.educational_metadata.estimated_reading_time
                          )}{" "}
                          min
                        </span>
                      </div>
                    )}
                    {message.educational_metadata.complexity_score && (
                      <div className="flex items-center space-x-1">
                        <Target size={12} />
                        <span>
                          Nível:{" "}
                          {message.educational_metadata.complexity_score < 0.3
                            ? "Básico"
                            : message.educational_metadata.complexity_score <
                              0.7
                            ? "Intermediário"
                            : "Avançado"}
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
                {showExport ? (
                  <ChevronUp size={14} />
                ) : (
                  <ChevronDown size={14} />
                )}
              </button>
              <AnimatePresence>
                {showExport && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-2 space-y-2 overflow-hidden"
                  >
                    <Button
                      onClick={handleExportTxt}
                      size="sm"
                      variant="outline"
                    >
                      Exportar como TXT
                    </Button>
                    <Button
                      onClick={handleExportPdf}
                      size="sm"
                      variant="outline"
                    >
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
              <div className="flex items-center space-x-2 text-sm font-semibold text-gray-700 mb-2">
                <BookOpen size={14} />
                <span>Contexto do RAG ({message.sources.length})</span>
              </div>
              <div className="space-y-2">
                {message.sources.map((source, index) => (
                  <div
                    key={index}
                    className="bg-gray-50 rounded-lg p-3 border border-gray-200 cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => onSourceClick?.(source)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-sm text-gray-900">
                          {source.title}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {source.page && `Página ${source.page} • `}
                          {source.source.split("/").pop()}
                        </div>
                        <p className="text-sm text-gray-700 mt-2 whitespace-pre-wrap">
                          {source.chunk}
                        </p>
                      </div>
                      <ExternalLink
                        size={14}
                        className="text-gray-400 flex-shrink-0 ml-2"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Educational Features Section */}
          {!isUser && hasEducationalFeatures && (
            <div className="mt-3">
              <button
                onClick={() =>
                  setShowEducationalFeatures(!showEducationalFeatures)
                }
                className="flex items-center space-x-2 text-sm text-red-600 hover:text-red-700 transition-colors"
              >
                <Lightbulb size={14} />
                <span>Explorar mais</span>
                {showEducationalFeatures ? (
                  <ChevronUp size={14} />
                ) : (
                  <ChevronDown size={14} />
                )}
              </button>

              <AnimatePresence>
                {showEducationalFeatures && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-3 space-y-3 overflow-hidden"
                  >
                    {/* Follow-up Questions */}
                    {message.follow_up_questions &&
                      message.follow_up_questions.length > 0 && (
                        <div>
                          <div className="flex items-center space-x-2 text-xs font-medium text-gray-700 mb-2">
                            <HelpCircle size={12} />
                            <span>Perguntas para aprofundar</span>
                          </div>
                          <div className="space-y-2">
                            {message.follow_up_questions.map(
                              (question, index) => (
                                <button
                                  key={index}
                                  onClick={() => onFollowUpClick?.(question)}
                                  className="block w-full text-left text-sm text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 rounded-lg px-3 py-2 transition-colors"
                                >
                                  <div className="flex items-center justify-between">
                                    <span>{question}</span>
                                    <ArrowRight
                                      size={14}
                                      className="flex-shrink-0 ml-2"
                                    />
                                  </div>
                                </button>
                              )
                            )}
                          </div>
                        </div>
                      )}

                    {/* Learning Suggestions */}
                    {message.learning_suggestions &&
                      message.learning_suggestions.length > 0 && (
                        <div>
                          <div className="flex items-center space-x-2 text-xs font-medium text-gray-700 mb-2">
                            <Target size={12} />
                            <span>Sugestões de aprendizado</span>
                          </div>
                          <div className="space-y-1">
                            {message.learning_suggestions.map(
                              (suggestion, index) => (
                                <div
                                  key={index}
                                  className="text-sm text-gray-600 bg-yellow-50 rounded-lg px-3 py-2 border-l-3 border-yellow-400"
                                >
                                  {suggestion}
                                </div>
                              )
                            )}
                          </div>
                        </div>
                      )}

                    {/* Related Topics */}
                    {message.related_topics &&
                      message.related_topics.length > 0 && (
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
                    {message.video_suggestions &&
                      message.video_suggestions.length > 0 && (
                        <div>
                          <div className="flex items-center space-x-2 text-xs font-medium text-gray-700 mb-2">
                            <Video size={12} />
                            <span>
                              Vídeos relacionados (
                              {message.video_suggestions.length})
                            </span>
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
                                      Tópico: {video.topic} • Nível:{" "}
                                      {video.difficulty_level}
                                      {video.duration &&
                                        ` • ${Math.ceil(
                                          video.duration / 60
                                        )} min`}
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
                                        <span>
                                          Assistir (
                                          {Math.floor(
                                            video.start_timestamp / 60
                                          )}
                                          :
                                          {(video.start_timestamp % 60)
                                            .toString()
                                            .padStart(2, "0")}
                                          )
                                        </span>
                                      </button>
                                      <button
                                        onClick={() =>
                                          onTopicExplore?.(video.topic)
                                        }
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
                    difficulty_level: selectedVideo.difficulty_level,
                  }}
                  matchedTopic={{
                    topic: selectedVideo.topic,
                    description: selectedVideo.description,
                    confidence: 0.8,
                  }}
                  onTimestampClick={(timestamp) => {
                    // Handle timestamp navigation
                    console.log("Navigate to timestamp:", timestamp);
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
          <div
            className={`text-xs text-gray-500 mt-2 ${
              isUser ? "text-right" : "text-left"
            }`}
          >
            {message.timestamp.toLocaleTimeString("pt-BR", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>
        </div>
      </div>
    </motion.div>
  );
};
