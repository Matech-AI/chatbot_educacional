import { create } from 'zustand';
import { useCallback } from 'react';
import type { Material } from '../types';
import { apiRequest, apiRequestJson } from '@/lib/api';

interface MaterialsState {
  materials: Material[];
  isLoading: boolean;
  isProcessing: boolean;
  fetchMaterials: () => Promise<void>;
  uploadMaterial: (file: File, description?: string, tags?: string[]) => Promise<boolean>;
  deleteMaterial: (id: string) => Promise<boolean>;
}

// API functions
async function fetchMaterialsAPI(): Promise<Material[]> {
  try {
    const data = await apiRequestJson<any[]>('/materials');
    
    // Convert the response to match our Material interface
    return data.map((item: any) => ({
      id: item.id,
      title: item.title,
      description: item.description,
      type: item.type as 'pdf' | 'docx' | 'txt' | 'video',
      path: item.path,
      size: item.size,
      uploadedAt: new Date(item.uploadedAt),
      uploadedBy: item.uploadedBy,
      tags: item.tags || [],
    }));
  } catch (error) {
    console.error('Error fetching materials:', error);
    return [];
  }
}

async function uploadMaterialAPI(file: File, description?: string, tags?: string[]): Promise<boolean> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    if (description) {
      formData.append('description', description);
    }
    if (tags && tags.length > 0) {
      formData.append('tags', JSON.stringify(tags));
    }
    const resp = await apiRequest('/materials/upload', {
      method: 'POST',
      body: formData,
    });
    return resp.ok;
  } catch (error) {
    console.error('Error uploading material:', error);
    return false;
  }
}

async function deleteMaterialAPI(id: string): Promise<boolean> {
  try {
    const resp = await apiRequest(`/materials/${id}`, { method: 'DELETE' });
    return resp.ok;
  } catch (error) {
    console.error('Error deleting material:', error);
    return false;
  }
}

// Adicionar esta função de API
async function updateMaterialAPI(id: string, description?: string, tags?: string[]): Promise<boolean> {
  try {
    const formData = new FormData();
    if (description) {
      formData.append('description', description);
    }
    if (tags && tags.length > 0) {
      formData.append('tags', JSON.stringify(tags));
    }
    const resp = await apiRequest(`/materials/${id}/metadata`, {
      method: 'PUT',
      body: formData,
    });
    return resp.ok;
  } catch (error) {
    console.error('Error updating material:', error);
    return false;
  }
}

export const useMaterialsStore = create<MaterialsState>((set, get) => ({
  materials: [],
  isLoading: false,
  isProcessing: false,

  fetchMaterials: async () => {
    // Prevent multiple simultaneous fetches
    if (get().isLoading) {
      return;
    }

    set({ isLoading: true });
    try {
      console.log('📚 Fetching materials...');
      const materials = await fetchMaterialsAPI();
      console.log(`✅ Fetched ${materials.length} materials`);
      set({ materials, isLoading: false });
    } catch (error) {
      console.error('❌ Error in fetchMaterials:', error);
      set({ isLoading: false });
    }
  },

  uploadMaterial: async (file, description, tags) => {
    set({ isProcessing: true });
    try {
      console.log('📤 Uploading material:', file.name);
      const success = await uploadMaterialAPI(file, description, tags);
      if (success) {
        console.log('✅ Upload successful, refreshing materials...');
        // Refresh materials list after successful upload
        await get().fetchMaterials();
      }
      set({ isProcessing: false });
      return success;
    } catch (error) {
      console.error('❌ Error in uploadMaterial:', error);
      set({ isProcessing: false });
      return false;
    }
  },

  deleteMaterial: async (id) => {
    set({ isProcessing: true });
    try {
      console.log('🗑️ Deleting material:', id);
      const success = await deleteMaterialAPI(id);
      if (success) {
        console.log('✅ Delete successful, updating local state...');
        // Remove material from local state
        set(state => ({
          materials: state.materials.filter(material => material.id !== id),
          isProcessing: false
        }));
      } else {
        set({ isProcessing: false });
      }
      return success;
    } catch (error) {
      console.error('❌ Error in deleteMaterial:', error);
      set({ isProcessing: false });
      return false;
    }
  },

  // Adicionar esta função ao store
  updateMaterial: async (id, description, tags) => {
    set({ isProcessing: true });
    try {
      console.log('✏️ Updating material:', id);
      const success = await updateMaterialAPI(id, description, tags);
      if (success) {
        console.log('✅ Update successful, refreshing materials...');
        // Refresh materials list after successful update
        await get().fetchMaterials();
      }
      set({ isProcessing: false });
      return success;
    } catch (error) {
      console.error('❌ Error in updateMaterial:', error);
      set({ isProcessing: false });
      return false;
    }
  },
}));

// Atualizar a interface MaterialsState
interface MaterialsState {
  materials: Material[];
  isLoading: boolean;
  isProcessing: boolean;
  fetchMaterials: () => Promise<void>;
  uploadMaterial: (file: File, description?: string, tags?: string[]) => Promise<boolean>;
  deleteMaterial: (id: string) => Promise<boolean>;
  updateMaterial: (id: string, description?: string, tags?: string[]) => Promise<boolean>;
}

// Hook personalizado para evitar re-renders desnecessários
export const useMaterialsActions = () => {
  const store = useMaterialsStore();
  
  return {
    fetchMaterials: useCallback(store.fetchMaterials, []),
    uploadMaterial: useCallback(store.uploadMaterial, []),
    deleteMaterial: useCallback(store.deleteMaterial, []),
  };
};