import { create } from 'zustand';
import { User, UserRole } from '../types';
import { supabase, getCurrentProfile } from '../lib/supabase';

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  error: null,
  
  login: async (email: string, password: string) => {
    try {
      set({ error: null });

      // Sign in with email and password
      const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (authError) {
        let errorMessage = 'Erro ao fazer login';
        
        // Map Supabase error messages to user-friendly messages
        switch (authError.message) {
          case 'Invalid login credentials':
            errorMessage = 'Email ou senha incorretos';
            break;
          case 'Email not confirmed':
            errorMessage = 'Email não confirmado';
            break;
          case 'User not found':
            errorMessage = 'Usuário não encontrado';
            break;
          default:
            errorMessage = `Erro: ${authError.message}`;
        }
        
        console.error('Authentication error:', {
          code: authError.status,
          message: authError.message,
          details: authError
        });
        
        set({ error: errorMessage });
        return false;
      }

      if (!authData.user) {
        console.error('No user data returned from authentication');
        set({ error: 'Dados do usuário não encontrados' });
        return false;
      }

      // Fetch user profile
      const profile = await getCurrentProfile();
      if (!profile) {
        console.error('No profile found for user:', authData.user.id);
        set({ error: 'Perfil do usuário não encontrado' });
        
        // Sign out since we couldn't get the profile
        await supabase.auth.signOut();
        return false;
      }

      // Create user object
      const user: User = {
        id: authData.user.id,
        name: profile.full_name,
        email: authData.user.email!,
        role: profile.role as UserRole,
        avatarUrl: profile.avatar_url || undefined
      };

      set({ 
        isAuthenticated: true, 
        user,
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
  
  logout: async () => {
    try {
      await supabase.auth.signOut();
      set({ 
        isAuthenticated: false, 
        user: null,
        error: null
      });
    } catch (error) {
      console.error('Logout error:', error);
      set({ error: 'Erro ao fazer logout' });
    }
  },

  checkAuth: async () => {
    try {
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();
      
      if (sessionError) {
        console.error('Session check error:', sessionError);
        set({ 
          isAuthenticated: false, 
          user: null,
          error: 'Erro ao verificar sessão'
        });
        return;
      }

      if (!session) {
        set({ 
          isAuthenticated: false, 
          user: null,
          error: null
        });
        return;
      }

      const profile = await getCurrentProfile();
      if (!profile) {
        console.error('No profile found for session user:', session.user.id);
        set({ 
          isAuthenticated: false, 
          user: null,
          error: 'Perfil não encontrado'
        });
        return;
      }

      set({
        isAuthenticated: true,
        user: {
          id: session.user.id,
          name: profile.full_name,
          email: session.user.email!,
          role: profile.role as UserRole,
          avatarUrl: profile.avatar_url || undefined
        },
        error: null
      });
    } catch (error) {
      console.error('Error checking auth:', error);
      set({ 
        isAuthenticated: false, 
        user: null,
        error: 'Erro ao verificar autenticação'
      });
    }
  },

  clearError: () => set({ error: null })
}));