// API utility functions - FIXED VERSION
const API_BASE = process.env.NODE_ENV === 'production' 
  ? 'https://your-backend-domain.com' 
  : 'http://localhost:8000';  // Backend runs on port 8000

// Get auth token from memory (localStorage not supported in Claude artifacts)
function getAuthToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('authToken');
  }
  return null;
}

function setAuthToken(token: string | null): void {
  if (typeof window !== 'undefined') {
    if (token) {
      localStorage.setItem('authToken', token);
    } else {
      localStorage.removeItem('authToken');
    }
  }
}

// Create headers with authentication
function createHeaders(additionalHeaders: Record<string, string> = {}): HeadersInit {
  const headers: Record<string, string> = {
    ...additionalHeaders,
  };

  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
}

// Generic API request function
export async function apiRequest(
  endpoint: string, 
  options: RequestInit = {}
): Promise<Response> {
  const url = `${API_BASE}${endpoint}`;
  
  const config: RequestInit = {
    ...options,
    headers: createHeaders(options.headers as Record<string, string>),
  };

  try {
    const response = await fetch(url, config);
    
    // Handle authentication errors
    if (response.status === 401) {
      setAuthToken(null);
      // In Claude artifacts, we can't redirect, so just throw error
      throw new Error('Authentication required - please login again');
    }

    return response;
  } catch (error) {
    console.error(`API request failed: ${endpoint}`, error);
    throw error;
  }
}

