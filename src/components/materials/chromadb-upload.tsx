import React, { useState, useRef } from "react";
import { Button } from "../ui/button";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  Database,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  FileText,
  Info,
  X,
} from "lucide-react";
import { formatFileSize } from "../../lib/utils";
import { ragApiRequest } from "@/lib/api";

interface ChromaDBUploadProps {
  onUploadSuccess?: () => void;
}

interface ChromaDBStatus {
  status: string;
  path: string;
  is_valid: boolean;
  reason?: string;
  collections: Array<{
    name: string;
    count: number;
  }>;
  total_documents: number;
  rag_handler_active: boolean;
}

export const ChromaDBUpload: React.FC<ChromaDBUploadProps> = ({
  onUploadSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isCheckingStatus, setIsCheckingStatus] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [status, setStatus] = useState<ChromaDBStatus | null>(null);
  const [message, setMessage] = useState<{
    type: "success" | "error" | "info";
    text: string;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Verificar status do ChromaDB
  const checkChromaDBStatus = async () => {
    setIsCheckingStatus(true);
    try {
      const response = await ragApiRequest("/chromadb/status", {
        method: "GET",
      });

      if (response.ok) {
        const statusData = await response.json();
        setStatus(statusData);

        if (statusData.is_valid) {
          setMessage({
            type: "success",
            text: `ChromaDB válido encontrado com ${statusData.total_documents} documentos`,
          });
        } else {
          setMessage({
            type: "info",
            text: statusData.reason || "ChromaDB não encontrado",
          });
        }
      }
    } catch (error) {
      setMessage({
        type: "error",
        text: "Erro ao verificar status do ChromaDB",
      });
    } finally {
      setIsCheckingStatus(false);
    }
  };

  // Upload do arquivo ChromaDB
  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setMessage(null);

    try {
      const formData = new FormData();
      formData.append("archive", file);
      formData.append("replace_existing", "true");

      const response = await fetch(
        `${import.meta.env.VITE_RAG_API_BASE_URL}/chromadb/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (response.ok) {
        const result = await response.json();
        setMessage({
          type: "success",
          text: `ChromaDB carregado com sucesso! ${result.total_documents} documentos em ${result.collections.length} coleções.`,
        });
        setFile(null);
        await checkChromaDBStatus();
        onUploadSuccess?.();
      } else {
        const error = await response.json();
        setMessage({
          type: "error",
          text: error.detail || "Erro no upload do ChromaDB",
        });
      }
    } catch (error) {
      setMessage({
        type: "error",
        text: "Erro de conexão durante o upload",
      });
    } finally {
      setIsUploading(false);
    }
  };

  // Handlers para drag & drop
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = (selectedFile: File) => {
    if (
      !selectedFile.name.toLowerCase().endsWith(".tar.gz") &&
      !selectedFile.name.toLowerCase().endsWith(".tgz")
    ) {
      setMessage({
        type: "error",
        text: "Arquivo deve ser .tar.gz contendo o diretório .chromadb",
      });
      return;
    }
    setFile(selectedFile);
    setMessage(null);
  };

  // Inicializar verificação de status
  React.useEffect(() => {
    checkChromaDBStatus();
  }, []);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Database size={20} className="text-blue-600" />
            Sincronização ChromaDB
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Upload de banco de dados ChromaDB pré-treinado
          </p>
        </div>

        <Button
          onClick={checkChromaDBStatus}
          disabled={isCheckingStatus}
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
        >
          <RefreshCw
            size={16}
            className={isCheckingStatus ? "animate-spin" : ""}
          />
          Verificar Status
        </Button>
      </div>

      {/* Status Atual */}
      {status && (
        <div
          className={`mb-6 p-4 rounded-lg border ${
            status.is_valid
              ? "bg-green-50 border-green-200"
              : "bg-yellow-50 border-yellow-200"
          }`}
        >
          <div className="flex items-start gap-3">
            {status.is_valid ? (
              <CheckCircle size={20} className="text-green-600 mt-0.5" />
            ) : (
              <Info size={20} className="text-yellow-600 mt-0.5" />
            )}
            <div className="flex-1">
              <h4 className="font-medium text-sm">
                {status.is_valid ? "ChromaDB Ativo" : "ChromaDB Não Encontrado"}
              </h4>
              {status.is_valid ? (
                <div className="mt-2 space-y-1">
                  <p className="text-sm text-gray-600">
                    📊 {status.total_documents} documentos em{" "}
                    {status.collections.length} coleções
                  </p>
                  {status.collections.map((col, idx) => (
                    <p key={idx} className="text-xs text-gray-500">
                      • {col.name}: {col.count} documentos
                    </p>
                  ))}
                  <p className="text-xs text-gray-500">
                    🤖 RAG Handler:{" "}
                    {status.rag_handler_active ? "Ativo" : "Inativo"}
                  </p>
                </div>
              ) : (
                <p className="text-sm text-gray-600 mt-1">{status.reason}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Área de Upload */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          dragActive
            ? "border-blue-400 bg-blue-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) =>
            e.target.files?.[0] && handleFileSelect(e.target.files[0])
          }
          className="hidden"
          accept=".tar.gz,.tgz"
        />

        <AnimatePresence mode="wait">
          {file ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex flex-col items-center"
            >
              <div className="mb-3 w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <FileText size={24} className="text-blue-600" />
              </div>
              <p className="font-medium text-gray-900 mb-1">{file.name}</p>
              <p className="text-sm text-gray-500 mb-4">
                {formatFileSize(file.size)}
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="flex items-center gap-2"
                >
                  {isUploading ? (
                    <RefreshCw size={16} className="animate-spin" />
                  ) : (
                    <Upload size={16} />
                  )}
                  {isUploading ? "Enviando..." : "Fazer Upload"}
                </Button>
                <Button
                  onClick={() => setFile(null)}
                  variant="outline"
                  disabled={isUploading}
                >
                  <X size={16} />
                </Button>
              </div>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="mb-3 w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto">
                <Database size={24} className="text-gray-600" />
              </div>
              <p className="text-lg font-medium text-gray-900 mb-2">
                Selecione o arquivo ChromaDB
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Arraste e solte ou clique para selecionar um arquivo .tar.gz
              </p>
              <Button variant="outline" className="flex items-center gap-2">
                <Upload size={16} />
                Selecionar Arquivo
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Instruções */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
          <Info size={16} />
          Instruções de Uso
        </h4>
        <div className="text-sm text-blue-800 space-y-1">
          <p>• O arquivo deve ser um .tar.gz contendo o diretório .chromadb</p>
          <p>• O sistema fará backup automático do ChromaDB atual</p>
          <p>• A integridade será verificada antes da substituição</p>
          <p>• O RAG handler será reinicializado automaticamente</p>
        </div>
      </div>

      {/* Mensagens */}
      <AnimatePresence>
        {message && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`mt-4 p-4 rounded-lg border ${
              message.type === "success"
                ? "bg-green-50 border-green-200 text-green-700"
                : message.type === "error"
                ? "bg-red-50 border-red-200 text-red-700"
                : "bg-blue-50 border-blue-200 text-blue-700"
            }`}
          >
            <div className="flex items-center gap-2">
              {message.type === "success" ? (
                <CheckCircle size={16} />
              ) : message.type === "error" ? (
                <AlertTriangle size={16} />
              ) : (
                <Info size={16} />
              )}
              {message.text}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
