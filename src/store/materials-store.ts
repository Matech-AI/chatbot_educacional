import { create } from 'zustand';
import { Material } from '../types';
import { fetchMaterials, uploadMaterial, deleteMaterial } from '../lib/materials';

interface MaterialsState {
  materials: Material[];
  isLoading: boolean;
  isProcessing: boolean;
  error: string | null;
  fetchMaterials: () => Promise<void>;
  uploadMaterial: (file: File, description?: string, tags?: string[]) => Promise<boolean>;
  deleteMaterial: (id: string) => Promise<boolean>;
}

export const useMaterialsStore = create<MaterialsState>((set, get) => ({
  materials: [],
  isLoading: false,
  isProcessing: false,
  error: null,

  fetchMaterials: async () => {
    set({ isLoading: true, error: null });
    try {
      const materials = await fetchMaterials();
      set({ materials, isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao carregar materiais';
      set({ error: message, isLoading: false });
    }
  },

  uploadMaterial: async (file, description, tags) => {
    set({ isProcessing: true, error: null });
    try {
      const material = await uploadMaterial(file, {
        title: file.name,
        description,
        tags
      });
      
      set(state => ({
        materials: [material, ...state.materials],
        isProcessing: false
      }));
      
      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao fazer upload';
      set({ error: message, isProcessing: false });
      return false;
    }
  },

  deleteMaterial: async (id) => {
    set({ isProcessing: true, error: null });
    try {
      await deleteMaterial(id);
      set(state => ({
        materials: state.materials.filter(m => m.id !== id),
        isProcessing: false
      }));
      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao excluir material';
      set({ error: message, isProcessing: false });
      return false;
    }
  }
}));