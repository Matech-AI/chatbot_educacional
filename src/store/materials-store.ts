import { create } from 'zustand';
import { Material } from '../types';
import { supabase } from '../lib/supabase';
import { syncDriveMaterials } from '../lib/drive';

interface MaterialsState {
  materials: Material[];
  isLoading: boolean;
  isProcessing: boolean;
  error: string | null;
  fetchMaterials: () => Promise<void>;
  uploadMaterial: (file: File, description?: string, tags?: string[]) => Promise<boolean>;
  deleteMaterial: (id: string) => Promise<boolean>;
  syncWithDrive: (folderId: string, credentials: string) => Promise<boolean>;
}

export const useMaterialsStore = create<MaterialsState>((set, get) => ({
  materials: [],
  isLoading: false,
  isProcessing: false,
  error: null,

  fetchMaterials: async () => {
    set({ isLoading: true, error: null });
    try {
      const { data, error } = await supabase
        .from('materials')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;

      set({ materials: data as Material[], isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao carregar materiais';
      set({ error: message, isLoading: false });
    }
  },

  uploadMaterial: async (file, description, tags) => {
    set({ isProcessing: true, error: null });
    try {
      // Upload file to storage
      const fileExt = file.name.split('.').pop();
      const fileName = `${Date.now()}.${fileExt}`;
      
      const { error: uploadError } = await supabase.storage
        .from('materials')
        .upload(fileName, file);

      if (uploadError) throw uploadError;

      // Get file URL
      const { data: { publicUrl } } = supabase.storage
        .from('materials')
        .getPublicUrl(fileName);

      // Create database record
      const { data, error } = await supabase
        .from('materials')
        .insert({
          title: file.name,
          description,
          type: fileExt,
          path: publicUrl,
          size: file.size,
          tags
        })
        .select()
        .single();

      if (error) throw error;

      // Update state
      set(state => ({
        materials: [data as Material, ...state.materials],
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
      // Get material to find file path
      const material = get().materials.find(m => m.id === id);
      if (!material) throw new Error('Material não encontrado');

      // Delete from storage if it's a local file
      if (material.path.includes(supabase.storageUrl)) {
        const fileName = material.path.split('/').pop();
        if (fileName) {
          await supabase.storage
            .from('materials')
            .remove([fileName]);
        }
      }

      // Delete database record
      const { error } = await supabase
        .from('materials')
        .delete()
        .eq('id', id);

      if (error) throw error;

      // Update state
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
  },

  syncWithDrive: async (folderId, credentials) => {
    set({ isProcessing: true, error: null });
    try {
      await syncDriveMaterials(folderId, credentials);
      await get().fetchMaterials();
      set({ isProcessing: false });
      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao sincronizar com Drive';
      set({ error: message, isProcessing: false });
      return false;
    }
  }
}));