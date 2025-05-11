import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Cloud, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { useMaterialsStore } from '../../store/materials-store';

interface DriveSyncProps {
  onSync: () => void;
}

export const DriveSync: React.FC<DriveSyncProps> = ({ onSync }) => {
  const { syncWithDrive, isProcessing, error } = useMaterialsStore();
  const [folderId, setFolderId] = useState('');
  const [credentials, setCredentials] = useState('');

  const handleSync = async () => {
    if (await syncWithDrive(folderId, credentials)) {
      setFolderId('');
      setCredentials('');
      onSync();
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
            onChange={(e) => setFolderId(e.target.value)}
            placeholder="Ex: 1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Credenciais do Google Cloud
          </label>
          <Textarea
            value={credentials}
            onChange={(e) => setCredentials(e.target.value)}
            placeholder="Cole o conteúdo do arquivo credentials.json"
            rows={8}
            className="font-mono text-sm"
          />
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
          disabled={!folderId || !credentials || isProcessing}
          isLoading={isProcessing}
          className="w-full flex items-center justify-center gap-2"
        >
          <Cloud size={18} />
          <span>Sincronizar Materiais</span>
        </Button>
      </div>
    </div>
  );
};