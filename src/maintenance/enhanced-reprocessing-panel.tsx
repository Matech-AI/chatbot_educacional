import React, { useState } from "react";
import { Button } from "../components/ui/button";
import { BrainCircuit } from "lucide-react";
import { ragApiRequestJson } from "../lib/api";

interface EnhancedReprocessingPanelProps {
  onSuccess?: () => void;
}

export const EnhancedReprocessingPanel: React.FC<
  EnhancedReprocessingPanelProps
> = ({ onSuccess }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleReprocess = async () => {
    if (
      !window.confirm(
        "Isso irá reprocessar todos os materiais com o sistema RAG aprimorado. Esta operação pode ser demorada e consumir muitos recursos. Deseja continuar?"
      )
    ) {
      return;
    }

    setIsLoading(true);
    setError(null);
    setMessage(null);

    try {
      const result = await ragApiRequestJson(
        "/reprocess-enhanced-materials",
        {
          method: "POST",
        }
      );

      setMessage(
        result.message || "Reprocessamento aprimorado iniciado com sucesso!"
      );
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Ocorreu um erro desconhecido."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border-2 border-blue-300 bg-blue-50 p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center text-white">
          <BrainCircuit size={20} />
        </div>
        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
          Aprimorado
        </span>
      </div>

      <h3 className="font-semibold text-gray-900 mb-2">
        Reprocessamento Inteligente (RAG)
      </h3>
      <p className="text-sm text-gray-600 mb-4">
        Utiliza o novo sistema RAG para extrair metadados educacionais, como
        conceitos-chave, nível de dificuldade e resumos.
      </p>

      <Button
        onClick={handleReprocess}
        disabled={isLoading}
        isLoading={isLoading}
        variant="default"
        className="w-full bg-blue-600 hover:bg-blue-700"
      >
        {isLoading ? "Reprocessando..." : "Iniciar Reprocessamento Inteligente"}
      </Button>

      {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
      {message && <p className="text-sm text-green-600 mt-2">{message}</p>}
    </div>
  );
};