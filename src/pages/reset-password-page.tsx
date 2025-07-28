import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { CheckCircle, XCircle, Loader2, Eye, EyeOff } from "lucide-react";
import { api } from "../lib/api";

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<"loading" | "form" | "success" | "error">("form");
  const [message, setMessage] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Extrair token e username da URL
  const token = searchParams.get("token");
  const username = searchParams.get("username");

  useEffect(() => {
    // Verificar se os parâmetros necessários estão presentes
    if (!token || !username) {
      setStatus("error");
      setMessage("Parâmetros de redefinição de senha inválidos ou ausentes.");
    }
  }, [token, username]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validações
    if (password.length < 6) {
      setError("A senha deve ter pelo menos 6 caracteres.");
      return;
    }

    if (password !== confirmPassword) {
      setError("As senhas não coincidem.");
      return;
    }

    if (!token || !username) {
      setError("Parâmetros inválidos.");
      return;
    }

    setStatus("loading");

    try {
      await api.confirmPasswordReset(token, username, password);
      setStatus("success");
      setMessage("Senha redefinida com sucesso! Agora você pode fazer login com sua nova senha.");
    } catch (error) {
      setStatus("error");
      setMessage(
        error instanceof Error
          ? error.message
          : "Ocorreu um erro durante a redefinição de senha. O link pode ter expirado ou ser inválido."
      );
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-[450px] shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl text-center">
            Redefinição de Senha
          </CardTitle>
          <CardDescription className="text-center">
            {status === "loading"
              ? "Processando sua solicitação..."
              : status === "form"
              ? "Defina sua nova senha"
              : status === "success"
              ? "Senha redefinida!"
              : "Falha na redefinição"}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center p-6">
          {status === "loading" && (
            <div className="flex flex-col items-center space-y-4">
              <Loader2 className="h-16 w-16 text-blue-500 animate-spin" />
              <p className="text-gray-600 text-center">
                Estamos processando sua solicitação, por favor aguarde...
              </p>
            </div>
          )}

          {status === "form" && (
            <form onSubmit={handleSubmit} className="w-full space-y-4">
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium text-gray-700">
                  Nova Senha
                </label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pr-10"
                    placeholder="Digite sua nova senha"
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="confirmPassword" className="text-sm font-medium text-gray-700">
                  Confirmar Senha
                </label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirme sua nova senha"
                />
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-800">
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full">
                Redefinir Senha
              </Button>
            </form>
          )}

          {status === "success" && (
            <div className="flex flex-col items-center space-y-4">
              <CheckCircle className="h-16 w-16 text-green-500" />
              <p className="text-gray-600 text-center">{message}</p>
            </div>
          )}

          {status === "error" && (
            <div className="flex flex-col items-center space-y-4">
              <XCircle className="h-16 w-16 text-red-500" />
              <p className="text-gray-600 text-center">{message}</p>
              <p className="text-gray-600 text-center">
                O link pode ter expirado ou ser inválido. Tente solicitar uma nova redefinição de senha.
              </p>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-center">
          <Button
            onClick={() => navigate("/login")}
            className="w-full"
            variant={status === "form" ? "outline" : "default"}
          >
            {status === "success" ? "Ir para o Login" : "Voltar para o Login"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default ResetPasswordPage;