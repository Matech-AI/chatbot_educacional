import { create } from 'zustand';
import { Material } from '../types';

// Mock materials data - copied from the mock DB to be self-contained
const mockMaterials = [
  {
    id: '1',
    title: 'Fundamentos do Treinamento de Força',
    description: 'Guia completo sobre os princípios básicos do treinamento de força',
    type: 'pdf',
    path: 'https://example.com/materials/strength-training.pdf',
    size: 2500000,
    uploadedAt: new Date(),
    uploadedBy: 'mock-user',
    tags: ['força', 'fundamentos', 'treino']
  },
  {
    id: '2',
    title: 'Anatomia Muscular',
    description: 'Estudo detalhado dos principais grupos musculares',
    type: 'pdf',
    path: 'https://example.com/materials/muscle-anatomy.pdf',
    size: 1800000,
    uploadedAt: new Date(),
    uploadedBy: 'mock-user',
    tags: ['anatomia', 'músculos']
  }
];

interface MaterialsState {
  materials: Material[];
  isLoading: boolean;
  isProcessing: boolean;
  error: string | null;
  fetchMaterials: () => Promise<void>;
  uploadMaterial: (file: File, description?: string, tags?: string[]) => Promise<boolean>;
  deleteMaterial: (id: string) => Promise<boolean>;
}

export const useMaterialsStore = create<MaterialsState>((set) => ({
  materials: [],
  isLoading: false,
  isProcessing: false,
  error: null,

  fetchMaterials: async () => {
    set({ isLoading: true, error: null });
    try {
      // Use mock data directly
      setTimeout(() => {
        set({ materials: mockMaterials as Material[], isLoading: false });
      }, 500); // Simulate network delay
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao carregar materiais';
      set({ error: message, isLoading: false });
    }
  },

  uploadMaterial: async (file, description, tags) => {
    set({ isProcessing: true, error: null });
    try {
      // Mock successful upload
      const mockMaterial: Material = {
        id: Math.random().toString(36).substring(7),
        title: file.name,
        description,
        type: file.name.split('.').pop() as any,
        path: URL.createObjectURL(file),
        size: file.size,
        uploadedAt: new Date(),
        uploadedBy: 'mock-user',
        tags
      };

      set(state => ({
        materials: [mockMaterial, ...state.materials],
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