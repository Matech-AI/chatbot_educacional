import React, { useState, useEffect } from 'react';
import { BackButton } from '../components/ui/back-button';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { motion } from 'framer-motion';
import {
  Settings,
  Users,
  Shield,
  Database,
  Server,
  Key,
  UserPlus,
  Edit,
  Trash2,
  Save,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Eye,
  EyeOff
} from 'lucide-react';

interface User {
  username: string;
  password: string;
  role: 'admin' | 'instructor' | 'student';
}

interface SystemConfig {
  maxFileSize: number;
  allowedFileTypes: string[];
  sessionTimeout: number;
  apiRateLimit: number;
  backupEnabled: boolean;
  debugMode: boolean;
}

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'users' | 'system' | 'permissions'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [systemConfig, setSystemConfig] = useState<SystemConfig>({
    maxFileSize: 50,
    allowedFileTypes: ['pdf', 'docx', 'txt', 'mp4', 'avi', 'mov'],
    sessionTimeout: 24,
    apiRateLimit: 100,
    backupEnabled: true,
    debugMode: false
  });
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});
  const [newUser, setNewUser] = useState<User>({ username: '', password: '', role: 'student' });
  const [showNewUserForm, setShowNewUserForm] = useState(false);
  const [editingUser, setEditingUser] = useState<string | null>(null);

  // Load users on component mount
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setIsLoading(true);
      // In a real app, this would be an API call
      const defaultUsers: User[] = [
        { username: 'admin', password: 'admin123', role: 'admin' },
        { username: 'instrutor', password: 'instrutor123', role: 'instructor' },
        { username: 'aluno', password: 'aluno123', role: 'student' }
      ];
      setUsers(defaultUsers);
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao carregar usuários' });
    } finally {
      setIsLoading(false);
    }
  };

  const saveUsers = async () => {
    try {
      setIsLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setMessage({ type: 'success', text: 'Usuários salvos com sucesso!' });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao salvar usuários' });
    } finally {
      setIsLoading(false);
    }
  };

  const saveSystemConfig = async () => {
    try {
      setIsLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setMessage({ type: 'success', text: 'Configurações do sistema salvas!' });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao salvar configurações' });
    } finally {
      setIsLoading(false);
    }
  };

  const addUser = () => {
    if (newUser.username && newUser.password) {
      setUsers([...users, { ...newUser }]);
      setNewUser({ username: '', password: '', role: 'student' });
      setShowNewUserForm(false);
      setMessage({ type: 'success', text: 'Usuário adicionado!' });
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const deleteUser = (username: string) => {
    if (users.length > 1) {
      setUsers(users.filter(u => u.username !== username));
      setMessage({ type: 'success', text: 'Usuário removido!' });
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const updateUser = (username: string, updates: Partial<User>) => {
    setUsers(users.map(u => u.username === username ? { ...u, ...updates } : u));
    setEditingUser(null);
  };

  const togglePasswordVisibility = (username: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [username]: !prev[username]
    }));
  };

  const tabs = [
    { id: 'users' as const, label: 'Gerenciar Usuários', icon: Users },
    { id: 'system' as const, label: 'Parâmetros do Sistema', icon: Database },
    { id: 'permissions' as const, label: 'Definir Permissões', icon: Shield }
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <header className="mb-6">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <BackButton />
          <h1 className="text-2xl font-bold text-gray-900 mt-2 flex items-center gap-2">
            <Settings size={28} className="text-gray-700" />
            ⚙️ Configurações
          </h1>
          <p className="text-gray-600 mt-1">
            Gerencie usuários, configure parâmetros do sistema e defina permissões
          </p>
        </motion.div>
      </header>

      {/* Message notification */}
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`mb-6 p-4 rounded-lg flex items-center gap-2 ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle size={20} />
          ) : (
            <AlertTriangle size={20} />
          )}
          {message.text}
        </motion.div>
      )}

      {/* Tabs */}
      <div className="mb-6">
        <nav className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'
                }`}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.2 }}
      >
        {activeTab === 'users' && (
          <div className="space-y-6">
            {/* Add User Button */}
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">Usuários do Sistema</h2>
              <Button
                onClick={() => setShowNewUserForm(!showNewUserForm)}
                className="flex items-center gap-2"
              >
                <UserPlus size={16} />
                Adicionar Usuário
              </Button>
            </div>

            {/* New User Form */}
            {showNewUserForm && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="bg-gray-50 rounded-lg p-4 border border-gray-200"
              >
                <h3 className="font-medium mb-3">Novo Usuário</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                  <Input
                    placeholder="Nome de usuário"
                    value={newUser.username}
                    onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  />
                  <Input
                    type="password"
                    placeholder="Senha"
                    value={newUser.password}
                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  />
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser({ ...newUser, role: e.target.value as User['role'] })}
                    className="rounded-md border border-gray-300 px-3 py-2 text-sm"
                  >
                    <option value="student">Aluno</option>
                    <option value="instructor">Instrutor</option>
                    <option value="admin">Administrador</option>
                  </select>
                  <Button onClick={addUser} size="sm">
                    Adicionar
                  </Button>
                </div>
              </motion.div>
            )}

            {/* Users Table */}
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Usuário
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Senha
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Função
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ações
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {users.map((user) => (
                      <tr key={user.username} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          {editingUser === user.username ? (
                            <Input
                              value={user.username}
                              onChange={(e) => updateUser(user.username, { username: e.target.value })}
                              size="sm"
                            />
                          ) : (
                            <span className="font-medium">{user.username}</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            {editingUser === user.username ? (
                              <Input
                                type="password"
                                value={user.password}
                                onChange={(e) => updateUser(user.username, { password: e.target.value })}
                                size="sm"
                              />
                            ) : (
                              <>
                                <span className="font-mono text-sm">
                                  {showPasswords[user.username] ? user.password : '••••••••'}
                                </span>
                                <button
                                  onClick={() => togglePasswordVisibility(user.username)}
                                  className="text-gray-400 hover:text-gray-600"
                                >
                                  {showPasswords[user.username] ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {editingUser === user.username ? (
                            <select
                              value={user.role}
                              onChange={(e) => updateUser(user.username, { role: e.target.value as User['role'] })}
                              className="rounded-md border border-gray-300 px-2 py-1 text-sm"
                            >
                              <option value="student">Aluno</option>
                              <option value="instructor">Instrutor</option>
                              <option value="admin">Administrador</option>
                            </select>
                          ) : (
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              user.role === 'admin' ? 'bg-red-100 text-red-800' :
                              user.role === 'instructor' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {user.role === 'admin' ? 'Administrador' :
                               user.role === 'instructor' ? 'Instrutor' : 'Aluno'}
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            {editingUser === user.username ? (
                              <button
                                onClick={() => setEditingUser(null)}
                                className="text-green-600 hover:text-green-800"
                              >
                                <Save size={16} />
                              </button>
                            ) : (
                              <button
                                onClick={() => setEditingUser(user.username)}
                                className="text-blue-600 hover:text-blue-800"
                              >
                                <Edit size={16} />
                              </button>
                            )}
                            {users.length > 1 && (
                              <button
                                onClick={() => deleteUser(user.username)}
                                className="text-red-600 hover:text-red-800"
                              >
                                <Trash2 size={16} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={saveUsers} isLoading={isLoading}>
                <Save size={16} className="mr-2" />
                Salvar Alterações
              </Button>
            </div>
          </div>
        )}

        {activeTab === 'system' && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold">Parâmetros do Sistema</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="font-medium mb-4 flex items-center gap-2">
                  <Server size={20} className="text-blue-600" />
                  Configurações de Arquivo
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tamanho máximo de arquivo (MB)
                    </label>
                    <Input
                      type="number"
                      value={systemConfig.maxFileSize}
                      onChange={(e) => setSystemConfig({
                        ...systemConfig,
                        maxFileSize: parseInt(e.target.value)
                      })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipos de arquivo permitidos
                    </label>
                    <Input
                      value={systemConfig.allowedFileTypes.join(', ')}
                      onChange={(e) => setSystemConfig({
                        ...systemConfig,
                        allowedFileTypes: e.target.value.split(',').map(s => s.trim())
                      })}
                      placeholder="pdf, docx, txt, mp4"
                    />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="font-medium mb-4 flex items-center gap-2">
                  <Key size={20} className="text-green-600" />
                  Configurações de Segurança
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Timeout de sessão (horas)
                    </label>
                    <Input
                      type="number"
                      value={systemConfig.sessionTimeout}
                      onChange={(e) => setSystemConfig({
                        ...systemConfig,
                        sessionTimeout: parseInt(e.target.value)
                      })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Limite de requisições por minuto
                    </label>
                    <Input
                      type="number"
                      value={systemConfig.apiRateLimit}
                      onChange={(e) => setSystemConfig({
                        ...systemConfig,
                        apiRateLimit: parseInt(e.target.value)
                      })}
                    />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="font-medium mb-4 flex items-center gap-2">
                  <Database size={20} className="text-purple-600" />
                  Configurações de Sistema
                </h3>
                <div className="space-y-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={systemConfig.backupEnabled}
                      onChange={(e) => setSystemConfig({
                        ...systemConfig,
                        backupEnabled: e.target.checked
                      })}
                      className="rounded border-gray-300"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      Backup automático habilitado
                    </span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={systemConfig.debugMode}
                      onChange={(e) => setSystemConfig({
                        ...systemConfig,
                        debugMode: e.target.checked
                      })}
                      className="rounded border-gray-300"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      Modo debug ativado
                    </span>
                  </label>
                </div>
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="font-medium mb-4 flex items-center gap-2">
                  <RefreshCw size={20} className="text-orange-600" />
                  Ações do Sistema
                </h3>
                <div className="space-y-3">
                  <Button variant="outline" className="w-full justify-start">
                    <RefreshCw size={16} className="mr-2" />
                    Reiniciar Sistema
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <Database size={16} className="mr-2" />
                    Backup Manual
                  </Button>
                  <Button variant="outline" className="w-full justify-start text-red-600 border-red-200 hover:bg-red-50">
                    <Trash2 size={16} className="mr-2" />
                    Limpar Cache
                  </Button>
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={saveSystemConfig} isLoading={isLoading}>
                <Save size={16} className="mr-2" />
                Salvar Configurações
              </Button>
            </div>
          </div>
        )}

        {activeTab === 'permissions' && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold">Definir Permissões</h2>
            
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h3 className="font-medium mb-3 text-red-600 flex items-center gap-2">
                    <Shield size={20} />
                    Administrador
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-600" />
                      <span>Gerenciar usuários</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-600" />
                      <span>Configurar sistema</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-600" />
                      <span>Gerenciar materiais</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-600" />
                      <span>Configurar assistente</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-600" />
                      <span>Acessar chat</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-600" />
                      <span>Ver debug</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="font-medium mb-3 text-blue-600 flex items-center gap-2">
                    <Users size={20} />
                    Instrutor
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full bg-gray-300"></div>
                      <span className="text-gray-500">Gerenciar usuários</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full bg-gray-300"></div>
                      <span className="text-gray-500">Configurar sistema</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-600" />
                      <span>Gerenciar materiais</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-600" />
                      <span>Configurar assistente</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-600" />
                      <span>Acessar chat</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full bg-gray-300"></div>
                      <span className="text-gray-500">Ver debug</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="font-medium mb-3 text-gray-600 flex items-center gap-2">
                    <Users size={20} />
                    Aluno
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full bg-gray-300"></div>
                      <span className="text-gray-500">Gerenciar usuários</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full bg-gray-300"></div>
                      <span className="text-gray-500">Configurar sistema</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full bg-gray-300"></div>
                      <span className="text-gray-500">Gerenciar materiais</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full bg-gray-300"></div>
                      <span className="text-gray-500">Configurar assistente</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-600" />
                      <span>Acessar chat</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-full bg-gray-300"></div>
                      <span className="text-gray-500">Ver debug</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <AlertTriangle size={20} className="text-yellow-600 mt-0.5" />
                <div>
                  <h3 className="font-medium text-yellow-800">Nota sobre Permissões</h3>
                  <p className="text-sm text-yellow-700 mt-1">
                    As permissões são aplicadas automaticamente baseadas na função do usuário.
                    Apenas administradores podem modificar essas configurações.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};

// Export default para funcionar com lazy loading
export default SettingsPage;

