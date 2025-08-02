import React, { useEffect, useState, Suspense, lazy } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";

// ========================================
// IMPORTS ESSENCIAIS (carregados imediatamente)
// ========================================
import { useAuthStore } from "./store/auth-store";

// ========================================
// IMPORTS LAZY (carregados sob demanda) - CORRIGIDOS COM FALLBACKS
// ========================================
const AppLayout = lazy(() =>
  import("./components/layout/app-layout").catch(() =>
    import("./components/layout/app-layout").then((m) => ({
      default: m.AppLayout || m.default,
    }))
  )
);

const LoginPage = lazy(() =>
  import("./pages/login-page").catch(() =>
    import("./pages/login-page").then((m) => ({
      default: m.LoginPage || m.default,
    }))
  )
);

const AuthVerificationPage = lazy(() =>
  import("./pages/auth-verification-page").catch(() =>
    import("./pages/auth-verification-page").then((m) => ({
      default: m.AuthVerificationPage || m.default,
    }))
  )
);

const HomePage = lazy(() =>
  import("./pages/home-page").catch(() =>
    import("./pages/home-page").then((m) => ({
      default: m.HomePage || m.default,
    }))
  )
);

const ChatPage = lazy(() =>
  import("./pages/chat-page").catch(() =>
    import("./pages/chat-page").then((m) => ({
      default: m.ChatPage || m.default,
    }))
  )
);

const EnhancedChatPage = lazy(() =>
  import("./pages/enhanced-chat-page").catch(() =>
    import("./pages/enhanced-chat-page").then((m) => ({
      default: m.EnhancedChatPage || m.default,
    }))
  )
);

const MaterialsPage = lazy(() =>
  import("./pages/materials-page").catch(() =>
    import("./pages/materials-page").then((m) => ({
      default: m.MaterialsPage || m.default,
    }))
  )
);

const AssistantPage = lazy(() =>
  import("./pages/assistant-page").catch(() =>
    import("./pages/assistant-page").then((m) => ({
      default: m.AssistantPage || m.default,
    }))
  )
);

const ResetPasswordPage = lazy(() =>
  import("./pages/reset-password-page").catch(() =>
    import("./pages/reset-password-page").then((m) => ({
      default: m.ResetPasswordPage || m.default,
    }))
  )
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
      <p className="text-gray-600 mb-4">
        {typeof error === "object" ? String(error) : error}
      </p>
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
      // Garantir que a mensagem de erro seja uma string
      let errorMessage;
      if (this.state.error) {
        try {
          if (typeof this.state.error.message === "object") {
            // Usar String() em vez de JSON.stringify para evitar erros de estrutura circular
            errorMessage = String(this.state.error.message);
          } else {
            errorMessage =
              this.state.error.message || "Erro interno do componente";
          }
        } catch (e) {
          errorMessage = "Erro ao processar mensagem de erro";
          console.error("Erro ao processar mensagem de erro:", e);
        }
      } else {
        errorMessage = "Erro interno do componente";
      }

      return (
        <ErrorFallback
          error={errorMessage}
          onRetry={() => this.setState({ hasError: false, error: undefined })}
        />
      );
    }

    return this.props.children;
  }
}

// ========================================
// PROTECTED ROUTE
// ========================================
// Componente base que não usa hooks do router
const ProtectedRouteBase: React.FC<{
  children: React.ReactNode;
  allowedRoles?: string[];
  currentPath?: string;
}> = ({ children, allowedRoles, currentPath }) => {
  const { isAuthenticated, user } = useAuthStore();

  console.log("ProtectedRouteBase - currentPath:", currentPath);
  console.log("ProtectedRouteBase - user.role:", user?.role);
  console.log("ProtectedRouteBase - allowedRoles:", allowedRoles);
  console.log("ProtectedRouteBase - isAuthenticated:", isAuthenticated);

  if (!isAuthenticated) {
    console.log("ProtectedRouteBase - Not authenticated, redirecting to /login");
    return <Navigate to="/login" replace />;
  }

  // Verificação adicional para estudantes
  if (user && user.role === "student" && currentPath) {
    const allowedStudentPaths = ["/", "/chat"];

    console.log("ProtectedRouteBase - Student check - allowedStudentPaths:", allowedStudentPaths);
    console.log("ProtectedRouteBase - Student check - is path allowed:", allowedStudentPaths.some(
      (path) => currentPath === path || currentPath.startsWith(path + "/")
    ));

    // Se o caminho atual não estiver na lista de permitidos para estudantes
    if (
      !allowedStudentPaths.some(
        (path) => currentPath === path || currentPath.startsWith(path + "/")
      )
    ) {
      console.log("ProtectedRouteBase - Student not allowed, redirecting to /");
      return <Navigate to="/" replace />;
    }
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    console.log("ProtectedRouteBase - User role not in allowedRoles, redirecting to /");
    return <Navigate to="/" replace />;
  }

  console.log("ProtectedRouteBase - Access granted");
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <ErrorBoundary>{children}</ErrorBoundary>
    </Suspense>
  );
};

