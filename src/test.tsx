import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom";

// TIPOS
interface User {
  username: string;
  role: string;
}

interface Material {
  id: string;
  title: string;
  description: string;
  type: string;
  size: number;
  uploadedAt: string;
  uploadedBy: string;
  tags: string[];
}

// UTILITÁRIOS
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// COMPONENTE LOGIN
const LoginPage: React.FC = () => {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("username", username);
      formData.append("password", password);

      const response = await fetch("/api/token", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("token", data.access_token);
        localStorage.setItem(
          "user",
          JSON.stringify({
            username,
            role:
              username === "admin"
                ? "admin"
                : username === "instrutor"
                ? "instructor"
                : "student",
          })
        );
        window.location.href = "/dashboard";
      } else {
        const errorData = await response.json().catch(() => ({}));
        setError(errorData.detail || "Credenciais inválidas");
      }
    } catch (err) {
      setError("Erro de conexão");
    } finally {
      setIsLoading(false);
    }
  };

  const quickLogin = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-red-600 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-2xl p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-white font-bold text-2xl">💪</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">DNA da Força</h1>
          <p className="text-gray-600 mt-2">v1.1 - Com Upload</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Usuário
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Senha
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm font-medium text-gray-700 mb-3">
            🚀 Login Rápido:
          </p>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => quickLogin("admin", "admin123")}
              className="text-xs bg-red-100 text-red-800 py-2 px-3 rounded"
            >
              Admin
            </button>
            <button
              onClick={() => quickLogin("instrutor", "instrutor123")}
              className="text-xs bg-green-100 text-green-800 py-2 px-3 rounded"
            >
              Instrutor
            </button>
            <button
              onClick={() => quickLogin("aluno", "aluno123")}
              className="text-xs bg-blue-100 text-blue-800 py-2 px-3 rounded"
            >
              Aluno
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// COMPONENTE DASHBOARD
const DashboardPage: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [backendStatus, setBackendStatus] = useState("Verificando...");

  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) setUser(JSON.parse(userData));
    testBackend();
  }, []);

  const testBackend = async () => {
    try {
      const response = await fetch("/api/health");
      if (response.ok) {
        const data = await response.json();
        setBackendStatus(`✅ ${data.message}`);
      } else {
        setBackendStatus("❌ Backend com problemas");
      }
    } catch (error) {
      setBackendStatus("❌ Backend offline");
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-red-600 rounded flex items-center justify-center">
                <span className="text-white font-bold">💪</span>
              </div>
              <h1 className="text-xl font-semibold">DNA da Força</h1>
              <span className="text-sm text-gray-500">v1.1</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm">
                <strong>{user?.username}</strong> ({user?.role})
              </span>
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            🎉 Sistema v1.1 Funcionando!
          </h2>
          <p className="text-gray-600 mb-8">
            Evolução gradual - Upload de materiais adicionado
          </p>

          {/* Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                🔐 Auth
              </h3>
              <p className="text-green-600 font-medium">✅ JWT Ativo</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                🔗 Backend
              </h3>
              <p className="text-sm font-medium">{backendStatus}</p>
              <button
                onClick={testBackend}
                className="text-blue-600 text-xs hover:text-blue-800 mt-1"
              >
                Testar
              </button>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                📁 Upload
              </h3>
              <p className="text-blue-600 font-medium">✅ Ativo</p>
            </div>
          </div>

          {/* Navigation */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Link
              to="/chat"
              className="block p-6 bg-white rounded-lg shadow hover:shadow-md border-l-4 border-blue-500"
            >
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                💬 Chat Expandido
              </h3>
              <p className="text-gray-600 text-sm">
                Respostas detalhadas sobre treino, nutrição, recuperação
              </p>
              <div className="mt-3 text-blue-600 text-sm font-medium">
                Acessar Chat →
              </div>
            </Link>

            <Link
              to="/materials"
              className="block p-6 bg-white rounded-lg shadow hover:shadow-md border-l-4 border-green-500"
            >
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                📚 Materiais
              </h3>
              <p className="text-gray-600 text-sm">
                Upload, download e gerenciamento de materiais
              </p>
              <div className="mt-3 text-green-600 text-sm font-medium">
                Gerenciar Materiais →
              </div>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
};

// COMPONENTE MATERIAIS
const MaterialsPage: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDescription, setUploadDescription] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) setUser(JSON.parse(userData));
    loadMaterials();
  }, []);

  const loadMaterials = async () => {
    try {
      const response = await fetch("/api/materials", {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (response.ok) {
        const data = await response.json();
        setMaterials(data);
      }
    } catch (error) {
      console.error("Erro ao carregar materiais:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("description", uploadDescription);

      const response = await fetch("/api/materials/upload", {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: formData,
      });

      if (response.ok) {
        setMessage(`✅ Upload realizado: ${uploadFile.name}`);
        setUploadFile(null);
        setUploadDescription("");
        loadMaterials();
      } else {
        const error = await response.json();
        setMessage(`❌ Erro: ${error.detail}`);
      }
    } catch (error) {
      setMessage("❌ Erro de conexão");
    } finally {
      setIsUploading(false);
    }
  };

  const canUpload = user?.role === "admin" || user?.role === "instructor";

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link
                to="/dashboard"
                className="text-blue-600 hover:text-blue-800"
              >
                ← Voltar
              </Link>
              <h1 className="text-xl font-semibold">📚 Materiais</h1>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-6">
        {/* Upload Form */}
        {canUpload && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">
              📤 Upload de Material
            </h2>
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Arquivo
                </label>
                <input
                  type="file"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  accept=".pdf,.docx,.txt,.mp4,.avi,.mov,.pptx"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Descrição
                </label>
                <textarea
                  value={uploadDescription}
                  onChange={(e) => setUploadDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={3}
                />
              </div>
              <button
                type="submit"
                disabled={!uploadFile || isUploading}
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isUploading ? "Fazendo upload..." : "Fazer Upload"}
              </button>
            </form>
            {message && (
              <div className="mt-4 p-3 bg-gray-50 rounded-md">
                <p className="text-sm">{message}</p>
              </div>
            )}
          </div>
        )}

        {/* Materials List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold">
              📋 Lista de Materiais ({materials.length})
            </h2>
          </div>

          {isLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Carregando...</p>
            </div>
          ) : (
            <div className="divide-y">
              {materials.map((material) => (
                <div key={material.id} className="p-6 hover:bg-gray-50">
                  <div className="flex justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium">{material.title}</h3>
                      <p className="text-gray-600 text-sm">
                        {material.description}
                      </p>
                      <div className="flex items-center space-x-4 text-xs text-gray-500 mt-2">
                        <span>📄 {material.type.toUpperCase()}</span>
                        <span>📊 {formatFileSize(material.size)}</span>
                        <span>📅 {formatDate(material.uploadedAt)}</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <a
                        href={`/api/materials/${material.id}`}
                        target="_blank"
                        className="bg-blue-600 text-white px-3 py-1 rounded text-xs"
                      >
                        Download
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// COMPONENTE CHAT
const ChatPage: React.FC = () => {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<
    Array<{ role: string; content: string }>
  >([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = { role: "user", content: message };
    setMessages((prev) => [...prev, userMessage]);
    setMessage("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ content: message }),
      });

      if (response.ok) {
        const data = await response.json();
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.answer },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Erro ao processar" },
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Erro de conexão" },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickQuestions = [
    "O que é treinamento de força?",
    "Como fazer periodização?",
    "Qual a importância da nutrição?",
    "Como otimizar a recuperação?",
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link to="/dashboard" className="text-blue-600">
                ← Voltar
              </Link>
              <h1 className="text-xl font-semibold">💬 Chat v1.1</h1>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto p-6">
        {/* Quick Questions */}
        {messages.length === 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">🚀 Perguntas Rápidas</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {quickQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => setMessage(q)}
                  className="text-left p-3 border rounded hover:bg-blue-50 text-sm"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="h-96 overflow-y-auto p-6">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 mt-8">
                <h3 className="text-lg font-medium mb-2">
                  Assistente DNA da Força v1.1
                </h3>
                <p>
                  Respostas expandidas sobre treino, nutrição, recuperação,
                  força, hipertrofia
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`mb-4 ${
                    msg.role === "user" ? "text-right" : "text-left"
                  }`}
                >
                  <div
                    className={`inline-block p-4 rounded-lg max-w-md ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-200"
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="text-left">
                <div className="inline-block p-4 rounded-lg bg-gray-200">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex space-x-3">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Digite sua pergunta..."
              className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !message.trim()}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg disabled:opacity-50"
            >
              Enviar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// PROTEÇÃO
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const token = localStorage.getItem("token");
  if (!token) return <Navigate to="/" replace />;
  return <>{children}</>;
};

// APP PRINCIPAL
function App() {
  console.log("🚀 DNA da Força Frontend v1.1");
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/materials"
          element={
            <ProtectedRoute>
              <MaterialsPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
