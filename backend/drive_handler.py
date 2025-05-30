import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import io
import requests
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DriveHandler:
    """Handles downloading and managing files from Google Drive with enhanced features"""

    def __init__(self, materials_dir: str = "data/materials"):
        self.materials_dir = Path(materials_dir)
        self.materials_dir.mkdir(parents=True, exist_ok=True)
        self.service = None
        self.api_key = None
        self.scopes = ['https://www.googleapis.com/auth/drive.readonly']

    def authenticate_with_api_key(self, api_key: str) -> bool:
        """Authenticate with Google Drive using API Key (for public files)"""
        try:
            self.api_key = api_key
            test_service = build('drive', 'v3', developerKey=api_key)

            # Test the API key by making a simple request
            test_service.files().list(pageSize=1).execute()

            self.service = test_service
            logger.info(
                "✅ Successfully authenticated with Google Drive using API Key")
            return True
        except Exception as e:
            logger.error(f"❌ Error authenticating with API Key: {str(e)}")
            return False

    def authenticate_with_credentials(self, credentials_path: str = 'credentials.json') -> bool:
        """Authenticate with Google Drive using OAuth2 credentials"""
        try:
            creds = None
            token_path = 'token.json'

            # Load existing token
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(
                    token_path, self.scopes)

            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(credentials_path):
                        raise FileNotFoundError(
                            f"Credentials file not found: {credentials_path}")

                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, self.scopes)
                    creds = flow.run_local_server(
                        port=8080, open_browser=False)

                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            self.service = build('drive', 'v3', credentials=creds)
            logger.info(
                "✅ Successfully authenticated with Google Drive using OAuth2")
            return True

        except Exception as e:
            logger.error(f"❌ Error authenticating with OAuth2: {str(e)}")
            return False

    def authenticate(self, credentials_path: str = 'credentials.json', api_key: str = None) -> bool:
        """Main authentication method that tries multiple approaches"""
        # First try API key if provided
        if api_key:
            if self.authenticate_with_api_key(api_key):
                return True

        # Try API key from environment
        env_api_key = os.getenv('GOOGLE_DRIVE_API_KEY')
        if env_api_key:
            if self.authenticate_with_api_key(env_api_key):
                return True

        # Finally try OAuth2 credentials
        return self.authenticate_with_credentials(credentials_path)

    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a file"""
        try:
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,size,parents,createdTime,modifiedTime"
            ).execute()
            return file_metadata
        except HttpError as e:
            logger.warning(
                f"⚠️ Could not get metadata for file {file_id}: {e}")
            return None

    def download_file(self, file_id: str, filename: str = None) -> Optional[Dict[str, Any]]:
        """Download a single file from Google Drive with enhanced error handling"""
        try:
            if not self.service:
                raise ValueError(
                    "Not authenticated. Call authenticate() first")

            # Get file metadata
            file_metadata = self.get_file_metadata(file_id)
            if not file_metadata:
                logger.error(f"❌ Could not get metadata for file {file_id}")
                return None

            filename = filename or file_metadata.get('name', f"file_{file_id}")
            mime_type = file_metadata.get('mimeType', '')
            file_size = int(file_metadata.get('size', 0)
                            ) if file_metadata.get('size') else 0

            logger.info(f"📁 Downloading: {filename} ({file_size} bytes)")

            # Skip Google Apps files (they need to be exported, not downloaded)
            if mime_type.startswith('application/vnd.google-apps'):
                logger.warning(f"⏭️ Skipping Google Apps file: {filename}")
                return None

            # Try to download the file
            file_content = None
            download_success = False

            # Method 1: Standard API download
            try:
                request = self.service.files().get_media(fileId=file_id)
                file = io.BytesIO()
                downloader = MediaIoBaseDownload(file, request)

                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.info(
                            f"📥 Download progress: {int(status.progress() * 100)}%")

                file_content = file.getvalue()
                download_success = True
                logger.info(f"✅ Downloaded via API: {filename}")

            except HttpError as api_error:
                logger.warning(
                    f"⚠️ API download failed for {filename}: {api_error}")

                # Method 2: Direct URL download (for public files)
                try:
                    direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                    response = requests.get(
                        direct_url, allow_redirects=True, timeout=30)

                    if response.status_code == 200 and len(response.content) > 0:
                        file_content = response.content
                        download_success = True
                        logger.info(f"✅ Downloaded via direct URL: {filename}")
                    else:
                        logger.error(
                            f"❌ Direct download failed: HTTP {response.status_code}")

                except Exception as direct_error:
                    logger.error(
                        f"❌ Direct download error: {str(direct_error)}")

            # Save file if download was successful
            if download_success and file_content:
                # Ensure filename has proper extension
                if not Path(filename).suffix and mime_type:
                    extension = self._get_extension_from_mime_type(mime_type)
                    if extension:
                        filename += extension

                file_path = self.materials_dir / filename

                # Avoid overwriting - add number suffix if file exists
                counter = 1
                original_path = file_path
                while file_path.exists():
                    stem = original_path.stem
                    suffix = original_path.suffix
                    file_path = self.materials_dir / \
                        f"{stem}_{counter}{suffix}"
                    counter += 1

                # Write file
                with open(file_path, 'wb') as f:
                    f.write(file_content)

                logger.info(f"💾 Saved: {file_path}")

                return {
                    'id': file_id,
                    'name': file_path.name,
                    'title': filename,
                    'path': str(file_path),
                    'size': len(file_content),
                    'type': file_path.suffix[1:].lower() if file_path.suffix else 'unknown',
                    'mime_type': mime_type,
                    'created_time': file_metadata.get('createdTime'),
                    'modified_time': file_metadata.get('modifiedTime')
                }
            else:
                logger.error(f"❌ Failed to download {filename}")
                return None

        except Exception as e:
            logger.error(f"❌ Error downloading file {file_id}: {str(e)}")
            return None

    def _get_extension_from_mime_type(self, mime_type: str) -> str:
        """Get file extension from MIME type"""
        mime_to_ext = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'text/plain': '.txt',
            'video/mp4': '.mp4',
            'video/avi': '.avi',
            'video/quicktime': '.mov',
            'video/webm': '.webm',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            'application/vnd.ms-powerpoint': '.ppt'
        }
        return mime_to_ext.get(mime_type, '')

    def list_folder_contents(self, folder_id: str) -> List[Dict[str, Any]]:
        """List all files in a Google Drive folder"""
        try:
            if not self.service:
                raise ValueError(
                    "Not authenticated. Call authenticate() first")

            logger.info(f"🔍 Listing contents of folder: {folder_id}")

            # List files in folder
            query = f"'{folder_id}' in parents and trashed = false"
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, size, parents, createdTime, modifiedTime)"
            ).execute()

            files = results.get('files', [])
            logger.info(f"📋 Found {len(files)} items in folder")

            return files

        except HttpError as e:
            logger.error(f"❌ Error listing folder contents: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error listing folder: {str(e)}")
            return []

    def process_folder(self, folder_id: str, download_all: bool = True) -> List[Dict[str, Any]]:
        """Process all files in a Google Drive folder"""
        try:
            files = self.list_folder_contents(folder_id)
            processed_files = []

            if not files:
                logger.warning(f"⚠️ No files found in folder {folder_id}")
                return []

            for file in files:
                file_name = file.get('name', 'Unknown')
                file_id = file.get('id')
                mime_type = file.get('mimeType', '')

                logger.info(f"📄 Processing: {file_name} (Type: {mime_type})")

                # Skip Google Apps files and folders
                if mime_type.startswith('application/vnd.google-apps'):
                    if mime_type == 'application/vnd.google-apps.folder':
                        logger.info(f"📁 Skipping subfolder: {file_name}")
                    else:
                        logger.warning(
                            f"⏭️ Skipping Google Apps file: {file_name}")
                    continue

                if download_all:
                    # Download the file
                    file_info = self.download_file(file_id, file_name)
                    if file_info:
                        processed_files.append(file_info)
                        logger.info(f"✅ Successfully processed: {file_name}")
                    else:
                        logger.warning(f"⚠️ Failed to process: {file_name}")
                else:
                    # Just return metadata without downloading
                    processed_files.append({
                        'id': file_id,
                        'name': file_name,
                        'title': file_name,
                        'size': int(file.get('size', 0)) if file.get('size') else 0,
                        'type': self._get_extension_from_mime_type(mime_type)[1:] or 'unknown',
                        'mime_type': mime_type,
                        'created_time': file.get('createdTime'),
                        'modified_time': file.get('modifiedTime')
                    })

            logger.info(
                f"🎉 Completed! Processed {len(processed_files)} out of {len(files)} files")
            return processed_files

        except Exception as e:
            logger.error(f"❌ Error processing folder: {str(e)}")
            return []

    def test_folder_access(self, folder_id: str) -> Dict[str, Any]:
        """Test access to a folder and return diagnostic information"""
        result = {
            'accessible': False,
            'public': False,
            'file_count': 0,
            'error': None,
            'files_sample': [],
            'folder_name': None
        }

        try:
            if not self.service:
                result['error'] = "Not authenticated"
                return result

            # Try to get folder metadata
            try:
                folder_info = self.service.files().get(fileId=folder_id).execute()
                result['folder_name'] = folder_info.get('name', 'Unknown')
                logger.info(f"📁 Folder name: {result['folder_name']}")
            except HttpError as e:
                if e.resp.status == 403:
                    result['error'] = "No permission to access folder"
                    return result
                elif e.resp.status == 404:
                    result['error'] = "Folder not found"
                    return result

            # Try to list files
            files = self.list_folder_contents(folder_id)
            if files:
                result['accessible'] = True
                result['file_count'] = len(files)
                result['files_sample'] = [f.get('name') for f in files[:5]]

                # Test if we can download a file
                if files:
                    test_file = files[0]
                    try:
                        self.service.files().get_media(
                            fileId=test_file['id']).execute()
                        result['public'] = True
                    except:
                        result['public'] = False
            else:
                result['error'] = "Could not list files in folder"

        except Exception as e:
            result['error'] = str(e)

        return result

    def cleanup_temp_files(self):
        """Clean up temporary authentication files"""
        temp_files = ['token.json', 'credentials.json']
        for file in temp_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    logger.info(f"🧹 Cleaned up temporary file: {file}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not remove {file}: {e}")

    def get_download_stats(self) -> Dict[str, Any]:
        """Get statistics about downloaded materials"""
        if not self.materials_dir.exists():
            return {'total_files': 0, 'total_size': 0, 'file_types': {}}

        files = list(self.materials_dir.iterdir())
        total_size = sum(f.stat().st_size for f in files if f.is_file())

        file_types = {}
        for file in files:
            if file.is_file():
                ext = file.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1

        return {
            'total_files': len(files),
            'total_size': total_size,
            'file_types': file_types,
            'directory': str(self.materials_dir)
        }


# Legacy function for compatibility
def load_pdf_as_documents(pdf_path):
    """Legacy function for compatibility"""
    try:
        from langchain.schema import Document
        with open(pdf_path, 'rb') as f:
            content = f"Content from {pdf_path}"
        return [Document(page_content=content, metadata={"source": pdf_path})]
    except ImportError:
        logger.warning("langchain not available, skipping PDF processing")
        return []
