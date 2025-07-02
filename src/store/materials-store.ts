import { create } from 'zustand';
import { useCallback } from 'react';
import type { Material } from '../types';
import { api } from '../lib/api';

interface MaterialsState {
  materials: Material[];
  isLoading: boolean;
  isProcessing: boolean;
  isEmbedding: boolean;
  fetchMaterials: () => Promise<void>;
  uploadMaterial: (file: File, description?: string, tags?: string[]) => Promise<boolean>;
  deleteMaterial: (id: string) => Promise<boolean>;
  embedAllMaterials: () => Promise<{ success: boolean; message: string }>;
}

export const useMaterialsStore = create<MaterialsState>((set, get) => ({
  materials: [],
  isLoading: false,
  isProcessing: false,
  isEmbedding: false,

  fetchMaterials: async () => {
    if (get().isLoading) return;
    set({ isLoading: true });
    try {
      console.log('📚 Fetching materials...');
      const materials = await api.materials.list();
      console.log(`✅ Fetched ${materials.length} materials`);
      set({ materials, isLoading: false });
    } catch (error) {
      console.error('❌ Error in fetchMaterials:', error);
      set({ isLoading: false });
    }
  },

  uploadMaterial: async (file: File, description?: string, tags?: string[]) => {
    set({ isProcessing: true });
    try {
      console.log('📤 Uploading material:', file.name);
      await api.materials.upload(file, description, tags);
      console.log('✅ Upload successful, refreshing materials...');
      await get().fetchMaterials();
      set({ isProcessing: false });
      return true;
    } catch (error) {
      console.error('❌ Error in uploadMaterial:', error);
      set({ isProcessing: false });
      return false;
    }
  },

  deleteMaterial: async (id: string) => {
    set({ isProcessing: true });
    try {
      console.log('🗑️ Deleting material:', id);
      await api.materials.delete(id);
      console.log('✅ Delete successful, updating local state...');
      set(state => ({
        materials: state.materials.filter(material => material.id !== id),
        isProcessing: false,
      }));
      return true;
    } catch (error) {
      console.error('❌ Error in deleteMaterial:', error);
      set({ isProcessing: false });
      return false;
    }
  },

  embedAllMaterials: async () => {
    set({ isEmbedding: true });
    try {
      console.log('⚡ Starting embedding process for all materials...');
      const response = await api.materials.embedAll();
      console.log('✅ Embedding process finished:', response.message);
      set({ isEmbedding: false });
      return { success: response.success, message: response.message };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      console.error('❌ Error in embedAllMaterials:', errorMessage);
      set({ isEmbedding: false });
      return { success: false, message: errorMessage };
    }
  },
}));

// Hook personalizado para evitar re-renders desnecessários
export const useMaterialsActions = () => {
  const store = useMaterialsStore();
  
  return {
    fetchMaterials: useCallback(store.fetchMaterials, []),
    uploadMaterial: useCallback(store.uploadMaterial, []),
    deleteMaterial: useCallback(store.deleteMaterial, []),
    embedAllMaterials: useCallback(store.embedAllMaterials, []),
  };
};