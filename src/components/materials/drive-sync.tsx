import React, { useState } from "react";
import { apiRequestJson } from "@/lib/api";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Switch } from "../ui/switch";
import {
  Cloud,
  AlertCircle,
  CheckCircle,
  Info,
  RefreshCw,
  Download,
  Eye,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "../../store/auth-store";

interface DriveSyncProps {
  onSync: () => void;
  isLoading: boolean;
}

interface DriveTestResult {
  accessible: boolean;
  public: boolean;
  file_count: number;
  error: string | null;
  files_sample: string[];
  folder_name: string | null;
}

interface DriveFile {
  id: string;
  name: string;
  title: string;
  size: number;
  type: string;
  mime_type?: string;
  created_time?: string;
  modified_time?: string;
}

export const DriveSync: React.FC<DriveSyncProps> = ({ onSync, isLoading }) => {
  const { user, isAuthenticated } = useAuthStore();

  // Carregar valores do localStorage se disponíveis
  const [folderInput, setFolderInput] = useState(
    localStorage.getItem("lastDriveFolderId") ||
      "1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ"
  );
  const [apiKey, setApiKey] = useState(
    localStorage.getItem("lastDriveApiKey") || ""
  );
  const [downloadFiles, setDownloadFiles] = useState(
    localStorage.getItem("lastDriveDownloadFiles") !== "false"
  );
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<DriveTestResult | null>(null);
  const [syncedFiles, setSyncedFiles] = useState<DriveFile[]>([]);

  const extractFolderIdFromUrl = (url: string): string | null => {
    try {
      const patterns = [
        /\/folders\/([a-zA-Z0-9_-]+)/,
        /id=([a-zA-Z0-9_-]+)/,
        /^([a-zA-Z0-9_-]{28,})$/,
      ];

      for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match && match[1]) {
          return match[1];
        }
      }
      return null;
    } catch (error) {
      return null;
    }
  };

  const validateDriveFolderId = (folderId: string): boolean => {
    const driveIdRegex = /^[a-zA-Z0-9_-]{28,}$/;
    return driveIdRegex.test(folderId.trim());
  };

  const testFolderAccess = async () => {
    if (!isAuthenticated) {
      setError("Você precisa estar logado para testar o acesso à pasta");
      return;
    }

    setIsTesting(true);
    setError("");
    setSuccess("");
    try {
      const folderId =
        extractFolderIdFromUrl(folderInput.trim()) || folderInput.trim();

      if (!folderId) {
        setError("ID da pasta é obrigatório");
        setIsTesting(false);
        return;
      }

      if (!validateDriveFolderId(folderId)) {
        setError("Formato do ID da pasta inválido");
        setIsTesting(false);
        return;
      }

      // Salvar o ID da pasta no localStorage
      localStorage.setItem("lastDriveFolderId", folderId);
      if (apiKey) {
        localStorage.setItem("lastDriveApiKey", apiKey);
      }

      const result = await apiRequestJson<DriveTestResult>(
        "/test-drive-folder",
        {
          method: "POST",
          body: JSON.stringify({
            folder_id: folderId,
            api_key: apiKey || undefined,
          }),
        }
      );
      setTestResult(result);

      if (result.accessible) {
        setSuccess("✅ Pasta acessível!");
        setTimeout(() => setSuccess(""), 2000);
      } else {
        setError("❌ Não foi possível acessar a pasta");
        setTimeout(() => setError(""), 4000);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Erro desconhecido";
      setError(`Erro ao testar acesso: ${errorMessage}`);
      setTimeout(() => setError(""), 4000);
      console.error("Erro no teste:", err);
    } finally {
      setIsTesting(false);
    }
  };

  const handleSync = async () => {
    if (!isAuthenticated) {
      setError("Você precisa estar logado para sincronizar arquivos");
      return;
    }

    try {
      setError(null);
      setSuccess(null);
      setIsProcessing(true);
      setSyncedFiles([]);

      const folderId =
        extractFolderIdFromUrl(folderInput.trim()) || folderInput.trim();

      if (!folderId) {
        setError("ID da pasta é obrigatório");
        return;
      }

      if (!validateDriveFolderId(folderId)) {
        setError("Formato do ID da pasta inválido");
        return;
      }

      console.log("Sincronizando pasta:", folderId);

      // Alterado de /api/sync-drive para /api/sync-drive-simple
      const result = await apiRequestJson<any>("/sync-drive-simple", {
        method: "POST",
        body: JSON.stringify({
          folder_id: folderId,
          api_key: apiKey || undefined,
          download_files: downloadFiles,
        }),
      });
      setSyncedFiles(result.files || []);

      setSuccess(
        `✅ ${result.files?.length ?? 0} arquivos baixados com sucesso!`
      );

      // Não redirecionar para a tela de materiais
      // Apenas limpar a mensagem de sucesso após alguns segundos
      setTimeout(() => {
        setSuccess(null);
      }, 5000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Erro desconhecido";
      setError(`Erro na sincronização: ${errorMessage}`);
      console.error("Erro na sincronização:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setSuccess(null);
    setTestResult(null);
    setFolderInput(e.target.value);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getFileIcon = (type: string): string => {
    switch (type.toLowerCase()) {
      case "pdf":
        return "📄";
      case "docx":
      case "doc":
        return "📝";
      case "txt":
        return "📃";
      case "video":
      case "mp4":
      case "avi":
      case "mov":
        return "🎥";
      default:
        return "📁";
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
      {!isAuthenticated && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-yellow-600" />
            <span className="text-yellow-800 font-medium">
              Você precisa estar logado para usar esta funcionalidade
            </span>
          </div>
        </div>
      )}

      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Cloud size={20} />
        Sincronizar com Google Drive
      </h2>

      <div className="space-y-4">
        {/* Folder ID Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ID ou URL da Pasta do Google Drive
          </label>
          <Input
            value={folderInput}
            onChange={handleInputChange}
            placeholder="Ex: 1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ"
            disabled={
              !isAuthenticated || isProcessing || isLoading || isTesting
            }
          />
          <p className="mt-1 text-xs text-gray-500">
            Cole o ID da pasta ou a URL completa do Google Drive
          </p>
        </div>

        {/* API Key Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Google Drive API Key (Opcional)
          </label>
          <Input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Sua API Key do Google Drive"
            disabled={
              !isAuthenticated || isProcessing || isLoading || isTesting
            }
          />
          <p className="mt-1 text-xs text-gray-500">
            Necessário para pastas privadas. Deixe em branco para pastas
            públicas.
          </p>
        </div>

        {/* Download Option - Restaurado para permitir escolha */}
        <div className="border border-gray-200 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <Switch
              checked={downloadFiles}
              onCheckedChange={setDownloadFiles}
              disabled={
                !isAuthenticated || isProcessing || isLoading || isTesting
              }
              id="download-switch"
            />
            <label
              htmlFor="download-switch"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              {downloadFiles ? "Baixar arquivos" : "Apenas listar arquivos"}
            </label>
          </div>
          <p className="mt-1 text-xs text-gray-500">
            {downloadFiles
              ? "Os arquivos serão baixados para o servidor"
              : "Apenas listará os arquivos sem baixar"}
          </p>
        </div>

        {/* Test Result */}
        <AnimatePresence>
          {testResult && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-blue-50 border border-blue-200 rounded-md p-3"
            >
              <div className="flex items-start gap-2">
                <Info
                  size={16}
                  className="text-blue-600 mt-0.5 flex-shrink-0"
                />
                <div className="text-sm">
                  <p className="font-medium text-blue-800">
                    Informações da Pasta: {testResult.folder_name || "Sem nome"}
                  </p>
                  <div className="mt-1 space-y-1 text-blue-700">
                    <p>• Arquivos encontrados: {testResult.file_count ?? 0}</p>
                    <p>• Acesso público: {testResult.public ? "Sim" : "Não"}</p>
                    {(testResult.files_sample || []).length > 0 && (
                      <p>
                        • Exemplos:{" "}
                        {(testResult.files_sample || []).slice(0, 3).join(", ")}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error Display */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-red-50 border border-red-200 rounded-md p-3 flex items-start gap-2"
            >
              <AlertCircle
                size={16}
                className="text-red-600 mt-0.5 flex-shrink-0"
              />
              <div>
                <p className="text-sm text-red-600 font-medium">Erro</p>
                <p className="text-sm text-red-500 mt-1">{error}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Success Display */}
        <AnimatePresence>
          {success && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-green-50 border border-green-200 rounded-md p-3 flex items-start gap-2"
            >
              <CheckCircle
                size={16}
                className="text-green-600 mt-0.5 flex-shrink-0"
              />
              <div>
                <p className="text-sm text-green-600 font-medium">Sucesso</p>
                <p className="text-sm text-green-600 mt-1">{success}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={testFolderAccess}
            disabled={
              !isAuthenticated ||
              !folderInput.trim() ||
              isLoading ||
              isProcessing ||
              isTesting
            }
            isLoading={isTesting}
            variant="outline"
            className="flex-1 flex items-center justify-center gap-2"
          >
            <Eye size={18} />
            <span>{isTesting ? "Testando..." : "Testar Acesso"}</span>
          </Button>

          <Button
            onClick={handleSync}
            disabled={
              !isAuthenticated ||
              !folderInput.trim() ||
              isLoading ||
              isProcessing ||
              isTesting
            }
            isLoading={isProcessing}
            className="flex-1 flex items-center justify-center gap-2"
          >
            <Download size={18} />
            <span>
              {isProcessing
                ? downloadFiles
                  ? "Baixando..."
                  : "Processando..."
                : downloadFiles
                ? "Baixar Materiais"
                : "Listar Materiais"}
            </span>
          </Button>
        </div>

        {/* Synced Files Display */}
        <AnimatePresence>
          {syncedFiles.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="border border-gray-200 rounded-lg p-3 max-h-60 overflow-y-auto"
            >
              <h4 className="font-medium text-gray-900 mb-2">
                {downloadFiles ? "Arquivos Baixados" : "Arquivos Encontrados"}
              </h4>
              <div className="space-y-2">
                {syncedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-2 bg-gray-50 rounded"
                  >
                    <span className="text-lg">{getFileIcon(file.type)}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {file.type.toUpperCase()} • {formatFileSize(file.size)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Instructions */}
        <div className="text-xs text-gray-500 space-y-1 bg-gray-50 rounded-lg p-3">
          <p>
            <strong>Como obter o ID da pasta:</strong>
          </p>
          <ol className="list-decimal list-inside space-y-1 ml-2">
            <li>Abra a pasta no Google Drive</li>
            <li>Copie o ID da URL (após /folders/)</li>
            <li>Ou cole a URL completa aqui</li>
          </ol>
          <p className="mt-2">
            <strong>Para pastas privadas:</strong> Configure uma API Key do
            Google Drive.
          </p>
        </div>
      </div>
    </div>
  );
};
