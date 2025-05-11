import { create } from 'zustand';
import { User, UserRole } from '../types';

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  clearError: () => void;
  checkAuth: () => void;
}

// Mock user data
const USERS = {
  admin: {
    id: 'admin-1',
    name: 'Administrador',
    role: 'admin' as UserRole,
    password: 'admin123',
    avatarUrl: 'https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg'
  },
  instrutor: {
    id: 'inst-1',
    name: 'Instrutor',
    role: 'instructor' as UserRole,
    password: 'instrutor123',
    avatarUrl: 'https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg'
  },
  aluno: {
    id: 'stud-1',
    name: 'Aluno',
    role: 'student' as UserRole,
    password: 'aluno123',
    avatarUrl: 'https://images.pexels.com/photos/614810/pexels-photo-614810.jpeg'
  }
};

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  error: null,
  
  checkAuth: () => {
    // Since we're using mock data, we'll just ensure the user starts as logged out
    set({ 
      isAuthenticated: false,
      user: null,
      error: null
    });
  },
  
  login: async (username: string, password: string) => {
    try {
      set({ error: null });
      
      // Get user from mock data
      const user = USERS[username as keyof typeof USERS];
      
      // Validate credentials
      if (!user || user.password !== password) {
        set({ error: 'Usuário ou senha incorretos' });
        return false;
      }
      
      // Create user object without password
      const { password: _, ...userWithoutPassword } = user;
      
      set({ 
        isAuthenticated: true, 
        user: userWithoutPassword,
        error: null
      });
      
      return true;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
      console.error('Login error:', error);
      set({ 
        error: `Erro ao fazer login: ${errorMessage}`,
        isAuthenticated: false,
        user: null
      });
      return false;
    }
  },
  
  logout: () => {
    set({ 
      isAuthenticated: false, 
      user: null,
      error: null
    });
  },
  
  clearError: () => set({ error: null })
}));