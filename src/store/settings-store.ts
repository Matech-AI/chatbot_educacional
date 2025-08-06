import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiRequestJson } from '../lib/api';

export interface SystemSettings {
  general: {
    siteName: string;
    description: string;
    language: string;
    timezone: string;
    maxFileSize: number;
    allowedFileTypes: string;
  };
  security: {
    sessionTimeout: number;
    maxLoginAttempts: number;
    requirePasswordChange: boolean;
    enableTwoFactor: boolean;
  };
  notifications: {
    emailNotifications: boolean;
    pushNotifications: boolean;
    maintenanceAlerts: boolean;
    systemUpdates: boolean;
  };
}

interface SettingsState {
  settings: SystemSettings;
  isLoading: boolean;
  isDirty: boolean;
  loadSettings: () => Promise<boolean>;
  updateSettings: (updates: Partial<SystemSettings>) => Promise<boolean>;
  saveSettings: () => Promise<boolean>;
  resetToDefault: () => void;
  setDirty: (dirty: boolean) => void;
}

// Configuração padrão
const DEFAULT_SETTINGS: SystemSettings = {
  general: {
    siteName: "DNA da Força",
    description: "Sistema Educacional de Treinamento Físico",
    language: "pt-BR",
    timezone: "America/Sao_Paulo",
    maxFileSize: 50,
    allowedFileTypes: ".pdf,.docx,.txt,.pptx",
  },
  security: {
    sessionTimeout: 180,
    maxLoginAttempts: 3,
    requirePasswordChange: false,
    enableTwoFactor: false,
  },
  notifications: {
    emailNotifications: true,
    pushNotifications: false,
    maintenanceAlerts: true,
    systemUpdates: true,
  },
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      settings: DEFAULT_SETTINGS,
      isLoading: false,
      isDirty: false,
      
      loadSettings: async () => {
        try {
          set({ isLoading: true });
          
          // Fazer chamada real para a API usando apiRequestJson
          const data = await apiRequestJson('/settings', {
            method: 'GET',
          });
          
          if (data.status === 'success') {
            set({ 
              settings: { ...DEFAULT_SETTINGS, ...data.settings },
              isLoading: false,
              isDirty: false
            });
            return true;
          } else {
            throw new Error(data.message || 'Erro ao carregar configurações');
          }
        } catch (error) {
          set({ isLoading: false });
          console.error('❌ Erro ao carregar configurações:', error);
          return false;
        }
      },
      
      updateSettings: async (updates) => {
        try {
          const currentSettings = get().settings;
          const newSettings = { ...currentSettings, ...updates };
          
          set({ 
            settings: newSettings,
            isDirty: true
          });
          
          return true;
        } catch (error) {
          console.error('❌ Erro ao atualizar configurações:', error);
          return false;
        }
      },
      
      saveSettings: async () => {
        try {
          set({ isLoading: true });
          
          const settings = get().settings;
          
          // Fazer chamada real para a API usando apiRequestJson
          const result = await apiRequestJson('/settings', {
            method: 'POST',
            body: JSON.stringify(settings),
          });
          
          if (result.status === 'success') {
            set({ 
              isLoading: false,
              isDirty: false
            });
            return true;
          } else {
            throw new Error(result.message || 'Erro ao salvar configurações');
          }
        } catch (error) {
          set({ isLoading: false });
          console.error('❌ Erro ao salvar configurações:', error);
          return false;
        }
      },
      
      resetToDefault: () => {
        set({ 
          settings: { ...DEFAULT_SETTINGS },
          isDirty: false
        });
      },
      
      setDirty: (dirty: boolean) => {
        set({ isDirty: dirty });
      }
    }),
    {
      name: 'system-settings-storage',
      partialize: (state) => ({ 
        settings: state.settings
      }),
      skipHydration: false,
    }
  )
); 