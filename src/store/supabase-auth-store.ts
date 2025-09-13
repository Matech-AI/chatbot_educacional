/**
 * Store de autenticação usando Supabase
 */

import { create } from 'zustand'
import { User, UserRole } from '../types'
import { auth, profile, Profile } from '../lib/supabase'
import { useChatStore } from './chat-store'

interface SupabaseAuthState {
  isAuthenticated: boolean
  user: User | null
  profile: Profile | null
  error: string | null
  isLoading: boolean
  
  // Ações
  signUp: (email: string, password: string, fullName: string, role?: string) => Promise<{ success: boolean; error?: string }>
  signIn: (email: string, password: string) => Promise<{ success: boolean; error?: string }>
  signOut: () => Promise<void>
  updateProfile: (updates: Partial<Profile>) => Promise<{ success: boolean; error?: string }>
  updatePassword: (newPassword: string) => Promise<{ success: boolean; error?: string }>
  resetPassword: (email: string) => Promise<{ success: boolean; error?: string }>
  clearError: () => void
  checkAuth: () => Promise<void>
  refreshProfile: () => Promise<void>
}

// Helper para converter Profile do Supabase para User do sistema
function profileToUser(profile: Profile): User {
  return {
    id: profile.id,
    name: profile.full_name,
    email: profile.email,
    role: profile.role as UserRole,
    avatar: profile.avatar_url || getDefaultAvatar(profile.role),
    isActive: profile.is_active,
    createdAt: new Date(profile.created_at),
    lastLogin: null // O Supabase não armazena last_login por padrão
  }
}

function getDefaultAvatar(role: string): string {
  const avatars = {
    admin: '👨‍💼',
    instructor: '👨‍🏫',
    student: '👨‍🎓'
  }
  return avatars[role as keyof typeof avatars] || avatars.student
}