// Wrapper que usa o hook useLocation e passa o valor para o componente base
const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  allowedRoles?: string[];
}> = (props) => {
  // Este hook só será chamado quando o componente for renderizado dentro do Router
  try {
    const location = useLocation();
    return <ProtectedRouteBase {...props} currentPath={location.pathname} />;
  } catch (error) {
    // Fallback para quando o hook não pode ser usado (durante renderização inicial)
    return <ProtectedRouteBase {...props} />;
  }
};

// ========================================
// PÁGINAS SIMPLES INLINE
// ========================================
// Settings page now lazy loaded
const SettingsPage = lazy(() =>
  import("./pages/settings-page").catch(() =>
    import("./pages/settings-page").then((m) => ({
      default: m.SettingsPage || m.default,
    }))
  )
);

const UserManagementPage = lazy(() =>
  import("./pages/user-management-page").catch(() =>
    import("./pages/user-management-page").then((m) => ({
      default: m.UserManagementPage || m.default,
    }))
  )
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

  useEffect(() => {
    const initializeAuth = () => {
      try {
        console.log("🚀 DNA da Força - Iniciando verificação de autenticação");
        checkAuth();
        setIsInitialized(true);
        console.log("✅ Autenticação verificada");
      } catch (error) {
        console.error("❌ Erro na inicialização:", error);
        setIsInitialized(true);
      }
    };

    initializeAuth();
  }, [checkAuth]);

  if (!isInitialized) {
    return <LoadingSpinner message="Verificando autenticação..." />;
  }

  return (
    <BrowserRouter>
      <ErrorBoundary>
        <Routes>
          <Route
            path="/login"
            element={
              <Suspense
                fallback={<LoadingSpinner message="Carregando login..." />}
              >
                <LoginPage />
              </Suspense>
            }
          />

          <Route
            path="/verify-account"
            element={
              <Suspense
                fallback={
                  <LoadingSpinner message="Carregando verificação..." />
                }
              >
                <AuthVerificationPage />
              </Suspense>
            }
          />

          <Route
            path="/reset-password"
            element={
              <Suspense
                fallback={
                  <LoadingSpinner message="Carregando redefinição de senha..." />
                }
              >
                <ResetPasswordPage />
              </Suspense>
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
                <Suspense
                  fallback={
                    <LoadingSpinner message="Carregando dashboard..." />
                  }
                >
                  <HomePage />
                </Suspense>
              }
            />

            <Route
              path="chat"
              element={
                <Suspense
                  fallback={<LoadingSpinner message="Carregando chat..." />}
                >
                  <EnhancedChatPage />
                </Suspense>
              }
            />

            <Route
              path="chat/classic"
              element={
                <Suspense
                  fallback={
                    <LoadingSpinner message="Carregando chat clássico..." />
                  }
                >
                  <ChatPage />
                </Suspense>
              }
            />

            <Route
              path="materials"
              element={
                <ProtectedRoute allowedRoles={["admin", "instructor"]}>
                  <Suspense
                    fallback={
                      <LoadingSpinner message="Carregando materiais..." />
                    }
                  >
                    <MaterialsPage />
                  </Suspense>
                </ProtectedRoute>
              }
            />

            <Route
              path="assistant"
              element={
                <ProtectedRoute allowedRoles={["admin", "instructor"]}>
                  <Suspense
                    fallback={
                      <LoadingSpinner message="Carregando assistente..." />
                    }
                  >
                    <AssistantPage />
                  </Suspense>
                </ProtectedRoute>
              }
            />

            <Route
              path="settings"
              element={
                <ProtectedRoute allowedRoles={["admin"]}>
                  <Suspense
                    fallback={
                      <LoadingSpinner message="Carregando configurações..." />
                    }
                  >
                    <SettingsPage />
                  </Suspense>
                </ProtectedRoute>
              }
            />

            <Route
              path="users"
              element={
                <ProtectedRoute allowedRoles={["admin"]}>
                  <Suspense
                    fallback={
                      <LoadingSpinner message="Carregando gerenciamento de usuários..." />
                    }
                  >
                    <UserManagementPage />
                  </Suspense>
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
