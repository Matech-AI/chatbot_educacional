import { supabase } from './supabase';

export async function syncDriveMaterials(folderId: string) {
  try {
    // Check authentication
    const { data: { session }, error: authError } = await supabase.auth.getSession();
    if (authError) throw new Error('Erro de autenticação');
    if (!session) throw new Error('Usuário não autenticado');

    // Check user role
    const { data: profile, error: profileError } = await supabase
      .from('profiles')
      .select('role')
      .eq('id', session.user.id)
      .single();

    if (profileError) throw new Error('Erro ao verificar permissões');
    if (!profile || !['admin', 'instructor'].includes(profile.role)) {
      throw new Error('Permissão negada');
    }

    // Get active Drive credentials
    const { data: credentials, error: credentialsError } = await supabase
      .from('drive_credentials')
      .select('credentials')
      .eq('is_active', true)
      .single();

    if (credentialsError || !credentials) {
      throw new Error('Credenciais do Google Drive não encontradas');
    }

    // Initialize system with Drive materials
    const response = await fetch('/api/initialize', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        drive_folder_id: folderId,
        credentials: credentials.credentials
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erro ao sincronizar com o Drive');
    }

    return await response.json();
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