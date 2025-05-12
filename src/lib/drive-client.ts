import { google } from 'googleapis';
import { Credentials, OAuth2Client } from 'google-auth-library';
import { supabase } from './supabase';

export class DriveClient {
  private oauth2Client: OAuth2Client;
  private drive;

  constructor() {
    this.oauth2Client = new google.auth.OAuth2(
      import.meta.env.VITE_GOOGLE_CLIENT_ID,
      import.meta.env.VITE_GOOGLE_CLIENT_SECRET,
      import.meta.env.VITE_GOOGLE_REDIRECT_URI
    );

    this.drive = google.drive({ version: 'v3', auth: this.oauth2Client });
  }

  async initialize() {
    // Get active credentials from Supabase
    const { data: credentials, error } = await supabase
      .from('drive_credentials')
      .select('credentials')
      .eq('is_active', true)
      .single();

    if (error || !credentials) {
      throw new Error('No active Google Drive credentials found');
    }

    this.oauth2Client.setCredentials(credentials.credentials as Credentials);
  }

  async listFiles(folderId: string) {
    try {
      const response = await this.drive.files.list({
        q: `'${folderId}' in parents and trashed = false`,
        fields: 'files(id, name, mimeType, size)',
        pageSize: 1000
      });

      return response.data.files || [];
    } catch (error) {
      console.error('Error listing files:', error);
      throw error;
    }
  }

  async downloadFile(fileId: string): Promise<{ buffer: Buffer; mimeType: string }> {
    try {
      const response = await this.drive.files.get(
        { fileId, alt: 'media' },
        { responseType: 'arraybuffer' }
      );

      const buffer = Buffer.from(response.data);
      const mimeType = response.headers['content-type'] || '';

      return { buffer, mimeType };
    } catch (error) {
      console.error('Error downloading file:', error);
      throw error;
    }
  }
}

export const driveClient = new DriveClient();