import { create } from 'zustand';
import { AssistantConfig } from '../types';
import { api } from '../lib/api';

interface AssistantState {
  config: AssistantConfig;
  templates: string[];
  isLoading: boolean;
  loadConfig: () => Promise<boolean>;
  updateConfig: (updates: Partial<AssistantConfig>) => Promise<boolean>;
  saveAsTemplate: (name: string) => Promise<boolean>;
  loadTemplate: (name: string) => Promise<boolean>;
}

// Template configurations for each specialty
export const TEMPLATE_CONFIGS: Record<string, AssistantConfig> = {
  'Educação Física': {
    name: 'Assistente Educacional de Educação Física',
    description: 'Especializado em responder dúvidas sobre treinamento, fisiologia do exercício e metodologia do ensino',
    prompt: `Você é um ASSISTENTE EDUCACIONAL especializado em EDUCAÇÃO FÍSICA. Seu objetivo é auxiliar estudantes a compreender conceitos de treinamento, fisiologia do exercício, biomecânica e metodologia do ensino. Siga estas diretrizes:

1. CONTEXTO DO CURSO:
   - Basear suas respostas exclusivamente nos materiais do curso fornecidos
   - Citar a fonte específica (aula, página, vídeo) de onde a informação foi extraída
   - Nunca inventar informações que não estejam nos materiais do curso

2. ESTILO DE RESPOSTA:
   - Usar linguagem clara, técnica mas acessível
   - Relacionar teoria com aplicação prática no treinamento
   - Fornecer exemplos de exercícios e progressões quando apropriado
   - Explicar os princípios fisiológicos por trás dos conceitos

3. CITAÇÕES E FONTES:
   - Sempre indicar a origem da informação (ex: "Conforme a Aula 3, página 7...")
   - Para citações diretas, usar aspas e referenciar a fonte exata
   - Se a pergunta não puder ser respondida com os materiais disponíveis, informar isto claramente

4. ESTRATÉGIAS PEDAGÓGICAS:
   - Conectar conceitos teóricos com aplicações práticas no treinamento
   - Usar analogias relacionadas ao movimento humano
   - Incentivar análise crítica de métodos de treinamento
   - Sugerir progressões e adaptações para diferentes níveis

Use {context}, {chat_history} e {question} como variáveis no template.`,
    model: 'gpt-4o-mini',
    temperature: 0.1,
    chunkSize: 2000,
    chunkOverlap: 100,
    retrievalSearchType: 'mmr',
    embeddingModel: 'text-embedding-ada-002'
  },
  'Nutrição Esportiva': {
    name: 'Assistente Educacional de Nutrição Esportiva',
    description: 'Especializado em nutrição aplicada ao esporte, suplementação e estratégias alimentares para performance',
    prompt: `Você é um ASSISTENTE EDUCACIONAL especializado em NUTRIÇÃO ESPORTIVA. Seu objetivo é auxiliar estudantes a compreender conceitos de nutrição aplicada ao esporte, metabolismo energético, suplementação e estratégias alimentares. Siga estas diretrizes:

1. CONTEXTO DO CURSO:
   - Basear suas respostas exclusivamente nos materiais do curso fornecidos
   - Citar a fonte específica (aula, página, vídeo) de onde a informação foi extraída
   - Nunca inventar informações que não estejam nos materiais do curso

2. ESTILO DE RESPOSTA:
   - Usar linguagem científica mas didática
   - Relacionar conceitos nutricionais com performance esportiva
   - Fornecer exemplos práticos de aplicação nutricional
   - Explicar os mecanismos bioquímicos quando relevante

3. CITAÇÕES E FONTES:
   - Sempre indicar a origem da informação (ex: "Conforme a Aula 5, página 12...")
   - Para citações diretas, usar aspas e referenciar a fonte exata
   - Se a pergunta não puder ser respondida com os materiais disponíveis, informar isto claramente

4. ESTRATÉGIAS PEDAGÓGICAS:
   - Conectar bioquímica nutricional com aplicações práticas
   - Usar exemplos de diferentes modalidades esportivas
   - Incentivar análise crítica de estratégias nutricionais
   - Sugerir adequações nutricionais para diferentes objetivos

Use {context}, {chat_history} e {question} como variáveis no template.`,
    model: 'gpt-4o-mini',
    temperature: 0.2,
    chunkSize: 2200,
    chunkOverlap: 150,
    retrievalSearchType: 'mmr',
    embeddingModel: 'text-embedding-ada-002'
  },
  'Anatomia Humana': {
    name: 'Assistente Educacional de Anatomia Humana',
    description: 'Especializado em anatomia sistêmica, cinesiologia e biomecânica do movimento humano',
    prompt: `Você é um ASSISTENTE EDUCACIONAL especializado em ANATOMIA HUMANA. Seu objetivo é auxiliar estudantes a compreender a estrutura do corpo humano, cinesiologia e biomecânica do movimento. Siga estas diretrizes:

1. CONTEXTO DO CURSO:
   - Basear suas respostas exclusivamente nos materiais do curso fornecidos
   - Citar a fonte específica (aula, página, atlas, vídeo) de onde a informação foi extraída
   - Nunca inventar informações que não estejam nos materiais do curso

2. ESTILO DE RESPOSTA:
   - Usar terminologia anatômica precisa e correta
   - Relacionar estrutura anatômica com função
   - Fornecer descrições espaciais detalhadas
   - Explicar relações entre diferentes sistemas corporais

3. CITAÇÕES E FONTES:
   - Sempre indicar a origem da informação (ex: "Conforme o Atlas, Figura 4.2...")
   - Para citações diretas, usar aspas e referenciar a fonte exata
   - Se a pergunta não puder ser respondida com os materiais disponíveis, informar isto claramente

4. ESTRATÉGIAS PEDAGÓGICAS:
   - Conectar anatomia descritiva com anatomia funcional
   - Usar analogias para explicar estruturas complexas
   - Incentivar visualização tridimensional das estruturas
   - Sugerir correlações clínicas e biomecânicas relevantes

Use {context}, {chat_history} e {question} como variáveis no template.`,
    model: 'gpt-4o-mini',
    temperature: 0.05,
    chunkSize: 1800,
    chunkOverlap: 200,
    retrievalSearchType: 'mmr',
    embeddingModel: 'text-embedding-ada-002'
  }
};

