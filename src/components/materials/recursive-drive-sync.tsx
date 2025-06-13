import React, { useState } from "react";
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
  FolderTree,
  Zap,
  BarChart3,
  Clock,
  Files,
  HardDrive,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

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

export const RecursiveDriveSync: React.FC<RecursiveDriveSyncProps> = ({
  onSync,
  isLoading,
}) => {
  const [folderInput, setFolderInput] = useState(
    "1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ"
  );
  const [apiKey, setApiKey] = useState("");
  const [maxDepth, setMaxDepth] = useState<number>(10);
  const [isRecursive, setIsRecursive] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [syncResult, setSyncResult] = useState<RecursiveSyncResult | null>(null);
  const [folderStructure, setFolderStructure] = useState<FolderStructure | null>(null);

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
        return;
      }

      const response = await fetch("/api/recursive-drive-analysis", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          root_folder_id: folderId,
          api_key: apiKey || undefined,
          max_depth: maxDepth,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setAnalysisResult(result);
      setFolderStructure(result.folder_structure);

      setSuccess(
        `✅ Análise concluída! ${result.statistics.total_folders} pastas e ${result.statistics.total_files} arquivos encontrados`
      );
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
      setSyncResult(null);

      const folderId =
        extractFolderIdFromUrl(folderInput.trim()) || folderInput.trim();

      if (!folderId || !validateDriveFolderId(folderId)) {
        setError("ID da pasta inválido");
        return;
      }

      console.log("Iniciando sincronização recursiva:", folderId);

      const response = await fetch("/api/recursive-drive-sync", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          root_folder_id: folderId,
          api_key: apiKey || undefined,
          max_depth: maxDepth,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result: RecursiveSyncResult = await response.json();
      setSyncResult(result);

      setSuccess(
        `🎉 Sincronização recursiva concluída! ${result.statistics.downloaded_files} arquivos baixados, ${result.statistics.skipped_duplicates} duplicatas evitadas`
      );

      // Refresh materials list
      setTimeout(() => {
        onSync();
      }, 2000);
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
    setAnalysisResult(null);
    setSyncResult(null);
    setFolderStructure(null);
    setFolderInput(e.target.value);
  };

  const renderFolderStructure = (structure: FolderStructure, level: number = 0) => {
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
              placeholder="Ex: 1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ"
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
                    {analysisResult.statistics.total_folders}
                  </div>
                  <div className="text-sm text-blue-600">Pastas</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-700">
                    {analysisResult.statistics.total_files}
                  </div>
                  <div className="text-sm text-blue-600">Arquivos</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-blue-700">
                    {analysisResult.root_folder}
                  </div>
                  <div className="text-sm text-blue-600">Pasta Raiz</div>
                </div>
              </div>

              {folderStructure && (
                <div className="mt-4">
                  <h4 className="font-medium text-gray-800 mb-2">Estrutura de Pastas:</h4>
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
                <div>⏱️ Análise: {formatTime(syncResult.timing.analysis_time)}</div>
                <div>📥 Download: {formatTime(syncResult.timing.download_time)}</div>
                <div>💾 Total processado: {syncResult.processed_files.length} arquivos</div>
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
              <AlertCircle size={16} className="text-red-600 mt-0.5 flex-shrink-0" />
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
              <CheckCircle size={16} className="text-green-600 mt-0.5 flex-shrink-0" />
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
            onClick={analyzeFolder}
            disabled={!folderInput.trim() || isLoading || isProcessing || isAnalyzing}
            isLoading={isAnalyzing}
            variant="outline"
            className="flex-1 flex items-center justify-center gap-2"
          >
            <Eye size={18} />
            <span>{isAnalyzing ? "Analisando..." : "Analisar Estrutura"}</span>
          </Button>

          <Button
            onClick={handleRecursiveSync}
            disabled={!folderInput.trim() || isLoading || isProcessing || isAnalyzing}
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
            <li>✅ Relatório detalhado de estatísticas e tempo</li>
            <li>✅ Análise prévia sem download para planejamento</li>
            <li>✅ Controle de profundidade máxima para segurança</li>
          </ul>
        </div>

        {/* Usage Instructions */}
        <div className="text-xs text-gray-500 space-y-2 bg-blue-50 rounded-lg p-3">
          <p><strong>Como usar:</strong></p>
          <ol className="list-decimal list-inside space-y-1 ml-2">
            <li>Cole o ID ou URL da pasta raiz do Google Drive</li>
            <li>Configure a API Key se necessário (para pastas privadas)</li>
            <li>Use "Analisar Estrutura" para ver o que será baixado</li>
            <li>Execute "Sincronizar Recursivamente" para baixar tudo</li>
          </ol>
          <p className="mt-2">
            <strong>⚠️ Atenção:</strong> O download recursivo pode levar tempo considerável
            dependendo do tamanho da estrutura. Use a análise prévia para estimar.
          </p>
        </div>
      </div>
    </div>
  );
};
