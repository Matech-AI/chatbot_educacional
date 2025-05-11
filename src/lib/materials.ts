import { supabase } from './supabase';
import type { Material } from '../types';

export async function fetchMaterials() {
  const { data, error } = await supabase
    .from('materials')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) {
    console.error('Error fetching materials:', error);
    throw error;
  }

  return data as Material[];
}

export async function uploadMaterial(
  file: File,
  metadata: {
    title: string;
    description?: string;
    tags?: string[];
  }
) {
  try {
    // Upload file to Supabase Storage
    const fileExt = file.name.split('.').pop();
    const fileName = `${Date.now()}.${fileExt}`;
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('materials')
      .upload(fileName, file);

    if (uploadError) throw uploadError;

    // Create material record in database
    const { data, error } = await supabase
      .from('materials')
      .insert({
        title: metadata.title,
        description: metadata.description,
        type: fileExt,
        path: uploadData.path,
        size: file.size,
        tags: metadata.tags
      })
      .select()
      .single();

    if (error) throw error;

    return data as Material;
  } catch (error) {
    console.error('Error uploading material:', error);
    throw error;
  }
}

export async function deleteMaterial(id: string) {
  const { error } = await supabase
    .from('materials')
    .delete()
    .eq('id', id);

  if (error) {
    console.error('Error deleting material:', error);
    throw error;
  }
}