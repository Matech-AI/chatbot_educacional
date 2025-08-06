import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/auth-store";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { User, Lock, Dumbbell, Eye, EyeOff } from "lucide-react";
import { motion } from "framer-motion";

interface ChangePasswordModalProps {
  onClose: () => void;
  isTemporary?: boolean;
}

const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({
  onClose,
  isTemporary = false,
}) => {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [accountActivated, setAccountActivated] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!currentPassword || !newPassword || !confirmPassword) {
      setError("Preencha todos os campos.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("A nova senha e a confirmação não coincidem.");
      return;
    }
    setIsLoading(true);
    try {
      const res = await fetch("/api/auth/change-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "Erro ao alterar senha.");
      } else {
        setSuccess(true);
        
        // Se for senha temporária, indicar que a conta foi ativada
        if (isTemporary) {
          setAccountActivated(true);
          setTimeout(() => {
            onClose();
            navigate("/"); // Redirecionar para a página inicial
          }, 2000);
        } else {
          setTimeout(() => onClose(), 1500);
        }
      }
    } catch (err) {
      setError("Erro de conexão com o servidor.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-sm relative">
        <button
          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
          onClick={onClose}
        >
          ×
        </button>
        <h2 className="text-lg font-bold mb-4">{isTemporary ? 'Alterar senha temporária' : 'Alterar senha'}</h2>
        {isTemporary && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
            Você está usando uma senha temporária. Por favor, altere-a para uma senha permanente de sua escolha para maior segurança e ativar sua conta.
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-3">
          <Input
            type="password"
            placeholder="Senha atual"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />
          <Input
            type="password"
            placeholder="Nova senha"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
          <Input
            type="password"
            placeholder="Confirmar nova senha"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
          {error && <div className="text-red-600 text-sm">{typeof error === 'object' ? String(error) : error}</div>}
          {success && (
            <div className="text-green-600 text-sm">
              Senha alterada com sucesso!
              {accountActivated && " Sua conta foi ativada."}
            </div>
          )}
          <div className="flex gap-2 mt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancelar
            </Button>
            <Button type="submit" isLoading={isLoading}>
              Alterar senha
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

const ResetPasswordModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [username, setUsername] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!username) {
      setError("Preencha o nome de usuário.");
      return;
    }
    setIsLoading(true);
    try {
      const res = await fetch("/api/auth/public/request-password-reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "Erro ao solicitar redefinição de senha.");
      } else {
        setSuccess(true);
        setTimeout(() => onClose(), 3000);
      }
    } catch (err) {
      setError("Erro de conexão com o servidor.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-sm relative">
        <button
          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
          onClick={onClose}
        >
          ×
        </button>
        <h2 className="text-lg font-bold mb-4">Esqueci minha senha</h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-800">
            Digite seu nome de usuário abaixo. Se a conta existir, enviaremos um email com instruções para redefinir sua senha.
          </div>
          <Input
            type="text"
            placeholder="Nome de usuário"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          {error && <div className="text-red-600 text-sm">{error}</div>}
          {success && (
            <div className="text-green-600 text-sm">
              Se o usuário existir, um email com instruções para redefinir sua senha foi enviado.
            </div>
          )}
          <div className="flex gap-2 mt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancelar
            </Button>
            <Button type="submit" isLoading={isLoading}>
              Enviar
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [showResetPassword, setShowResetPassword] = useState(false);
  const [isTempPassword, setIsTempPassword] = useState(false);

  const navigate = useNavigate();
  const { login, error, clearError, isAuthenticated } = useAuthStore();

  // Redireciona automaticamente se já estiver autenticado
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Clear error when component unmounts or when inputs change
  useEffect(() => {
    return () => clearError();
  }, [clearError]);

  useEffect(() => {
    if (username || password) {
      clearError();
    }
  }, [username, password, clearError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const result = await login(username, password);
      if (result.success) {
        // Usar a informação de senha temporária da API
        if (result.is_temporary_password) {
          setIsTempPassword(true);
          setShowChangePassword(true);
        } else {
          navigate("/");
        }
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-md w-full"
      >
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Header */}
          <div className="bg-red-600 p-6 text-white">
            <div className="mb-4 flex justify-center">
              <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center">
                <Dumbbell size={32} className="text-red-600" />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-center">DNA da Força</h1>
            <p className="text-center text-red-200 mt-1">
              Assistente de Treinamento
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Usuário
                </label>
                <Input
                  icon={<User size={18} />}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Seu usuário"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Senha
                </label>
                <Input
                  type={showPassword ? "text" : "password"}
                  icon={<Lock size={18} />}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Sua senha"
                  required
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      tabIndex={-1}
                      className="focus:outline-none"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  }
                />
              </div>

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm"
                >
                  {typeof error === 'object' ? String(error) : error}
                </motion.div>
              )}

              <div className="flex justify-end mt-2">
                <button
                  type="button"
                  className="text-xs text-blue-600 hover:underline"
                  onClick={() => setShowResetPassword(true)}
                >
                  Esqueci minha senha?
                </button>
              </div>

              <Button
                type="submit"
                className="w-full bg-red-600 hover:bg-red-700"
                isLoading={isLoading}
              >
                Entrar
              </Button>
            </div>
          </form>

          {showChangePassword && (
            <ChangePasswordModal 
              isTemporary={isTempPassword}
              onClose={() => {
                setShowChangePassword(false);
                if (isTempPassword) {
                  navigate("/");
                }
              }} 
            />
          )}
          {showResetPassword && (
            <ResetPasswordModal onClose={() => setShowResetPassword(false)} />
          )}

          {/* Footer */}
          <div className="px-6 py-4 text-center text-xs text-gray-500 border-t border-gray-200">
            <p>DNA da Força v1.7 - Assistente de Treinamento</p>
            <p className="mt-1">Desenvolvido pela Matech AI</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

// Export default para funcionar com lazy loading
export default LoginPage;
