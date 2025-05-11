import os
import logging
from pathlib import Path
from typing import List, Optional
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DriveHandler:
    """Handles downloading and managing files from Google Drive"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, materials_dir: str = "data/materials"):
        self.materials_dir = Path(materials_dir)
        self.materials_dir.mkdir(parents=True, exist_ok=True)
        self.service = None
    
    def authenticate(self, credentials_path: str = 'credentials.json'):
        """Authenticate with Google Drive"""
        creds = None
        token_path = 'token.json'

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
                
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('drive', 'v3', credentials=creds)
        logger.info("Successfully authenticated with Google Drive")
    
    def download_file(self, file_id: str) -> Optional[dict]:
        """
        Download a single file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            Dictionary with file info or None if failed
        """
        try:
            if not self.service:
                raise ValueError("Not authenticated. Call authenticate() first")

            # Get file metadata
            file_metadata = self.service.files().get(fileId=file_id).execute()
            filename = file_metadata['name']
            
            # Download file
            request = self.service.files().get_media(fileId=file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Download {int(status.progress() * 100)}%")
            
            # Save file
            file_path = self.materials_dir / filename
            with open(file_path, 'wb') as f:
                f.write(file.getvalue())
                    
            logger.info(f"Downloaded {filename}")
            
            return {
                'name': filename,
                'path': str(file_path),
                'size': file.getbuffer().nbytes,
                'type': filename.split('.')[-1].lower()
            }
            
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {str(e)}")
            return None
    
    def process_folder(self, folder_id: str) -> List[dict]:
        """
        Process all files in a Google Drive folder
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            List of dictionaries with file information
        """
        try:
            if not self.service:
                raise ValueError("Not authenticated. Call authenticate() first")

            # List files in folder
            results = self.service.files().list(
                q=f"'{folder_id}' in parents",
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType)"
            ).execute()
            
            files = results.get('files', [])
            downloaded_files = []
            
            for file in files:
                # Only download PDFs and documents
                if file['mimeType'] in [
                    'application/pdf',
                    'application/vnd.google-apps.document'
                ]:
                    file_info = self.download_file(file['id'])
                    if file_info:
                        downloaded_files.append(file_info)
            
            return downloaded_files
                
        except Exception as e:
            logger.error(f"Error processing folder: {str(e)}")
            return []