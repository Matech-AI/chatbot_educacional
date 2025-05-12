import { driveClient } from './drive-client';
import * as fs from 'fs';
import * as path from 'path';

const MATERIALS_DIR = path.join(process.cwd(), 'data', 'materials');

interface ProcessedFile {
  id: string;
  name: string;
  path: string;
  type: string;
  size: number;
}

export async function processDriveMaterials(folderId: string): Promise<ProcessedFile[]> {
  try {
    // Ensure materials directory exists
    if (!fs.existsSync(MATERIALS_DIR)) {
      fs.mkdirSync(MATERIALS_DIR, { recursive: true });
    }

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
        const fileName = `${Date.now()}-${file.name}`;
        const filePath = path.join(MATERIALS_DIR, fileName);

        // Download file
        await driveClient.downloadFile(file.id!, filePath);

        processedFiles.push({
          id: file.id!,
          name: file.name!,
          path: filePath,
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