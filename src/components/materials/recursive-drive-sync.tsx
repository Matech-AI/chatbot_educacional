import React, { useState } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Switch } from "../ui/switch";
import {
  AlertCircle,
  CheckCircle,
  Info,
  Download,
  Eye,
  FolderTree,
  Zap,
  BarChart3,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// Importar as funções de API no topo do arquivo
import { apiRequest, apiRequestJson } from "../../lib/api";

interface RecursiveDriveSyncProps {
  onSync: () => void;
  isLoading: boolean;
}

interface DriveStats {
  total_folders: number;
  total_files: number;
  downloaded_files: number;
  skipped_duplicates: number;
  errors: number;
}

interface DriveTimings {
  analysis_time: number;
  download_time: number;
  total_time: number;
}

interface RecursiveSyncResult {
  status: string;
  message: string;
  statistics: DriveStats;
  timing: DriveTimings;
  processed_files: any[];
  final_statistics: any;
}

interface FolderStructure {
  id: string;
  name: string;
  path: string;
  subfolders: Record<string, FolderStructure>;
  files: any[];
}

// Adicionar no início do componente RecursiveDriveSync
export const RecursiveDriveSync: React.FC<RecursiveDriveSyncProps> = ({
  onSync,
  isLoading,
}) => {
  // Carregar valores do localStorage se disponíveis
  const [folderInput, setFolderInput] = useState(
    localStorage.getItem("lastDriveFolderId") ||
      "1T67sTJgCvz-PDSDS2NUnhPSTjhDXnscg"
  );
  const [apiKey, setApiKey] = useState(
    localStorage.getItem("lastDriveApiKey") || ""
  );
  const [maxDepth, setMaxDepth] = useState<number>(
    parseInt(localStorage.getItem("lastDriveMaxDepth") || "10")
  );
  const [isRecursive, setIsRecursive] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isForceRedownload, setIsForceRedownload] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [testResult, setTestResult] = useState<any>(null);
  const [syncResult, setSyncResult] = useState<RecursiveSyncResult | null>(
    null
  );
  const [folderStructure, setFolderStructure] =
    useState<FolderStructure | null>(null);
  const [currentDownloadId, setCurrentDownloadId] = useState<string | null>(
    null
  );
  const [progressInterval, setProgressInterval] =
    useState<NodeJS.Timeout | null>(null);

  // Controles para sincronização por módulos (em partes)
  const [modulePrefix, setModulePrefix] = useState(
    localStorage.getItem("moduleSyncPrefix") || "Módulo "
  );
  const [moduleName, setModuleName] = useState(
    localStorage.getItem("moduleSyncName") || ""
  );
  const [moduleBatchSize, setModuleBatchSize] = useState<number>(
    parseInt(localStorage.getItem("moduleSyncBatchSize") || "2")
  );
  const [moduleMaxDepth, setModuleMaxDepth] = useState<number>(
    parseInt(localStorage.getItem("moduleSyncMaxDepth") || "2")
  );

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

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(1)}s`;
  };

  const testFolderAccess = async () => {
    try {
      setError(null);
      setSuccess(null);
      setIsTesting(true);
      setTestResult(null);

      const folderId =
        extractFolderIdFromUrl(folderInput.trim()) || folderInput.trim();

      if (!folderId || !validateDriveFolderId(folderId)) {
        setError("ID da pasta inválido");
        setIsTesting(false);
        return;
      }

      // Salvar valores no localStorage
      localStorage.setItem("lastDriveFolderId", folderId);
      if (apiKey) localStorage.setItem("lastDriveApiKey", apiKey);
      localStorage.setItem("lastDriveMaxDepth", maxDepth.toString());

      // Definir uma mensagem de status inicial
      setSuccess("🔍 Testando acesso à pasta...");

      // Testar acesso básico à pasta
      const result = await apiRequestJson("/test-drive-folder", {
        method: "POST",
        body: JSON.stringify({
          folder_id: folderId,
          api_key: apiKey || undefined,
        }),
      });

      setTestResult(result);

      if (result.accessible) {
        setSuccess(
          "✅ Pasta acessível! Clique em 'Analisar Estrutura' para ver detalhes completos."
        );
        setTimeout(() => setSuccess(""), 3000);
      } else {
        setError("❌ Não foi possível acessar a pasta");
        setTimeout(() => setError(""), 4000);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Erro desconhecido";
      setError(`Erro ao testar acesso: ${errorMessage}`);
      console.error("Erro no teste:", err);
    } finally {
      setIsTesting(false);
    }
  };

  const analyzeFolder = async () => {
    try {
      setError(null);
      setSuccess(null);
      setIsAnalyzing(true);
      setAnalysisResult(null);

      const folderId =
        extractFolderIdFromUrl(folderInput.trim()) || folderInput.trim();

      if (!folderId || !validateDriveFolderId(folderId)) {
        setError("ID da pasta inválido");
        setIsAnalyzing(false);
        return;
      }

      // Salvar valores no localStorage
      localStorage.setItem("lastDriveFolderId", folderId);
      if (apiKey) localStorage.setItem("lastDriveApiKey", apiKey);
      localStorage.setItem("lastDriveMaxDepth", maxDepth.toString());
      localStorage.setItem("lastDriveAuthSuccess", "true");

      // Definir uma mensagem de status inicial
      setSuccess("🔍 Analisando estrutura de pastas...");

      // Substituir a chamada fetch direta por apiRequestJson
      const result = await apiRequestJson("/recursive-drive-analysis", {
        method: "POST",
        body: JSON.stringify({
          folder_id: folderId,
          root_folder_id: folderId,
          api_key: apiKey || undefined,
          max_depth: maxDepth,
        }),
      });

      // Verificar se a análise ainda está em andamento (não foi cancelada)
      if (isAnalyzing) {
        setAnalysisResult(result);
        setFolderStructure(result.folder_structure);

        setSuccess(
          `✅ Análise concluída! ${result.statistics.total_folders} pastas e ${result.statistics.total_files} arquivos encontrados`
        );
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Erro desconhecido";
      setError(`Erro na análise: ${errorMessage}`);
      console.error("Erro na análise:", err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRecursiveSync = async () => {
    try {
      setError(null);
      setSuccess(null);
      setIsProcessing(true);

      // Adicionar esta lógica para extrair o ID da pasta
      const folderId =
        extractFolderIdFromUrl(folderInput.trim()) || folderInput.trim();

      if (!folderId || !validateDriveFolderId(folderId)) {
        setError("ID da pasta inválido");
        setIsProcessing(false);
        return;
      }

      console.log("Iniciando sincronização recursiva:", folderId);

      // Substituir a chamada fetch direta pela função da API
      const result = await apiRequestJson("/drive/sync-recursive", {
        method: "POST",
        body: JSON.stringify({
          folder_id: folderId,
          api_key: apiKey || undefined,
          max_depth: maxDepth,
        }),
      });

      // Verificar se o download foi iniciado com sucesso
      if (result.status === "started" && result.download_id) {
        // Armazenar o ID do download atual
        const downloadId = result.download_id;
        setCurrentDownloadId(downloadId);

        let isCompleted = false;
        let progressResult = null;

        // Definir uma mensagem de status inicial
        setSuccess(
          "⏳ Download iniciado em segundo plano. Monitorando progresso..."
        );

        // Monitorar o progresso a cada 2 segundos
        const interval = setInterval(async () => {
          try {
            // Usar a API para obter o progresso
            const progress = await apiRequestJson(
              `/drive/download-progress?download_id=${downloadId}`
            );

            // Atualizar a mensagem de status com o progresso atual
            if (progress.status === "analyzing") {
              setSuccess("🔍 Analisando estrutura de pastas...");
            } else if (progress.status === "processing") {
              setSuccess(
                `📥 Baixando arquivos: ${progress.downloaded_files || 0} de ${
                  progress.total_files || "?"
                }`
              );
            } else if (progress.status === "completed" && progress.result) {
              // Download concluído, limpar o intervalo
              clearInterval(interval);
              setProgressInterval(null);
              isCompleted = true;
              progressResult = progress.result;

              // Limpar o ID do download atual
              setCurrentDownloadId(null);

              // Atualizar o estado com o resultado final
              setSyncResult(progressResult);

              // Exibir mensagem de sucesso
              setSuccess(
                `🎉 Sincronização recursiva concluída! ${progressResult.statistics.downloaded_files} arquivos baixados, ${progressResult.statistics.skipped_duplicates} duplicatas evitadas`
              );

              // Refresh materials list
              setTimeout(() => {
                onSync();
              }, 2000);

              // Finalizar o processamento
              setIsProcessing(false);
            } else if (progress.status === "error") {
              // Erro no download, limpar o intervalo
              clearInterval(interval);
              setProgressInterval(null);
              setCurrentDownloadId(null);
              throw new Error(
                progress.error || "Erro desconhecido no download"
              );
            } else if (progress.status === "cancelled") {
              // Download cancelado, limpar o intervalo
              clearInterval(interval);
              setProgressInterval(null);
              setCurrentDownloadId(null);
              setIsProcessing(false);
              setSuccess("❌ Download cancelado");
            }
          } catch (err) {
            clearInterval(interval);
            setProgressInterval(null);
            setCurrentDownloadId(null);
            throw err;
          }
        }, 2000);

        // Armazenar o intervalo para poder cancelá-lo posteriormente
        setProgressInterval(interval);

        // Definir um timeout para evitar que o intervalo continue indefinidamente
        setTimeout(() => {
          if (!isCompleted) {
            clearInterval(interval);
            setProgressInterval(null);
            setCurrentDownloadId(null);
            setIsProcessing(false);
          }
        }, 30 * 60 * 1000); // 30 minutos de timeout
      } else {
        // Se não recebemos um download_id, algo deu errado
        throw new Error("Não foi possível iniciar o download recursivo");
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Erro desconhecido";
      setError(`Erro na sincronização: ${errorMessage}`);
      console.error("Erro na sincronização:", err);
      setIsProcessing(false);
      setCurrentDownloadId(null);
    }
  };

  // Sincronização por módulos (em partes)
  const handleModuleSync = async () => {
    try {
      setError(null);
      setSuccess(null);
      setIsProcessing(true);

      const folderId =
        extractFolderIdFromUrl(folderInput.trim()) || folderInput.trim();

      if (!folderId || !validateDriveFolderId(folderId)) {
        setError("ID da pasta inválido");
        setIsProcessing(false);
        return;
      }

      // Persistir preferências
      localStorage.setItem("lastDriveFolderId", folderId);
      if (apiKey) localStorage.setItem("lastDriveApiKey", apiKey);
      localStorage.setItem("moduleSyncPrefix", modulePrefix);
      localStorage.setItem("moduleSyncName", moduleName);
      localStorage.setItem("moduleSyncBatchSize", String(moduleBatchSize));
      localStorage.setItem("moduleSyncMaxDepth", String(moduleMaxDepth));

      // Montar payload
      const payload: any = {
        folder_id: folderId,
        batch_size: moduleBatchSize,
        max_depth: moduleMaxDepth,
        download_files: true,
      };
      if (moduleName.trim()) payload.module_name = moduleName.trim();
      if (!moduleName.trim() && modulePrefix.trim())
        payload.module_prefix = modulePrefix.trim();
      if (apiKey) payload.api_key = apiKey;

      const result = await apiRequestJson("/drive/download-module", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (result.status === "started" && result.download_id) {
        const downloadId = result.download_id as string;
        setCurrentDownloadId(downloadId);

        setSuccess(
          "⏳ Sincronização por módulos iniciada. Monitorando progresso..."
        );

        const interval = setInterval(async () => {
          try {
            const progress = await apiRequestJson(
              `/drive/download-progress?download_id=${downloadId}`
            );

            if (progress.status === "analyzing") {
              setSuccess("🔍 Analisando módulos...");
            } else if (progress.status === "processing") {
              const cm = progress.current_module || "";
              const pm = progress.processed_modules || 0;
              const df = progress.downloaded_files || 0;
              const tf = progress.total_files || "?";
              setSuccess(
                `📦 Módulo atual: ${
                  cm || "(aguardando)"
                } | Processados: ${pm} | Arquivos: ${df} de ${tf}`
              );
            } else if (progress.status === "completed" && progress.result) {
              clearInterval(interval);
              setProgressInterval(null);
              setCurrentDownloadId(null);
              setSuccess(
                "🎉 Sincronização por módulos concluída com sucesso. Atualizando materiais..."
              );
              setTimeout(() => {
                onSync();
                setIsProcessing(false);
              }, 1500);
            } else if (progress.status === "error") {
              clearInterval(interval);
              setProgressInterval(null);
              setCurrentDownloadId(null);
              throw new Error(
                progress.error || "Erro desconhecido no download"
              );
            }
          } catch (err) {
            clearInterval(interval);
            setProgressInterval(null);
            setCurrentDownloadId(null);
            setIsProcessing(false);
            setError(
              err instanceof Error
                ? err.message
                : "Erro desconhecido no progresso"
            );
          }
        }, 2000);

        setProgressInterval(interval);
      } else {
        throw new Error("Não foi possível iniciar a sincronização por módulos");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
      setIsProcessing(false);
    }
  };

  const handleCancelSync = async () => {
    try {
      // Se estiver analisando, apenas interrompe a análise
      if (isAnalyzing) {
        setIsAnalyzing(false);
        setSuccess("❌ Análise cancelada pelo usuário");
        return;
      }

      // Caso contrário, procede com o cancelamento do download
      if (!currentDownloadId) {
        setError("Não há download em andamento para cancelar");
        return;
      }

      // Limpar o intervalo de progresso
      if (progressInterval) {
        clearInterval(progressInterval);
        setProgressInterval(null);
      }

      // Chamar a API para cancelar o download
      await apiRequestJson("/drive/cancel-download", {
        method: "POST",
        body: JSON.stringify({
          download_id: currentDownloadId,
        }),
      });

      // Atualizar o estado
      setCurrentDownloadId(null);
      setIsProcessing(false);
      setSuccess("❌ Download cancelado pelo usuário");
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Erro desconhecido";
      setError(`Erro ao cancelar: ${errorMessage}`);
      console.error("Erro ao cancelar:", err);
    }
  };

  const handleForceRedownload = async () => {
    setIsForceRedownload(true);
    setError(null);
    setSuccess(null);

    try {
      console.log("Forçando re-download de todos os arquivos...");

      const result = await apiRequestJson("/recursive-drive-force-redownload", {
        method: "POST",
      });

      if (result.status === "success") {
        setSuccess(
          `Modo de re-download forçado ativado! Encontrados ${result.existing_files_count} arquivos existentes.`
        );
        // Limpar resultados anteriores
        setAnalysisResult(null);
        setSyncResult(null);
      } else {
        setError("Erro ao ativar modo de re-download forçado");
      }
    } catch (error) {
      console.error("Erro ao forçar re-download:", error);
      setError("Erro ao ativar modo de re-download forçado");
    } finally {
      setIsForceRedownload(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setSuccess(null);
    setAnalysisResult(null);
    setTestResult(null);
    setSyncResult(null);
    setFolderStructure(null);
    setFolderInput(e.target.value);
  };

  const renderFolderStructure = (
    structure: FolderStructure,
    level: number = 0
  ) => {
    const indent = level * 20;

    return (
      <div key={structure.id} style={{ marginLeft: `${indent}px` }}>
        <div className="flex items-center gap-2 py-1">
          <FolderTree size={16} className="text-blue-600" />
          <span className="font-medium text-sm">{structure.name}</span>
          <span className="text-xs text-gray-500">
            ({structure.files.length} arquivos)
          </span>
        </div>
        {Object.values(structure.subfolders).map((subfolder) =>
          renderFolderStructure(subfolder, level + 1)
        )}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <h2 className="text-xl font-semibold mb-6 flex items-center gap-3">
        <Zap size={24} className="text-orange-600" />
        Sincronização Recursiva do Google Drive
      </h2>

      <div className="space-y-6">
        {/* Configuration Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ID ou URL da Pasta Raiz
            </label>
            <Input
              value={folderInput}
              onChange={handleInputChange}
              placeholder="Ex: 1T67sTJgCvz-PDSDS2NUnhPSTjhDXnscg"
              disabled={isProcessing || isLoading || isAnalyzing}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Key (Opcional)
            </label>
            <Input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Google Drive API Key"
              disabled={isProcessing || isLoading || isAnalyzing}
            />
          </div>
        </div>

        {/* Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-gray-200 rounded-lg p-4">
            <Switch
              checked={isRecursive}
              onCheckedChange={setIsRecursive}
              disabled={isProcessing || isLoading || isAnalyzing}
              label="Download Recursivo"
              description="Baixar todas as subpastas e arquivos automaticamente"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Profundidade Máxima
            </label>
            <Input
              type="number"
              value={maxDepth}
              onChange={(e) => setMaxDepth(parseInt(e.target.value) || 10)}
              min={1}
              max={50}
              disabled={isProcessing || isLoading || isAnalyzing}
            />
            <p className="text-xs text-gray-500 mt-1">
              Limite de níveis de pastas a processar
            </p>
          </div>
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

        {/* Analysis Results */}
        <AnimatePresence>
          {analysisResult && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-blue-50 border border-blue-200 rounded-lg p-4"
            >
              <h3 className="font-medium text-blue-800 mb-3 flex items-center gap-2">
                <BarChart3 size={18} />
                Resultado da Análise
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-700">
                    {analysisResult.statistics?.total_folders || 0}
                  </div>
                  <div className="text-sm text-blue-600">Pastas</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-700">
                    {analysisResult.statistics?.total_files || 0}
                  </div>
                  <div className="text-sm text-blue-600">Arquivos</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-blue-700">
                    {analysisResult.root_folder || "N/A"}
                  </div>
                  <div className="text-sm text-blue-600">Pasta Raiz</div>
                </div>
              </div>

              {folderStructure && (
                <div className="mt-4">
                  <h4 className="font-medium text-gray-800 mb-2">
                    Estrutura de Pastas:
                  </h4>
                  <div className="max-h-40 overflow-y-auto bg-white rounded border p-3">
                    {renderFolderStructure(folderStructure)}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Sync Results */}
        <AnimatePresence>
          {syncResult && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-green-50 border border-green-200 rounded-lg p-4"
            >
              <h3 className="font-medium text-green-800 mb-3 flex items-center gap-2">
                <CheckCircle size={18} />
                Resultado da Sincronização
              </h3>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-xl font-bold text-green-700">
                    {syncResult.statistics.downloaded_files}
                  </div>
                  <div className="text-sm text-green-600">Baixados</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-yellow-700">
                    {syncResult.statistics.skipped_duplicates}
                  </div>
                  <div className="text-sm text-yellow-600">Duplicatas</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-red-700">
                    {syncResult.statistics.errors}
                  </div>
                  <div className="text-sm text-red-600">Erros</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-blue-700">
                    {formatTime(syncResult.timing.total_time)}
                  </div>
                  <div className="text-sm text-blue-600">Tempo Total</div>
                </div>
              </div>

              <div className="text-sm text-gray-600 space-y-1">
                <div>
                  ⏱️ Análise: {formatTime(syncResult.timing.analysis_time)}
                </div>
                <div>
                  📥 Download: {formatTime(syncResult.timing.download_time)}
                </div>
                <div>
                  💾 Total processado: {syncResult.processed_files.length}{" "}
                  arquivos
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
        <div className="flex gap-3">
          <Button
            onClick={testFolderAccess}
            disabled={
              !folderInput.trim() ||
              isLoading ||
              isProcessing ||
              isAnalyzing ||
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
            onClick={analyzeFolder}
            disabled={
              !folderInput.trim() ||
              isLoading ||
              isProcessing ||
              isAnalyzing ||
              isTesting
            }
            isLoading={isAnalyzing}
            variant="outline"
            className="flex-1 flex items-center justify-center gap-2"
          >
            <BarChart3 size={18} />
            <span>{isAnalyzing ? "Analisando..." : "Analisar Estrutura"}</span>
          </Button>

          <Button
            onClick={handleForceRedownload}
            disabled={
              isLoading ||
              isProcessing ||
              isAnalyzing ||
              isTesting ||
              isForceRedownload
            }
            isLoading={isForceRedownload}
            variant="outline"
            className="flex-1 flex items-center justify-center gap-2"
          >
            <Zap size={18} />
            <span>
              {isForceRedownload ? "Ativando..." : "Forçar Re-download"}
            </span>
          </Button>

          <Button
            onClick={handleRecursiveSync}
            disabled={
              !folderInput.trim() ||
              isLoading ||
              isProcessing ||
              isAnalyzing ||
              isTesting
            }
            isLoading={isProcessing}
            className="flex-1 flex items-center justify-center gap-2"
          >
            <Download size={18} />
            <span>
              {isProcessing
                ? "Sincronizando..."
                : isRecursive
                ? "Sincronizar Recursivamente"
                : "Sincronizar Pasta"}
            </span>
          </Button>

          <Button
            onClick={handleCancelSync}
            variant="danger"
            className="flex-1 flex items-center justify-center gap-2"
            disabled={!isProcessing && !isAnalyzing && !isTesting}
          >
            <X size={18} />
            <span>Cancelar</span>
          </Button>
        </div>

        {/* Information Box */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-800 mb-2 flex items-center gap-2">
            <Info size={16} />
            Funcionalidades da Sincronização Recursiva
          </h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>✅ Navega automaticamente por todas as subpastas</li>
            <li>✅ Mantém a estrutura hierárquica de pastas localmente</li>
            <li>✅ Detecta e evita arquivos duplicados por conteúdo</li>
            <li>✅ Verifica arquivos existentes antes de baixar</li>
            <li>✅ Relatório detalhado de estatísticas e tempo</li>
            <li>✅ Análise prévia sem download para planejamento</li>
            <li>✅ Controle de profundidade máxima para segurança</li>
            <li>✅ Opção de forçar re-download quando necessário</li>
          </ul>
        </div>

        {/* Usage Instructions */}
        <div className="text-xs text-gray-500 space-y-2 bg-blue-50 rounded-lg p-3">
          <p>
            <strong>Como usar:</strong>
          </p>
          <ol className="list-decimal list-inside space-y-1 ml-2">
            <li>Cole o ID ou URL da pasta raiz do Google Drive</li>
            <li>Configure a API Key se necessário (para pastas privadas)</li>
            <li>
              Use "Testar Acesso" para verificar se a pasta está acessível
            </li>
            <li>
              Use "Analisar Estrutura" para ver detalhes completos da estrutura
            </li>
            <li>
              Use "Forçar Re-download" se quiser baixar arquivos novamente
              (ignora duplicatas)
            </li>
            <li>Execute "Sincronizar Recursivamente" para baixar tudo</li>
          </ol>
          <p className="mt-2">
            <strong>⚠️ Atenção:</strong> O download recursivo pode levar tempo
            considerável dependendo do tamanho da estrutura. Use a análise
            prévia para estimar.
          </p>
        </div>
      </div>
    </div>
  );
};
