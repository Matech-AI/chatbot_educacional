import { google } from 'googleapis';
import { OAuth2Client } from 'google-auth-library';
import * as fs from 'fs';
import * as path from 'path';

export class DriveClient {
  private oauth2Client: OAuth2Client;
  private drive;

  constructor() {
    this.oauth2Client = new google.auth.OAuth2(
      process.env.GOOGLE_CLIENT_ID,
      process.env.GOOGLE_CLIENT_SECRET,
      process.env.GOOGLE_REDIRECT_URI
    );

    this.drive = google.drive({ version: 'v3', auth: this.oauth2Client });
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

  async downloadFile(fileId: string, destinationPath: string): Promise<void> {
    try {
      const dest = fs.createWriteStream(destinationPath);
      const response = await this.drive.files.get(
        { fileId, alt: 'media' },
        { responseType: 'stream' }
      );

      return new Promise((resolve, reject) => {
        response.data
          .on('end', () => resolve())
          .on('error', (err: Error) => reject(err))
          .pipe(dest);
      });
    } catch (error) {
      console.error('Error downloading file:', error);
      throw error;
    }
  }
}

export const driveClient = new DriveClient();