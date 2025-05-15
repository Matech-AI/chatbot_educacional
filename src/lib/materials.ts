import type { Material } from '../types';

// Mock materials data
const mockMaterials: Material[] = [
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

let materials = [...mockMaterials];

export async function fetchMaterials() {
  return materials;
}

export async function uploadMaterial(
  file: File,
  description?: string,
  tags?: string[]
) {
  try {
    const newMaterial: Material = {
      id: Math.random().toString(36).substring(7),
      title: file.name,
      description,
      type: file.name.split('.').pop() as 'pdf' | 'docx' | 'txt' | 'video',
      path: URL.createObjectURL(file),
      size: file.size,
      uploadedAt: new Date(),
      uploadedBy: 'mock-user',
      tags
    };

    materials = [newMaterial, ...materials];
    return true;
  } catch (error) {
    console.error('Error uploading material:', error);
    throw error;
  }
}

export async function deleteMaterial(id: string) {
  try {
    materials = materials.filter(m => m.id !== id);
    return true;
  } catch (error) {
    console.error('Error deleting material:', error);
    return false;
  }
}