// API utility functions - FIXED VERSION
const API_BASE = process.env.NODE_ENV === 'production' 
  ? 'https://your-backend-domain.com' 
  : '/api';  // Usar /api para que o proxy do Vite funcione

// Get auth token from memory (localStorage not supported in Claude artifacts)
const AUTH_TOKEN_KEY = 'token';

function getAuthToken(): string | null {
  try {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  } catch (e) {
    console.error('Failed to get auth token from localStorage', e);
    return null;
  }
}

function setAuthToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(AUTH_TOKEN_KEY, token);
    } else {
      localStorage.removeItem(AUTH_TOKEN_KEY);
    }
  } catch (e) {
    console.error('Failed to set auth token in localStorage', e);
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

  // Ensure Content-Type is set for JSON requests if not already specified
  if (!headers['Content-Type'] && !headers['content-type']) {
    headers['Content-Type'] = 'application/json';
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
      const errorData = await response.text();
      throw new Error(`401 Unauthorized: ${errorData}`);
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
): Promise<T> {
  // Add JSON content type for POST/PUT requests
  if (['POST', 'PUT', 'PATCH'].includes(options.method?.toUpperCase() || '')) {
    options.headers = {
      ...options.headers,
      'Content-Type': 'application/json',
    };
  }

  try {
    const response = await apiRequest(endpoint, options);
    
    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorData}`);
    }

    return response.json();
  } catch (error) {
    console.error(`API request failed: ${endpoint}`, error);
    throw error;
  }
}

// Specific API functions
export const api = {
  // Authentication
  // No objeto api
  login: async (username: string, password: string) => {
  // Use URLSearchParams para enviar dados no formato de formulário
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await apiRequest('/auth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: formData,
  });
  
  if (response.ok) {
    const data = await response.json();
    setAuthToken(data.access_token);
    return { success: true, is_temporary_password: data.is_temporary_password };
  }
  
  return { success: false };
  },

  // Set token after login
  setToken: (token: string) => {
    setAuthToken(token);
  },

  // Clear token on logout
  clearToken: () => {
    setAuthToken(null);
  },

  // Get current user info
  getCurrentUser: () => apiRequestJson('/auth/me'),

  // Change password
  changePassword: (currentPassword: string, newPassword: string) => 
    apiRequestJson('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    }),

  // Reset password (admin only)
  resetPassword: (username: string, newPassword: string) =>
    apiRequestJson('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({
        username,
        new_password: newPassword,
      }),
    }),
    
  // Reset password (public)
  requestPasswordReset: (username: string) => 
    apiRequestJson('/auth/public/request-password-reset', { 
      method: 'POST', 
      body: JSON.stringify({ 
        username, 
      }), 
    }), 

  // Confirm password reset (public)
  confirmPasswordReset: (token: string, username: string, newPassword: string) => 
    apiRequestJson('/auth/public/confirm-password-reset', { 
      method: 'POST', 
      body: JSON.stringify({ 
        token, 
        username, 
        new_password: newPassword, 
      }), 
    }),

  // User management (admin only)
  users: {
    list: () => apiRequestJson('/auth/users'),
    create: (userData: any) => apiRequestJson('/auth/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    }),
    update: (username: string, userData: any) => apiRequestJson(`/auth/users/${username}`, {
      method: 'PUT', 
      body: JSON.stringify(userData),
    }),
    delete: (username: string) => apiRequestJson(`/auth/users/${username}`, {
      method: 'DELETE',
    }),
  },

  // Approved users management (admin only)
  approvedUsers: {
    list: () => apiRequestJson('/auth/approved-users'),
    add: (userData: any) => apiRequestJson('/auth/approved-users', {
      method: 'POST',
      body: JSON.stringify(userData),
    }),
    remove: (username: string) => apiRequestJson(`/auth/approved-users/${username}`, {
      method: 'DELETE',
    }),
  },

  // Health check
  health: () => apiRequestJson('/health'),

  // Enhanced Educational Chat
  educationalChat: (data: {
    content: string;
    user_level?: string;
    learning_style?: string;
    session_id?: string;
    current_topic?: string;
    learning_objectives?: string[];
  }) => apiRequestJson('/chat/educational', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // Topic exploration
  exploreTopic: (topic: string, userLevel: string = 'intermediate') =>
    apiRequestJson('/chat/explore-topic', {
      method: 'POST',
      body: JSON.stringify({ topic, user_level: userLevel }),
    }),

  // Learning path
  getLearningPath: (topic: string, userLevel: string = 'intermediate') =>
    apiRequestJson(`/chat/learning-path/${encodeURIComponent(topic)}?user_level=${userLevel}`),

  // Session context
  getSessionContext: (sessionId: string) =>
    apiRequestJson(`/chat/session/${sessionId}/context`),

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
  },

  // Chat
  chat: (content: string) => apiRequestJson('/chat', {
    method: 'POST',
    body: JSON.stringify({ content }),
  }),

  chatAuth: (content: string) => apiRequestJson('/chat-auth', {
    method: 'POST',
    body: JSON.stringify({ content }),
  }),

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
    getDriveStatsDetailed: () => apiRequestJson('/drive-stats-detailed'),
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

  // Video endpoints
  video: {
    // Get video embed data with optional topic-based timestamp
    getEmbed: (videoPath: string, driveId?: string, topicQuery?: string) => 
      apiRequestJson('/video/embed', {
        method: 'POST',
        body: JSON.stringify({
          video_path: videoPath,
          ...(driveId && { drive_id: driveId }),
          ...(topicQuery && { topic_query: topicQuery })
        }),
      }),

    // Search for videos related to a topic
    search: (topicQuery: string, userLevel: string = 'intermediate') =>
      apiRequestJson('/video/search', {
        method: 'POST',
        body: JSON.stringify({
          topic_query: topicQuery,
          user_level: userLevel
        }),
      }),

    // Analyze video content and get timestamps
    analyze: (videoId: string) => apiRequestJson(`/video/analyze/${encodeURIComponent(videoId)}`),

    // List all available videos
    list: () => apiRequestJson('/video/list'),
  },

  // Debug endpoints
  debug: {
    drive: () => apiRequestJson('/debug/drive'),
  },
};