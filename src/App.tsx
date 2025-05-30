import React, { useEffect, useState, Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

// ========================================
// IMPORTS ESSENCIAIS (carregados imediatamente)
// ========================================
import { useAuthStore } from "./store/auth-store";

// ========================================
// IMPORTS LAZY (carregados sob demanda)
// ========================================
const AppLayout = lazy(() =>
  import("./components/layout/app-layout").then((module) => ({
    default: module.AppLayout,
  }))
);
const LoginPage = lazy(() =>
  import("./pages/login-page").then((module) => ({ default: module.LoginPage }))
);
const HomePage = lazy(() =>
  import("./pages/home-page").then((module) => ({ default: module.HomePage }))
);
const ChatPage = lazy(() =>
  import("./pages/chat-page").then((module) => ({ default: module.ChatPage }))
);
const MaterialsPage = lazy(() =>
  import("./pages/materials-page").then((module) => ({
    default: module.MaterialsPage,
  }))
);
const AssistantPage = lazy(() =>
  import("./pages/assistant-page").then((module) => ({
    default: module.AssistantPage,
  }))
);

// ========================================
// COMPONENTE DE LOADING
// ========================================
const LoadingSpinner: React.FC<{ message?: string }> = ({
  message = "Carregando...",
}) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-red-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <h1 className="text-xl font-semibold text-gray-900 mb-2">DNA da Força</h1>
      <p className="text-gray-600">{message}</p>
    </div>
  </div>
);

// ========================================
// COMPONENTE DE ERRO
// ========================================
const ErrorFallback: React.FC<{ error?: string; onRetry?: () => void }> = ({
  error = "Erro ao carregar componente",
  onRetry,
}) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <span className="text-red-600 text-2xl">⚠️</span>
      </div>
      <h1 className="text-xl font-semibold text-gray-900 mb-2">
        Ops! Algo deu errado
      </h1>
      <p className="text-gray-600 mb-4">{error}</p>
      <div className="space-y-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700"
          >
            Tentar novamente
          </button>
        )}
        <button
          onClick={() => {
            localStorage.clear();
            window.location.href = "/login";
          }}
          className="w-full bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700"
        >
          Reiniciar aplicação
        </button>
      </div>
    </div>
  </div>
);

// ========================================
// WRAPPER PARA LAZY COMPONENTS
// ========================================
const LazyWrapper: React.FC<{
  children: React.ReactNode;
  fallback?: React.ReactNode;
}> = ({ children, fallback }) => (
  <Suspense fallback={fallback || <LoadingSpinner />}>
    <ErrorBoundary>{children}</ErrorBoundary>
  </Suspense>
);

// ========================================
// ERROR BOUNDARY CLASS
// ========================================
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("❌ Error Boundary capturou erro:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorFallback
          error={this.state.error?.message || "Erro interno do componente"}
          onRetry={() => this.setState({ hasError: false, error: undefined })}
        />
      );
    }

    return this.props.children;
  }
}

// ========================================
// PROTECTED ROUTE COM VERIFICAÇÕES
// ========================================
const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  allowedRoles?: string[];
}> = ({ children, allowedRoles }) => {
  const { isAuthenticated, user } = useAuthStore();

  console.log("🔐 ProtectedRoute check:", {
    isAuthenticated,
    userRole: user?.role,
    allowedRoles,
    hasUser: !!user,
  });

  // Check if user is authenticated
  if (!isAuthenticated) {
    console.log("❌ User not authenticated, redirecting to login");
    return <Navigate to="/login" replace />;
  }

  // Check if user has required role
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    console.log("❌ User role not allowed, redirecting to home");
    return <Navigate to="/" replace />;
  }

  console.log("✅ Access granted");
  return <LazyWrapper>{children}</LazyWrapper>;
};

// ========================================
// PÁGINAS SIMPLES INLINE (fallback)
// ========================================
const SimpleSettingsPage: React.FC = () => (
  <div className="p-6 max-w-4xl mx-auto">
    <h1 className="text-2xl font-bold text-gray-900 mb-4">⚙️ Configurações</h1>
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <p className="text-gray-600 mb-4">🚧 Página em construção</p>
      <div className="space-y-2 text-sm text-gray-600">
        <p>• Configurar parâmetros do sistema</p>
        <p>• Gerenciar usuários</p>
        <p>• Definir permissões</p>
      </div>
    </div>
  </div>
);

