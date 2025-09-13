/**
 * Cliente Supabase para autenticação e operações de banco de dados
 */

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Variáveis de ambiente do Supabase não configuradas')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
})

// Tipos para o banco de dados
export interface Profile {
  id: string
  full_name: string
  email: string
  role: 'admin' | 'instructor' | 'student'
  avatar_url?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  email: string
  profile: Profile
}

// Funções de autenticação
export const auth = {
  // Registrar novo usuário
  async signUp(email: string, password: string, fullName: string, role: string = 'student') {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
          role: role
        }
      }
    })
    
    if (error) throw error
    return data
  },

  // Fazer login
  async signIn(email: string, password: string) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password
    })
    
    if (error) throw error
    return data
  },

  // Fazer logout
  async signOut() {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  },

  // Obter usuário atual
  async getCurrentUser() {
    const { data: { user } } = await supabase.auth.getUser()
    return user
  },

  // Obter sessão atual
  async getSession() {
    const { data: { session } } = await supabase.auth.getSession()
    return session
  },

  // Atualizar senha
  async updatePassword(newPassword: string) {
    const { data, error } = await supabase.auth.updateUser({
      password: newPassword
    })
    
    if (error) throw error
    return data
  },

  // Reset de senha
  async resetPassword(email: string) {
    const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`
    })
    
    if (error) throw error
    return data
  },

  // Escutar mudanças de autenticação
  onAuthStateChange(callback: (event: string, session: any) => void) {
    return supabase.auth.onAuthStateChange(callback)
  }
}

// Funções de perfil
export const profile = {
  // Obter perfil do usuário atual
  async getCurrentProfile(): Promise<Profile | null> {
    const user = await auth.getCurrentUser()
    if (!user) return null

    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', user.id)
      .single()

    if (error) throw error
    return data
  },

  // Atualizar perfil
  async updateProfile(updates: Partial<Profile>) {
    const user = await auth.getCurrentUser()
    if (!user) throw new Error('Usuário não autenticado')

    const { data, error } = await supabase
      .from('profiles')
      .update({
        ...updates,
        updated_at: new Date().toISOString()
      })
      .eq('id', user.id)
      .select()
      .single()

    if (error) throw error
    return data
  },

  // Obter todos os perfis (apenas admin)
  async getAllProfiles(): Promise<Profile[]> {
    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .order('created_at', { ascending: false })

    if (error) throw error
    return data
  },

  // Atualizar role do usuário (apenas admin)
  async updateUserRole(userId: string, role: string) {
    const { data, error } = await supabase
      .from('profiles')
      .update({
        role,
        updated_at: new Date().toISOString()
      })
      .eq('id', userId)
      .select()
      .single()

    if (error) throw error
    return data
  }
}

// Funções de materiais
export const materials = {
  // Obter todos os materiais
  async getAll() {
    const { data, error } = await supabase
      .from('materials')
      .select('*')
      .order('created_at', { ascending: false })

    if (error) throw error
    return data
  },

  // Obter material por ID
  async getById(id: string) {
    const { data, error } = await supabase
      .from('materials')
      .select('*')
      .eq('id', id)
      .single()

    if (error) throw error
    return data
  },

  // Criar novo material
  async create(material: any) {
    const { data, error } = await supabase
      .from('materials')
      .insert(material)
      .select()
      .single()

    if (error) throw error
    return data
  },

  // Atualizar material
  async update(id: string, updates: any) {
    const { data, error } = await supabase
      .from('materials')
      .update({
        ...updates,
        updated_at: new Date().toISOString()
      })
      .eq('id', id)
      .select()
      .single()

    if (error) throw error
    return data
  },

  // Deletar material
  async delete(id: string) {
    const { error } = await supabase
      .from('materials')
      .delete()
      .eq('id', id)

    if (error) throw error
  }
}

// Funções de chat
export const chat = {
  // Obter sessões de chat do usuário
  async getSessions(userId: string) {
    const { data, error } = await supabase
      .from('chat_sessions')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })

    if (error) throw error
    return data
  },

  // Criar nova sessão
  async createSession(session: any) {
    const { data, error } = await supabase
      .from('chat_sessions')
      .insert(session)
      .select()
      .single()

    if (error) throw error
    return data
  },

  // Obter mensagens de uma sessão
  async getMessages(sessionId: string) {
    const { data, error } = await supabase
      .from('chat_messages')
      .select('*')
      .eq('session_id', sessionId)
      .order('created_at', { ascending: true })

    if (error) throw error
    return data
  },

  // Adicionar mensagem
  async addMessage(message: any) {
    const { data, error } = await supabase
      .from('chat_messages')
      .insert(message)
      .select()
      .single()

    if (error) throw error
    return data
  }
}

export default supabase