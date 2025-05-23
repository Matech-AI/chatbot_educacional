// API utility functions
const API_BASE = '/api';

// Get auth token from localStorage
function getAuthToken(): string | null {
  return localStorage.getItem('token');
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
      localStorage.removeItem('token');
      window.location.href = '/login';
      throw new Error('Authentication required');
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
      'Content-Type': 'application/json',
      ...options.headers,
    };
  }

  const response = await apiRequest(endpoint, options);
  
  if (!response.ok) {
    const errorData = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorData}`);
  }

  return response.json();
}

// Specific API functions
export const api = {
  // Health check
  health: () => apiRequestJson('/health'),

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

  // System initialization
  initialize: (apiKey: string, driveFolderId?: string, credentialsFile?: File) => {
    const formData = new FormData();
    formData.append('api_key', apiKey);
    
    if (driveFolderId) {
      formData.append('drive_folder_id', driveFolderId);
    }
    
    if (credentialsFile) {
      formData.append('credentials_json', credentialsFile);
    }

    return apiRequest('/initialize', {
      method: 'POST',
      body: formData,
    });
  },

  // Drive sync
  syncDrive: (folderId: string) => apiRequestJson('/sync-drive', {
    method: 'POST',
    body: JSON.stringify({ folder_id: folderId }),
  }),
};