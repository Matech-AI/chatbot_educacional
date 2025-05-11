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
  description?: string,
  tags?: string[]
) {
  try {
    // Get current user
    const { data: { user }, error: userError } = await supabase.auth.getUser();
    if (userError) throw userError;
    if (!user) throw new Error('User not authenticated');

    // Upload file to storage
    const fileExt = file.name.split('.').pop();
    const fileName = `${Date.now()}.${fileExt}`;
    
    const { error: uploadError, data: uploadData } = await supabase.storage
      .from('materials')
      .upload(fileName, file, {
        cacheControl: '3600',
        upsert: false
      });

    if (uploadError) throw uploadError;

    // Get the public URL
    const { data: { publicUrl } } = supabase.storage
      .from('materials')
      .getPublicUrl(fileName);

    // Create material record
    const { data, error: insertError } = await supabase
      .from('materials')
      .insert({
        title: file.name,
        description,
        type: fileExt,
        path: publicUrl,
        size: file.size,
        tags,
        uploaded_by: user.id
      })
      .select()
      .single();

    if (insertError) throw insertError;

    return true;
  } catch (error) {
    console.error('Error uploading material:', error);
    throw error;
  }
}

export async function deleteMaterial(id: string) {
  try {
    // Get the material to find its file path
    const { data: material, error: fetchError } = await supabase
      .from('materials')
      .select('path')
      .eq('id', id)
      .single();

    if (fetchError) throw fetchError;

    // Extract filename from path
    const fileName = material.path.split('/').pop();

    // Delete file from storage
    if (fileName) {
      const { error: storageError } = await supabase.storage
        .from('materials')
        .remove([fileName]);

      if (storageError) throw storageError;
    }

    // Delete database record
    const { error: deleteError } = await supabase
      .from('materials')
      .delete()
      .eq('id', id);

    if (deleteError) throw deleteError;

    return true;
  } catch (error) {
    console.error('Error deleting material:', error);
    return false;
  }
}