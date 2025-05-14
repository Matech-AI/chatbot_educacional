// Temporary mock authentication functions
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