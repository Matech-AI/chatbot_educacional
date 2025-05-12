import { driveClient } from './drive-client';

interface ProcessedFile {
  id: string;
  name: string;
  content: ArrayBuffer;
  type: string;
  size: number;
}

export async function processDriveMaterials(folderId: string): Promise<ProcessedFile[]> {
  try {
    // List all files in the folder
    const files = await driveClient.listFiles(folderId);
    const processedFiles: ProcessedFile[] = [];

    // Process each file
    for (const file of files) {
      // Only process documents
      if (!file.mimeType?.includes('pdf') && 
          !file.mimeType?.includes('document') && 
          !file.mimeType?.includes('text')) {
        continue;
      }

      try {
        // Download file content
        const content = await driveClient.downloadFile(file.id!);

        processedFiles.push({
          id: file.id!,
          name: file.name!,
          content,
          type: file.mimeType!.split('/').pop()!,
          size: Number(file.size)
        });

        console.log(`Successfully downloaded: ${file.name}`);
      } catch (error) {
        console.error(`Error processing file ${file.name}:`, error);
      }
    }

    return processedFiles;
  } catch (error) {
    console.error('Error processing Drive materials:', error);
    throw error;
  }
}