import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Cloud, AlertCircle } from 'lucide-react';
import { syncDriveMaterials, validateDriveCredentials } from '../../lib/drive';
import { motion } from 'framer-motion';

interface DriveSyncProps {
  onSync: () => void;
  isLoading?: boolean;
}

export const DriveSync: React.FC<DriveSyncProps> = ({ onSync, isLoading }) => {
  const [folderId, setFolderId] = useState('');
  const [credentials, setCredentials] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSync = async () => {
    try {
      setError(null);
      setIsSyncing(true);

      // Validate credentials format
      if (!validateDriveCredentials(credentials)) {
        throw new Error('Credenciais do Google Cloud inválidas');
      }

      // Validate folder ID format
      if (!folderId.match(/^[a-zA-Z0-9_-]+$/)) {
        throw new Error('ID da pasta do Drive inválido');
      }

      await syncDriveMaterials(folderId, credentials);
      onSync();
      
      // Clear form
      setFolderId('');
      setCredentials('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao sincronizar com o Drive');
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Sincronizar com Google Drive</h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ID da Pasta do Drive
          </label>
          <Input
            value={folderId}
            onChange={(e) => setFolderId(e.target.value)}
            placeholder="Ex: 1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ"
          />
          <p className="text-xs text-gray-500 mt-1">
            ID da pasta contendo os materiais de treino
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Credenciais do Google Cloud
          </label>
          <Textarea
            value={credentials}
            onChange={(e) => setCredentials(e.target.value)}
            placeholder="Cole aqui o conteúdo do arquivo credentials.json"
            rows={8}
            className="font-mono text-sm"
          />
          <p className="text-xs text-gray-500 mt-1">
            Credenciais obtidas do Console do Google Cloud
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

        <Button
          onClick={handleSync}
          disabled={!folderId || !credentials || isSyncing || isLoading}
          isLoading={isSyncing || isLoading}
          className="w-full flex items-center justify-center gap-2"
        >
          <Cloud size={18} />
          <span>Sincronizar Materiais</span>
        </Button>
      </div>
    </div>
  );
};