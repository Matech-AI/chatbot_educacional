import { create } from 'zustand';
import { User, UserRole } from '../types';
import { supabase, getCurrentProfile } from '../lib/supabase';

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
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
      const profile = await getCurrentProfile();
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
  },

  checkAuth: async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        set({ isAuthenticated: false, user: null });
        return;
      }

      const profile = await getCurrentProfile();
      if (!profile) {
        set({ isAuthenticated: false, user: null });
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
        }
      });
    } catch (error) {
      console.error('Error checking auth:', error);
      set({ isAuthenticated: false, user: null });
    }
  }
}));