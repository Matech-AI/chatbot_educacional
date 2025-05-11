import { supabase } from './supabase';

interface DriveFile {
  id: string;
  name: string;
  mimeType: string;
  size: number;
}

export async function syncDriveMaterials(folderId: string, credentials: string) {
  try {
    // Check authentication
    const { data: { session }, error: authError } = await supabase.auth.getSession();
    if (authError) throw new Error('Authentication error');
    if (!session) throw new Error('Not authenticated');

    // Validate credentials format
    if (!validateDriveCredentials(credentials)) {
      throw new Error('Invalid credentials format');
    }

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

export function validateDriveCredentials(credentials: string): boolean {
  try {
    const credentialsObj = JSON.parse(credentials);
    return !!(
      credentialsObj.installed?.client_id &&
      credentialsObj.installed?.client_secret &&
      credentialsObj.installed?.redirect_uris
    );
  } catch {
    return false;
  }
}