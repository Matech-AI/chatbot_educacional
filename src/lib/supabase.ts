// Mock authentication functions
export const isAuthenticated = async () => {
  return true;
};

export const getCurrentProfile = async () => {
  return {
    id: 'mock-user',
    full_name: 'Test User',
    role: 'admin',
    avatar_url: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
};

// Mock materials data
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

export const supabase = {
  auth: {
    getSession: async () => ({
      data: {
        session: {
          user: {
            id: 'mock-user',
            email: 'test@example.com'
          },
          access_token: 'mock-token'
        }
      },
      error: null
    }),
    getUser: async () => ({
      data: {
        user: {
          id: 'mock-user',
          email: 'test@example.com'
        }
      },
      error: null
    })
  },
  from: (table: string) => ({
    select: () => ({
      order: () => Promise.resolve({ data: mockMaterials, error: null }),
      eq: () => Promise.resolve({ data: mockMaterials[0], error: null })
    }),
    insert: () => ({
      select: () => ({
        single: () => Promise.resolve({ data: mockMaterials[0], error: null })
      })
    }),
    delete: () => ({
      eq: () => Promise.resolve({ error: null })
    })
  }),
  storage: {
    from: () => ({
      upload: () => Promise.resolve({ data: { path: 'mock-path' }, error: null }),
      getPublicUrl: () => ({ data: { publicUrl: 'https://example.com/mock-file' } }),
      remove: () => Promise.resolve({ error: null })
    })
  }
};