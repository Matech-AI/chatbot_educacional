import { driveClient } from './drive-client';
import { supabase } from './supabase';

export async function processDriveMaterials(folderId: string) {
  try {
    // Initialize the Drive client
    await driveClient.initialize();

    // List all files in the folder
    const files = await driveClient.listFiles(folderId);

    // Process each file
    const processedFiles = await Promise.all(
      files.map(async (file) => {
        // Only process documents
        if (!file.mimeType?.includes('pdf') && 
            !file.mimeType?.includes('document') && 
            !file.mimeType?.includes('text')) {
          return null;
        }

        try {
          // Download file
          const { buffer, mimeType } = await driveClient.downloadFile(file.id!);

          // Upload to Supabase storage
          const fileName = `${Date.now()}-${file.name}`;
          const { error: uploadError } = await supabase.storage
            .from('materials')
            .upload(fileName, buffer, {
              contentType: mimeType,
              cacheControl: '3600'
            });

          if (uploadError) throw uploadError;

          // Get public URL
          const { data: { publicUrl } } = supabase.storage
            .from('materials')
            .getPublicUrl(fileName);

          // Create material record
          const { data: material, error: insertError } = await supabase
            .from('materials')
            .insert({
              title: file.name,
              type: mimeType.split('/').pop(),
              path: publicUrl,
              size: Number(file.size),
              source: 'google_drive',
              source_id: file.id
            })
            .select()
            .single();

          if (insertError) throw insertError;

          return material;
        } catch (error) {
          console.error(`Error processing file ${file.name}:`, error);
          return null;
        }
      })
    );

    return processedFiles.filter(Boolean);
  } catch (error) {
    console.error('Error processing Drive materials:', error);
    throw error;
  }
}