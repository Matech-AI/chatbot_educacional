import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Cloud, AlertCircle, HelpCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { validateDriveCredentials } from '../../lib/drive';

interface DriveSyncProps {
  onSync: () => void;
  isLoading: boolean;
}

export const DriveSync: React.FC<DriveSyncProps> = ({ onSync, isLoading }) => {
  const [folderId, setFolderId] = useState('');
  const [credentials, setCredentials] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSync = async () => {
    try {
      setError(null);

      // Validate folder ID
      if (!folderId.trim()) {
        setError('ID da pasta é obrigatório');
        return;
      }

      // Validate credentials
      if (!credentials.trim()) {
        setError('Credenciais são obrigatórias');
        return;
      }

      // Validate credentials format
      if (!validateDriveCredentials(credentials)) {
        setError('Formato de credenciais inválido');
        return;
      }

      onSync();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao sincronizar');
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Sincronizar com Google Drive</h2>
        <a
          href="https://console.cloud.google.com/apis/credentials"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1"
        >
          <HelpCircle size={14} />
          <span>Ajuda</span>
        </a>
      </div>

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

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Credenciais do Google Cloud
          </label>
          <Textarea
            value={credentials}
            onChange={(e) => {
              setError(null);
              setCredentials(e.target.value);
            }}
            placeholder="Cole o conteúdo do arquivo credentials.json"
            rows={8}
            className="font-mono text-sm"
          />
          <p className="mt-1 text-xs text-gray-500">
            Obtenha suas credenciais no Console do Google Cloud
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
          disabled={!folderId || !credentials || isLoading}
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