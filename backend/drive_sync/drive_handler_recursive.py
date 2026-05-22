import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Set
import io
import mimetypes
import requests
import json
import time
import hashlib
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaIoBaseUpload

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RecursiveDriveHandler:
    """Enhanced Drive Handler with recursive folder processing and duplicate detection"""

    def __init__(self, materials_dir: str = "data/materials"):
        # Allow overriding materials dir via env
        resolved_dir = os.getenv('MATERIALS_DIR', materials_dir)
        self.materials_dir = Path(resolved_dir)
        self.materials_dir.mkdir(parents=True, exist_ok=True)
        self.service = None
        self.api_key = None

        # Track processed files to avoid duplicates
        self.processed_files: Dict[str, str] = {}  # filename -> file_id
        self.file_hashes: Dict[str, str] = {}      # hash -> filepath
        self.download_stats = {
            'total_folders': 0,
            'total_files': 0,
            'downloaded_files': 0,
            'skipped_duplicates': 0,
            'errors': 0
        }

        # Flag para controlar cancelamento de operações
        self.cancel_flag = False

        # Full drive access needed for bidirectional sync (read + write)
        self.scopes = [
            'https://www.googleapis.com/auth/drive'
        ]

        # Adicionar cache de autenticação
        self.auth_cache = {
            'last_auth_time': 0,
            'auth_valid_for': 30 * 60,  # 30 minutos em segundos
            'auth_method': None,
            'is_authenticated': False
        }

        # Download options (can be configured by API layer or env)
        self.include_videos: bool = os.getenv(
            'INCLUDE_DRIVE_VIDEOS', 'false').lower() == 'true'
        # Export Google Docs to PDF by default so conteúdo fica local
        self.export_google_docs: bool = os.getenv(
            'EXPORT_GOOGLE_DOCS', 'true').lower() == 'true'

        logger.info(
            f"🚀 Initialized RecursiveDriveHandler with materials directory: {self.materials_dir}")

    def _resolve_credentials_path(self, default_path: str = 'data/credentials.json') -> str:
        env_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
        candidate_paths = [
            env_path,
            default_path,
            '/app/data/credentials.json',
            '/etc/secrets/credentials.json',
            'credentials.json',
        ]
        for path in candidate_paths:
            if path and os.path.exists(path):
                logger.info(f"🔎 Using credentials file: {path}")
                return path
        return env_path or default_path

    def _resolve_token_path(self) -> str:
        env_token = os.getenv('GOOGLE_TOKEN_PATH')
        candidate_paths = [
            env_token,
            'data/token.json',
            '/app/data/token.json',
            '/etc/secrets/token.json',
            'token.json',
            '/app/token.json',
        ]
        for path in candidate_paths:
            if path and os.path.exists(path):
                logger.info(f"🔎 Using token file (exists): {path}")
                return path
        return env_token or '/app/data/token.json'

    def authenticate(self, credentials_path: str = 'data/credentials.json', api_key: Optional[str] = None) -> bool:
        """Main authentication method that tries multiple approaches in order"""
        logger.info("🚀 Starting Google Drive authentication process...")

        # Verificar se já estamos autenticados e o cache ainda é válido
        current_time = time.time()
        if (self.service and
            self.auth_cache['is_authenticated'] and
                current_time - self.auth_cache['last_auth_time'] < self.auth_cache['auth_valid_for']):
            logger.info(
                f"✅ Using cached authentication ({self.auth_cache['auth_method']})")
            return True

        # Priorizar token.json existente
        token_path = self._resolve_token_path()
        if os.path.exists(token_path):
            try:
                logger.info(
                    "🔄 Found existing token.json, attempting to use it directly")
                creds = Credentials.from_authorized_user_file(
                    token_path, self.scopes)

                # Verificar se o token é válido ou pode ser atualizado
                if creds and creds.valid:
                    logger.info("✅ Existing token is valid")
                    self.service = build('drive', 'v3', credentials=creds)

                    # Atualizar o cache de autenticação
                    self.auth_cache['last_auth_time'] = time.time()
                    self.auth_cache['auth_method'] = 'oauth2'
                    self.auth_cache['is_authenticated'] = True

                    return True
                elif creds and creds.expired and creds.refresh_token:
                    logger.info("🔄 Existing token expired, refreshing...")
                    creds.refresh(Request())
                    # Salvar o token atualizado
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                    logger.info("✅ Token refreshed successfully")
                    self.service = build('drive', 'v3', credentials=creds)

                    # Atualizar o cache de autenticação
                    self.auth_cache['last_auth_time'] = time.time()
                    self.auth_cache['auth_method'] = 'oauth2'
                    self.auth_cache['is_authenticated'] = True

                    return True
            except Exception as e:
                logger.warning(f"⚠️ Error using existing token: {e}")
                # Continuar com outros métodos de autenticação

        # Tentar outros métodos de autenticação se o token.json não funcionou
        auth_methods = [
            ("API Key", lambda: self.authenticate_with_api_key(
                api_key) if api_key else False),
            ("Environment API Key", lambda: self.authenticate_with_api_key(os.getenv(
                'GOOGLE_DRIVE_API_KEY')) if os.getenv('GOOGLE_DRIVE_API_KEY') else False),
            ("OAuth2 Credentials",
             lambda: self.authenticate_with_credentials(self._resolve_credentials_path(credentials_path))),
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

        # Resetar o cache de autenticação em caso de falha
        self.auth_cache['is_authenticated'] = False

        logger.error("❌ All authentication methods failed")
        return False

    def authenticate_with_api_key(self, api_key: Optional[str]) -> bool:
        """Authenticate with Google Drive using API Key (for public files)"""
        try:
            logger.info("🔑 Attempting authentication with API Key...")
            if not api_key or len(api_key) < 10:
                logger.error("❌ Invalid API key provided")
                return False

            self.api_key = api_key
            self.service = build('drive', 'v3', developerKey=api_key)

            # Test the API key
            try:
                test_result = self.service.files().list(
                    pageSize=1, fields="files(id,name)").execute()
                logger.info("✅ API Key test successful")
            except HttpError as e:
                if e.resp.status == 403:
                    logger.warning(
                        "⚠️ API Key has limited permissions, but may work for public files")
                else:
                    logger.error(
                        f"❌ API Key test failed: HTTP {e.resp.status}")
                    return False

            # Atualizar o cache de autenticação
            self.auth_cache['last_auth_time'] = time.time()
            self.auth_cache['auth_method'] = 'api_key'
            self.auth_cache['is_authenticated'] = True

            logger.info(
                "✅ Successfully authenticated with Google Drive using API Key")
            return True

        except Exception as e:
            logger.error(f"❌ Error authenticating with API Key: {str(e)}")
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
            token_path = self._resolve_token_path()
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
                            creds = flow.run_console()  # type: ignore
                            logger.info("✅ Console authentication successful")
                        except Exception as console_error:
                            logger.error(
                                f"❌ Console authentication also failed: {console_error}")
                            return False

                # Save the credentials for the next run
                if creds:
                    logger.info("💾 Saving credentials to token.json...")
                    try:
                        writable_candidates = [
                            token_path,
                            '/app/data/token.json',
                            'token.json',
                        ]
                        saved = False
                        for wpath in writable_candidates:
                            try:
                                Path(wpath).parent.mkdir(
                                    parents=True, exist_ok=True)
                                with open(wpath, 'w') as token:
                                    token.write(creds.to_json())
                                logger.info(
                                    f"✅ Credentials saved successfully at {wpath}")
                                saved = True
                                break
                            except Exception:
                                continue
                        if not saved:
                            logger.warning(
                                "⚠️ Could not save credentials to any known writable location")
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

    def authenticate_public_access(self) -> bool:
        """Try to authenticate for public file access without API key"""
        try:
            logger.info("🔓 Attempting public access without authentication...")
            self.service = build('drive', 'v3')

            # Atualizar o cache de autenticação
            self.auth_cache['last_auth_time'] = time.time()
            self.auth_cache['auth_method'] = 'public'
            self.auth_cache['is_authenticated'] = True

            logger.info("✅ Public service built successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Public access failed: {str(e)}")
            return False

    def get_folder_structure(self, folder_id: str, current_path: str = "", max_depth: Optional[int] = None, current_depth: int = 0) -> Dict[str, Any]:
        """Get complete folder structure recursively with optional depth limit"""
        logger.info(
            f"📁 Analyzing folder structure: {folder_id} at path: {current_path}")

        if not self.service:
            logger.error(
                "Drive service not initialized. Please authenticate first.")
            raise Exception("Drive service not initialized.")

        # Verificar flag de cancelamento
        if self.cancel_flag:
            logger.info("🛑 Análise de estrutura de pastas cancelada")
            raise Exception("Operação cancelada pelo usuário")

        try:
            # Get folder info
            try:
                folder_info = self.service.files().get(
                    fileId=folder_id, fields="id,name").execute()
                folder_name = folder_info.get('name', 'Unknown')
            except Exception as e:
                logger.warning(
                    f"Could not get folder info for {folder_id}: {e}")
                folder_name = f'folder_{folder_id[:8]}'

            structure = {
                'id': folder_id,
                'name': folder_name,
                'path': current_path,
                'subfolders': {},
                'files': []
            }

            # Check if we've reached the maximum depth
            if max_depth is not None and current_depth >= max_depth:
                return structure

            # List all items in folder
            query = f"'{folder_id}' in parents and trashed = false"
            try:
                results = self.service.files().list(
                    q=query,
                    pageSize=1000,
                    fields="files(id,name,mimeType,size,parents,createdTime,modifiedTime)"
                ).execute()

                items = results.get('files', [])
                logger.info(
                    f"📊 Found {len(items)} items in folder: {folder_name}")

                for item in items:
                    # Verificar flag de cancelamento periodicamente
                    if self.cancel_flag:
                        logger.info(
                            "🛑 Análise de estrutura de pastas cancelada durante o processamento")
                        raise Exception("Operação cancelada pelo usuário")

                    if item.get('mimeType') == 'application/vnd.google-apps.folder':
                        # It's a subfolder - recurse
                        subfolder_path = os.path.join(
                            current_path, folder_name) if current_path else folder_name
                        try:
                            structure['subfolders'][item['id']] = self.get_folder_structure(
                                item['id'],
                                subfolder_path,
                                max_depth=max_depth,
                                current_depth=current_depth + 1
                            )
                            self.download_stats['total_folders'] += 1
                        except Exception as e:
                            logger.error(
                                f"Error processing subfolder {item.get('name', 'Unknown')}: {e}")
                    else:
                        # It's a file
                        file_info = {
                            'id': item.get('id'),
                            'name': item.get('name', 'Unknown'),
                            'size': int(item.get('size', 0)) if item.get('size') else 0,
                            'mimeType': item.get('mimeType', ''),
                            'createdTime': item.get('createdTime'),
                            'modifiedTime': item.get('modifiedTime')
                        }
                        structure['files'].append(file_info)
                        self.download_stats['total_files'] += 1

            except Exception as e:
                logger.error(f"Error listing folder contents: {e}")

            return structure

        except Exception as e:
            logger.error(f"❌ Error getting folder structure: {str(e)}")
            return {
                'id': folder_id,
                'name': 'Error',
                'path': current_path,
                'subfolders': {},
                'files': []
            }

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

    def force_redownload_all(self):
        """Force redownload of all files by clearing cache and scanning existing files"""
        logger.info(
            "🔄 Force redownload mode: clearing cache and rescanning existing files...")
        self.clear_file_hashes_cache()
        # Rescan existing files to rebuild cache
        existing_hashes = self.scan_existing_files()
        self.file_hashes.update(existing_hashes)
        logger.info(
            f"✅ Force redownload mode activated. Found {len(existing_hashes)} existing files")
        return {
            "status": "success",
            "message": "Force redownload mode activated",
            "existing_files_count": len(existing_hashes)
        }

    def analyze_folder_recursive(self, folder_id: str, max_depth: int = None) -> Dict[str, Any]:
        """Analyze a Google Drive folder recursively and return detailed information"""
        logger.info(f"📊 Starting recursive analysis of folder: {folder_id}")

        # Reset stats for analysis
        self.download_stats = {
            'total_folders': 0,
            'total_files': 0,
            'downloaded_files': 0,
            'skipped_duplicates': 0,
            'errors': 0
        }
        self.cancel_flag = False

        start_time = time.time()

        try:
            # Get the complete folder structure
            folder_structure = self.get_folder_structure(
                folder_id, max_depth=max_depth)

            analysis_time = time.time() - start_time

            # Calculate additional statistics
            total_size = 0
            file_types = {}

            def analyze_structure_recursive(structure):
                nonlocal total_size, file_types

                # Analyze files in current folder
                for file_info in structure.get('files', []):
                    file_size = file_info.get('size', 0)
                    total_size += file_size

                    mime_type = file_info.get('mimeType', 'unknown')
                    file_types[mime_type] = file_types.get(mime_type, 0) + 1

                # Analyze subfolders
                for subfolder in structure.get('subfolders', {}).values():
                    analyze_structure_recursive(subfolder)

            analyze_structure_recursive(folder_structure)

            analysis_result = {
                'status': 'success',
                'folder_id': folder_id,
                'folder_name': folder_structure.get('name', 'Unknown'),
                'statistics': {
                    'total_folders': self.download_stats['total_folders'],
                    'total_files': self.download_stats['total_files'],
                    'total_size_bytes': total_size,
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'file_types': file_types,
                    'analysis_time_seconds': round(analysis_time, 2)
                },
                'folder_structure': folder_structure,
                'analysis_timestamp': time.time()
            }

            logger.info(
                f"✅ Recursive analysis completed in {analysis_time:.2f}s")
            logger.info(
                f"📊 Found {self.download_stats['total_folders']} folders and {self.download_stats['total_files']} files")

            return analysis_result

        except Exception as e:
            logger.error(f"❌ Error in recursive analysis: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'statistics': self.download_stats
            }

    def sync_folder_recursive(self, folder_id: str, max_depth: Optional[int] = None) -> Dict[str, Any]:
        """Sync a Google Drive folder recursively (background task)"""
        logger.info(f"🔄 Starting recursive sync of folder: {folder_id}")
        try:
            result = self.download_drive_recursive(folder_id, max_depth)
            logger.info(
                f"✅ Recursive sync completed: {result.get('status', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"❌ Error in recursive sync: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'statistics': self.download_stats
            }

    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()

    def is_duplicate_file(self, filename: str, file_content: bytes) -> Tuple[bool, str]:
        """Check if file is duplicate by name or content"""
        file_hash = self.calculate_file_hash(file_content)

        # Check by hash first (exact content match)
        if file_hash in self.file_hashes:
            return True, f"Content duplicate of: {self.file_hashes[file_hash]}"

        # Check by filename (more lenient - just warn)
        if filename in self.processed_files:
            logger.warning(f"⚠️ Filename duplicate detected: {filename}")

        return False, ""

    def scan_existing_files(self) -> Dict[str, str]:
        """Scan existing files in materials directory and calculate their hashes"""
        logger.info(f"🔍 Scanning existing files in: {self.materials_dir}")

        existing_hashes = {}

        if not self.materials_dir.exists():
            logger.info(
                "📁 Materials directory does not exist, no existing files to scan")
            return existing_hashes

        try:
            # Recursively scan all files in the materials directory
            for file_path in self.materials_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        # Calculate hash of existing file
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                            file_hash = self.calculate_file_hash(file_content)

                        # Store hash -> relative path mapping
                        relative_path = str(
                            file_path.relative_to(self.materials_dir))
                        existing_hashes[file_hash] = relative_path

                        # Also store filename -> file_id mapping for processed_files
                        self.processed_files[file_path.name] = f"existing_{file_hash[:8]}"

                        logger.debug(
                            f"📄 Found existing file: {relative_path} (hash: {file_hash[:16]}...)")

                    except Exception as e:
                        logger.warning(
                            f"⚠️ Could not process existing file {file_path}: {e}")
                        continue

            logger.info(f"✅ Scanned {len(existing_hashes)} existing files")
            return existing_hashes

        except Exception as e:
            logger.error(f"❌ Error scanning existing files: {e}")
            return existing_hashes

    def is_file_already_downloaded(self, filename: str, file_content: bytes, folder_path: str) -> Tuple[bool, str]:
        """Check if file is already downloaded by content hash or path"""
        file_hash = self.calculate_file_hash(file_content)

        # Check by hash first (exact content match)
        if file_hash in self.file_hashes:
            existing_path = self.file_hashes[file_hash]
            return True, f"Content duplicate of: {existing_path}"

        # Check if file exists at expected path
        expected_path = self.materials_dir / folder_path / filename
        if expected_path.exists():
            try:
                with open(expected_path, 'rb') as f:
                    existing_content = f.read()
                    existing_hash = self.calculate_file_hash(existing_content)

                if existing_hash == file_hash:
                    return True, f"File already exists at: {expected_path.relative_to(self.materials_dir)}"
                else:
                    logger.warning(
                        f"⚠️ File exists but content differs: {expected_path}")
            except Exception as e:
                logger.warning(
                    f"⚠️ Could not read existing file {expected_path}: {e}")

        # Check by filename (just log warning)
        if filename in self.processed_files:
            logger.warning(f"⚠️ Filename duplicate detected: {filename}")

        return False, ""

    def download_file_with_duplicate_check(self, file_id: str, filename: str, folder_path: str) -> Optional[Dict[str, Any]]:
        """Download a single file with duplicate checking"""
        try:
            logger.info(
                f"📥 Downloading file: {filename} in folder: {folder_path}")

            # Get file metadata
            file_metadata = self.get_file_metadata(file_id)
            if not file_metadata:
                logger.warning(
                    f"⚠️ Could not get metadata for file: {filename}")
                self.download_stats['errors'] += 1
                return None

            mime_type = file_metadata.get('mimeType', '')
            file_size = int(file_metadata.get('size', 0)
                            ) if file_metadata.get('size') else 0

            # Handle Google Apps files (Docs/Sheets/Slides)
            if mime_type.startswith('application/vnd.google-apps'):
                if not self.export_google_docs:
                    logger.info(
                        f"⏭️ Skipping Google Apps file (export disabled): {filename}")
                return None

                export_map = {
                    'application/vnd.google-apps.document': ('application/pdf', '.pdf'),
                    'application/vnd.google-apps.presentation': ('application/pdf', '.pdf'),
                    'application/vnd.google-apps.spreadsheet': ('application/pdf', '.pdf'),
                    'application/vnd.google-apps.drawing': ('application/pdf', '.pdf'),
                }
                export_mime, export_ext = export_map.get(
                    mime_type, ('application/pdf', '.pdf'))
                try:
                    logger.info(
                        f"📤 Exporting Google Apps file to {export_ext}: {filename}")
                    export_request = self.service.files().export(
                        fileId=file_id, mimeType=export_mime
                    ) if self.service else None
                    exported_content = export_request.execute() if export_request else None
                    if not exported_content or len(exported_content) < 100:
                        logger.warning(
                            f"⚠️ Export returned empty content for: {filename}")
                        self.download_stats['errors'] += 1
                        return None
                    file_content = exported_content
                    download_method = "export"
                    # Adjust filename extension to exported one
                    base_name, _ = os.path.splitext(filename)
                    filename = base_name + export_ext
                except HttpError as e:
                    logger.error(
                        f"❌ Export failed (HTTP {e.resp.status}) for {filename}")
                    self.download_stats['errors'] += 1
                    return None
                except Exception as e:
                    logger.error(f"❌ Export failed for {filename}: {e}")
                    self.download_stats['errors'] += 1
                    return None

            # Video files: optional download (disabled by default)
            video_extensions = ['.mp4', '.avi', '.mov',
                                '.webm', '.mkv', '.flv', '.wmv']
            if (any(filename.lower().endswith(ext) for ext in video_extensions) or mime_type.startswith('video/')) and not self.include_videos:
                logger.info(
                    f"⏭️ Skipping video file (include_videos=False): {filename}")
                return None

            # Download file content
            file_content = None
            download_method = None

            if self.service:
                try:
                    request = self.service.files().get_media(fileId=file_id)
                    file = io.BytesIO()
                    downloader = MediaIoBaseDownload(file, request)

                    done = False
                    retry_count = 0
                    max_retries = 3

                    while not done and retry_count < max_retries:
                        try:
                            status, done = downloader.next_chunk()
                            if status:
                                progress = int(status.progress() * 100)
                                if progress % 20 == 0:  # Log every 20%
                                    logger.debug(
                                        f"📥 Download progress for {filename}: {progress}%")
                        except Exception as chunk_error:
                            retry_count += 1
                            logger.warning(
                                f"⚠️ Chunk download error (retry {retry_count}): {chunk_error}")
                            if retry_count >= max_retries:
                                raise chunk_error
                            time.sleep(1)  # Brief pause before retry

                    file_content = file.getvalue()
                    download_method = "api_download"
                    logger.info(
                        f"✅ Downloaded via API: {len(file_content)} bytes")

                except HttpError as api_error:
                    logger.warning(
                        f"⚠️ API download failed: HTTP {api_error.resp.status}")
                    # Try public access methods as fallback
                    public_result = self.try_public_file_access(file_id)
                    if public_result:
                        file_content = public_result['content']
                        download_method = public_result['method']
                except Exception as download_error:
                    logger.error(
                        f"❌ Download error for {filename}: {download_error}")
                    self.download_stats['errors'] += 1
                    return None

            if not file_content:
                logger.error(f"❌ Could not download file: {filename}")
                self.download_stats['errors'] += 1
                return None

            # Check for duplicates using enhanced duplicate detection
            is_duplicate, duplicate_info = self.is_file_already_downloaded(
                filename, file_content, folder_path)
            if is_duplicate:
                logger.info(
                    f"⏭️ Skipping duplicate file: {filename} ({duplicate_info})")
                self.download_stats['skipped_duplicates'] += 1
                return None

            # Create directory structure
            full_folder_path = self.materials_dir / folder_path
            full_folder_path.mkdir(parents=True, exist_ok=True)

            # Clean filename for filesystem compatibility
            safe_filename = self.sanitize_filename(filename)
            file_path = full_folder_path / safe_filename

            # Handle filename conflicts in same directory
            counter = 1
            original_path = file_path
            while file_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                file_path = full_folder_path / f"{stem}_{counter}{suffix}"
                counter += 1

            # Write file
            try:
                with open(file_path, 'wb') as f:
                    f.write(file_content)
            except Exception as write_error:
                logger.error(
                    f"❌ Error writing file {file_path}: {write_error}")
                self.download_stats['errors'] += 1
                return None

            # Track this file
            file_hash = self.calculate_file_hash(file_content)
            self.processed_files[filename] = file_id
            self.file_hashes[file_hash] = str(
                file_path.relative_to(self.materials_dir))

            self.download_stats['downloaded_files'] += 1
            logger.info(
                f"💾 Successfully saved: {file_path.relative_to(self.materials_dir)}")

            return {
                'id': file_id,
                'name': file_path.name,
                'original_name': filename,
                'path': str(file_path),
                'relative_path': str(file_path.relative_to(self.materials_dir)),
                'size': len(file_content),
                'type': file_path.suffix[1:].lower() if file_path.suffix else 'unknown',
                'mime_type': mime_type,
                'download_method': download_method,
                'folder_path': folder_path,
                'created_time': file_metadata.get('createdTime'),
                'modified_time': file_metadata.get('modifiedTime')
            }

        except Exception as e:
            logger.error(f"❌ Error downloading file {filename}: {str(e)}")
            self.download_stats['errors'] += 1
            return None

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility"""
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Trim whitespace and dots
        filename = filename.strip(' .')

        # Ensure not empty
        if not filename:
            filename = 'unnamed_file'

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext

        return filename

    def process_folder_recursive(self, folder_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process folder structure recursively and download all files"""
        processed_files = []

        # Verificar flag de cancelamento
        if self.cancel_flag:
            logger.info("🛑 Folder processing cancelled")
            raise Exception("Operation cancelled by user")

        folder_path = folder_structure['path']
        folder_name = folder_structure['name']

        # Create current folder path
        current_folder_path = os.path.join(
            folder_path, folder_name) if folder_path else folder_name

        logger.info(f"📂 Processing folder: {current_folder_path}")

        # Process files in current folder
        for file_info in folder_structure['files']:
            # Verificar flag de cancelamento periodicamente
            if self.cancel_flag:
                logger.info("🛑 File processing cancelled")
                raise Exception("Operation cancelled by user")

            try:
                file_result = self.download_file_with_duplicate_check(
                    file_info['id'],
                    file_info['name'],
                    current_folder_path
                )
                if file_result:
                    processed_files.append(file_result)
            except Exception as e:
                logger.error(
                    f"Error processing file {file_info.get('name', 'Unknown')}: {e}")
                self.download_stats['errors'] += 1

        # Process subfolders recursively
        for subfolder_structure in folder_structure['subfolders'].values():
            # Verificar flag de cancelamento periodicamente
            if self.cancel_flag:
                logger.info("🛑 Subfolder processing cancelled")
                raise Exception("Operation cancelled by user")

            try:
                subfolder_files = self.process_folder_recursive(
                    subfolder_structure)
                processed_files.extend(subfolder_files)
            except Exception as e:
                logger.error(f"Error processing subfolder: {e}")
                self.download_stats['errors'] += 1

        return processed_files

    async def download_drive_recursive_async(self, root_folder_id: str, max_depth: Optional[int] = None) -> Dict[str, Any]:
        """Versão assíncrona do download recursivo"""
        # Implementação assíncrona usando asyncio
        return {}

    def download_drive_recursive(self, root_folder_id: str, max_depth: Optional[int] = None) -> Dict[str, Any]:
        """Main method to download entire Drive folder structure recursively with low memory footprint"""
        logger.info(
            f"🚀 Starting recursive download (streaming) of folder: {root_folder_id}")

        # Reset stats and cancel flag
        self.download_stats = {
            'total_folders': 0,
            'total_files': 0,
            'downloaded_files': 0,
            'skipped_duplicates': 0,
            'errors': 0
        }
        self.cancel_flag = False

        # Scan existing files to avoid re-downloading
        logger.info("🔍 Scanning existing files to avoid duplicates...")
        existing_hashes = self.scan_existing_files()
        self.file_hashes.update(existing_hashes)
        logger.info(f"📊 Found {len(existing_hashes)} existing files to skip")

        start_time = time.time()

        processed_files_sample: List[Dict[str, Any]] = []
        processed_files_sample_limit: int = 200

        def download_folder_recursive(folder_id: str, parent_path: str = "", current_depth: int = 0):
            # Verificar profundidade máxima
            if max_depth is not None and current_depth >= max_depth:
                return []

            if self.cancel_flag:
                raise Exception("Operação cancelada pelo usuário")

            processed: List[Dict[str, Any]] = []

            # Tentar obter nome da pasta (melhor logging e path)
            try:
                folder_info = self.service.files().get(
                    fileId=folder_id, fields="id,name").execute() if self.service else {"name": "unknown"}
                folder_name = folder_info.get('name', 'Unknown')
            except Exception:
                folder_name = f'folder_{folder_id[:8]}'

            current_path = os.path.join(
                parent_path, folder_name) if parent_path else folder_name
            logger.info(f"📂 Processing folder (stream): {current_path}")

            # Listar itens desta pasta em páginas menores para reduzir pico de memória
            page_token = None
            while True:
                if self.cancel_flag:
                    raise Exception("Operação cancelada pelo usuário")

                query = f"'{folder_id}' in parents and trashed = false"
                try:
                    request = self.service.files().list(
                        q=query,
                        pageSize=200,
                        pageToken=page_token,
                        fields="nextPageToken, files(id,name,mimeType,size,parents,createdTime,modifiedTime)"
                    ) if self.service else None

                    results = request.execute() if request else {"files": []}
                    items = results.get('files', [])
                    self.download_stats['total_files'] += len(
                        [i for i in items if i.get('mimeType') != 'application/vnd.google-apps.folder'])
                    self.download_stats['total_folders'] += len(
                        [i for i in items if i.get('mimeType') == 'application/vnd.google-apps.folder'])

                    logger.info(
                        f"📊 Found {len(items)} items in folder: {folder_name}")

                    # Primeiro processa arquivos
                    for item in items:
                        if item.get('mimeType') == 'application/vnd.google-apps.folder':
                            continue
                        if self.cancel_flag:
                            raise Exception("Operação cancelada pelo usuário")
                        try:
                            file_result = self.download_file_with_duplicate_check(
                                item.get('id'),
                                item.get('name', 'Unknown'),
                                current_path
                            )
                            if file_result:
                                # Guardar apenas uma amostra para reduzir uso de memória
                                if len(processed_files_sample) < processed_files_sample_limit:
                                    processed_files_sample.append(file_result)
                                processed.append(file_result)
                        except Exception as e:
                            logger.error(
                                f"Error processing file {item.get('name','Unknown')}: {e}")
                            self.download_stats['errors'] += 1

                    # Depois processa subpastas
                    for item in items:
                        if item.get('mimeType') == 'application/vnd.google-apps.folder':
                            if self.cancel_flag:
                                raise Exception(
                                    "Operação cancelada pelo usuário")
                            try:
                                processed.extend(
                                    download_folder_recursive(
                                        item['id'], current_path, current_depth + 1)
                                )
                            except Exception as e:
                                logger.error(
                                    f"Error processing subfolder {item.get('name','Unknown')}: {e}")
                                self.download_stats['errors'] += 1

                    page_token = results.get('nextPageToken')
                    if not page_token:
                        break
                except Exception as e:
                    logger.error(
                        f"Error listing folder contents (stream): {e}")
                    break

            return processed

        try:
            processed_files = download_folder_recursive(root_folder_id, "", 0)

            total_time = time.time() - start_time
            logger.info("🎉 Recursive download (streaming) completed!")
            logger.info(f"📊 Final Statistics:")
            logger.info(
                f"   Total folders (seen): {self.download_stats['total_folders']}")
            logger.info(
                f"   Total files (seen): {self.download_stats['total_files']}")
            logger.info(
                f"   Files downloaded: {self.download_stats['downloaded_files']}")
            logger.info(
                f"   Duplicates skipped: {self.download_stats['skipped_duplicates']}")
            logger.info(f"   Errors: {self.download_stats['errors']}")
            logger.info(f"   Total time: {total_time:.2f}s")

            return {
                'status': 'success',
                'statistics': self.download_stats,
                'processed_files': processed_files[:processed_files_sample_limit],
                'processed_files_total': len(processed_files),
                'folder_structure': {},  # não retornamos a árvore completa para reduzir memória
                'timing': {
                    'total_time': total_time
                }
            }
        except Exception as e:
            logger.error(
                f"❌ Error in recursive download (streaming): {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'statistics': self.download_stats
            }

    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a file"""
        try:
            if not self.service:
                return None

            file_metadata = self.service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,size,parents,createdTime,modifiedTime,webViewLink"
            ).execute()

            return file_metadata

        except HttpError as e:
            logger.warning(
                f"⚠️ HTTP Error getting metadata for file {file_id}: {e}")
            return None
        except Exception as e:
            logger.warning(
                f"⚠️ Error getting metadata for file {file_id}: {e}")
            return None

    def try_public_file_access(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Try to access a file through public methods"""
        logger.info(f"🔓 Trying public access for file: {file_id}")

        public_urls = [
            f"https://drive.google.com/uc?export=download&id={file_id}",
            f"https://drive.google.com/file/d/{file_id}/view",
        ]

        for i, url in enumerate(public_urls):
            try:
                logger.info(f"🌐 Trying public URL method {i+1}...")
                response = requests.get(url, allow_redirects=True, timeout=30)

                if response.status_code == 200 and len(response.content) > 100:
                    content_type = response.headers.get(
                        'content-type', '').lower()

                    # Skip HTML error pages
                    if 'text/html' in content_type and b'<html' in response.content[:1000]:
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

    def get_download_stats(self) -> Dict[str, Any]:
        """Get statistics about downloaded materials"""
        if not self.materials_dir.exists():
            return {
                'total_folders': 0,
                'total_files': 0,
                'total_size': 0,
                'file_types': {},
                'directory': str(self.materials_dir),
                'processed_files_count': 0,
                'unique_hashes_count': 0,
                'downloaded_files': 0,
                'skipped_duplicates': 0,
                'errors': 0
            }

        files = list(self.materials_dir.rglob("*"))
        total_size = sum(f.stat().st_size for f in files if f.is_file())

        # Contar pastas
        total_folders = len([f for f in files if f.is_dir()])

        file_types = {}
        for file in files:
            if file.is_file():
                ext = file.suffix.lower() or 'no_extension'
                file_types[ext] = file_types.get(ext, 0) + 1

        return {
            'total_folders': total_folders,
            'total_files': len([f for f in files if f.is_file()]),
            'total_size': total_size,
            'file_types': file_types,
            'directory': str(self.materials_dir),
            'processed_files_count': len(self.processed_files),
            'unique_hashes_count': len(self.file_hashes),
            'downloaded_files': self.download_stats.get('downloaded_files', 0),
            'skipped_duplicates': self.download_stats.get('skipped_duplicates', 0),
            'errors': self.download_stats.get('errors', 0)
        }

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

    def reset(self):
        """Reset handler state"""
        logger.info("🔄 Resetting RecursiveDriveHandler...")
        self.processed_files.clear()
        # Don't clear file_hashes to preserve existing file information
        self.download_stats = {
            'total_folders': 0,
            'total_files': 0,
            'downloaded_files': 0,
            'skipped_duplicates': 0,
            'errors': 0
        }
        self.cancel_flag = False  # Resetar flag de cancelamento
        logger.info("✅ Handler reset completed")

    def set_cancel_flag(self, value: bool = True):
        """Define o flag de cancelamento para interromper operações em andamento"""
        self.cancel_flag = value
        logger.info(f"🛑 Flag de cancelamento definido como: {value}")

    # ==========================================
    # UPLOAD / CREATE METHODS (bidirectional sync)
    # ==========================================

    def create_folder(self, folder_name: str, parent_folder_id: str) -> Optional[str]:
        """Create a folder in Google Drive and return its ID."""
        if not self.service:
            logger.error("❌ Service not initialized")
            return None
        try:
            metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            folder = self.service.files().create(
                body=metadata, fields='id'
            ).execute()
            folder_id = folder.get('id')
            logger.info(f"📁 Created folder '{folder_name}' with id: {folder_id}")
            return folder_id
        except HttpError as e:
            logger.error(f"❌ HTTP error creating folder '{folder_name}': {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error creating folder '{folder_name}': {e}")
            return None

    def ensure_folder_exists(self, folder_name: str, parent_folder_id: str) -> Optional[str]:
        """Return the ID of a folder named folder_name inside parent, creating it if needed."""
        if not self.service:
            logger.error("❌ Service not initialized")
            return None
        try:
            query = (
                f"name = '{folder_name}' "
                f"and '{parent_folder_id}' in parents "
                f"and mimeType = 'application/vnd.google-apps.folder' "
                f"and trashed = false"
            )
            results = self.service.files().list(
                q=query, fields="files(id, name)", pageSize=1
            ).execute()
            files = results.get('files', [])
            if files:
                folder_id = files[0]['id']
                logger.info(f"📁 Found existing folder '{folder_name}': {folder_id}")
                return folder_id
            logger.info(f"📁 Folder '{folder_name}' not found — creating it")
            return self.create_folder(folder_name, parent_folder_id)
        except HttpError as e:
            logger.error(f"❌ HTTP error checking folder '{folder_name}': {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error checking folder '{folder_name}': {e}")
            return None

    def upload_file_to_drive(
        self,
        file_path: str,
        parent_folder_id: str,
        filename: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Upload a local file to a Google Drive folder.

        Returns a dict with id, name, webViewLink on success, or None.
        """
        if not self.service:
            logger.error("❌ Service not initialized")
            return None
        try:
            local_path = Path(file_path)
            if not local_path.exists():
                logger.error(f"❌ File not found: {file_path}")
                return None

            upload_name = filename or local_path.name
            mime_type, _ = mimetypes.guess_type(str(local_path))
            mime_type = mime_type or 'application/octet-stream'

            metadata = {
                'name': upload_name,
                'parents': [parent_folder_id]
            }
            media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)
            file_obj = self.service.files().create(
                body=metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()

            logger.info(f"⬆️ Uploaded '{upload_name}' → {file_obj.get('webViewLink', '')}")
            return file_obj
        except HttpError as e:
            logger.error(f"❌ HTTP error uploading '{file_path}': {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error uploading '{file_path}': {e}")
            return None

    def upload_bytes_to_drive(
        self,
        file_content: bytes,
        filename: str,
        parent_folder_id: str,
        mime_type: str = 'application/octet-stream'
    ) -> Optional[Dict[str, Any]]:
        """Upload raw bytes as a file to a Google Drive folder."""
        if not self.service:
            logger.error("❌ Service not initialized")
            return None
        try:
            metadata = {
                'name': filename,
                'parents': [parent_folder_id]
            }
            media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=mime_type, resumable=True)
            file_obj = self.service.files().create(
                body=metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            logger.info(f"⬆️ Uploaded bytes as '{filename}' → {file_obj.get('webViewLink', '')}")
            return file_obj
        except HttpError as e:
            logger.error(f"❌ HTTP error uploading bytes '{filename}': {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error uploading bytes '{filename}': {e}")
            return None

    def upload_to_materiais_chatbot_educacional(
        self,
        file_path: str,
        discipline: str,
        root_folder_id: str,
        root_folder_name: str = 'materiais_chatbot_educacional'
    ) -> Optional[Dict[str, Any]]:
        """Upload file_path to root_folder_id/materiais_chatbot_educacional/discipline/filename.

        Creates intermediate folders if they don't exist.
        Returns Drive file metadata on success, or None.
        """
        if not self.service:
            logger.error("❌ Service not initialized — authenticate first")
            return None

        materiais_id = self.ensure_folder_exists(root_folder_name, root_folder_id)
        if not materiais_id:
            logger.error(f"❌ Could not find/create '{root_folder_name}' folder")
            return None

        discipline_id = self.ensure_folder_exists(discipline, materiais_id)
        if not discipline_id:
            logger.error(f"❌ Could not find/create discipline folder '{discipline}'")
            return None

        return self.upload_file_to_drive(file_path, discipline_id)

    def list_discipline_folders(self, root_folder_id: str, root_folder_name: str = 'materiais_chatbot_educacional') -> List[Dict[str, Any]]:
        """Return the list of subfolders (disciplines) inside materiais_chatbot_educacional."""
        if not self.service:
            return []
        materiais_id = self.ensure_folder_exists(root_folder_name, root_folder_id)
        if not materiais_id:
            return []
        try:
            query = (
                f"'{materiais_id}' in parents "
                f"and mimeType = 'application/vnd.google-apps.folder' "
                f"and trashed = false"
            )
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                orderBy="name"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            logger.error(f"❌ Error listing discipline folders: {e}")
            return []