// API request with JSON response
export async function apiRequestJson<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T | null> {
  // Add JSON content type for POST/PUT/PATCH requests
  if (['POST', 'PUT', 'PATCH'].includes(options.method?.toUpperCase() || '')) {
    options.headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
  }

  const response = await apiRequest(endpoint, options);
  
  if (!response.ok) {
    const errorData = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorData}`);
  }

  // Handle cases where the response might be empty
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

// Specific API functions
export const api = {
  // Authentication
  login: (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    return apiRequest('/token', {
      method: 'POST',
      body: formData,
    });
  },

  // Set token after login
  setToken: (token: string) => {
    setAuthToken(token);
  },

  // Clear token on logout
  clearToken: () => {
    setAuthToken(null);
  },

  // Health check
  health: () => apiRequestJson('/health'),

  // Materials
  materials: {
    list: () => apiRequestJson('/materials'),
    
    upload: (file: File, description?: string, tags?: string[]) => {
      const formData = new FormData();
      formData.append('file', file);
      
      if (description) {
        formData.append('description', description);
      }
      
      if (tags && tags.length > 0) {
        formData.append('tags', JSON.stringify(tags));
      }

      return apiRequest('/materials/upload', {
        method: 'POST',
        body: formData,
      });
    },

    delete: (filename: string) => apiRequest(`/materials/${filename}`, {
      method: 'DELETE',
    }),

    download: (filename: string) => apiRequest(`/materials/${filename}`),
    
    embed: (materialId: string) => apiRequestJson('/materials/embed', {
      method: 'POST',
      body: JSON.stringify({ material_id: materialId }),
    }),
  },

  // Chat
  chat: (content: string) => apiRequestJson('/chat', {
    method: 'POST',
    body: JSON.stringify({ content }),
  }),

  chatAuth: (content: string, knowledgeBaseIds?: string[]) => apiRequestJson('/chat-auth', {
    method: 'POST',
    body: JSON.stringify({ content, knowledge_base_ids: knowledgeBaseIds }),
  }),

  knowledgeBases: {
    list: () => apiRequestJson('/knowledge-bases'),
  },

  documents: {
    list: (knowledgeBaseId?: string) => {
      const params = new URLSearchParams();
      if (knowledgeBaseId) {
        params.append('knowledge_base_id', knowledgeBaseId);
      }
      return apiRequestJson(`/documents?${params}`);
    },
    delete: (knowledgeBaseId?: string, filename?: string) => {
      const params = new URLSearchParams();
      if (knowledgeBaseId) {
        params.append('knowledge_base_id', knowledgeBaseId);
      }
      if (filename) {
        params.append('filename', filename);
      }
      return apiRequestJson(`/documents?${params}`, { method: 'DELETE' });
    },
  },

  // Drive Sync (Recursive)
  drive: {
    // Analyze folder structure without downloading
    analyzeFolder: (folderId: string, apiKey?: string) => {
      const params = new URLSearchParams({ folder_id: folderId });
      if (apiKey) params.append('api_key', apiKey);
      
      return apiRequestJson(`/drive/analyze-folder?${params}`);
    },

    // Start recursive sync
    syncRecursive: (folderId: string, apiKey?: string, credentialsJson?: string) => 
      apiRequestJson('/drive/sync-recursive', {
        method: 'POST',
        body: JSON.stringify({
          folder_id: folderId,
          ...(apiKey && { api_key: apiKey }),
          ...(credentialsJson && { credentials_json: credentialsJson })
        }),
      }),

    // Get download progress
    getProgress: (downloadId?: string) => {
      const params = downloadId ? `?download_id=${downloadId}` : '';
      return apiRequestJson(`/drive/download-progress${params}`);
    },

    // Cancel download
    cancelDownload: (downloadId: string) => 
      apiRequestJson('/drive/cancel-download', {
        method: 'POST',
        body: JSON.stringify({ download_id: downloadId }),
      }),

    // Get folder stats
    getFolderStats: () => apiRequestJson('/drive/folder-stats'),

    // Test connection
    testConnection: (apiKey?: string) => {
      const params = apiKey ? `?api_key=${apiKey}` : '';
      return apiRequestJson(`/drive/test-connection${params}`);
    },

    // Clear cache
    clearCache: () => apiRequestJson('/drive/clear-cache', { method: 'POST' }),
  },

  // Legacy Drive endpoints (for backward compatibility)
  legacy: {
    testDriveFolder: (folderId: string, apiKey?: string) => 
      apiRequestJson('/test-drive-folder', {
        method: 'POST',
        body: JSON.stringify({
          folder_id: folderId,
          ...(apiKey && { api_key: apiKey })
        }),
      }),

    syncDrive: (folderId: string, apiKey?: string, downloadFiles: boolean = true) => 
      apiRequestJson('/sync-drive', {
        method: 'POST',
        body: JSON.stringify({
          folder_id: folderId,
          download_files: downloadFiles,
          ...(apiKey && { api_key: apiKey })
        }),
      }),

    getDriveStats: () => apiRequestJson('/drive-stats'),
  },

  // Maintenance
  maintenance: {
    cleanupDuplicates: () => apiRequestJson('/maintenance/cleanup-duplicates', { method: 'POST' }),
    cleanupEmptyFolders: () => apiRequestJson('/maintenance/cleanup-empty-folders', { method: 'POST' }),
    optimizeStorage: () => apiRequestJson('/maintenance/optimize-storage', { method: 'POST' }),
    resetMaterials: () => apiRequestJson('/maintenance/reset-materials', { method: 'POST' }),
    resetChromaDB: () => apiRequestJson('/maintenance/reset-chromadb', { method: 'POST' }),
    resetComponent: (component: string, confirm: boolean = false) => 
      apiRequestJson('/maintenance/reset-component', {
        method: 'POST',
        body: JSON.stringify({ component, confirm }),
      }),
    getSystemReport: () => apiRequestJson('/maintenance/system-report'),
    healthCheck: () => apiRequestJson('/maintenance/health-check'),
  },

  // Analytics
  analytics: {
    getFolderStructure: () => apiRequestJson('/analytics/folder-structure'),
    getFileDistribution: () => apiRequestJson('/analytics/file-distribution'),
    getStorageEfficiency: () => apiRequestJson('/analytics/storage-efficiency'),
    getDownloadReport: () => apiRequestJson('/analytics/download-report'),
  },

  // System initialization
  initialize: (apiKey: string, driveFolderId?: string, driveApiKey?: string, credentialsFile?: File) => {
    const formData = new FormData();
    formData.append('api_key', apiKey);
    
    if (driveFolderId) {
      formData.append('drive_folder_id', driveFolderId);
    }
    
    if (driveApiKey) {
      formData.append('drive_api_key', driveApiKey);
    }
    
    if (credentialsFile) {
      formData.append('credentials_json', credentialsFile);
    }

    return apiRequest('/initialize', {
      method: 'POST',
      body: formData,
    });
  },

  // System status
  getStatus: () => apiRequestJson('/status'),

  // Debug endpoints
  debug: {
    drive: () => apiRequestJson('/debug/drive'),
  },
};