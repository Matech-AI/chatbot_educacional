import React from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft } from "lucide-react";
import { useAuthStore } from "../../store/auth-store";

export const BackButton: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return null;
  }

  return (
    <button
      type="button"
      onClick={() => navigate("/")}
      className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 transition-colors -ml-1 px-1 py-0.5 rounded-md hover:bg-slate-100"
    >
      <ChevronLeft size={16} />
      <span>Início</span>
    </button>
  );
};
