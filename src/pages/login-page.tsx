import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/auth-store';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { User, Lock, Dumbbell } from 'lucide-react';
import { motion } from 'framer-motion';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const navigate = useNavigate();
  const { login, error, clearError } = useAuthStore();

  // Clear error when component unmounts or when inputs change
  useEffect(() => {
    return () => clearError();
  }, [clearError]);

  useEffect(() => {
    if (email || password) {
      clearError();
    }
  }, [email, password, clearError]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const success = await login(email, password);
      if (success) {
        navigate('/');
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
            <p className="text-center text-red-200 mt-1">Assistente de Treinamento</p>
          </div>
          
          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <Input
                  icon={<User size={18} />}
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Seu email"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Senha
                </label>
                <Input
                  type="password"
                  icon={<Lock size={18} />}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Sua senha"
                  required
                />
              </div>
              
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm"
                >
                  {error}
                </motion.div>
              )}
              
              <Button 
                type="submit" 
                className="w-full bg-red-600 hover:bg-red-700"
                isLoading={isLoading}
              >
                Entrar
              </Button>
            </div>
          </form>
          
          {/* Demo Access Info */}
          <div className="p-4 bg-gray-50 border-t border-gray-200">
            <div className="text-sm">
              <h3 className="font-medium text-gray-900 mb-2">Acessos para demonstração:</h3>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="bg-white p-2 rounded border border-gray-200">
                  <p className="font-semibold">Admin</p>
                  <p className="text-gray-500 break-all">admin@dnadaforca.com</p>
                  <p className="text-gray-500">Senha: admin123</p>
                </div>
                <div className="bg-white p-2 rounded border border-gray-200">
                  <p className="font-semibold">Instrutor</p>
                  <p className="text-gray-500 break-all">instrutor@dnadaforca.com</p>
                  <p className="text-gray-500">Senha: instrutor123</p>
                </div>
                <div className="bg-white p-2 rounded border border-gray-200">
                  <p className="font-semibold">Aluno</p>
                  <p className="text-gray-500 break-all">aluno@dnadaforca.com</p>
                  <p className="text-gray-500">Senha: aluno123</p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Footer */}
          <div className="px-6 py-4 text-center text-xs text-gray-500 border-t border-gray-200">
            <p>DNA da Força - Assistente de Treinamento</p>
            <p className="mt-1">Desenvolvido por Matheus Bernardes</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};