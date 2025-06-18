import { create } from 'zustand';
import { api } from '../lib/api';
import { Material } from '../types';

interface MaterialsState {
  materials: Material[];
  isLoading: boolean;
  error: string | null;
  fetchMaterials: () => Promise<void>;
  embedMaterial: (materialId: string) => Promise<boolean>;
}

export const useMaterialsStore = create<MaterialsState>((set) => ({
  materials: [],
  isLoading: false,
  error: null,
  fetchMaterials: async () => {
    set({ isLoading: true, error: null });
    try {
      const materials = await api.materials.list();
      set({ materials, isLoading: false });
    } catch (error) {
      console.error("Failed to fetch materials:", error);
      set({ isLoading: false, error: 'Failed to fetch materials' });
    }
  },
  embedMaterial: async (materialId: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.materials.embed(materialId);
      set({ isLoading: false });
      // Optionally, you could refetch materials or update a specific material's state
      return true;
    } catch (error) {
      console.error("Failed to embed material:", error);
      set({ isLoading: false, error: `Failed to embed material ${materialId}` });
      return false;
    }
  },
}));