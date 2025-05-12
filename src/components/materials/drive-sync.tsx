import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Cloud, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { processDriveMaterials } from '../../lib/materials-processor';

interface DriveSyncProps {
  onSync: () => void;
  isLoading: boolean;
}

export const DriveSync: React.FC<DriveSyncProps> = ({ onSync, isLoading }) => {
  const [folderId, setFolderId] = useState('1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ');
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<string>('');

  const handleSync = async () => {
    try {
      setError(null);
      setProgress('Conectando ao Google Drive...');

      // Validate folder ID
      if (!folderId.trim()) {
        setError('ID da pasta é obrigatório');
        return;
      }

      setProgress('Processando arquivos...');
      const files = await processDriveMaterials(folderId);
      
      setProgress(`Processados ${files.length} arquivos com sucesso!`);
      console.log(`Successfully processed ${files.length} files`);
      
      onSync();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao sincronizar');
      setProgress('');
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Sincronizar com Google Drive</h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ID da Pasta
          </label>
          <Input
            value={folderId}
            onChange={(e) => {
              setError(null);
              setFolderId(e.target.value);
            }}
            placeholder="Ex: 1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ"
          />
          <p className="mt-1 text-xs text-gray-500">
            ID da pasta do Google Drive contendo os materiais
          </p>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 border border-red-200 rounded-md p-3 flex items-start gap-2"
          >
            <AlertCircle size={16} className="text-red-600 mt-0.5" />
            <p className="text-sm text-red-600">{error}</p>
          </motion.div>
        )}

        {progress && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <p className="text-sm text-blue-600">{progress}</p>
          </div>
        )}

        <Button
          onClick={handleSync}
          disabled={!folderId || isLoading}
          isLoading={isLoading}
          className="w-full flex items-center justify-center gap-2"
        >
          <Cloud size={18} />
          <span>Sincronizar Materiais</span>
        </Button>
      </div>
    </div>
  );
};