const SimpleDebugPage: React.FC = () => {
  const { user, isAuthenticated } = useAuthStore();

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">🔍 Debug</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="font-semibold mb-2">👤 Usuário</h2>
          <div className="text-sm space-y-1">
            <p>
              <strong>Autenticado:</strong> {isAuthenticated ? "✅" : "❌"}
            </p>
            <p>
              <strong>Nome:</strong> {user?.name || "N/A"}
            </p>
            <p>
              <strong>Role:</strong> {user?.role || "N/A"}
            </p>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="font-semibold mb-2">💾 Storage</h2>
          <div className="text-sm space-y-1">
            <p>
              <strong>Token:</strong>{" "}
              {localStorage.getItem("token") ? "✅" : "❌"}
            </p>
            <p>
              <strong>User Data:</strong>{" "}
              {localStorage.getItem("user") ? "✅" : "❌"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ========================================
// APP PRINCIPAL
// ========================================
function App() {
  const { checkAuth, isAuthenticated } = useAuthStore();
  const [isInitialized, setIsInitialized] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);

  // Verificação de autenticação controlada
  useEffect(() => {
    let mounted = true;

    const initializeAuth = async () => {
      try {
        console.log("🚀 DNA da Força - Iniciando verificação de autenticação");

        // Prevenir múltiplas inicializações
        if (isInitialized) {
          return;
        }

        checkAuth();

        if (mounted) {
          setIsInitialized(true);
          console.log("✅ Autenticação verificada");
        }
      } catch (error) {
        console.error("❌ Erro na inicialização:", error);
        if (mounted) {
          setInitError(
            error instanceof Error ? error.message : "Erro desconhecido"
          );
          setIsInitialized(true);
        }
      }
    };

    // ✅ Usar setTimeout para evitar chamadas síncronas que podem causar loops
    const timeoutId = setTimeout(initializeAuth, 0);

    return () => {
      mounted = false;
      clearTimeout(timeoutId);
    };
  }, []); // ✅ Sem dependências - executar apenas uma vez

  // Mostrar loading enquanto inicializa
  if (!isInitialized) {
    return <LoadingSpinner message="Verificando autenticação..." />;
  }

  // Mostrar erro se houve problema na inicialização
  if (initError) {
    return (
      <ErrorFallback
        error={`Erro na inicialização: ${initError}`}
        onRetry={() => {
          setInitError(null);
          setIsInitialized(false);
        }}
      />
    );
  }

  console.log("🎯 Renderizando App - Autenticado:", isAuthenticated);

  return (
    <BrowserRouter>
      <ErrorBoundary>
        <Routes>
          <Route
            path="/login"
            element={
              <LazyWrapper
                fallback={<LoadingSpinner message="Carregando login..." />}
              >
                <LoginPage />
              </LazyWrapper>
            }
          />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route
              index
              element={
                <LazyWrapper
                  fallback={
                    <LoadingSpinner message="Carregando dashboard..." />
                  }
                >
                  <HomePage />
                </LazyWrapper>
              }
            />

            <Route
              path="chat"
              element={
                <LazyWrapper
                  fallback={<LoadingSpinner message="Carregando chat..." />}
                >
                  <ChatPage />
                </LazyWrapper>
              }
            />

            <Route
              path="materials"
              element={
                <ProtectedRoute allowedRoles={["admin", "instructor"]}>
                  <LazyWrapper
                    fallback={
                      <LoadingSpinner message="Carregando materiais..." />
                    }
                  >
                    <MaterialsPage />
                  </LazyWrapper>
                </ProtectedRoute>
              }
            />

            <Route
              path="assistant"
              element={
                <ProtectedRoute allowedRoles={["admin", "instructor"]}>
                  <LazyWrapper
                    fallback={
                      <LoadingSpinner message="Carregando assistente..." />
                    }
                  >
                    <AssistantPage />
                  </LazyWrapper>
                </ProtectedRoute>
              }
            />

            <Route
              path="settings"
              element={
                <ProtectedRoute allowedRoles={["admin"]}>
                  <SimpleSettingsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="debug"
              element={
                <ProtectedRoute allowedRoles={["admin"]}>
                  <SimpleDebugPage />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* Redirect unknown routes */}
          <Route
            path="*"
            element={
              isAuthenticated ? (
                <Navigate to="/" replace />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
        </Routes>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
