import { create } from 'zustand';
import { AssistantConfig } from '../types';

interface AssistantState {
  config: AssistantConfig;
  templates: string[];
  isLoading: boolean;
  updateConfig: (updates: Partial<AssistantConfig>) => Promise<boolean>;
  saveAsTemplate: (name: string) => Promise<boolean>;
  loadTemplate: (name: string) => Promise<boolean>;
}

// Default configuration
const DEFAULT_CONFIG: AssistantConfig = {
  name: 'Assistente Educacional de Educação Física',
  description: 'Especializado em responder dúvidas sobre treinamento e fisiologia do exercício',
  prompt: `Você é um ASSISTENTE EDUCACIONAL especializado. Seu objetivo é auxiliar estudantes a compreender o conteúdo do curso e responder dúvidas com base nos materiais fornecidos. Siga estas diretrizes:

1. CONTEXTO DO CURSO:
   - Basear suas respostas exclusivamente nos materiais do curso fornecidos
   - Citar a fonte específica (aula, página, vídeo) de onde a informação foi extraída
   - Nunca inventar informações que não estejam nos materiais do curso

2. ESTILO DE RESPOSTA:
   - Usar linguagem clara, direta e educativa
   - Adaptar o nível de complexidade ao contexto da pergunta
   - Fornecer explicações passo a passo quando apropriado
   - Incluir exemplos práticos para conceitos complexos

3. CITAÇÕES E FONTES:
   - Sempre indicar a origem da informação (ex: "Conforme a Aula 3, página 7...")
   - Para citações diretas, usar aspas e referenciar a fonte exata
   - Se a pergunta não puder ser respondida com os materiais disponíveis, informar isto claramente

4. ESTRATÉGIAS PEDAGÓGICAS:
   - Favorecer a compreensão sobre a memorização
   - Usar analogias para explicar conceitos difíceis
   - Incentivar o pensamento crítico ao invés de fornecer apenas respostas diretas
   - Sugerir materiais adicionais do curso que possam ser relevantes para aprofundamento`,
  model: 'gpt-4o-mini',
  temperature: 0.1,
  chunkSize: 2500,
  chunkOverlap: 0,
  retrievalSearchType: 'mmr',
  embeddingModel: 'text-embedding-ada-002'
};

export const useAssistantStore = create<AssistantState>((set) => ({
  config: DEFAULT_CONFIG,
  templates: ['Educação Física', 'Nutrição Esportiva', 'Anatomia Humana'],
  isLoading: false,
  
  updateConfig: async (updates) => {
    try {
      set({ isLoading: true });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      
      set(state => ({ 
        config: { ...state.config, ...updates },
        isLoading: false
      }));
      
      return true;
    } catch (error) {
      set({ isLoading: false });
      console.error('Error updating assistant config:', error);
      return false;
    }
  },
  
  saveAsTemplate: async (name) => {
    try {
      set({ isLoading: true });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      set(state => ({ 
        templates: [...state.templates, name],
        isLoading: false
      }));
      
      return true;
    } catch (error) {
      set({ isLoading: false });
      console.error('Error saving template:', error);
      return false;
    }
  },
  
  loadTemplate: async (name) => {
    try {
      set({ isLoading: true });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // In a real app, this would load a template from the backend
      // For now, we'll just pretend we loaded a template
      set(state => ({ 
        config: {
          ...state.config,
          name: `Assistente de ${name}`,
          description: `Especializado em ${name}`,
        },
        isLoading: false
      }));
      
      return true;
    } catch (error) {
      set({ isLoading: false });
      console.error('Error loading template:', error);
      return false;
    }
  }
}));