'use client';
import { create } from 'zustand';
import { api } from '../lib/api';

export interface Document {
  filename: string;
  knowledge_base_id: string;
  last_updated: number;
  source: string;
}

interface DocumentState {
  documents: Document[];
  isLoading: boolean;
  error: string | null;
  fetchDocuments: (knowledgeBaseId?: string) => Promise<void>;
  deleteDocument: (filename: string, knowledgeBaseId?: string) => Promise<boolean>;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  isLoading: false,
  error: null,
  fetchDocuments: async (knowledgeBaseId?: string) => {
    set({ isLoading: true, error: null });
    try {
      const documents = await api.documents.list(knowledgeBaseId);
      set({ documents, isLoading: false });
    } catch (error) {
      console.error("Failed to fetch documents:", error);
      set({ isLoading: false, error: 'Failed to fetch documents' });
    }
  },
  deleteDocument: async (filename: string, knowledgeBaseId?: string) => {
    const previousDocuments = get().documents;
    // Optimistically remove the document from the UI
    set((state) => ({
      documents: state.documents.filter((doc) => doc.filename !== filename),
    }));
    try {
      await api.documents.delete(knowledgeBaseId, filename);
      return true;
    } catch (error) {
      console.error("Failed to delete document:", error);
      // Revert the state if the API call fails
      set({ documents: previousDocuments, error: `Failed to delete document ${filename}` });
      return false;
    }
  },
}));