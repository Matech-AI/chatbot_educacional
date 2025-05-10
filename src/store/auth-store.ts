import { create } from 'zustand';
import { User, UserRole } from '../types';
import { supabase } from '../lib/supabase';

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  apiKey: string | null;
  login: (email: string, password: string, apiKey: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  apiKey: null,
  
  login: async (email: string, password: string, apiKey: string) => {
    try {
      const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (authError) throw authError;

      // Get user profile data
      const { data: profile, error: profileError } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', authData.user.id)
        .single();

      if (profileError) throw profileError;

      const user: User = {
        id: authData.user.id,
        name: profile.full_name,
        email: authData.user.email!,
        role: profile.role as UserRole,
        avatarUrl: profile.avatar_url
      };

      set({ 
        isAuthenticated: true, 
        user,
        apiKey 
      });

      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  },
  
  logout: async () => {
    try {
      await supabase.auth.signOut();
      set({ 
        isAuthenticated: false, 
        user: null, 
        apiKey: null 
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  }
}));