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
  Download,
} from "lucide-react";
import { formatFileSize } from "../../lib/utils";
import { ragApiRequest, RAG_API_BASE } from "@/lib/api";

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
  const [isDownloading, setIsDownloading] = useState(false);
  const [isCompressing, setIsCompressing] = useState(false);
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
      // Escolher endpoint baseado no tipo de arquivo
      const isZipFile = file.name.toLowerCase().endsWith(".zip");
      const endpoint = isZipFile
        ? "/chromadb/upload-folder"
        : "/chromadb/upload";

      const formData = new FormData();
      const fieldName = isZipFile ? "folder" : "archive";
      formData.append(fieldName, file);
      formData.append("replace_existing", "true");

      const response = await fetch(
        `${RAG_API_BASE}${endpoint}`,
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

  // Download do ChromaDB
  const handleDownloadChromaDB = async () => {
    setIsDownloading(true);
    setMessage(null);

    try {
      const response = await fetch(
        `${RAG_API_BASE}/chromadb/download`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (response.ok) {
        try {
          // Criar blob e fazer download
          const blob = await response.blob();

          // Verificar se o blob é válido
          if (blob.size === 0) {
            throw new Error("Arquivo vazio recebido");
          }

          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `chromadb_complete_${Date.now()}.tar.gz`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);

          setMessage({
            type: "success",
            text: "Download do ChromaDB iniciado com sucesso!",
          });
        } catch (blobError) {
          console.error("Erro ao processar blob:", blobError);
          setMessage({
            type: "error",
            text: "Erro ao processar arquivo de download",
          });
        }
      } else {
        const error = await response.json();
        setMessage({
          type: "error",
          text: error.detail || "Erro ao fazer download do ChromaDB",
        });
      }
    } catch (error) {
      setMessage({
        type: "error",
        text: "Erro de conexão durante o download",
      });
    } finally {
      setIsDownloading(false);
    }
  };

  // Compactar pasta .chromadb em .tar.gz
  const handleCompressChromaDB = async () => {
    setIsCompressing(true);
    setMessage(null);

    try {
      console.log("🚀 Iniciando compressão do ChromaDB...");

      console.log(`🔗 URL da API RAG: ${RAG_API_BASE}`);
      console.log(`📡 Endpoint: ${RAG_API_BASE}/chromadb/compress`);

      const response = await fetch(`${RAG_API_BASE}/chromadb/compress`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      });

      console.log(
        `📊 Status da resposta: ${response.status} ${response.statusText}`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Erro ${response.status}: ${response.statusText}`
        );
      }

      // Agora o backend retorna informações do arquivo criado
      const data = await response.json();
      console.log("📊 Resposta do servidor:", data);

      if (data.status === "success") {
        setMessage({
          type: "success",
          text: `✅ ChromaDB compactado com sucesso! Arquivo: ${data.file_name} (${data.file_size_mb} MB) - Salvo em: ${data.file_path}`,
        });

        // Mostrar informações detalhadas no console
        console.log("🎉 Compressão concluída!");
        console.log(`📁 Arquivo: ${data.file_name}`);
        console.log(`📏 Tamanho: ${data.file_size_mb} MB`);
        console.log(`📍 Localização: ${data.file_path}`);
        console.log(`🕒 Criado em: ${data.created_at}`);
      } else {
        throw new Error(data.message || "Erro desconhecido na compressão");
      }
    } catch (error) {
      console.error("💥 Erro durante compressão:", error);

      let errorMessage = "Erro de conexão durante a compactação";

      if (error instanceof TypeError && error.message.includes("fetch")) {
        errorMessage = "Erro de rede - verifique a conexão com o servidor RAG";
      } else if (error instanceof Error && error.name === "AbortError") {
        errorMessage = "Timeout - a operação demorou muito tempo";
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      setMessage({
        type: "error",
        text: errorMessage,
      });
    } finally {
      setIsCompressing(false);
    }
  };

  // 🆕 NOVO: Compactar pasta .chromadb local em .tar.gz
  const handleCompressLocalChromaDB = async () => {
    setIsCompressing(true);
    setMessage(null);

    try {
      // Em produção, não podemos acessar caminhos locais do usuário
      // Mostrar instruções para compactação manual
      setMessage({
        type: "info",
        text: `📋 Para compactar sua pasta .chromadb local:

1. **Windows**: Use 7-Zip ou WinRAR para criar um arquivo .tar.gz
2. **Linux/Mac**: Use o comando: tar -czf chromadb.tar.gz .chromadb/
3. **Faça upload** do arquivo .tar.gz usando o botão "Upload ChromaDB" acima

⚠️ O servidor não pode acessar arquivos do seu PC diretamente.`,
      });
    } catch (error) {
      setMessage({
        type: "error",
        text: "Erro ao processar solicitação",
      });
    } finally {
      setIsCompressing(false);
    }
  };

  // 🆕 NOVO: Compactar pasta .chromadb local e fazer upload automático para o servidor
  const handleCompressAndUploadLocalChromaDB = async () => {
    setIsCompressing(true);
    setMessage(null);

    try {
      // Em produção, não podemos acessar caminhos locais do usuário
      // Mostrar instruções para compactação manual
      setMessage({
        type: "info",
        text: `📋 Para sincronizar sua pasta .chromadb local:

1. **Compacte manualmente** sua pasta .chromadb:
   • Windows: Use 7-Zip ou WinRAR → .tar.gz
   • Linux/Mac: tar -czf chromadb.tar.gz .chromadb/

2. **Faça upload** do arquivo .tar.gz usando o botão "Upload ChromaDB" acima

3. **O sistema** fará o resto automaticamente!

⚠️ O servidor não pode acessar arquivos do seu PC diretamente.`,
      });
    } catch (error) {
      setMessage({
        type: "error",
        text: "Erro ao processar solicitação",
      });
    } finally {
      setIsCompressing(false);
    }
  };

  // Listar backups do ChromaDB
  const handleListBackups = async () => {
    try {
      console.log("📋 Listando backups do ChromaDB...");

      const response = await fetch(`${RAG_API_BASE}/chromadb/backups`);
      const data = await response.json();

      console.log("📊 Lista de backups:", data);

      if (data.status === "success") {
        if (data.total_backups > 0) {
          const backupInfo = data.backups
            .map(
              (backup: any) =>
                `📦 ${backup.filename} (${backup.size_mb} MB) - ${backup.created_at}`
            )
            .join("\n");

          setMessage({
            type: "success",
            text: `✅ ${data.total_backups} backup(s) encontrado(s):\n${backupInfo}`,
          });
        } else {
          setMessage({
            type: "info",
            text: "ℹ️ Nenhum backup encontrado",
          });
        }
      } else {
        throw new Error(data.detail || "Erro ao listar backups");
      }
    } catch (error) {
      console.error("💥 Erro ao listar backups:", error);
      setMessage({
        type: "error",
        text: `Erro ao listar backups: ${
          error instanceof Error ? error.message : "Erro desconhecido"
        }`,
      });
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
      !selectedFile.name.toLowerCase().endsWith(".tgz") &&
      !selectedFile.name.toLowerCase().endsWith(".zip")
    ) {
      setMessage({
        type: "error",
        text: "Arquivo deve ser .tar.gz ou .zip contendo o diretório .chromadb",
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

        <div className="flex flex-wrap gap-2 mb-4">
          <Button
            onClick={checkChromaDBStatus}
            disabled={isCheckingStatus}
            variant="outline"
            size="sm"
            className="flex items-center gap-2 flex-shrink-0"
          >
            <RefreshCw
              size={16}
              className={isCheckingStatus ? "animate-spin" : ""}
            />
            Verificar Status
          </Button>

          {/* Botões que aparecem sempre, independente do status */}
          <Button
            onClick={handleCompressChromaDB}
            disabled={isCompressing || !status?.is_valid}
            variant="outline"
            size="sm"
            className="flex items-center gap-2 border-blue-300 text-blue-700 hover:bg-blue-50 flex-shrink-0"
            title={
              !status?.is_valid
                ? "ChromaDB não está ativo"
                : "Compactar pasta .chromadb"
            }
          >
            <RefreshCw
              size={16}
              className={isCompressing ? "animate-spin" : ""}
            />
            {isCompressing ? "Compactando..." : "Compactar .chromadb"}
          </Button>

          <Button
            onClick={handleDownloadChromaDB}
            disabled={isDownloading || !status?.is_valid}
            variant="default"
            size="sm"
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 flex-shrink-0"
            title={
              !status?.is_valid
                ? "ChromaDB não está ativo"
                : "Download do ChromaDB completo"
            }
          >
            <Download
              size={16}
              className={isDownloading ? "animate-spin" : ""}
            />
            {isDownloading ? "Gerando..." : "Download ChromaDB"}
          </Button>

          {/* Botões de instruções - sempre visíveis */}
          <Button
            onClick={handleCompressLocalChromaDB}
            disabled={isCompressing}
            variant="outline"
            size="sm"
            className="flex items-center gap-2 border-purple-300 text-purple-700 hover:bg-purple-50 flex-shrink-0"
            title="Compactar pasta .chromadb local em .tar.gz"
          >
            <RefreshCw
              size={16}
              className={isCompressing ? "animate-spin" : ""}
            />
            {isCompressing ? "Processando..." : "📋 Instruções Local"}
          </Button>

          <Button
            onClick={handleCompressAndUploadLocalChromaDB}
            disabled={isCompressing}
            variant="default"
            size="sm"
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white flex-shrink-0"
            title="Compactar pasta .chromadb local e fazer upload automático para o servidor"
          >
            <Upload size={16} className={isCompressing ? "animate-spin" : ""} />
            {isCompressing ? "Processando..." : "📋 Instruções + Upload"}
          </Button>

          {/* Botão de listar backups - sempre visível */}
          <Button
            onClick={handleListBackups}
            disabled={isCompressing}
            variant="outline"
            size="sm"
            className="flex items-center gap-2 border-teal-300 text-teal-700 hover:bg-teal-50 flex-shrink-0"
            title="Listar backups do ChromaDB"
          >
            📋
            {isCompressing ? "Processando..." : "Listar Backups"}
          </Button>
        </div>
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
          accept=".tar.gz,.tgz,.zip"
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
                Arraste e solte ou clique para selecionar um arquivo .tar.gz ou
                .zip
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
          <p>
            • <strong>Upload:</strong> Aceita arquivos .tar.gz ou .zip contendo
            o diretório .chromadb
          </p>
          <p>
            • <strong>Compactar:</strong> Converte pasta .chromadb ativa em
            arquivo .tar.gz para download
          </p>
          <p>
            • <strong>📋 Instruções Local:</strong> 🆕 Mostra instruções para
            compactar pasta .chromadb local em .tar.gz
          </p>
          <p>
            • <strong>📋 Instruções + Upload:</strong> 🆕 Mostra instruções para
            sincronizar pasta .chromadb local com o servidor
          </p>
          <p>
            • <strong>Download:</strong> Baixa o ChromaDB completo em formato
            .tar.gz
          </p>
          <p>• O sistema fará backup automático do ChromaDB atual</p>
          <p>• A integridade será verificada antes da substituição</p>
          <p>• O RAG handler será reinicializado automaticamente</p>
        </div>
      </div>

      {/* 🆕 NOVO: Informações sobre Compactação Local */}
      <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
        <h4 className="font-medium text-purple-900 mb-2 flex items-center gap-2">
          <Info size={16} />
          🆕 Instruções para Compactação Local - .chromadb → .tar.gz
        </h4>
        <div className="text-sm text-purple-800 space-y-1">
          <p>
            • <strong>Funcionalidade:</strong> Mostra instruções para converter
            pasta .chromadb local em arquivo .tar.gz
          </p>
          <p>
            • <strong>Uso:</strong> Ideal para atualizar o ChromaDB do servidor
            com dados locais
          </p>
          <p>
            • <strong>Processo:</strong>
            1. Clique em "📋 Instruções Local" ou "📋 Instruções + Upload" 2.
            Siga as instruções exibidas para compactação manual 3. Faça upload
            do arquivo .tar.gz gerado 4. Sistema processa e atualiza
            automaticamente
          </p>
          <p>
            • <strong>Vantagens:</strong> Mantém integridade dos dados, permite
            controle total sobre o processo e funciona em qualquer ambiente
          </p>
          <p>
            • <strong>Exemplos de caminhos:</strong>- Windows:
            C:\projetos\.chromadb ou C:\Users\usuario\.chromadb - Linux/Mac:
            /home/usuario/.chromadb ou /opt/projetos\.chromadb
          </p>
          <p>
            • <strong>⚠️ Importante:</strong> Em produção, o servidor não pode
            acessar arquivos do seu PC diretamente. Use compactação manual.
          </p>
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