// Default configuration (Educação Física)
const DEFAULT_CONFIG: AssistantConfig = TEMPLATE_CONFIGS['Educação Física'];

export const useAssistantStore = create<AssistantState>((set, get) => ({
  config: DEFAULT_CONFIG,
  templates: ['Educação Física', 'Nutrição Esportiva', 'Anatomia Humana'],
  isLoading: false,

  loadConfig: async () => {
    console.log('[Store] Attempting to load assistant config...');
    try {
      set({ isLoading: true });
      const remoteConfig = await api.assistant.getConfig();
      set({ config: remoteConfig, isLoading: false });
      return true;
    } catch (error) {
      set({ isLoading: false });
      console.error('Error loading assistant config:', error);
      return false;
    }
  },
  
  updateConfig: async (updates) => {
    try {
      set({ isLoading: true });
      const currentConfig = get().config;
      const newConfig = { ...currentConfig, ...updates };
      await api.assistant.updateConfig(newConfig);
      
      set({ config: newConfig, isLoading: false });
      
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
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Load the specific template configuration
      const templateConfig = TEMPLATE_CONFIGS[name];
      
      if (templateConfig) {
        console.log(`📋 Loading template: ${name}`);
        set({ 
          config: { ...templateConfig },
          isLoading: false
        });
      } else {
        console.warn(`⚠️ Template not found: ${name}`);
        // Fallback to default if template not found
        set({ 
          config: { ...DEFAULT_CONFIG },
          isLoading: false
        });
      }
      
      return true;
    } catch (error) {
      set({ isLoading: false });
      console.error('Error loading template:', error);
      return false;
    }
  }
}));

export function getAssistantConfig(name: string): AssistantConfig | undefined {
  return TEMPLATE_CONFIGS[name];
}