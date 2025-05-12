import { google } from 'googleapis';
import { OAuth2Client } from 'google-auth-library';

const CREDENTIALS = {
  client_id: "405717380359-hevec8ueh9gbithso2aeavmfop4g17q3.apps.googleusercontent.com",
  client_secret: "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",
  redirect_uri: "http://localhost:5173"
};

export class DriveClient {
  private oauth2Client: OAuth2Client;
  private drive;

  constructor() {
    this.oauth2Client = new google.auth.OAuth2(
      CREDENTIALS.client_id,
      CREDENTIALS.client_secret,
      CREDENTIALS.redirect_uri
    );

    // For demo purposes, we'll use API key authentication
    this.drive = google.drive({ 
      version: 'v3', 
      auth: this.oauth2Client
    });
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

  async downloadFile(fileId: string): Promise<ArrayBuffer> {
    try {
      const response = await this.drive.files.get(
        { fileId, alt: 'media' },
        { responseType: 'arraybuffer' }
      );

      return response.data;
    } catch (error) {
      console.error('Error downloading file:', error);
      throw error;
    }
  }
}

export const driveClient = new DriveClient();