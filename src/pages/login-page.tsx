import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/auth-store';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { User, Lock, KeyRound, Dumbbell } from 'lucide-react';
import { motion } from 'framer-motion';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const navigate = useNavigate();
  const { login } = useAuthStore();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      const success = await login(email, password, apiKey);
      
      if (success) {
        navigate('/');
      } else {
        setError('Credenciais inválidas ou chave API incorreta.');
      }
    } catch (err) {
      setError('Erro ao fazer login. Tente novamente.');
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
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  OpenAI API Key
                </label>
                <Input
                  type="password"
                  icon={<KeyRound size={18} />}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Necessário para utilizar os recursos de IA
                </p>
              </div>
              
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                  {error}
                </div>
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