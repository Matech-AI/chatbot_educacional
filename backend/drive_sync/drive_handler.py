import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import io
import requests
import json
import time
import hashlib
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DriveHandler:
    """Handles downloading and managing files from Google Drive with enhanced error handling"""

    def __init__(self, materials_dir: str = "data/materials"):
        self.materials_dir = Path(materials_dir)
        self.materials_dir.mkdir(parents=True, exist_ok=True)
        self.service = None
        self.api_key = None

        # Adicionar rastreamento de arquivos processados e hashes
        self.processed_files = {}
        self.file_hashes = {}
        self.download_stats = {
            'total_files': 0,
            'downloaded_files': 0,
            'skipped_duplicates': 0,
            'errors': 0
        }

        # Updated scopes for better access
        self.scopes = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.metadata.readonly'
        ]

        # Adicionar cache de autenticação
        self.auth_cache = {
            'last_auth_time': 0,
            'auth_valid_for': 30 * 60,  # 30 minutos em segundos
            'auth_method': None,
            'is_authenticated': False
        }

        logger.info(
            f"🚀 Initialized DriveHandler with materials directory: {self.materials_dir}")
        logger.info(
            f"📁 Materials directory exists: {self.materials_dir.exists()}")

    def authenticate_public_access(self) -> bool:
        """Try to authenticate for public file access without API key"""
        try:
            logger.info("🔓 Attempting public access without authentication...")

            # Build service without authentication for public files
            self.service = build('drive', 'v3')
            logger.info("✅ Public service built successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Public access failed: {str(e)}")
            return False

    def authenticate_with_api_key(self, api_key: str) -> bool:
        """Authenticate with Google Drive using API Key (for public files)"""
        try:
            logger.info("🔑 Attempting authentication with API Key...")
            logger.info(f"🔑 API Key length: {len(api_key) if api_key else 0}")

            if not api_key or len(api_key) < 10:
                logger.error("❌ Invalid API key provided")
                return False

            self.api_key = api_key

            # Build service with API key
            test_service = build('drive', 'v3', developerKey=api_key)

            # Test the API key with a simple request (public files only)
            logger.info("🔍 Testing API key with a simple request...")
            try:
                # Try to get info about a known public file or do a simple query
                test_result = test_service.files().list(
                    pageSize=1,
                    q="'root' in parents",
                    fields="files(id,name)"
                ).execute()

                logger.info(
                    f"✅ API Key test successful. Found {len(test_result.get('files', []))} accessible files")

            except HttpError as e:
                if e.resp.status == 403:
                    logger.warning(
                        "⚠️ API Key has limited permissions, but may work for public files")
                    # Continue anyway as it might work for public files
                else:
                    logger.error(
                        f"❌ API Key test failed: HTTP {e.resp.status}")
                    return False

            self.service = test_service

            # Atualizar o cache de autenticação
            self.auth_cache['last_auth_time'] = time.time()
            self.auth_cache['auth_method'] = 'api_key'
            self.auth_cache['is_authenticated'] = True

            logger.info(
                "✅ Successfully authenticated with Google Drive using API Key")
            return True

        except Exception as e:
            logger.error(f"❌ Error authenticating with API Key: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            return False

    def authenticate_with_credentials(self, credentials_path: str = 'data/credentials.json') -> bool:
        """Authenticate with Google Drive using OAuth2 credentials with improved flow"""
        try:
            # Verificar se já estamos autenticados e o cache ainda é válido
            current_time = time.time()
            if (self.service and
                self.auth_cache['is_authenticated'] and
                self.auth_cache['auth_method'] == 'oauth2' and
                    current_time - self.auth_cache['last_auth_time'] < self.auth_cache['auth_valid_for']):
                logger.info("✅ Using cached OAuth2 authentication")
                return True

            logger.info("🔐 Attempting OAuth2 authentication...")
            logger.info(f"📄 Credentials file path: {credentials_path}")
            logger.info(
                f"📄 Credentials file exists: {os.path.exists(credentials_path)}")

            creds = None
            token_path = 'token.json'
            logger.info(f"🎫 Token file path: {token_path}")
            logger.info(f"🎫 Token file exists: {os.path.exists(token_path)}")

            # Load existing token
            if os.path.exists(token_path):
                logger.info("📖 Loading existing token from file...")
                try:
                    creds = Credentials.from_authorized_user_file(
                        token_path, self.scopes)
                    logger.info(
                        f"🎫 Token loaded. Valid: {creds.valid if creds else False}")

                    if creds and creds.expired:
                        logger.info(f"🎫 Token expired: {creds.expired}")
                except Exception as e:
                    logger.warning(f"⚠️ Error loading token: {e}")
                    creds = None

            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                logger.info(
                    "🔄 Credentials invalid or missing, refreshing/creating new ones...")

                if creds and creds.expired and creds.refresh_token:
                    logger.info("🔄 Refreshing expired credentials...")
                    try:
                        creds.refresh(Request())
                        logger.info("✅ Credentials refreshed successfully")
                    except Exception as e:
                        logger.warning(f"⚠️ Token refresh failed: {e}")
                        creds = None

                if not creds:
                    if not os.path.exists(credentials_path):
                        logger.error(
                            f"❌ Credentials file not found: {credentials_path}")
                        raise FileNotFoundError(
                            f"Credentials file not found: {credentials_path}")

                    logger.info("🌐 Starting OAuth2 flow...")

                    # Create flow with improved settings
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path,
                        self.scopes,
                        redirect_uri='http://localhost:8080'  # Explicit redirect URI
                    )

                    # Run local server with better error handling
                    try:
                        logger.info("🖥️ Starting local server for OAuth2...")
                        # Modificação aqui: Adicionar access_type='offline' e prompt='consent'
                        # para garantir que recebamos um refresh_token de longa duração
                        flow.authorization_url(
                            access_type='offline', prompt='consent')

                        creds = flow.run_local_server(
                            port=8080,
                            open_browser=False,
                            success_message='Authentication successful! You can close this window.',
                            timeout_seconds=300  # 5 minute timeout
                        )
                        logger.info("✅ OAuth2 flow completed successfully")

                    except Exception as oauth_error:
                        logger.error(f"❌ OAuth2 flow failed: {oauth_error}")

                        # Try console flow as fallback
                        logger.info(
                            "🔄 Trying console-based authentication as fallback...")
                        try:
                            # Também adicionar access_type='offline' e prompt='consent' aqui
                            auth_url, _ = flow.authorization_url(
                                access_type='offline', prompt='consent')
                            print(f"Please go to this URL: {auth_url}")
                            creds = flow.run_console()
                            logger.info("✅ Console authentication successful")
                        except Exception as console_error:
                            logger.error(
                                f"❌ Console authentication also failed: {console_error}")
                            return False

                # Save the credentials for the next run
                if creds:
                    logger.info("💾 Saving credentials to token.json...")
                    try:
                        with open(token_path, 'w') as token:
                            token.write(creds.to_json())
                        logger.info("✅ Credentials saved successfully")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not save credentials: {e}")

            if creds:
                logger.info("🔨 Building Google Drive service...")
                self.service = build('drive', 'v3', credentials=creds)

                # Test the service with a simple request
                try:
                    about = self.service.about().get(fields="user").execute()
                    user_email = about.get('user', {}).get(
                        'emailAddress', 'Unknown')
                    logger.info(
                        f"✅ Successfully authenticated as: {user_email}")
                except Exception as e:
                    logger.warning(
                        f"⚠️ Could not get user info, but service created: {e}")

                # Atualizar o cache de autenticação
                self.auth_cache['last_auth_time'] = time.time()
                self.auth_cache['auth_method'] = 'oauth2'
                self.auth_cache['is_authenticated'] = True

                logger.info(
                    "✅ Successfully authenticated with Google Drive using OAuth2")
                return True
            else:
                logger.error("❌ No valid credentials obtained")
                return False

        except Exception as e:
            logger.error(f"❌ Error authenticating with OAuth2: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            return False

    def authenticate(self, credentials_path: str = 'data/credentials.json', api_key: str = None) -> bool:
        """Main authentication method that tries multiple approaches in order"""
        # Verificar se já estamos autenticados e o cache ainda é válido
        current_time = time.time()
        if (self.service and
            self.auth_cache['is_authenticated'] and
                current_time - self.auth_cache['last_auth_time'] < self.auth_cache['auth_valid_for']):
            logger.info(
                f"✅ Using cached authentication ({self.auth_cache['auth_method']})")
            return True

        logger.info("🚀 Starting Google Drive authentication process...")

        auth_methods = [
            ("API Key", lambda: self.authenticate_with_api_key(
                api_key) if api_key else False),
            ("Environment API Key", lambda: self.authenticate_with_api_key(os.getenv(
                'GOOGLE_DRIVE_API_KEY')) if os.getenv('GOOGLE_DRIVE_API_KEY') else False),
            ("OAuth2 Credentials",
             lambda: self.authenticate_with_credentials(credentials_path)),
            ("Public Access", self.authenticate_public_access)
        ]

        for method_name, auth_func in auth_methods:
            logger.info(f"🔄 Trying authentication method: {method_name}")

            try:
                if auth_func():
                    logger.info(
                        f"✅ Authentication successful with: {method_name}")
                    return True
                else:
                    logger.info(f"❌ Authentication failed with: {method_name}")
            except Exception as e:
                logger.error(f"❌ Error with {method_name}: {e}")

        logger.error("❌ All authentication methods failed")
        return False

    def try_public_file_access(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Try to access a file through public methods"""
        logger.info(f"🔓 Trying public access for file: {file_id}")

        # Method 1: Direct download URL for public files
        public_urls = [
            f"https://drive.google.com/uc?export=download&id={file_id}",
            f"https://drive.google.com/file/d/{file_id}/view",
            f"https://docs.google.com/document/d/{file_id}/export?format=pdf"
        ]

        for i, url in enumerate(public_urls):
            try:
                logger.info(f"🌐 Trying public URL method {i+1}: {url[:50]}...")

                response = requests.get(url, allow_redirects=True, timeout=10)
                logger.info(f"🌐 Response status: {response.status_code}")
                logger.info(f"🌐 Content length: {len(response.content)}")

                if response.status_code == 200 and len(response.content) > 100:
                    # Check if it's actually file content and not an error page
                    content_type = response.headers.get(
                        'content-type', '').lower()
                    logger.info(f"🌐 Content type: {content_type}")

                    # Skip HTML error pages
                    if 'text/html' in content_type and b'<html' in response.content[:1000]:
                        logger.info(
                            "⚠️ Received HTML page, probably not a direct file")
                        continue

                    logger.info(f"✅ Public access successful via URL {i+1}")
                    return {
                        'content': response.content,
                        'size': len(response.content),
                        'method': f'public_url_{i+1}'
                    }

            except Exception as e:
                logger.info(f"⚠️ Public URL method {i+1} failed: {e}")
                continue

        logger.info("❌ All public access methods failed")
        return None

    def authenticate(self, credentials_path: str = 'data/credentials.json', api_key: str = None) -> bool:
        """Main authentication method that tries multiple approaches in order"""
        logger.info("🚀 Starting Google Drive authentication process...")

        auth_methods = [
            ("API Key", lambda: self.authenticate_with_api_key(
                api_key) if api_key else False),
            ("Environment API Key", lambda: self.authenticate_with_api_key(os.getenv(
                'GOOGLE_DRIVE_API_KEY')) if os.getenv('GOOGLE_DRIVE_API_KEY') else False),
            ("OAuth2 Credentials",
             lambda: self.authenticate_with_credentials(credentials_path)),
            ("Public Access", self.authenticate_public_access)
        ]

        for method_name, auth_func in auth_methods:
            logger.info(f"🔄 Trying authentication method: {method_name}")

            try:
                if auth_func():
                    logger.info(
                        f"✅ Authentication successful with: {method_name}")
                    return True
                else:
                    logger.info(f"❌ Authentication failed with: {method_name}")
            except Exception as e:
                logger.error(f"❌ Error with {method_name}: {e}")

        logger.error("❌ All authentication methods failed")
        return False

    def test_folder_access(self, folder_id: str) -> Dict[str, Any]:
        """Test access to a folder with improved error handling"""
        logger.info(f"🔍 Testing access to folder: {folder_id}")

        result = {
            'accessible': False,
            'public': False,
            'file_count': 0,
            'error': None,
            'files_sample': [],
            'folder_name': None,
            'auth_method': None
        }

        try:
            # First, try to get folder info
            if self.service:
                try:
                    logger.info("📁 Attempting to get folder metadata...")
                    folder_info = self.service.files().get(
                        fileId=folder_id,
                        fields="id,name,parents,permissions"
                    ).execute()

                    result['folder_name'] = folder_info.get('name', 'Unknown')
                    result['auth_method'] = 'api_authenticated'
                    logger.info(f"✅ Folder found: {result['folder_name']}")

                except HttpError as e:
                    logger.error(f"❌ HTTP Error accessing folder: {e}")
                    logger.error(f"❌ Status code: {e.resp.status}")

                    if e.resp.status == 403:
                        result['error'] = f"Permission denied (403). Folder may be private or API key lacks permissions."

                        # Try public access as fallback for the folder
                        logger.info("🔄 Trying public folder access...")
                        return self._try_public_folder_access(folder_id, result)

                    elif e.resp.status == 404:
                        result['error'] = "Folder not found (404). Check the folder ID."
                        return result
                    else:
                        result['error'] = f"HTTP {e.resp.status}: {str(e)}"
                        return result

                # Try to list files
                logger.info("📂 Attempting to list files in folder...")
                files = self.list_folder_contents(folder_id)

                if files is not None:
                    result['accessible'] = True
                    result['file_count'] = len(files)
                    result['files_sample'] = [
                        f.get('name', 'Unknown') for f in files[:5]]

                    logger.info(f"✅ Folder accessible with {len(files)} files")

                    # Test download access on first file
                    if files:
                        test_file = files[0]
                        logger.info(
                            f"🧪 Testing download access with: {test_file.get('name')}")

                        try:
                            # Try to get download media
                            self.service.files().get_media(
                                fileId=test_file['id']).execute()
                            result['public'] = True
                            logger.info("✅ Files are downloadable")
                        except HttpError as download_error:
                            if download_error.resp.status == 403:
                                logger.info(
                                    "ℹ️ Files require authentication to download")
                                result['public'] = False
                            else:
                                logger.warning(
                                    f"⚠️ Download test failed: {download_error}")
                                result['public'] = False
                        except Exception as e:
                            logger.warning(f"⚠️ Download test error: {e}")
                            result['public'] = False
                else:
                    result['error'] = "Could not list files in folder"
                    logger.warning("⚠️ Folder found but could not list files")
            else:
                result['error'] = "No authenticated service available"
                logger.error("❌ No service available for testing")

        except Exception as e:
            logger.error(f"❌ Unexpected error testing folder access: {e}")
            result['error'] = f"Unexpected error: {str(e)}"

        logger.info(f"🏁 Folder access test completed: {result}")
        return result

    def _try_public_folder_access(self, folder_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Try to access folder as public"""
        logger.info("🔓 Attempting public folder access...")

        # For public folders, we can try to construct direct file URLs
        # This is a fallback method for when API access is restricted

        # Try to find files in the folder using public methods
        public_folder_url = f"https://drive.google.com/drive/folders/{folder_id}"

        try:
            response = requests.get(public_folder_url, timeout=10)
            if response.status_code == 200:
                # If we can access the folder page, it might be public
                result['accessible'] = True
                result['public'] = True
                result['auth_method'] = 'public_access'
                result['folder_name'] = 'Public Folder (limited info)'
                result['error'] = "Accessible as public folder, but file listing requires API access"
                logger.info("✅ Folder appears to be publicly accessible")
            else:
                result['error'] = f"Folder not publicly accessible (HTTP {response.status_code})"
                logger.info(
                    f"❌ Public folder access failed: HTTP {response.status_code}")

        except Exception as e:
            result['error'] = f"Public access test failed: {str(e)}"
            logger.info(f"❌ Public access test error: {e}")

        return result

    def list_folder_contents(self, folder_id: str) -> List[Dict[str, Any]]:
        """Alias para list_folder_contents_with_pagination para manter compatibilidade"""
        return self.list_folder_contents_with_pagination(folder_id)

    def list_folder_contents_with_pagination(self, folder_id: str) -> List[Dict[str, Any]]:
        """List all files in a Google Drive folder with pagination support"""
        try:
            if not self.service:
                logger.error("❌ Service not initialized")
                return []

            logger.info(f"📋 Listing contents of folder: {folder_id}")

            # List files in folder with more fields
            query = f"'{folder_id}' in parents and trashed = false"
            logger.info(f"🔍 Using query: {query}")

            files = []
            page_token = None
            page_count = 0

            while True:
                page_count += 1
                logger.info(f"📄 Fetching page {page_count}...")

                results = self.service.files().list(
                    q=query,
                    pageSize=100,
                    fields="nextPageToken, files(id, name, mimeType, size, parents, createdTime, modifiedTime, webViewLink, permissions)",
                    pageToken=page_token
                ).execute()

                page_files = results.get('files', [])
                files.extend(page_files)
                logger.info(
                    f"📊 Found {len(page_files)} items on page {page_count}")

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            logger.info(f"📊 Total files found: {len(files)}")
            return files

        except HttpError as e:
            logger.error(f"❌ HTTP Error listing folder contents: {e}")
            logger.error(f"❌ Status code: {e.resp.status}")

            if e.resp.status == 403:
                logger.error(
                    "❌ Insufficient permissions to list folder contents")
            elif e.resp.status == 404:
                logger.error("❌ Folder not found")

            return []

        except Exception as e:
            logger.error(f"❌ Unexpected error listing folder: {str(e)}")
            return []

    def download_file(self, file_id: str, filename: str = None) -> Optional[Dict[str, Any]]:
        """Download a single file with duplicate checking and memory optimization"""
        try:
            logger.info(f"📥 Starting download for file ID: {file_id}")

            # Get file metadata if service is available
            file_metadata = None
            if self.service:
                file_metadata = self.get_file_metadata(file_id)

            if file_metadata:
                filename = filename or file_metadata.get(
                    'name', f"file_{file_id}")
                mime_type = file_metadata.get('mimeType', '')
                file_size = int(file_metadata.get('size', 0)
                                ) if file_metadata.get('size') else 0

                logger.info(
                    f"📁 File: {filename} ({mime_type}) - {file_size} bytes")

                # Skip large files (opcional, ajuste o limite conforme necessário)
                if file_size > 100 * 1024 * 1024:  # 100 MB
                    logger.warning(
                        f"⚠️ Skipping large file: {filename} ({file_size / (1024 * 1024):.2f} MB)")
                    self.download_stats['errors'] += 1
                    return None
            else:
                filename = filename or f"file_{file_id}"
                mime_type = ''
                file_size = 0
                logger.info(
                    f"📁 Downloading: {filename} (metadata unavailable)")

            # Skip Google Apps files
            if mime_type.startswith('application/vnd.google-apps'):
                logger.warning(f"⏭️ Skipping Google Apps file: {filename}")
                return None

            file_content = None
            download_method = None

            # Method 1: Standard API download (if service available)
            if self.service:
                try:
                    logger.info("🔄 Attempting API download...")
                    request = self.service.files().get_media(fileId=file_id)
                    file = io.BytesIO()
                    downloader = MediaIoBaseDownload(file, request)

                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            progress = int(status.progress() * 100)
                            logger.info(f"📥 Download progress: {progress}%")

                    file_content = file.getvalue()
                    download_method = "api_download"
                    logger.info(
                        f"✅ Downloaded via API: {len(file_content)} bytes")

                except HttpError as api_error:
                    logger.warning(
                        f"⚠️ API download failed: HTTP {api_error.resp.status}")
                    if api_error.resp.status == 403:
                        logger.info("🔄 Trying public access methods...")

            # Method 2: Public access methods (fallback)
            if not file_content:
                logger.info("🔄 Attempting public download methods...")
                public_result = self.try_public_file_access(file_id)

                if public_result:
                    file_content = public_result['content']
                    download_method = public_result['method']
                    logger.info(
                        f"✅ Downloaded via {download_method}: {len(file_content)} bytes")

            # Check for duplicates and save file if download was successful
            if file_content:
                # Verificar duplicados
                is_duplicate, duplicate_info = self.is_duplicate_file(
                    filename, file_content)
                if is_duplicate:
                    logger.info(
                        f"⏭️ Skipping duplicate file: {filename} - {duplicate_info}")
                    self.download_stats['skipped_duplicates'] += 1
                    return None

                # Registrar hash do arquivo
                file_hash = self.calculate_file_hash(file_content)

                # Salvar arquivo
                result = self._save_downloaded_file(
                    file_content, filename, file_id, mime_type,
                    file_metadata or {}, download_method
                )

                if result:
                    # Registrar arquivo processado
                    self.processed_files[filename] = file_id
                    self.file_hashes[file_hash] = result['path']
                    self.download_stats['downloaded_files'] += 1

                return result
            else:
                logger.error(f"❌ All download methods failed for: {filename}")
                self.download_stats['errors'] += 1
                return None

        except Exception as e:
            logger.error(f"❌ Error downloading file {file_id}: {str(e)}")
            self.download_stats['errors'] += 1
            return None

    def _save_downloaded_file(self, file_content: bytes, filename: str, file_id: str,
                              mime_type: str, metadata: Dict, method: str) -> Dict[str, Any]:
        """Save downloaded file to disk"""
        logger.info(f"💾 Saving file: {filename}")

        # Ensure filename has proper extension
        if not Path(filename).suffix and mime_type:
            extension = self._get_extension_from_mime_type(mime_type)
            if extension:
                filename += extension
                logger.info(f"📝 Added extension: {filename}")

        file_path = self.materials_dir / filename

        # Avoid overwriting - add number suffix if file exists
        counter = 1
        original_path = file_path
        while file_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            file_path = self.materials_dir / f"{stem}_{counter}{suffix}"
            counter += 1
            logger.info(f"📝 File exists, using new name: {file_path.name}")

        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_content)

        logger.info(f"💾 Successfully saved: {file_path}")
        logger.info(f"📊 Final file size: {file_path.stat().st_size} bytes")

        return {
            'id': file_id,
            'name': file_path.name,
            'title': filename,
            'path': str(file_path),
            'size': len(file_content),
            'type': file_path.suffix[1:].lower() if file_path.suffix else 'unknown',
            'mime_type': mime_type,
            'download_method': method,
            'created_time': metadata.get('createdTime'),
            'modified_time': metadata.get('modifiedTime')
        }

    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a file"""
        try:
            if not self.service:
                return None

            logger.info(f"📋 Getting metadata for file: {file_id}")

            file_metadata = self.service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,size,parents,createdTime,modifiedTime,webViewLink"
            ).execute()

            logger.info(
                f"✅ Metadata retrieved for: {file_metadata.get('name', 'Unknown')}")
            return file_metadata

        except HttpError as e:
            logger.warning(
                f"⚠️ HTTP Error getting metadata for file {file_id}: {e}")
            return None
        except Exception as e:
            logger.warning(
                f"⚠️ Error getting metadata for file {file_id}: {e}")
            return None

    def process_folder(self, folder_id: str, download_all: bool = False) -> List[Dict[str, Any]]:
        """Process files in a Google Drive folder (non-recursive)"""
        logger.info(
            f"📂 Processing folder: {folder_id}, download_all={download_all}")

        # Get files in folder
        # Changed from list_folder_contents to list_folder_contents_with_pagination
        files = self.list_folder_contents_with_pagination(folder_id)
        if not files:
            logger.warning("⚠️ No files found in folder")
            return []

        logger.info(f"📊 Found {len(files)} files in folder")

        # Process files in batches
        processed_files = []
        batch_size = 10  # Adjust as needed

        for i in range(0, len(files), batch_size):
            batch = files[i:i+batch_size]
            batch_results = []

            logger.info(
                f"📦 Processing batch {i//batch_size + 1}/{(len(files) + batch_size - 1)//batch_size}")

            for file in batch:
                file_id = file.get('id')
                file_name = file.get('name', 'Unknown')
                mime_type = file.get('mimeType', '')

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
                    logger.info(f"⬇️ Downloading file: {file_name}")
                    file_info = self.download_file(file_id, file_name)
                    if file_info:
                        batch_results.append(file_info)
                        logger.info(f"✅ Successfully processed: {file_name}")
                    else:
                        logger.warning(f"⚠️ Failed to process: {file_name}")
                else:
                    # Just return metadata
                    batch_results.append({
                        'id': file_id,
                        'name': file_name,
                        'title': file_name,
                        'size': int(file.get('size', 0)) if file.get('size') else 0,
                        'type': self._get_extension_from_mime_type(mime_type)[1:] or 'unknown',
                        'mime_type': mime_type,
                        'created_time': file.get('createdTime'),
                        'modified_time': file.get('modifiedTime')
                    })

            # Add batch results to processed files
            processed_files.extend(batch_results)
            logger.info(
                f"✅ Processed batch {i//batch_size + 1}/{(len(files) + batch_size - 1)//batch_size}")

        logger.info(f"🎉 Processing completed!")
        logger.info(
            f"📊 Successfully processed: {len(processed_files)} out of {len(files)} files")

        return processed_files

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
            'application/vnd.ms-powerpoint': '.ppt',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'application/zip': '.zip'
        }
        return mime_to_ext.get(mime_type, '')

    def cleanup_temp_files(self):
        """Clean up temporary authentication files"""
        # Comentado para manter o token.json entre sessões
        # temp_files = ['token.json']  # Keep credentials.json
        # for file in temp_files:
        #     if os.path.exists(file):
        #         try:
        #             os.remove(file)
        #             logger.info(f"🧹 Cleaned up temporary file: {file}")
        #         except Exception as e:
        #             logger.warning(f"⚠️ Could not remove {file}: {e}")

        # Apenas registra que a função foi chamada sem remover arquivos
        logger.info(
            "🧹 Função cleanup_temp_files chamada, mas token.json foi preservado")

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
            'total_files': len([f for f in files if f.is_file()]),
            'total_size': total_size,
            'file_types': file_types,
            'directory': str(self.materials_dir)
        }

    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()

    def is_duplicate_file(self, filename: str, file_content: bytes) -> tuple[bool, str]:
        """Check if file is duplicate by content hash"""
        file_hash = self.calculate_file_hash(file_content)

        # Check by hash (exact content match)
        if file_hash in self.file_hashes:
            return True, f"Content duplicate of: {self.file_hashes[file_hash]}"

        # Check by filename (just log warning)
        if filename in self.processed_files:
            logger.warning(f"⚠️ Filename duplicate detected: {filename}")

        return False, ""

    def clear_file_hashes_cache(self):
        """Clear the file hashes cache to allow redownloading files"""
        logger.info(
            f"🧹 Clearing file hashes cache. Before: {len(self.file_hashes)} entries")
        self.file_hashes = {}
        self.processed_files = {}
        logger.info(f"✅ File hashes cache cleared successfully")
        return {
            "status": "success",
            "message": "File hashes cache cleared successfully",
            "cleared_entries": len(self.file_hashes)
        }
