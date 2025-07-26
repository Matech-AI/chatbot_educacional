import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/auth-store";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { api } from "../../lib/api";

const TemporaryPasswordCheck: React.FC = () => {
  const [showModal, setShowModal] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();
  const { user, checkAuth } = useAuthStore();

  // Verificar se o usuário está usando senha temporária
  useEffect(() => {
    const checkTemporaryPassword = async () => {
      try {
        // Obter informações atualizadas do usuário
        const userData = await api.getCurrentUser();
        if (userData.is_temporary_password) {
          setShowModal(true);
        }
      } catch (error) {
        console.error("Erro ao verificar senha temporária:", error);
      }
    };

    if (user) {
      checkTemporaryPassword();
    }
  }, [user]);

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
        // Atualizar informações do usuário após a troca de senha
        checkAuth();
        setTimeout(() => {
          setShowModal(false);
          navigate("/");
        }, 1500);
      }
    } catch (err) {
      setError("Erro de conexão com o servidor.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!showModal) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Alterar Senha Temporária</h2>
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
          <p className="font-semibold">Atenção!</p>
          <p>Você está usando uma senha temporária. Por favor, altere-a para uma senha permanente de sua escolha para maior segurança e ativar sua conta.</p>
          <p className="mt-2">Você não poderá acessar o sistema até alterar sua senha.</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Senha Atual (Temporária)</label>
            <Input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nova Senha</label>
            <Input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirmar Nova Senha</label>
            <Input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          
          {error && <div className="text-red-600 text-sm">{error}</div>}
          {success && <div className="text-green-600 text-sm">Senha alterada com sucesso! Sua conta foi ativada.</div>}
          
          <Button type="submit" className="w-full" isLoading={isLoading}>
            Alterar Senha e Ativar Conta
          </Button>
        </form>
      </div>
    </div>
  );
};

export default TemporaryPasswordCheck;