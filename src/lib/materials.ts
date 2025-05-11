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
    // Create bucket if it doesn't exist
    const { data: buckets } = await supabase.storage.listBuckets();
    const materialsBucket = buckets?.find(b => b.name === 'materials');
    
    if (!materialsBucket) {
      const { data: newBucket, error: bucketError } = await supabase.storage.createBucket('materials', {
        public: false,
        allowedMimeTypes: ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
      });
      
      if (bucketError) throw bucketError;
    }

    // Upload file to Supabase Storage
    const fileExt = file.name.split('.').pop();
    const fileName = `${Date.now()}.${fileExt}`;
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('materials')
      .upload(fileName, file, {
        cacheControl: '3600',
        upsert: false
      });

    if (uploadError) throw uploadError;

    // Get the public URL for the uploaded file
    const { data: { publicUrl } } = supabase.storage
      .from('materials')
      .getPublicUrl(fileName);

    // Create material record in database
    const { data, error } = await supabase
      .from('materials')
      .insert({
        title: metadata.title,
        description: metadata.description,
        type: fileExt,
        path: publicUrl,
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
  } catch (error) {
    console.error('Error deleting material:', error);
    throw error;
  }
}