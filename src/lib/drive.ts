import { supabase } from './supabase';

interface DriveFile {
  id: string;
  name: string;
  mimeType: string;
  size: number;
}

export async function syncDriveMaterials(folderId: string, credentials: string) {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    // Send credentials and folder ID to backend
    const formData = new FormData();
    formData.append('drive_folder_id', folderId);
    
    // Create a Blob from the credentials string and append it
    const credentialsBlob = new Blob([credentials], { type: 'application/json' });
    formData.append('credentials_json', credentialsBlob, 'credentials.json');

    // Initialize system with Drive materials
    const response = await fetch('/api/initialize', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      },
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to sync Drive materials');
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error syncing Drive materials:', error);
    throw error;
  }
}

export async function validateDriveCredentials(credentials: string): Promise<boolean> {
  try {
    const credentialsObj = JSON.parse(credentials);
    return !!(
      credentialsObj.web?.client_id &&
      credentialsObj.web?.client_secret &&
      credentialsObj.web?.auth_uri &&
      credentialsObj.web?.token_uri
    );
  } catch {
    return false;
  }
}