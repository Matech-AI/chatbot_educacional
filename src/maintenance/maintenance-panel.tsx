import React, { useState, useEffect } from "react";
import { Button } from "../components/ui/button";
import {
  Trash2,
  RefreshCw,
  Settings,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Database,
  HardDrive,
  FolderX,
  Zap,
  Download,
  FileText,
  Clock,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { apiRequestJson } from "../lib/api";
import { EnhancedReprocessingPanel } from "./enhanced-reprocessing-panel";
import { ChromaDBUpload } from "../components/materials/chromadb-upload";

interface MaintenancePanelProps {
  onRefresh?: () => void;
}

interface SystemReport {
  timestamp: string;
  generated_by: string;
  system_info: {
    version: string;
    python_version: string;
    platform: string;
  };
  directories: {
    materials: {
      exists: boolean;
      total_files: number;
      total_folders: number;
      total_size_bytes: number;
      total_size_mb: number;
      file_types: Record<string, number>;
      size_distribution: Record<string, number>;
    };
    chromadb: {
      exists: boolean;
      size_bytes: number;
    };
  };
  drive_status: {
    handler_initialized: boolean;
    service_available: boolean;
    authentication_method: string;
    processed_files_count: number;
    unique_hashes_count: number;
  };
  rag_status: {
    initialized: boolean;
    stats: any;
  };
  file_analysis: {
    duplicates: {
      total_files_scanned: number;
      unique_files: number;
      duplicate_groups: number;
      duplicate_files: number;
      wasted_space_bytes: number;
      wasted_space_mb: number;
      efficiency_percentage: number;
    };
  };
  recommendations: string[];
}

export const MaintenancePanel: React.FC<MaintenancePanelProps> = ({
  onRefresh,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [systemReport, setSystemReport] = useState<SystemReport | null>(null);
  const [activeOperation, setActiveOperation] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    generateSystemReport();
  }, []);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const apiCall = async (endpoint: string, method: string = "POST") => {
    if (method === "GET") {
      return await apiRequestJson(endpoint, { method: "GET" });
    } else {
      return await apiRequestJson(endpoint, { method: "POST" });
    }
  };

  const generateSystemReport = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const report = await apiCall("/maintenance/system-report", "GET");
      setSystemReport(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar relatório");
    } finally {
      setIsLoading(false);
    }
  };

  const runOperation = async (
    operation: string,
    endpoint: string,
    confirmMessage?: string
  ) => {
    if (confirmMessage && !window.confirm(confirmMessage)) {
      return;
    }

    try {
      setActiveOperation(operation);
      setError(null);
      setResults(null);

      const result = await apiCall(endpoint);
      setResults(result);

      // Refresh system report after operation
      setTimeout(() => {
        generateSystemReport();
        if (onRefresh) onRefresh();
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro na operação");
    } finally {
      setActiveOperation(null);
    }
  };

  const operations = [
    {
      id: "cleanup-duplicates",
      title: "Remover Duplicatas",
      description: "Remove arquivos duplicados com base no conteúdo",
      icon: <Trash2 size={20} />,
      color: "bg-yellow-500",
      endpoint: "/maintenance/cleanup-duplicates",
      confirmMessage:
        "Tem certeza que deseja remover todos os arquivos duplicados?",
      recommended:
        (systemReport?.file_analysis?.duplicates?.duplicate_files || 0) > 0,
    },
    {
      id: "cleanup-folders",
      title: "Limpar Pastas Vazias",
      description: "Remove pastas vazias da estrutura",
      icon: <FolderX size={20} />,
      color: "bg-blue-500",
      endpoint: "/maintenance/cleanup-empty-folders",
      recommended: false,
    },
    {
      id: "optimize-storage",
      title: "Otimizar Armazenamento",
      description: "Executa limpeza completa de duplicatas e pastas vazias",
      icon: <Zap size={20} />,
      color: "bg-green-500",
      endpoint: "/maintenance/optimize-storage",
      confirmMessage: "Deseja executar a otimização completa do armazenamento?",
      recommended: true,
    },
    {
      id: "reset-materials",
      title: "Resetar Materiais",
      description: "Remove TODOS os materiais baixados",
      icon: <AlertTriangle size={20} />,
      color: "bg-red-500",
      endpoint: "/maintenance/reset-materials",
      confirmMessage: "ATENÇÃO: Isso removerá TODOS os materiais! Tem certeza?",
      dangerous: true,
    },
    {
      id: "reset-chromadb",
      title: "Resetar Banco Vetorial",
      description: "Reseta o banco vetorial do chat",
      icon: <Database size={20} />,
      color: "bg-purple-500",
      endpoint: "/maintenance/reset-chromadb",
      confirmMessage: "Isso resetará o sistema de chat. Continuar?",
      dangerous: true,
    },
    {
      id: "clear-drive-cache",
      title: "Limpar Cache do Drive",
      description:
        "Limpa o cache de hashes para permitir baixar arquivos novamente",
      icon: <RefreshCw size={20} />,
      color: "bg-indigo-500",
      endpoint: "/maintenance/clear-drive-cache",
      confirmMessage: "Deseja limpar o cache de hashes do Google Drive?",
      recommended: false,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Settings size={24} />
            Painel de Manutenção
          </h2>
          <p className="text-gray-600 mt-1">
            Ferramentas para otimização e limpeza do sistema
          </p>
        </div>

        <Button
          onClick={generateSystemReport}
          disabled={isLoading}
          variant="outline"
          className="flex items-center gap-2"
        >
          <RefreshCw size={16} className={isLoading ? "animate-spin" : ""} />
          Atualizar Relatório
        </Button>
      </div>

      {/* System Status Cards */}
      {systemReport && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Arquivos</p>
                <p className="text-2xl font-bold text-gray-900">
                  {systemReport.directories.materials?.total_files || 0}
                </p>
              </div>
              <FileText size={24} className="text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Tamanho Total
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {systemReport.directories.materials
                    ? formatBytes(
                        systemReport.directories.materials.total_size_bytes
                      )
                    : "0 B"}
                </p>
              </div>
              <HardDrive size={24} className="text-green-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Duplicatas</p>
                <p className="text-2xl font-bold text-red-600">
                  {systemReport.file_analysis?.duplicates?.duplicate_files || 0}
                </p>
              </div>
              <Trash2 size={24} className="text-red-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Eficiência</p>
                <p className="text-2xl font-bold text-green-600">
                  {systemReport.file_analysis?.duplicates
                    ?.efficiency_percentage || 100}
                  %
                </p>
              </div>
              <BarChart3 size={24} className="text-green-600" />
            </div>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {systemReport?.recommendations &&
        systemReport.recommendations.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-medium text-blue-800 mb-2 flex items-center gap-2">
              <CheckCircle size={18} />
              Recomendações do Sistema
            </h3>
            <ul className="text-sm text-blue-700 space-y-1">
              {systemReport.recommendations.map((recommendation, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-blue-600">•</span>
                  {recommendation}
                </li>
              ))}
            </ul>
          </div>
        )}

      {/* Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-2"
          >
            <AlertTriangle
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

      {/* Results Display */}
      <AnimatePresence>
        {results && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-green-50 border border-green-200 rounded-lg p-4"
          >
            <h3 className="font-medium text-green-800 mb-2 flex items-center gap-2">
              <CheckCircle size={18} />
              Resultado da Operação
            </h3>
            <div className="text-sm text-green-700">
              <p className="mb-2">{results.message}</p>

              {results.statistics && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                  {Object.entries(results.statistics).map(
                    ([key, value]: [string, any]) => (
                      <div key={key} className="bg-white rounded p-2">
                        <div className="text-xs text-gray-600 capitalize">
                          {key.replace(/_/g, " ")}
                        </div>
                        <div className="font-bold text-green-800">{value}</div>
                      </div>
                    )
                  )}
                </div>
              )}

              {results.results && (
                <div className="mt-3 space-y-2">
                  {Object.entries(results.results).map(
                    ([key, value]: [string, any]) => (
                      <div key={key} className="text-xs">
                        <strong>{key.replace(/_/g, " ")}:</strong>{" "}
                        {JSON.stringify(value)}
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Operations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {operations.map((operation) => (
          <div
            key={operation.id}
            className={`bg-white rounded-lg border-2 p-4 ${
              operation.recommended
                ? "border-green-300 bg-green-50"
                : operation.dangerous
                ? "border-red-300 bg-red-50"
                : "border-gray-200"
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div
                className={`w-10 h-10 ${operation.color} rounded-lg flex items-center justify-center text-white`}
              >
                {operation.icon}
              </div>

              {operation.recommended && (
                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                  Recomendado
                </span>
              )}

              {operation.dangerous && (
                <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">
                  Perigoso
                </span>
              )}
            </div>

            <h3 className="font-semibold text-gray-900 mb-2">
              {operation.title}
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              {operation.description}
            </p>

            <Button
              onClick={() =>
                runOperation(
                  operation.id,
                  operation.endpoint,
                  operation.confirmMessage
                )
              }
              disabled={activeOperation === operation.id || isLoading}
              isLoading={activeOperation === operation.id}
              variant={operation.dangerous ? "danger" : "default"}
              className="w-full"
            >
              {activeOperation === operation.id ? "Executando..." : "Executar"}
            </Button>
          </div>
        ))}
      </div>

      {/* Enhanced Reprocessing Panel */}
      <EnhancedReprocessingPanel onSuccess={generateSystemReport} />

      {/* ChromaDB Upload Section */}
      <ChromaDBUpload
        onUploadSuccess={() => {
          generateSystemReport();
          onRefresh?.();
        }}
      />

      {/* Detailed Report */}
      {systemReport && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart3 size={20} />
            Relatório Detalhado do Sistema
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* System Info */}
            <div>
              <h4 className="font-medium text-gray-900 mb-2">
                Informações do Sistema
              </h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Versão:</span>
                  <span className="font-medium">
                    {systemReport.system_info.version}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Python:</span>
                  <span className="font-medium">
                    {systemReport.system_info.python_version}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Platform:</span>
                  <span className="font-medium">
                    {systemReport.system_info.platform}
                  </span>
                </div>
              </div>
            </div>

            {/* Drive Status */}
            <div>
              <h4 className="font-medium text-gray-900 mb-2">
                Status do Google Drive
              </h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Conectado:</span>
                  <span
                    className={`font-medium ${
                      systemReport.drive_status.service_available
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {systemReport.drive_status.service_available
                      ? "Sim"
                      : "Não"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Método:</span>
                  <span className="font-medium">
                    {systemReport.drive_status.authentication_method}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Arquivos processados:</span>
                  <span className="font-medium">
                    {systemReport.drive_status.processed_files_count}
                  </span>
                </div>
              </div>
            </div>

            {/* File Types */}
            {systemReport.directories.materials?.file_types && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">
                  Tipos de Arquivo
                </h4>
                <div className="space-y-1 text-sm">
                  {Object.entries(
                    systemReport.directories.materials.file_types
                  ).map(([type, count]) => (
                    <div key={type} className="flex justify-between">
                      <span className="text-gray-600">
                        {type || "sem extensão"}:
                      </span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Duplicate Analysis */}
            {systemReport.file_analysis?.duplicates && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">
                  Análise de Duplicatas
                </h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Grupos de duplicatas:</span>
                    <span className="font-medium text-red-600">
                      {systemReport.file_analysis.duplicates.duplicate_groups}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Espaço desperdiçado:</span>
                    <span className="font-medium text-red-600">
                      {systemReport.file_analysis.duplicates.wasted_space_mb} MB
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Eficiência:</span>
                    <span className="font-medium text-green-600">
                      {
                        systemReport.file_analysis.duplicates
                          .efficiency_percentage
                      }
                      %
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Relatório gerado por: {systemReport.generated_by}</span>
              <span className="flex items-center gap-1">
                <Clock size={12} />
                {new Date(systemReport.timestamp).toLocaleString("pt-BR")}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
