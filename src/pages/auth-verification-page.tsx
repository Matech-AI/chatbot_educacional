import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

const AuthVerificationPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    const verifyToken = async () => {
      const token = searchParams.get("token");
      const username = searchParams.get("username");

      if (!token || !username) {
        setStatus("error");
        setMessage("Parâmetros de verificação inválidos ou ausentes.");
        return;
      }

      try {
        const response = await fetch(`/api/auth/public/verify-token`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, username }),
        });

        if (response.ok) {
          setStatus("success");
          setMessage(
            "Conta verificada com sucesso! Uma senha temporária foi enviada para seu e-mail."
          );
        } else {
          const errorData = await response.text();
          setStatus("error");
          setMessage(
            errorData ||
              "Ocorreu um erro durante a verificação. Por favor, tente novamente."
          );
        }
      } catch (error) {
        setStatus("error");
        setMessage(
          error instanceof Error
            ? error.message
            : "Ocorreu um erro durante a verificação. Por favor, tente novamente."
        );
      }
    };

    verifyToken();
  }, [searchParams, navigate]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-[450px] shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl text-center">
            Verificação de Conta
          </CardTitle>
          <CardDescription className="text-center">
            {status === "loading"
              ? "Verificando sua conta..."
              : status === "success"
              ? "Verificação concluída!"
              : "Falha na verificação"}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center p-6">
          {status === "loading" && (
            <div className="flex flex-col items-center space-y-4">
              <Loader2 className="h-16 w-16 text-blue-500 animate-spin" />
              <p className="text-gray-600 text-center">
                Estamos verificando sua conta, por favor aguarde...
              </p>
            </div>
          )}

          {status === "success" && (
            <div className="flex flex-col items-center space-y-4">
              <CheckCircle className="h-16 w-16 text-green-500" />
              <p className="text-gray-600 text-center">{message}</p>
              <p className="text-gray-600 text-center">
                Sua conta foi verificada com sucesso. Agora você pode fazer
                login usando a senha temporária enviada para seu e-mail.
              </p>
            </div>
          )}

          {status === "error" && (
            <div className="flex flex-col items-center space-y-4">
              <XCircle className="h-16 w-16 text-red-500" />
              <p className="text-gray-600 text-center">{message}</p>
              <p className="text-gray-600 text-center">
                Não foi possível verificar sua conta. O link pode ter expirado
                ou ser inválido.
              </p>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-center">
          <Button
            onClick={() => navigate("/login")}
            className="w-full"
            variant={status === "error" ? "outline" : "default"}
          >
            {status === "success" ? "Ir para o Login" : "Voltar para o Login"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default AuthVerificationPage;
