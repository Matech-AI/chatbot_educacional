import { create } from 'zustand';
import { User, UserRole } from '../types';
import { api } from '../lib/api';

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
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
      console.log('🔐 No token found');
      set({ 
        isAuthenticated: false,
        user: null,
        error: null
      });
      return;
    }

    try {
      const payload = decodeToken(token);
      
      if (!payload) {
        throw new Error('Invalid token format');
      }

      // Check if token is expired (para JWT real)
      const currentTime = Date.now() / 1000;
      if (payload.exp && payload.exp < currentTime) {
        throw new Error('Token expired');
      }

      const user = createUserFromToken(payload);
      
      console.log('✅ Token validated successfully for user:', user.name);
      set({ 
        isAuthenticated: true,
        user,
        error: null
      });
    } catch (error) {
      console.error('❌ Token validation failed:', error);
      localStorage.removeItem('token');
      set({ 
        isAuthenticated: false,
        user: null,
        error: null
      });
    }
  },
  
  login: async (username: string, password: string) => {
    try {
      console.log('🔐 Attempting login for:', username);
      set({ error: null });
      
      const response = await api.login(username, password);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || 'Credenciais inválidas';
        console.error('❌ Login failed:', errorMessage);
        set({ error: errorMessage });
        return false;
      }
      
      const data = await response.json();
      const token = data.access_token;
      
      if (!token) {
        console.error('❌ No token received from server');
        set({ error: 'Token não recebido do servidor' });
        return false;
      }

      console.log('📥 Token received:', token.substring(0, 20) + '...');
      
      // Save token to localStorage
      localStorage.setItem('token', token);
      
      // Decode token and create user
      const payload = decodeToken(token);
      if (!payload) {
        console.error('❌ Could not decode received token');
        set({ error: 'Token inválido recebido' });
        return false;
      }

      const user = createUserFromToken(payload);
      
      console.log('✅ Login successful for:', user.name, '(Role:', user.role + ')');
      set({ 
        isAuthenticated: true, 
        user,
        error: null
      });
      
      return true;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro de conexão';
      console.error('❌ Login error:', error);
      set({ 
        error: errorMessage,
        isAuthenticated: false,
        user: null
      });
      return false;
    }
  },
  
  logout: () => {
    console.log('🚪 Logging out...');
    localStorage.removeItem('token');
    set({ 
      isAuthenticated: false, 
      user: null,
      error: null
    });
  },
  
  clearError: () => set({ error: null })
}));