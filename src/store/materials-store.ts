import { create } from 'zustand';
import type { Material } from '../types';

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
    const response = await fetch('/api/materials', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch materials');
    }
    
    const data = await response.json();
    
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
    
    const response = await fetch('/api/materials/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error('Failed to upload material');
    }
    
    return true;
  } catch (error) {
    console.error('Error uploading material:', error);
    return false;
  }
}

async function deleteMaterialAPI(id: string): Promise<boolean> {
  try {
    const response = await fetch(`/api/materials/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete material');
    }
    
    return true;
  } catch (error) {
    console.error('Error deleting material:', error);
    return false;
  }
}

export const useMaterialsStore = create<MaterialsState>((set, get) => ({
  materials: [],
  isLoading: false,
  isProcessing: false,

  fetchMaterials: async () => {
    set({ isLoading: true });
    try {
      const materials = await fetchMaterialsAPI();
      set({ materials, isLoading: false });
    } catch (error) {
      console.error('Error in fetchMaterials:', error);
      set({ isLoading: false });
    }
  },

  uploadMaterial: async (file, description, tags) => {
    set({ isProcessing: true });
    try {
      const success = await uploadMaterialAPI(file, description, tags);
      if (success) {
        // Refresh materials list after successful upload
        await get().fetchMaterials();
      }
      set({ isProcessing: false });
      return success;
    } catch (error) {
      console.error('Error in uploadMaterial:', error);
      set({ isProcessing: false });
      return false;
    }
  },

  deleteMaterial: async (id) => {
    set({ isProcessing: true });
    try {
      const success = await deleteMaterialAPI(id);
      if (success) {
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
      console.error('Error in deleteMaterial:', error);
      set({ isProcessing: false });
      return false;
    }
  },
}));