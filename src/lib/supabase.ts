import { api } from './api';

// Checa se o usuário está autenticado
export const isAuthenticated = async () => {
  try {
    const user = await api.getCurrentUser();
    return !!user;
  } catch {
    return false;
  }
};

// Busca o perfil do usuário autenticado
export const getCurrentProfile = async () => {
  return api.getCurrentUser();
};

// Funções para materiais (exemplo)
export const getMaterials = async () => {
  return api.materials.list();
};

export const uploadMaterial = async (file: File, description?: string, tags?: string[]) => {
  return api.materials.upload(file, description, tags);
};

export const deleteMaterial = async (filename: string) => {
  return api.materials.delete(filename);
};