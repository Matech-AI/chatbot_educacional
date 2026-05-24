import React, { useState, useEffect } from "react";
import { Button } from "../components/ui/button";
import {
  BrainCircuit,
  FolderOpen,
  CheckSquare,
  Square,
  FileText,
  Presentation,
  FileCode,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { ragApiRequestJson } from "../lib/api";

interface Subfolder {
  name: string;
  file_count: number;
}

interface PipelineStep {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  status: "pending" | "running" | "done" | "skipped";
}

interface EnhancedReprocessingPanelProps {
  onSuccess?: () => void;
}

const SUPPORTED_FORMATS = [
  { ext: "PDF", icon: <FileText size={12} />, color: "text-red-600" },
  { ext: "PPTX", icon: <Presentation size={12} />, color: "text-orange-600" },
  { ext: "DOCX", icon: <FileText size={12} />, color: "text-blue-600" },
  { ext: "MD", icon: <FileCode size={12} />, color: "text-green-600" },
  { ext: "TXT", icon: <FileText size={12} />, color: "text-gray-600" },
];

const INITIAL_STEPS: PipelineStep[] = [
  {
    id: "preprocess",
    label: "Pré-processamento",
    description: "Converte PPTX, DOCX, MD e PDFs em texto estruturado",
    icon: <FileText size={14} />,
    status: "pending",
  },
  {
    id: "chunk",
    label: "Segmentação",
    description: "Divide os documentos em chunks com overlap inteligente",
    icon: <BrainCircuit size={14} />,
    status: "pending",
  },
  {
    id: "embed",
    label: "Geração de Embeddings",
    description: "Cria vetores semânticos para cada chunk",
    icon: <BrainCircuit size={14} />,
    status: "pending",
  },
  {
    id: "index",
    label: "Indexação no ChromaDB",
    description: "Persiste os vetores no banco de dados vetorial",
    icon: <BrainCircuit size={14} />,
    status: "pending",
  },
];

export const EnhancedReprocessingPanel: React.FC<
  EnhancedReprocessingPanelProps
> = ({ onSuccess }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [subfolders, setSubfolders] = useState<Subfolder[]>([]);
  const [selectedFolders, setSelectedFolders] = useState<Set<string>>(
    new Set()
  );
  const [loadingFolders, setLoadingFolders] = useState(true);
  const [showFolders, setShowFolders] = useState(true);
  const [steps, setSteps] = useState<PipelineStep[]>(INITIAL_STEPS);

  useEffect(() => {
    fetchSubfolders();
  }, []);

  const fetchSubfolders = async () => {
    setLoadingFolders(true);
    try {
      const data = await ragApiRequestJson("/materials/subfolders");
      setSubfolders(data.subfolders || []);
      // Pre-select all by default
      setSelectedFolders(
        new Set((data.subfolders || []).map((f: Subfolder) => f.name))
      );
    } catch {
      setSubfolders([]);
    } finally {
      setLoadingFolders(false);
    }
  };

  const toggleFolder = (name: string) => {
    setSelectedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedFolders.size === subfolders.length) {
      setSelectedFolders(new Set());
    } else {
      setSelectedFolders(new Set(subfolders.map((f) => f.name)));
    }
  };

  const simulatePipeline = () => {
    const delays = [0, 1200, 3000, 5000];
    INITIAL_STEPS.forEach((step, i) => {
      setTimeout(() => {
        setSteps((prev) =>
          prev.map((s) =>
            s.id === step.id
              ? { ...s, status: "running" }
              : s.id === INITIAL_STEPS[i - 1]?.id
              ? { ...s, status: "done" }
              : s
          )
        );
      }, delays[i]);
    });
  };

  const handleReprocess = async () => {
    if (selectedFolders.size === 0) {
      setError("Selecione ao menos uma pasta para treinar.");
      return;
    }

    const folderList = Array.from(selectedFolders);
    const isAll = folderList.length === subfolders.length;

    const confirmMsg = isAll
      ? "Treinar a IA com TODOS os materiais. Esta operação pode levar vários minutos. Continuar?"
      : `Treinar a IA apenas com: ${folderList.join(", ")}. Continuar?`;

    if (!window.confirm(confirmMsg)) return;

    setIsLoading(true);
    setError(null);
    setMessage(null);
    setSteps(INITIAL_STEPS.map((s) => ({ ...s, status: "pending" })));
    simulatePipeline();

    try {
      const result = await ragApiRequestJson("/reprocess-enhanced-materials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          training_dirs: isAll ? null : folderList,
        }),
      });

      setSteps((prev) => prev.map((s) => ({ ...s, status: "done" })));
      setMessage(result.message || "Reprocessamento iniciado com sucesso!");
      if (onSuccess) onSuccess();
    } catch (err) {
      setSteps((prev) =>
        prev.map((s) =>
          s.status === "running" ? { ...s, status: "pending" } : s
        )
      );
      setError(
        err instanceof Error ? err.message : "Ocorreu um erro desconhecido."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const allSelected = selectedFolders.size === subfolders.length;

  return (
    <div className="bg-white rounded-lg border border-blue-200 p-4 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center text-white shrink-0">
            <BrainCircuit size={18} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-sm">
              Treinamento RAG
            </h3>
            <p className="text-xs text-gray-500">
              Indexa materiais para o chatbot responder com precisão
            </p>
          </div>
        </div>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full shrink-0">
          Aprimorado
        </span>
      </div>

      {/* Formatos suportados */}
      <div className="flex flex-wrap gap-1">
        {SUPPORTED_FORMATS.map(({ ext, icon, color }) => (
          <span
            key={ext}
            className={`flex items-center gap-0.5 text-xs px-1.5 py-0.5 bg-gray-100 rounded ${color}`}
          >
            {icon} {ext}
          </span>
        ))}
        <span className="text-xs text-gray-400 self-center ml-1">
          • vídeos: apenas metadados
        </span>
      </div>

      {/* Seleção de pastas */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <button
          className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 text-sm font-medium text-gray-700"
          onClick={() => setShowFolders((v) => !v)}
        >
          <span className="flex items-center gap-1.5">
            <FolderOpen size={14} />
            Pastas para treinar
            {!loadingFolders && (
              <span className="text-xs font-normal text-gray-400">
                ({selectedFolders.size}/{subfolders.length} selecionadas)
              </span>
            )}
          </span>
          {showFolders ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        {showFolders && (
          <div className="p-2 space-y-1">
            {loadingFolders ? (
              <div className="flex items-center gap-2 px-2 py-1 text-xs text-gray-400">
                <Loader2 size={12} className="animate-spin" /> Carregando
                pastas...
              </div>
            ) : subfolders.length === 0 ? (
              <p className="text-xs text-gray-400 px-2 py-1">
                Nenhuma subpasta encontrada em materials/
              </p>
            ) : (
              <>
                <button
                  className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 px-2 py-0.5"
                  onClick={toggleAll}
                >
                  {allSelected ? (
                    <CheckSquare size={12} />
                  ) : (
                    <Square size={12} />
                  )}
                  {allSelected ? "Desmarcar todas" : "Selecionar todas"}
                </button>
                {subfolders.map((folder) => (
                  <label
                    key={folder.name}
                    className="flex items-center gap-2 px-2 py-1 rounded hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedFolders.has(folder.name)}
                      onChange={() => toggleFolder(folder.name)}
                      className="w-3.5 h-3.5 accent-blue-600"
                    />
                    <span className="text-sm text-gray-700 flex-1 truncate">
                      {folder.name}
                    </span>
                    <span className="text-xs text-gray-400 shrink-0">
                      {folder.file_count} arquivo
                      {folder.file_count !== 1 ? "s" : ""}
                    </span>
                  </label>
                ))}
              </>
            )}
          </div>
        )}
      </div>

      {/* Pipeline de processamento */}
      {isLoading && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-gray-600 mb-1">Pipeline:</p>
          {steps.map((step, i) => (
            <div key={step.id} className="flex items-start gap-2">
              <div className="mt-0.5 shrink-0">
                {step.status === "done" ? (
                  <div className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center">
                    <span className="text-white text-xs">✓</span>
                  </div>
                ) : step.status === "running" ? (
                  <Loader2
                    size={16}
                    className="animate-spin text-blue-500"
                  />
                ) : (
                  <div className="w-4 h-4 rounded-full border-2 border-gray-300" />
                )}
              </div>
              <div>
                <p
                  className={`text-xs font-medium ${
                    step.status === "done"
                      ? "text-green-700"
                      : step.status === "running"
                      ? "text-blue-700"
                      : "text-gray-400"
                  }`}
                >
                  {step.label}
                </p>
                <p className="text-xs text-gray-400">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Botão */}
      <Button
        onClick={handleReprocess}
        disabled={isLoading || selectedFolders.size === 0}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm"
      >
        {isLoading ? (
          <span className="flex items-center gap-2">
            <Loader2 size={14} className="animate-spin" />
            Processando...
          </span>
        ) : (
          "Iniciar Treinamento"
        )}
      </Button>

      {/* Mensagens */}
      {error && (
        <div className="flex items-start gap-1.5 text-xs text-red-600 bg-red-50 p-2 rounded">
          <AlertCircle size={13} className="mt-0.5 shrink-0" />
          {error}
        </div>
      )}
      {message && !isLoading && (
        <div className="text-xs text-green-700 bg-green-50 p-2 rounded">
          ✓ {message} O processo roda em background — pode levar vários
          minutos.
        </div>
      )}
    </div>
  );
};
