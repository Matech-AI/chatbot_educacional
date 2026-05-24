import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { apiRequestJson } from "../lib/api";

const REDIRECT_URI =
  typeof window !== "undefined"
    ? `${window.location.origin}/auth/google/callback`
    : "";

const GoogleCallbackPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState("Conectando ao Google Drive...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    const errorParam = searchParams.get("error");

    const notifyAndClose = (type: string, payload?: Record<string, string>) => {
      if (window.opener) {
        window.opener.postMessage({ type, ...payload }, window.location.origin);
        window.close();
      } else {
        setTimeout(() => navigate("/materials?tab=private-drive"), 2000);
      }
    };

    if (errorParam) {
      setError(`Autorização negada: ${errorParam}`);
      setTimeout(() => notifyAndClose("GOOGLE_OAUTH_ERROR", { error: `Autorização negada: ${errorParam}` }), 2000);
      return;
    }

    if (!code) {
      setError("Código de autorização não encontrado.");
      setTimeout(() => notifyAndClose("GOOGLE_OAUTH_ERROR", { error: "Código de autorização não encontrado." }), 2000);
      return;
    }

    apiRequestJson("/auth/google/exchange", {
      method: "POST",
      body: JSON.stringify({ code, redirect_uri: REDIRECT_URI }),
    })
      .then((data: any) => {
        setMessage(data.message || "Drive conectado com sucesso!");
        setTimeout(() => notifyAndClose("GOOGLE_OAUTH_SUCCESS"), 1500);
      })
      .catch((err: Error) => {
        setError(err.message || "Erro ao conectar Drive.");
        setTimeout(() => notifyAndClose("GOOGLE_OAUTH_ERROR", { error: err.message || "Erro ao conectar Drive." }), 2000);
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
        {error ? (
          <>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-red-600 text-2xl">✕</span>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Erro</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <p className="text-sm text-gray-400">Redirecionando...</p>
          </>
        ) : (
          <>
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
              <span className="text-2xl">🔗</span>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Google Drive
            </h2>
            <p className="text-gray-600">{message}</p>
          </>
        )}
      </div>
    </div>
  );
};

export default GoogleCallbackPage;
