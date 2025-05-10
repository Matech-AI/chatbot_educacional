import { create } from 'zustand';
import { Material } from '../types';
import { generateUniqueId } from '../lib/utils';

interface MaterialsState {
  materials: Material[];
  isLoading: boolean;
  isProcessing: boolean;
  uploadMaterial: (file: File, description?: string, tags?: string[]) => Promise<boolean>;
  deleteMaterial: (id: string) => Promise<boolean>;
  updateMaterial: (id: string, updates: Partial<Material>) => Promise<boolean>;
}

// Mock materials data
const MOCK_MATERIALS: Material[] = [
  {
    id: 'mat-1',
    title: 'Princípios do Treinamento de Força',
    description: 'Fundamentos científicos sobre a aplicação de cargas para desenvolvimento muscular',
    type: 'pdf',
    path: '/data/materiais/princ-treinamento.pdf',
    size: 2450000,
    uploadedAt: new Date(2023, 5, 15),
    uploadedBy: 'Instrutor',
    tags: ['força', 'fundamentos', 'periodização']
  },
  {
    id: 'mat-2',
    title: 'Periodização do Treinamento',
    description: 'Métodos avançados de periodização para atletas e praticantes',
    type: 'pdf',
    path: '/data/materiais/periodizacao.pdf',
    size: 1840000,
    uploadedAt: new Date(2023, 6, 22),
    uploadedBy: 'Instrutor',
    tags: ['periodização', 'avançado', 'desempenho']
  },
  {
    id: 'mat-3',
    title: 'Nutrição Esportiva',
    description: 'Guia completo sobre nutrição para maximizar resultados',
    type: 'pdf',
    path: '/data/materiais/nutricao.pdf',
    size: 3120000,
    uploadedAt: new Date(2023, 7, 10),
    uploadedBy: 'Instrutor',
    tags: ['nutrição', 'suplementação', 'recuperação']
  },
  {
    id: 'mat-4',
    title: 'Prevenção de Lesões',
    description: 'Estratégias e técnicas para evitar lesões durante o treinamento',
    type: 'docx',
    path: '/data/materiais/prevencao.docx',
    size: 890000,
    uploadedAt: new Date(2023, 8, 5),
    uploadedBy: 'Instrutor',
    tags: ['lesões', 'prevenção', 'segurança']
  }
];

export const useMaterialsStore = create<MaterialsState>((set, get) => ({
  materials: MOCK_MATERIALS,
  isLoading: false,
  isProcessing: false,
  
  uploadMaterial: async (file, description, tags) => {
    set({ isProcessing: true });
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Get file type
      const extension = file.name.split('.').pop()?.toLowerCase() || '';
      let type: 'pdf' | 'docx' | 'txt' | 'video' = 'txt';
      
      if (extension === 'pdf') type = 'pdf';
      else if (extension === 'docx') type = 'docx';
      else if (['mp4', 'webm', 'mov', 'avi'].includes(extension)) type = 'video';
      
      // Create new material
      const newMaterial: Material = {
        id: generateUniqueId(),
        title: file.name,
        description: description || '',
        type,
        path: `/data/materiais/${file.name}`,
        size: file.size,
        uploadedAt: new Date(),
        uploadedBy: 'Usuário',
        tags: tags || []
      };
      
      set(state => ({ 
        materials: [...state.materials, newMaterial],
        isProcessing: false
      }));
      
      return true;
    } catch (error) {
      set({ isProcessing: false });
      console.error('Error uploading material:', error);
      return false;
    }
  },
  
  deleteMaterial: async (id) => {
    set({ isProcessing: true });
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      set(state => ({ 
        materials: state.materials.filter(material => material.id !== id),
        isProcessing: false
      }));
      
      return true;
    } catch (error) {
      set({ isProcessing: false });
      console.error('Error deleting material:', error);
      return false;
    }
  },
  
  updateMaterial: async (id, updates) => {
    set({ isProcessing: true });
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      set(state => ({ 
        materials: state.materials.map(material => 
          material.id === id ? { ...material, ...updates } : material
        ),
        isProcessing: false
      }));
      
      return true;
    } catch (error) {
      set({ isProcessing: false });
      console.error('Error updating material:', error);
      return false;
    }
  }
}));