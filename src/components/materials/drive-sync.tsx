import React, { useState } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Cloud, AlertCircle, CheckCircle } from "lucide-react";
import { motion } from "framer-motion";
import {
  processDriveMaterials,
  validateDriveFolderId,
  extractFolderIdFromUrl,
} from "../../lib/materials-processor";

interface DriveSyncProps {
  onSync: () => void;
  isLoading: boolean;
}

export const DriveSync: React.FC<DriveSyncProps> = ({ onSync, isLoading }) => {
  const [folderInput, setFolderInput] = useState(
    "1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ"
  );
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSync = async () => {
    try {
      setError(null);
      setSuccess(null);
      setIsProcessing(true);

      // Extract folder ID from input (handles URLs and IDs)
      const folderId =
        extractFolderIdFromUrl(folderInput.trim()) || folderInput.trim();

      // Validate folder ID
      if (!folderId) {
        setError("ID da pasta é obrigatório");
        return;
      }

      if (!validateDriveFolderId(folderId)) {
        setError("Formato do ID da pasta inválido");
        return;
      }

      console.log("Sincronizando pasta:", folderId);

      // Process Drive materials
      const files = await processDriveMaterials(folderId);

      setSuccess(`✅ ${files.length} arquivos processados com sucesso!`);

      // Call onSync to refresh materials list
      setTimeout(() => {
        onSync();
        setSuccess(null);
      }, 2000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Erro desconhecido ao sincronizar";
      setError(errorMessage);
      console.error("Erro na sincronização:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setSuccess(null);
    setFolderInput(e.target.value);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
      <h2 className="text-lg font-semibold mb-4">
        Sincronizar com Google Drive
      </h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ID ou URL da Pasta do Google Drive
          </label>
          <Input
            value={folderInput}
            onChange={handleInputChange}
            placeholder="Ex: 1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ ou URL completa"
            disabled={isProcessing || isLoading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Cole o ID da pasta ou a URL completa do Google Drive
          </p>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 border border-red-200 rounded-md p-3 flex items-start gap-2"
          >
            <AlertCircle
              size={16}
              className="text-red-600 mt-0.5 flex-shrink-0"
            />
            <div>
              <p className="text-sm text-red-600 font-medium">
                Erro na sincronização
              </p>
              <p className="text-sm text-red-500 mt-1">{error}</p>
            </div>
          </motion.div>
        )}

        {success && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-green-50 border border-green-200 rounded-md p-3 flex items-start gap-2"
          >
            <CheckCircle
              size={16}
              className="text-green-600 mt-0.5 flex-shrink-0"
            />
            <div>
              <p className="text-sm text-green-600 font-medium">
                Sincronização concluída
              </p>
              <p className="text-sm text-green-600 mt-1">{success}</p>
            </div>
          </motion.div>
        )}

        <Button
          onClick={handleSync}
          disabled={!folderInput.trim() || isLoading || isProcessing}
          isLoading={isProcessing}
          className="w-full flex items-center justify-center gap-2"
        >
          <Cloud size={18} />
          <span>
            {isProcessing ? "Sincronizando..." : "Sincronizar Materiais"}
          </span>
        </Button>

        <div className="text-xs text-gray-500 space-y-1">
          <p>
            <strong>Como obter o ID da pasta:</strong>
          </p>
          <ol className="list-decimal list-inside space-y-1 ml-2">
            <li>Abra a pasta no Google Drive</li>
            <li>Copie o ID da URL (após /folders/)</li>
            <li>Ou cole a URL completa aqui</li>
          </ol>
        </div>
      </div>
    </div>
  );
};
