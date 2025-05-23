import type { Material } from '../types';

export async function fetchMaterials(): Promise<Material[]> {
  const res = await fetch('/api/materials');
  return await res.json();
}

export async function uploadMaterial(
  file: File,
  description?: string,
  tags?: string[]
) {
  const formData = new FormData();
  formData.append('file', file);
  // Se quiser enviar description/tags, adicione ao formData
  const res = await fetch('/api/materials/upload', {
    method: 'POST',
    body: formData,
  });
  return await res.json();
}

export async function syncDriveMaterials(folderId: string) {
  const res = await fetch('/api/sync-drive', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ folder_id: folderId }),
  });
  return await res.json();
}