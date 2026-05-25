import { create } from 'zustand';
import { User, UserRole } from '../types';
import { api } from '../lib/api';
import { useChatStore } from './chat-store';
import { GUEST_USER_ID } from '../constants/branding';

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  error: string | null;
  login: (
    username: string,
    password: string
  ) => Promise<{ success: boolean; is_temporary_password?: boolean }>;
  logout: () => void;
  clearError: () => void;
  checkAuth: () => void;
}

// Helper function to decode JWT payload (para JWT real)
function decodeJWTPayload(token: string): any {
  try {
    // Verificar se é um JWT real (tem 3 partes separadas por ponto)
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null; // Não é um JWT real
    }
    
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error decoding JWT:', error);
    return null;
  }
}

// Helper function para decodificar token simplificado (formato: username-role-timestamp)
function decodeSimpleToken(token: string): any {
  try {
    const parts = token.split('-');
    if (parts.length >= 3) {
      const username = parts[0];
      const role = parts[1];
      const timestamp = parseFloat(parts[2]);
      
      // Verificar se o token não expirou (24 horas)
      const now = Date.now() / 1000;
      const tokenTime = timestamp / 1000;
      
      if (now - tokenTime > 24 * 60 * 60) { // 24 horas em segundos
        console.log('Simple token expired');
        return null;
      }
      
      return {
        sub: username,
        role: role,
        exp: timestamp + (24 * 60 * 60 * 1000) // Expira em 24 horas
      };
    }
    return null;
  } catch (error) {
    console.error('Error decoding simple token:', error);
    return null;
  }
}

// Helper function para decodificar qualquer tipo de token
function decodeToken(token: string): any {
  // Primeiro tenta JWT real
  const jwtPayload = decodeJWTPayload(token);
  if (jwtPayload) {
    console.log('✅ Decoded as JWT token');
    return jwtPayload;
  }
  
  // Se não funcionar, tenta token simplificado
  const simplePayload = decodeSimpleToken(token);
  if (simplePayload) {
    console.log('✅ Decoded as simple token');
    return simplePayload;
  }
  
  console.error('❌ Could not decode token in any format');
  return null;
}

// Helper function to create user from token payload
function createUserFromToken(payload: any): User {
  // Map backend roles to frontend roles
  const roleMap: Record<string, UserRole> = {
    'admin': 'admin',
    'instructor': 'instructor', 
    'student': 'student'
  };

  const username = payload.sub || 'unknown';
  const role = payload.role || 'student';

  return {
    id: username,
    username,
    name: getUserDisplayName(username),
    role: roleMap[role] || 'student',
    email: payload.email,
    avatarUrl: getDefaultAvatar(role)
  };
}

function getUserDisplayName(username: string): string {
  const nameMap: Record<string, string> = {
    'admin': 'Administrador',
    'instrutor': 'Instrutor',
    'aluno': 'Aluno'
  };
  
  return nameMap[username] || username;
}

function getDefaultAvatar(role: string): string {
  const avatars = {
    admin: 'https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg',
    instructor: 'https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg',
    student: 'https://images.pexels.com/photos/614810/pexels-photo-614810.jpeg'
  };
  return avatars[role as keyof typeof avatars] || avatars.student;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  isAuthenticated: false,
  user: null,
  error: null,
  
  checkAuth: () => {
    const token = localStorage.getItem('token');

    if (!token) {
      console.log('🔐 No token found — modo visitante');
      useChatStore.getState().setCurrentUser(GUEST_USER_ID);
      set({ isAuthenticated: false, user: null, error: null });
      return;
    }

    let payload: any = null;
    try {
      payload = decodeToken(token);
    } catch {
      // ignore decode errors below
    }

    if (!payload) {
      console.warn('❌ Token inválido — limpando');
      localStorage.removeItem('token');
      useChatStore.getState().setCurrentUser(GUEST_USER_ID);
      set({ isAuthenticated: false, user: null, error: null });
      return;
    }

    const currentTime = Date.now() / 1000;
    if (payload.exp && payload.exp < currentTime) {
      console.warn('❌ Token expirado — limpando');
      localStorage.removeItem('token');
      useChatStore.getState().setCurrentUser(GUEST_USER_ID);
      set({ isAuthenticated: false, user: null, error: null });
      return;
    }

    // Token locally valid → set auth state SYNCHRONOUSLY so ProtectedRoute
    // and child useEffects already see isAuthenticated: true on first render.
    const user = createUserFromToken(payload);
    console.log('✅ Token local válido para:', user.name);
    set({ isAuthenticated: true, user, error: null });
    useChatStore.getState().setCurrentUser(user.id);

    // Validate with backend in background — if it fails, log out gracefully.
    // Do NOT use apiRequest here to avoid the generic setAuthToken(null) side-effect;
    // handle the 401 ourselves so only an explicit backend rejection clears state.
    fetch('/api/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (res.status === 401) {
          console.warn('❌ Backend rejeitou o token — encerrando sessão');
          localStorage.removeItem('token');
          useChatStore.getState().setCurrentUser(GUEST_USER_ID);
          set({ isAuthenticated: false, user: null, error: 'Sessão expirada. Faça login novamente.' });
        } else {
          console.log('✅ Token validado pelo backend para:', user.name);
        }
      })
      .catch(() => {
        // Backend offline — keep the user logged in with the local token.
        console.warn('⚠️ Não foi possível validar token no backend (offline?). Mantendo sessão local.');
      });
  },
  
  login: async (username: string, password: string) => {
    try {
      console.log('🔐 Attempting login for:', username);
      set({ error: null });
      
      const result = await api.login(username, password);
      
      if (!result.success) {
        console.error('❌ Login failed: Credenciais inválidas');
        set({ error: 'Credenciais inválidas' });
        return { success: false };
      }
      
      // Obter o token do localStorage (já foi salvo pela função api.login)
      const token = localStorage.getItem('token');
      
      if (!token) {
        console.error('❌ No token received from server');
        set({ error: 'Token não recebido do servidor' });
        return { success: false };
      }

      console.log('📥 Token received:', token.substring(0, 20) + '...');
      
      // Decode token and create user
      const payload = decodeToken(token);
      if (!payload) {
        console.error('❌ Could not decode received token');
        set({ error: 'Token inválido recebido' });
        return { success: false };
      }

      const user = createUserFromToken(payload);
      
      console.log('✅ Login successful for:', user.name, '(Role:', user.role + ')');
      set({ 
        isAuthenticated: true, 
        user,
        error: null
      });
      
      // Definir o usuário atual no chat store
      useChatStore.getState().setCurrentUser(user.id);
      
      return result; // Retorna o objeto completo para que login-page.tsx possa acessar is_temporary_password
    } catch (error) {
      // Garantir que o erro seja uma string
      let errorMessage;
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'object') {
        errorMessage = String(error);
      } else {
        errorMessage = String(error || 'Erro de conexão');
      }
      console.error('❌ Login error:', errorMessage);
      set({ 
        error: errorMessage,
        isAuthenticated: false,
        user: null
      });
      return { success: false };
    }
  },
  
  logout: () => {
    console.log('🚪 Logging out...');
    localStorage.removeItem('token');
    
    // Limpar sessão autenticada e voltar ao modo visitante
    useChatStore.getState().clearUserData();
    useChatStore.getState().setCurrentUser(GUEST_USER_ID);
    
    set({ 
      isAuthenticated: false, 
      user: null,
      error: null
    });
  },
  
  clearError: () => set({ error: null })
}));