export const useSupabaseAuthStore = create<SupabaseAuthState>((set, get) => ({
  isAuthenticated: false,
  user: null,
  profile: null,
  error: null,
  isLoading: false,

  signUp: async (email: string, password: string, fullName: string, role: string = 'student') => {
    try {
      set({ isLoading: true, error: null })
      
      const { data, error } = await auth.signUp(email, password, fullName, role)
      
      if (error) {
        set({ error: error.message, isLoading: false })
        return { success: false, error: error.message }
      }
      
      // Se o usuário foi criado com sucesso, mas precisa confirmar email
      if (data.user && !data.session) {
        set({ isLoading: false })
        return { 
          success: true, 
          error: 'Usuário criado! Verifique seu email para confirmar a conta.' 
        }
      }
      
      // Se já tem sessão (email confirmado automaticamente)
      if (data.user && data.session) {
        const userProfile = await profile.getCurrentProfile()
        if (userProfile) {
          const user = profileToUser(userProfile)
          set({
            isAuthenticated: true,
            user,
            profile: userProfile,
            isLoading: false,
            error: null
          })
          
          // Definir usuário no chat store
          useChatStore.getState().setCurrentUser(user.id)
        }
      }
      
      return { success: true }
      
    } catch (error: any) {
      set({ error: error.message, isLoading: false })
      return { success: false, error: error.message }
    }
  },

  signIn: async (email: string, password: string) => {
    try {
      set({ isLoading: true, error: null })
      
      const { data, error } = await auth.signIn(email, password)
      
      if (error) {
        set({ error: error.message, isLoading: false })
        return { success: false, error: error.message }
      }
      
      if (data.user) {
        // Buscar perfil do usuário
        const userProfile = await profile.getCurrentProfile()
        
        if (userProfile) {
          const user = profileToUser(userProfile)
          set({
            isAuthenticated: true,
            user,
            profile: userProfile,
            isLoading: false,
            error: null
          })
          
          // Definir usuário no chat store
          useChatStore.getState().setCurrentUser(user.id)
          
          return { success: true }
        } else {
          set({ error: 'Perfil do usuário não encontrado', isLoading: false })
          return { success: false, error: 'Perfil do usuário não encontrado' }
        }
      }
      
      set({ error: 'Erro desconhecido no login', isLoading: false })
      return { success: false, error: 'Erro desconhecido no login' }
      
    } catch (error: any) {
      set({ error: error.message, isLoading: false })
      return { success: false, error: error.message }
    }
  },

  signOut: async () => {
    try {
      await auth.signOut()
      set({
        isAuthenticated: false,
        user: null,
        profile: null,
        error: null
      })
      
      // Limpar usuário do chat store
      useChatStore.getState().setCurrentUser(null)
      
    } catch (error: any) {
      set({ error: error.message })
    }
  },

  updateProfile: async (updates: Partial<Profile>) => {
    try {
      set({ isLoading: true, error: null })
      
      const updatedProfile = await profile.updateProfile(updates)
      
      if (updatedProfile) {
        const user = profileToUser(updatedProfile)
        set({
          user,
          profile: updatedProfile,
          isLoading: false,
          error: null
        })
        
        return { success: true }
      }
      
      set({ error: 'Falha ao atualizar perfil', isLoading: false })
      return { success: false, error: 'Falha ao atualizar perfil' }
      
    } catch (error: any) {
      set({ error: error.message, isLoading: false })
      return { success: false, error: error.message }
    }
  },

  updatePassword: async (newPassword: string) => {
    try {
      set({ isLoading: true, error: null })
      
      await auth.updatePassword(newPassword)
      
      set({ isLoading: false, error: null })
      return { success: true }
      
    } catch (error: any) {
      set({ error: error.message, isLoading: false })
      return { success: false, error: error.message }
    }
  },

  resetPassword: async (email: string) => {
    try {
      set({ isLoading: true, error: null })
      
      await auth.resetPassword(email)
      
      set({ isLoading: false, error: null })
      return { success: true }
      
    } catch (error: any) {
      set({ error: error.message, isLoading: false })
      return { success: false, error: error.message }
    }
  },

  clearError: () => {
    set({ error: null })
  },

  checkAuth: async () => {
    try {
      set({ isLoading: true })
      
      const user = await auth.getCurrentUser()
      
      if (user) {
        const userProfile = await profile.getCurrentProfile()
        
        if (userProfile) {
          const userObj = profileToUser(userProfile)
          set({
            isAuthenticated: true,
            user: userObj,
            profile: userProfile,
            isLoading: false,
            error: null
          })
          
          // Definir usuário no chat store
          useChatStore.getState().setCurrentUser(userObj.id)
        } else {
          set({
            isAuthenticated: false,
            user: null,
            profile: null,
            isLoading: false,
            error: 'Perfil não encontrado'
          })
        }
      } else {
        set({
          isAuthenticated: false,
          user: null,
          profile: null,
          isLoading: false,
          error: null
        })
      }
      
    } catch (error: any) {
      set({
        isAuthenticated: false,
        user: null,
        profile: null,
        isLoading: false,
        error: error.message
      })
    }
  },

  refreshProfile: async () => {
    try {
      const userProfile = await profile.getCurrentProfile()
      
      if (userProfile) {
        const user = profileToUser(userProfile)
        set({
          user,
          profile: userProfile
        })
      }
      
    } catch (error: any) {
      console.error('Erro ao atualizar perfil:', error)
    }
  }
}))

// Escutar mudanças de autenticação do Supabase
auth.onAuthStateChange((event, session) => {
  const store = useSupabaseAuthStore.getState()
  
  if (event === 'SIGNED_IN' && session?.user) {
    // Usuário fez login
    store.checkAuth()
  } else if (event === 'SIGNED_OUT') {
    // Usuário fez logout
    store.signOut()
  } else if (event === 'TOKEN_REFRESHED' && session?.user) {
    // Token foi renovado
    store.refreshProfile()
  }
})
