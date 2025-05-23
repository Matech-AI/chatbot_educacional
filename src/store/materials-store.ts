import { create } from 'zustand';
import { fetchMaterials, uploadMaterial, syncDriveMaterials } from '../lib/materials';
import type { Material } from '../types';

interface MaterialsState {
  materials: Material[];
  isLoading: boolean;
  isProcessing: boolean;
  fetchMaterials: () => Promise<void>;
  uploadMaterial: (file: File, description?: string, tags?: string[]) => Promise<boolean>;
  deleteMaterial: (id: string) => Promise<boolean>;
}

export const useMaterialsStore = create<MaterialsState>((set, get) => ({
  materials: [],
  isLoading: false,
  isProcessing: false,

  fetchMaterials: async () => {
    set({ isLoading: true });
    try {
      const materials = await fetchMaterials();
      set({ materials });
    } finally {
      set({ isLoading: false });
    }
  },

  uploadMaterial: async (file, description, tags) => {
    set({ isProcessing: true });
    try {
      const result = await uploadMaterial(file, description, tags);
      await get().fetchMaterials();
      return result.success;
    } finally {
      set({ isProcessing: false });
    }
  },

  deleteMaterial: async (id) => {
    // Implemente a exclusão no backend e recarregue a lista
    return false;
  }
}));