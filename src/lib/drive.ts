import { supabase } from './supabase';

interface DriveFile {
  id: string;
  name: string;
  mimeType: string;
  size: number;
}

export async function syncDriveMaterials(folderId: string) {
  try {
    // Check authentication
    const { data: { session }, error: authError } = await supabase.auth.getSession();
    if (authError) throw new Error('Authentication error');
    if (!session) throw new Error('Not authenticated');

    // Get active credentials from database
    const { data: credentialsData, error: credentialsError } = await supabase
      .from('drive_credentials')
      .select('credentials')
      .eq('is_active', true)
      .single();

    if (credentialsError) throw new Error('Failed to get Drive credentials');
    if (!credentialsData) throw new Error('No active Drive credentials found');

    // Send folder ID to backend
    const formData = new FormData();
    formData.append('drive_folder_id', folderId);

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
      credentialsObj.web?.client_id &&
      credentialsObj.web?.client_secret &&
      credentialsObj.web?.auth_uri &&
      credentialsObj.web?.token_uri
    );
  } catch {
    return false;
  }
}