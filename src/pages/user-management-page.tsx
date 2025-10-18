import React, { useState, useEffect } from "react";
import { useAuthStore } from "../store/auth-store";
import { api } from "../lib/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  User,
  UserPlus,
  Edit,
  Trash2,
  Shield,
  ShieldOff,
  RefreshCw,
} from "lucide-react";
import { motion } from "framer-motion";

interface UserData {
  id: string;
  username: string;
  email?: string;
  full_name?: string;
  role: string;
  disabled: boolean;
  approved: boolean;
  created_at: string;
  updated_at: string;
  external_id?: string;
  last_login?: string;
}

interface ApprovedUser {
  external_id: string;
  username: string;
  email?: string;
  full_name?: string;
  role: string;
}

const UserManagementPage: React.FC = () => {
  const { user } = useAuthStore();
  const [users, setUsers] = useState<UserData[]>([]);
  const [approvedUsers, setApprovedUsers] = useState<ApprovedUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showAddApproved, setShowAddApproved] = useState(false);
  const [activeTab, setActiveTab] = useState<"users" | "approved">("users");

  // Check if user is admin
  if (!user || user.role !== "admin") {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          <p>
            Acesso negado. Apenas administradores podem acessar esta página.
          </p>
        </div>
      </div>
    );
  }

  const loadUsers = async () => {
    try {
      setLoading(true);
      const usersData: UserData[] = await api.users.list();

      // Ordenar usuários por ID numérico (external_id)
      // TODO: Quando migrar para BD, considerar usar ORDER BY na query SQL
      const sortedUsers = usersData.sort((a: UserData, b: UserData) => {
        const idA = parseInt(a.external_id || "0") || 0;
        const idB = parseInt(b.external_id || "0") || 0;
        return idA - idB;
      });

      setUsers(sortedUsers);
    } catch (err) {
      console.error("Error loading users:", err);
      // Check if it's an authentication error
      if (err instanceof Error && err.message.includes("401 Unauthorized")) {
        setError("Erro de autenticação. Por favor, faça login novamente.");
        // Redirect to login after a short delay
        setTimeout(() => {
          useAuthStore.getState().logout();
          window.location.href = "/login";
        }, 2000);
      } else {
        setError("Erro ao carregar usuários");
      }
    } finally {
      setLoading(false);
    }
  };

  const loadApprovedUsers = async () => {
    try {
      setLoading(true);
      const approvedData = await api.approvedUsers.list();
      setApprovedUsers(approvedData);
    } catch (err) {
      console.error("Error loading approved users:", err);
      // Check if it's an authentication error
      if (err instanceof Error && err.message.includes("401 Unauthorized")) {
        setError("Erro de autenticação. Por favor, faça login novamente.");
        // Redirect to login after a short delay
        setTimeout(() => {
          useAuthStore.getState().logout();
          window.location.href = "/login";
        }, 2000);
      } else {
        setError("Erro ao carregar usuários aprovados");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
    loadApprovedUsers();
  }, []);

  const handleDeleteUser = async (username: string) => {
    if (!confirm(`Tem certeza que deseja excluir o usuário ${username}?`)) {
      return;
    }

    try {
      await api.users.delete(username);
      await loadUsers();
    } catch (err) {
      setError("Erro ao excluir usuário");
      console.error("Error deleting user:", err);
    }
  };

  const handleToggleUserStatus = async (
    username: string,
    disabled: boolean
  ) => {
    try {
      await api.users.update(username, { disabled: !disabled });
      await loadUsers();
    } catch (err) {
      setError("Erro ao atualizar status do usuário");
      console.error("Error updating user status:", err);
    }
  };

  const handleToggleApproval = async (username: string, approved: boolean) => {
    try {
      await api.users.update(username, { approved: !approved });
      await loadUsers();
    } catch (err) {
      setError("Erro ao atualizar aprovação do usuário");
      console.error("Error updating user approval:", err);
    }
  };

  const formatDate = (dateString: string) => {
    // Criar um objeto Date a partir da string ISO
    const date = new Date(dateString);

    // Ajustar para o fuso horário de São Paulo (GMT-3)
    // Isso é necessário porque o timestamp está em UTC
    return date.toLocaleString("pt-BR", {
      timeZone: "America/Sao_Paulo",
    });
  };

  const getRoleLabel = (role: string) => {
    const roles = {
      admin: "Administrador",
      instructor: "Instrutor",
      student: "Aluno",
    };
    return roles[role as keyof typeof roles] || role;
  };

  const getRoleBadgeColor = (role: string) => {
    const colors = {
      admin: "bg-red-100 text-red-800",
      instructor: "bg-blue-100 text-blue-800",
      student: "bg-green-100 text-green-800",
    };
    return colors[role as keyof typeof colors] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Gerenciamento de Usuários
        </h1>
        <p className="text-gray-600">
          Gerencie usuários, aprovações e sincronização com plataforma externa
        </p>
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md"
        >
          {error}
          <button
            onClick={() => setError(null)}
            className="float-right text-red-500 hover:text-red-700"
          >
            ×
          </button>
        </motion.div>
      )}

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab("users")}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === "users"
                  ? "border-red-500 text-red-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <User className="w-4 h-4 inline-block mr-2" />
              Usuários ({users.length})
            </button>
          </nav>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mb-6 flex flex-wrap gap-3">
        <Button
          onClick={() => setShowCreateUser(true)}
          className="bg-red-600 hover:bg-red-700"
        >
          <UserPlus className="w-4 h-4 mr-2" />
          Criar Usuário
        </Button>

        {/* Removendo o botão de adicionar à lista de aprovados */}

        <Button
          onClick={() => {
            loadUsers();
            // Removendo a chamada para loadApprovedUsers
          }}
          variant="outline"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Atualizar
        </Button>
      </div>

      {/* Users Tab */}
      {activeTab === "users" && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID Numérico
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usuário
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Último Login
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Criado em
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-6 py-4 text-center text-gray-500"
                    >
                      Carregando usuários...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-6 py-4 text-center text-gray-500"
                    >
                      Nenhum usuário encontrado
                    </td>
                  </tr>
                ) : (
                  users.map((userData) => (
                    <tr key={userData.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {userData.external_id
                          ? (() => {
                              const parsed = parseInt(userData.external_id);
                              return isNaN(parsed)
                                ? userData.external_id
                                : parsed;
                            })()
                          : "N/A"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {userData.username}
                          </div>
                          <div className="text-sm text-gray-500">
                            {userData.email || "Sem email"}
                          </div>
                          {userData.full_name && (
                            <div className="text-sm text-gray-500">
                              {userData.full_name}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleBadgeColor(
                            userData.role
                          )}`}
                        >
                          {getRoleLabel(userData.role)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col space-y-1">
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              userData.disabled
                                ? "bg-red-100 text-red-800"
                                : "bg-green-100 text-green-800"
                            }`}
                          >
                            {userData.disabled ? "Inativo" : "Ativo"}
                          </span>
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              userData.approved
                                ? "bg-blue-100 text-blue-800"
                                : "bg-yellow-100 text-yellow-800"
                            }`}
                          >
                            {userData.approved ? "Aprovado" : "Pendente"}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {userData.last_login
                          ? formatDate(userData.last_login)
                          : "Nunca"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(userData.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button
                            onClick={() =>
                              handleToggleUserStatus(
                                userData.username,
                                userData.disabled
                              )
                            }
                            className={`text-xs px-2 py-1 rounded ${
                              userData.disabled
                                ? "bg-green-100 text-green-700 hover:bg-green-200"
                                : "bg-yellow-100 text-yellow-700 hover:bg-yellow-200"
                            }`}
                          >
                            {userData.disabled ? "Ativar" : "Desativar"}
                          </button>

                          <button
                            onClick={() =>
                              handleToggleApproval(
                                userData.username,
                                userData.approved
                              )
                            }
                            className={`text-xs px-2 py-1 rounded ${
                              userData.approved
                                ? "bg-yellow-100 text-yellow-700 hover:bg-yellow-200"
                                : "bg-blue-100 text-blue-700 hover:bg-blue-200"
                            }`}
                          >
                            {userData.approved ? "Reprovar" : "Aprovar"}
                          </button>

                          {userData.username !== user?.username && (
                            <button
                              onClick={() =>
                                handleDeleteUser(userData.username)
                              }
                              className="text-xs px-2 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateUser && (
        <CreateUserModal
          onClose={() => setShowCreateUser(false)}
          onSuccess={() => {
            setShowCreateUser(false);
            loadUsers();
          }}
        />
      )}

      {/* Removendo completamente o modal de Add Approved User */}
      {showAddApproved && (
        <AddApprovedUserModal
          onClose={() => setShowAddApproved(false)}
          onSuccess={() => {
            setShowAddApproved(false);
            loadApprovedUsers();
          }}
        />
      )}
    </div>
  );
};

// Create User Modal Component
const CreateUserModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    full_name: "",
    role: "student",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdUser, setCreatedUser] = useState<{
    user: any;
    password: string | null;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await api.users.create(formData);
      setCreatedUser({
        user: response.user,
        password: response.generated_password,
      });
      // Não fechamos o modal imediatamente para mostrar a senha
    } catch (err) {
      setError("Erro ao criar usuário");
      console.error("Error creating user:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-bold mb-4">Criar Novo Usuário</h3>

        {createdUser ? (
          <div className="space-y-4">
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
              <p className="font-bold">Usuário criado com sucesso!</p>
              <p>
                Nome de usuário:{" "}
                <span className="font-mono">{createdUser.user.username}</span>
              </p>
              {createdUser.password && (
                <div>
                  <p className="mt-2 font-bold">Senha gerada:</p>
                  <div className="bg-gray-100 p-2 rounded font-mono text-center text-lg mt-1 border border-gray-300">
                    {createdUser.password}
                  </div>
                  <p className="text-xs mt-1 text-gray-600">
                    Guarde esta senha em um local seguro. Ela não será mostrada
                    novamente.
                  </p>
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <Button type="button" onClick={onSuccess} className="w-full">
                Fechar
              </Button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              placeholder="Nome de usuário"
              value={formData.username}
              onChange={(e) =>
                setFormData({ ...formData, username: e.target.value })
              }
              required
            />

            <Input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) =>
                setFormData({ ...formData, email: e.target.value })
              }
              required
            />

            <Input
              placeholder="Nome completo (opcional)"
              value={formData.full_name}
              onChange={(e) =>
                setFormData({ ...formData, full_name: e.target.value })
              }
            />

            <select
              value={formData.role}
              onChange={(e) =>
                setFormData({ ...formData, role: e.target.value })
              }
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-red-500"
            >
              <option value="student">Aluno</option>
              <option value="instructor">Instrutor</option>
              <option value="admin">Administrador</option>
            </select>

            {error && <div className="text-red-600 text-sm">{error}</div>}

            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancelar
              </Button>
              <Button type="submit" isLoading={loading}>
                Adicionar
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

// Add Approved User Modal Component
const AddApprovedUserModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    full_name: "",
    role: "student",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await api.approvedUsers.add(formData);
      onSuccess();
    } catch (err) {
      setError("Erro ao adicionar usuário à lista de aprovados");
      console.error("Error adding approved user:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-bold mb-4">
          Adicionar à Lista de Aprovados
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            placeholder="Nome de usuário"
            value={formData.username}
            onChange={(e) =>
              setFormData({ ...formData, username: e.target.value })
            }
            required
          />

          <Input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) =>
              setFormData({ ...formData, email: e.target.value })
            }
            required
          />

          <Input
            placeholder="Nome completo (opcional)"
            value={formData.full_name}
            onChange={(e) =>
              setFormData({ ...formData, full_name: e.target.value })
            }
          />

          <select
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-red-500"
          >
            <option value="student">Aluno</option>
            <option value="instructor">Instrutor</option>
            <option value="admin">Administrador</option>
          </select>

          {/* Campo ID externo removido */}

          {error && <div className="text-red-600 text-sm">{error}</div>}

          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={loading}>
              Adicionar
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UserManagementPage;
