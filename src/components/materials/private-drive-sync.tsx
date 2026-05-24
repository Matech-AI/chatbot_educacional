import React, { useState, useEffect, useCallback } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { apiRequestJson } from "../../lib/api";
import {
  CheckCircle,
  AlertCircle,
  Link,
  Link2Off,
  Download,
  Loader2,
  ExternalLink,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface GoogleStatus {
  connected: boolean;
  google_email?: string;
  connected_at?: string;
}

interface SyncResult {
  status: string;
  message: string;
  statistics: {
    listed: number;
    downloaded: number;
    skipped: number;
    errors: number;
    files: Array<{ name: string; status?: string; error?: string }>;
  };
}

const REDIRECT_URI =
  typeof window !== "undefined"
    ? `${window.location.origin}/auth/google/callback`
    : "";

function extractFolderId(input: string): string {
  const match = input.match(/folders\/([a-zA-Z0-9_-]+)/);
  if (match) return match[1];
  if (/^[a-zA-Z0-9_-]{20,}$/.test(input.trim())) return input.trim();
  return input.trim();
}

export const PrivateDriveSync: React.FC<{ onSync: () => void }> = ({
  onSync,
}) => {
  const [status, setStatus] = useState<GoogleStatus | null>(null);
  const [folderInput, setFolderInput] = useState(
    () => localStorage.getItem("privateDriveFolderId") || ""
  );
  const [subfolder, setSubfolder] = useState("Drive Privado");
  const [isSyncing, setIsSyncing] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [result, setResult] = useState<SyncResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await apiRequestJson<GoogleStatus>("/auth/google/status");
      setStatus(data);
    } catch {
      setStatus({ connected: false });
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    const handler = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type === "GOOGLE_OAUTH_SUCCESS") {
        fetchStatus();
        setIsConnecting(false);
      } else if (event.data?.type === "GOOGLE_OAUTH_ERROR") {
        setError(event.data.error || "Erro ao conectar com Google.");
        setIsConnecting(false);
      }
    };
    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, [fetchStatus]);

  const handleConnect = async () => {
    setIsConnecting(true);
    setError(null);
    try {
      const data = await apiRequestJson<{ auth_url: string }>(
        `/auth/google?redirect_uri=${encodeURIComponent(REDIRECT_URI)}`
      );
      const w = 500;
      const h = 700;
      const left = Math.round(window.screenX + (window.outerWidth - w) / 2);
      const top = Math.round(window.screenY + (window.outerHeight - h) / 2);
      const popup = window.open(
        data.auth_url,
        "googleOAuth",
        `width=${w},height=${h},left=${left},top=${top},resizable=yes,scrollbars=yes`
      );
      if (!popup) {
        setError("Popup bloqueado pelo navegador. Permita popups para este site.");
        setIsConnecting(false);
      }
    } catch (err: any) {
      setError(err.message || "Erro ao iniciar conexão com Google.");
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm("Desconectar Drive pessoal?")) return;
    try {
      await apiRequestJson("/auth/google/disconnect", { method: "DELETE" });
      setStatus({ connected: false });
      setResult(null);
    } catch (err: any) {
      setError(err.message || "Erro ao desconectar.");
    }
  };

  const handleSync = async () => {
    if (!folderInput.trim()) {
      setError("Informe o ID ou URL da pasta do Google Drive.");
      return;
    }
    const folderId = extractFolderId(folderInput);
    localStorage.setItem("privateDriveFolderId", folderInput);
    setIsSyncing(true);
    setError(null);
    setResult(null);
    try {
      const data = await apiRequestJson<SyncResult>("/drive/private-sync", {
        method: "POST",
        body: JSON.stringify({ folder_id: folderId, subfolder, download_files: true }),
      });
      setResult(data);
      onSync();
    } catch (err: any) {
      setError(err.message || "Erro durante a sincronização.");
    } finally {
      setIsSyncing(false);
    }
  };

  if (!status) {
    return (
      <div className="flex items-center justify-center py-12 text-gray-500">
        <Loader2 className="animate-spin mr-2" size={20} />
        Verificando conexão...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Status card */}
      <div
        className={`rounded-xl border-2 p-5 flex items-start gap-4 ${
          status.connected
            ? "border-green-200 bg-green-50"
            : "border-gray-200 bg-gray-50"
        }`}
      >
        <div
          className={`mt-0.5 w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
            status.connected ? "bg-green-100" : "bg-gray-200"
          }`}
        >
          {status.connected ? (
            <CheckCircle size={22} className="text-green-600" />
          ) : (
            <Link2Off size={22} className="text-gray-500" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-900">
            {status.connected ? "Drive pessoal conectado" : "Drive pessoal não conectado"}
          </p>
          {status.connected && status.google_email && (
            <p className="text-sm text-gray-600 truncate">{status.google_email}</p>
          )}
          {!status.connected && (
            <p className="text-sm text-gray-500">
              Conecte sua conta Google para sincronizar pastas privadas.
            </p>
          )}
        </div>
        <div className="flex-shrink-0">
          {status.connected ? (
            <Button
              onClick={handleDisconnect}
              variant="outline"
              className="text-red-600 border-red-200 hover:bg-red-50 text-sm"
            >
              <Link2Off size={14} className="mr-1.5" />
              Desconectar
            </Button>
          ) : (
            <Button
              onClick={handleConnect}
              disabled={isConnecting}
              className="bg-blue-600 hover:bg-blue-700 text-white text-sm"
            >
              {isConnecting ? (
                <Loader2 size={14} className="animate-spin mr-1.5" />
              ) : (
                <Link size={14} className="mr-1.5" />
              )}
              Conectar Google
              <ExternalLink size={12} className="ml-1.5 opacity-70" />
            </Button>
          )}
        </div>
      </div>

      {/* Info box */}
      {!status.connected && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
          <p className="font-medium mb-1">Como funciona:</p>
          <ol className="list-decimal ml-4 space-y-1">
            <li>Clique em "Conectar Google" e autorize o acesso ao Drive.</li>
            <li>Informe o ID ou URL da pasta que deseja sincronizar.</li>
            <li>Os arquivos serão baixados para a biblioteca de materiais.</li>
          </ol>
        </div>
      )}

      {/* Sync form */}
      <AnimatePresence>
        {status.connected && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                ID ou URL da pasta do Drive
              </label>
              <Input
                value={folderInput}
                onChange={(e) => setFolderInput(e.target.value)}
                placeholder="https://drive.google.com/drive/folders/... ou ID direto"
                disabled={isSyncing}
              />
              <p className="text-xs text-gray-400 mt-1">
                Apenas arquivos da pasta raiz (sem subpastas). A pasta deve estar acessível pela sua conta.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Subpasta de destino (em Materiais)
              </label>
              <Input
                value={subfolder}
                onChange={(e) => setSubfolder(e.target.value)}
                placeholder="Drive Privado"
                disabled={isSyncing}
              />
            </div>

            <Button
              onClick={handleSync}
              disabled={isSyncing || !folderInput.trim()}
              className="w-full bg-red-600 hover:bg-red-700 text-white"
            >
              {isSyncing ? (
                <>
                  <Loader2 size={16} className="animate-spin mr-2" />
                  Sincronizando...
                </>
              ) : (
                <>
                  <Download size={16} className="mr-2" />
                  Sincronizar Drive Pessoal
                </>
              )}
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg p-4"
          >
            <AlertCircle size={18} className="text-red-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-red-700">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Result */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-green-50 border border-green-200 rounded-xl p-5 space-y-3"
          >
            <div className="flex items-center gap-2">
              <CheckCircle size={18} className="text-green-600" />
              <p className="font-medium text-green-800">{result.message}</p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Baixados", value: result.statistics.downloaded, color: "text-green-700" },
                { label: "Ignorados", value: result.statistics.skipped, color: "text-yellow-700" },
                { label: "Erros", value: result.statistics.errors, color: "text-red-700" },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-white rounded-lg p-3 text-center border border-green-100">
                  <p className={`text-xl font-bold ${color}`}>{value}</p>
                  <p className="text-xs text-gray-500">{label}</p>
                </div>
              ))}
            </div>

            {result.statistics.files.length > 0 && (
              <details className="text-sm">
                <summary className="cursor-pointer text-gray-600 font-medium">
                  Ver arquivos ({result.statistics.files.length})
                </summary>
                <ul className="mt-2 space-y-1 max-h-48 overflow-y-auto">
                  {result.statistics.files.map((f, i) => (
                    <li key={i} className="flex items-center gap-2 text-xs text-gray-600">
                      <span
                        className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          f.status === "downloaded"
                            ? "bg-green-500"
                            : f.status === "error"
                            ? "bg-red-500"
                            : "bg-yellow-400"
                        }`}
                      />
                      <span className="truncate">{f.name}</span>
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
