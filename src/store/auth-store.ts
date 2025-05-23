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

// Helper function to decode JWT payload
function decodeJWTPayload(token: string): any {
  try {
    const base64Url = token.split('.')[1];
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

// Helper function to create user from JWT payload
function createUserFromToken(payload: any): User {
  // Map backend roles to frontend roles
  const roleMap: Record<string, UserRole> = {
    'admin': 'admin',
    'instructor': 'instructor', 
    'student': 'student'
  };

  return {
    id: payload.sub || 'unknown',
    name: payload.sub === 'admin' ? 'Administrador' : 
          payload.sub === 'instrutor' ? 'Instrutor' : 
          payload.sub === 'aluno' ? 'Aluno' : payload.sub,
    role: roleMap[payload.role] || 'student',
    email: payload.email,
    avatarUrl: getDefaultAvatar(payload.role)
  };
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
      set({ 
        isAuthenticated: false,
        user: null,
        error: null
      });
      return;
    }

    try {
      const payload = decodeJWTPayload(token);
      
      if (!payload) {
        throw new Error('Invalid token');
      }

      // Check if token is expired
      const currentTime = Date.now() / 1000;
      if (payload.exp && payload.exp < currentTime) {
        throw new Error('Token expired');
      }

      const user = createUserFromToken(payload);
      
      set({ 
        isAuthenticated: true,
        user,
        error: null
      });
    } catch (error) {
      console.error('Token validation failed:', error);
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
      set({ error: null });
      
      const response = await api.login(username, password);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        set({ error: errorData.detail || 'Credenciais inválidas' });
        return false;
      }
      
      const data = await response.json();
      const token = data.access_token;
      
      if (!token) {
        set({ error: 'Token não recebido do servidor' });
        return false;
      }

      // Save token to localStorage
      localStorage.setItem('token', token);
      
      // Decode token and create user
      const payload = decodeJWTPayload(token);
      if (!payload) {
        set({ error: 'Token inválido recebido' });
        return false;
      }

      const user = createUserFromToken(payload);
      
      set({ 
        isAuthenticated: true, 
        user,
        error: null
      });
      
      return true;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro de conexão';
      console.error('Login error:', error);
      set({ 
        error: errorMessage,
        isAuthenticated: false,
        user: null
      });
      return false;
    }
  },
  
  logout: () => {
    localStorage.removeItem('token');
    set({ 
      isAuthenticated: false, 
      user: null,
      error: null
    });
  },
  
  clearError: () => set({ error: null })
}));