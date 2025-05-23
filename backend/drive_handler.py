import os
import logging
from pathlib import Path
from typing import List, Optional
import io
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DriveHandler:
    """Handles downloading and managing files from Google Drive with read-only access"""

    def __init__(self, materials_dir: str = "data/materials"):
        self.materials_dir = Path(materials_dir)
        self.materials_dir.mkdir(parents=True, exist_ok=True)
        self.service = None
        self.api_key = None

    def authenticate_with_api_key(self, api_key: str):
        """Authenticate with Google Drive using API Key (for public files)"""
        try:
            self.api_key = api_key

            # Test the API key by making a simple request
            test_service = build('drive', 'v3', developerKey=api_key)

            # Try to list some files to validate the key
            test_service.files().list(pageSize=1).execute()

            self.service = test_service
            logger.info(
                "✅ Successfully authenticated with Google Drive using API Key")
            return True
        except Exception as e:
            logger.error(f"❌ Error authenticating with API Key: {str(e)}")
            return False

    def authenticate(self, credentials_path: str = 'credentials.json'):
        """Authenticate with Google Drive using OAuth2 (fallback method)"""
        try:
            # Try to read API key from environment or credentials file first
            api_key = os.getenv('GOOGLE_DRIVE_API_KEY')
            if api_key:
                return self.authenticate_with_api_key(api_key)

            # If no API key, try traditional OAuth2 method
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request

            SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

            creds = None
            token_path = 'token.json'

            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(
                    token_path, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(credentials_path):
                        raise FileNotFoundError(
                            f"Credentials file not found: {credentials_path}")

                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES)
                    creds = flow.run_local_server(
                        port=8080, open_browser=False)

                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            self.service = build('drive', 'v3', credentials=creds)
            logger.info(
                "✅ Successfully authenticated with Google Drive using OAuth2")
            return True

        except Exception as e:
            logger.error(f"❌ Error authenticating with OAuth2: {str(e)}")
            return False

    def download_file(self, file_id: str, filename: str = None) -> Optional[dict]:
        """Download a single file from Google Drive"""
        try:
            if not self.service:
                raise ValueError(
                    "Not authenticated. Call authenticate() first")

            # Get file metadata
            try:
                file_metadata = self.service.files().get(fileId=file_id).execute()
                filename = filename or file_metadata['name']
                file_size = file_metadata.get('size', 0)

                logger.info(f"📁 Downloading: {filename} ({file_size} bytes)")

            except HttpError as e:
                if e.resp.status == 403:
                    logger.warning(
                        f"⚠️  No permission to access file metadata for {file_id}")
                    filename = filename or f"file_{file_id}"
                else:
                    raise

            # Try multiple download methods
            download_success = False
            file_content = None

            # Method 1: Standard API download
            try:
                request = self.service.files().get_media(fileId=file_id)
                file = io.BytesIO()

                from googleapiclient.http import MediaIoBaseDownload
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
                if api_error.resp.status == 403:
                    logger.warning(
                        f"⚠️  API download failed for {filename}, trying direct URL...")

                    # Method 2: Direct URL download (for public files)
                    try:
                        direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                        response = requests.get(
                            direct_url, allow_redirects=True)

                        if response.status_code == 200:
                            file_content = response.content
                            download_success = True
                            logger.info(
                                f"✅ Downloaded via direct URL: {filename}")
                        else:
                            logger.error(
                                f"❌ Direct download failed: HTTP {response.status_code}")

                    except Exception as direct_error:
                        logger.error(
                            f"❌ Direct download error: {str(direct_error)}")
                else:
                    raise

            # Save file if download was successful
            if download_success and file_content:
                # Ensure filename has extension
                if not Path(filename).suffix and file_metadata:
                    mime_type = file_metadata.get('mimeType', '')
                    if 'pdf' in mime_type:
                        filename += '.pdf'
                    elif 'document' in mime_type:
                        filename += '.docx'
                    elif 'text' in mime_type:
                        filename += '.txt'

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

                with open(file_path, 'wb') as f:
                    f.write(file_content)

                logger.info(f"💾 Saved: {file_path}")

                return {
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': len(file_content),
                    'type': file_path.suffix[1:].lower() if file_path.suffix else 'unknown',
                    'id': file_id
                }
            else:
                logger.error(f"❌ Failed to download {filename}")
                return None

        except Exception as e:
            logger.error(f"❌ Error downloading file {file_id}: {str(e)}")
            return None

    def process_folder(self, folder_id: str) -> List[dict]:
        """Process all files in a Google Drive folder"""
        try:
            if not self.service:
                raise ValueError(
                    "Not authenticated. Call authenticate() first")

            logger.info(f"🔍 Processing folder: {folder_id}")

            # List files in folder
            try:
                results = self.service.files().list(
                    q=f"'{folder_id}' in parents and trashed = false",
                    pageSize=100,
                    fields="nextPageToken, files(id, name, mimeType, size, parents)"
                ).execute()
            except HttpError as e:
                if e.resp.status == 403:
                    logger.error("❌ No permission to list folder contents")
                    return []
                raise

            files = results.get('files', [])
            downloaded_files = []

            logger.info(f"📋 Found {len(files)} items in folder")

            for file in files:
                file_name = file.get('name', 'Unknown')
                file_id = file.get('id')
                mime_type = file.get('mimeType', '')

                logger.info(f"📄 Processing: {file_name} (Type: {mime_type})")

                # Skip Google Apps files (Docs, Sheets, Slides, etc.)
                if mime_type.startswith('application/vnd.google-apps'):
                    logger.warning(
                        f"⏭️  Skipping Google Apps file: {file_name}")
                    continue

                # Skip folders
                if mime_type == 'application/vnd.google-apps.folder':
                    logger.warning(f"📁 Skipping subfolder: {file_name}")
                    continue

                # Download regular files
                file_info = self.download_file(file_id, file_name)
                if file_info:
                    downloaded_files.append(file_info)
                    logger.info(f"✅ Successfully processed: {file_name}")
                else:
                    logger.warning(f"⚠️  Failed to process: {file_name}")

            logger.info(
                f"🎉 Completed! Downloaded {len(downloaded_files)} out of {len(files)} files")
            return downloaded_files

        except Exception as e:
            logger.error(f"❌ Error processing folder: {str(e)}")
            return []

    def test_folder_access(self, folder_id: str) -> dict:
        """Test access to a folder and return diagnostic information"""
        result = {
            'accessible': False,
            'public': False,
            'file_count': 0,
            'error': None,
            'files_sample': []
        }

        try:
            if not self.service:
                result['error'] = "Not authenticated"
                return result

            # Try to get folder metadata
            try:
                folder_info = self.service.files().get(fileId=folder_id).execute()
                logger.info(
                    f"📁 Folder name: {folder_info.get('name', 'Unknown')}")
            except HttpError as e:
                if e.resp.status == 403:
                    result['error'] = "No permission to access folder"
                    return result
                elif e.resp.status == 404:
                    result['error'] = "Folder not found"
                    return result

            # Try to list files
            try:
                results = self.service.files().list(
                    q=f"'{folder_id}' in parents and trashed = false",
                    pageSize=5,
                    fields="files(id, name, mimeType)"
                ).execute()

                files = results.get('files', [])
                result['accessible'] = True
                result['file_count'] = len(files)
                result['files_sample'] = [f.get('name') for f in files]

                # Test if we can download a file
                if files:
                    test_file = files[0]
                    try:
                        self.service.files().get_media(
                            fileId=test_file['id']).execute()
                        result['public'] = True
                    except:
                        result['public'] = False

            except HttpError as e:
                result['error'] = f"Cannot list files: HTTP {e.resp.status}"

        except Exception as e:
            result['error'] = str(e)

        return result


def load_pdf_as_documents(pdf_path):
    """Legacy function for compatibility"""
    try:
        from langchain.schema import Document
        # This would need actual PDF extraction logic
        with open(pdf_path, 'rb') as f:
            content = f"Content from {pdf_path}"  # Placeholder
        return [Document(page_content=content, metadata={"source": pdf_path})]
    except ImportError:
        logger.warning("langchain not available, skipping PDF processing")
        return []
