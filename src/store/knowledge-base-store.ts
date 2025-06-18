import { create } from 'zustand';
import { api } from '../lib/api';

export interface KnowledgeBase {
  id: string;
  name: string;
}

interface KnowledgeBaseState {
  knowledgeBases: KnowledgeBase[];
  isLoading: boolean;
  error: string | null;
  fetchKnowledgeBases: () => Promise<void>;
}

export const useKnowledgeBaseStore = create<KnowledgeBaseState>((set) => ({
  knowledgeBases: [],
  isLoading: false,
  error: null,
  fetchKnowledgeBases: async () => {
    set({ isLoading: true, error: null });
    try {
      const data: string[] = await api.knowledgeBases.list();
      const formattedData: KnowledgeBase[] = data.map((name: string) => ({ id: name, name }));
      set({ knowledgeBases: formattedData, isLoading: false });
    } catch (error) {
      console.error("Failed to fetch knowledge bases:", error);
      set({ isLoading: false, error: 'Failed to fetch knowledge bases' });
    }
  },
}));