import { create } from 'zustand';
import { User, UserRole } from '../types';
import { supabase } from '../lib/supabase';

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  
  login: async (email: string, password: string) => {
    try {
      // Sign in with email and password
      const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (authError) {
        console.error('Authentication error:', authError.message);
        return false;
      }

      if (!authData.user) {
        console.error('No user data returned');
        return false;
      }

      // Fetch user profile
      const { data: profile, error: profileError } = await supabase
        .from('profiles')
        .select('full_name, role, avatar_url')
        .eq('id', authData.user.id)
        .single();

      if (profileError) {
        console.error('Profile fetch error:', profileError.message);
        await supabase.auth.signOut();
        return false;
      }

      if (!profile) {
        console.error('No profile found');
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
        user
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
        user: null
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  }
}));