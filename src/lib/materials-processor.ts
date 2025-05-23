import { api } from './api';

// Process Drive materials function
export async function processDriveMaterials(folderId: string): Promise<any[]> {
  try {
    console.log('Processing Drive materials from folder:', folderId);
    
    // Call the backend sync endpoint
    const response = await api.syncDrive(folderId);
    
    if (response && response.files) {
      console.log(`Successfully processed ${response.files.length} files from Drive`);
      return response.files;
    }
    
    return [];
  } catch (error) {
    console.error('Error processing Drive materials:', error);
    throw new Error('Falha ao sincronizar materiais do Google Drive');
  }
}

// Validate Drive folder ID format
export function validateDriveFolderId(folderId: string): boolean {
  // Basic validation for Google Drive folder ID format
  const driveIdRegex = /^[a-zA-Z0-9_-]{28,}$/;
  return driveIdRegex.test(folderId.trim());
}

// Extract folder ID from Google Drive URL
export function extractFolderIdFromUrl(url: string): string | null {
  try {
    // Match various Google Drive folder URL formats
    const patterns = [
      /\/folders\/([a-zA-Z0-9_-]+)/,
      /id=([a-zA-Z0-9_-]+)/,
      /^([a-zA-Z0-9_-]{28,})$/
    ];
    
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match && match[1]) {
        return match[1];
      }
    }
    
    return null;
  } catch (error) {
    console.error('Error extracting folder ID from URL:', error);
    return null;
  }
}