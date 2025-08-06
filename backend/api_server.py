from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import json
import sys
import time
import hashlib
import shutil
import tempfile
import mimetypes
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from uuid import uuid4
import asyncio
from dotenv import load_dotenv
import aiohttp
from drive_sync.drive_handler import DriveHandler
from drive_sync.drive_handler_recursive import RecursiveDriveHandler
from auth.auth import get_current_user, User, router as auth_router
from auth.auth import get_optional_current_user
from auth.user_management import router as user_management_router
from chat_agents.educational_agent import router as educational_agent_router
import threading
import asyncio
from contextlib import asynccontextmanager

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="DNA da Força AI API",
    description="Sistema educacional com IA para treinamento físico - Versão Recursiva Completa",
    version="1.7.0"
)

# Configure CORS
cors_origins = os.getenv(
    "CORS_ORIGINS", "https://chatbot-educacional.vercel.app,http://localhost:3000,http://127.0.0.1:3000,https://dna-forca-frontend.vercel.app").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclua o router de user_management para expor /auth/users e outros endpoints de autenticação
app.include_router(user_management_router)
# Inclua o router de autenticação para endpoints públicos como redefinição de senha
app.include_router(auth_router)
# Se necessário, inclua outros routers:
app.include_router(educational_agent_router)

# RAG Server URL
RAG_SERVER_URL = os.getenv("RAG_SERVER_URL", "http://localhost:8001")

# User-specific handlers with thread locks
user_drive_handlers = {}
user_handler_locks = {}

# Global handler for shared operations
drive_handler = RecursiveDriveHandler()
simple_drive_handler = DriveHandler()

# Global lock for user handler creation
user_handler_creation_lock = threading.Lock()

# Global state for download tracking
download_progress = {}
active_downloads = {}

# Global lock for download progress updates
download_progress_lock = threading.Lock()

# User authentication status cache
user_auth_status = {}  # Armazenar status de autenticação por usuário

# Sistema de persistência para configurações do sistema
system_settings_file = Path("data/system_settings.json")
system_settings = None


def load_system_settings():
    """Carregar configurações do sistema do arquivo"""
    global system_settings

    if system_settings_file.exists():
        try:
            with open(system_settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                system_settings = data.get('settings', None)
                logger.info(f"✅ Configurações do sistema carregadas")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar configurações do sistema: {e}")
            system_settings = None


def save_system_settings():
    """Salvar configurações do sistema no arquivo"""
    global system_settings

    try:
        # Criar diretório se não existir
        system_settings_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'settings': system_settings,
            'last_updated': time.time()
        }

        with open(system_settings_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Configurações do sistema salvas")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar configurações do sistema: {e}")


def get_default_system_settings():
    """Retornar configurações padrão do sistema"""
    return {
        "general": {
            "siteName": "DNA da Força",
            "description": "Sistema Educacional de Treinamento Físico",
            "language": "pt-BR",
            "timezone": "America/Sao_Paulo",
            "maxFileSize": 50,
            "allowedFileTypes": ".pdf,.docx,.txt,.pptx",
        },
        "security": {
            "sessionTimeout": 180,
            "maxLoginAttempts": 3,
            "requirePasswordChange": False,
            "enableTwoFactor": False,
        },
        "notifications": {
            "emailNotifications": True,
            "pushNotifications": False,
            "maintenanceAlerts": True,
            "systemUpdates": True,
        }
    }


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

logger.info(
    "🚀 DNA da Força API v1.7.0 - Microserviços e Configurações Persistentes")

# ========================================
# MODELS
# ========================================


class Question(BaseModel):
    content: str


class Response(BaseModel):
    answer: str
    sources: List[dict]
    response_time: float


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class MaterialUpload(BaseModel):
    title: str
    description: Optional[str] = None
    tags: List[str] = []


class DriveSync(BaseModel):
    folder_id: str
    api_key: Optional[str] = None
    download_files: bool = True
    root_folder_id: Optional[str] = None
    max_depth: Optional[int] = None


class DriveTest(BaseModel):
    folder_id: str
    api_key: Optional[str] = None


class RecursiveSync(BaseModel):
    folder_id: str
    api_key: Optional[str] = None
    credentials_json: Optional[str] = None


class SystemStatus(BaseModel):
    status: str
    version: str
    rag_initialized: bool
    drive_authenticated: bool
    materials_count: int
    backend_uptime: str


class ResetComponent(BaseModel):
    component: str
    confirm: bool = False


class SystemSettingsGeneral(BaseModel):
    siteName: str
    description: str
    language: str
    timezone: str
    maxFileSize: int
    allowedFileTypes: str


class SystemSettingsSecurity(BaseModel):
    sessionTimeout: int
    maxLoginAttempts: int
    requirePasswordChange: bool
    enableTwoFactor: bool


class SystemSettingsNotifications(BaseModel):
    emailNotifications: bool
    pushNotifications: bool
    maintenanceAlerts: bool
    systemUpdates: bool


class SystemSettings(BaseModel):
    general: SystemSettingsGeneral
    security: SystemSettingsSecurity
    notifications: SystemSettingsNotifications

# ========================================
# UTILITY FUNCTIONS
# ========================================


def get_file_type(filename: str) -> str:
    """Get file type from filename"""
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        # Video files are no longer supported - they will be replaced by PDF files
        if mime_type == 'application/pdf':
            return 'pdf'
        elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            return 'docx'
        elif mime_type == 'text/plain':
            return 'txt'

    ext = Path(filename).suffix.lower()
    # Video extensions removed - videos will be replaced by PDF files
    if ext == '.pdf':
        return 'pdf'
    elif ext in ['.docx', '.doc']:
        return 'docx'
    elif ext == '.txt':
        return 'txt'
    else:
        return 'unknown'


def format_file_info(file_path: Path, uploaded_by: str = "system") -> dict:
    """Format file information for API response"""
    stat = file_path.stat()
    materials_dir = Path("data/materials")

    # Obter caminho relativo à pasta materials
    try:
        relative_path = file_path.relative_to(materials_dir)
        file_id = str(relative_path).replace("\\", "/")
    except ValueError:
        file_id = file_path.name

    return {
        "id": file_id,
        "title": file_path.stem.replace('_', ' ').title(),
        "description": f"Material: {file_path.name}",
        "type": get_file_type(file_path.name),
        "path": f"/api/materials/{file_id}",
        "size": stat.st_size,
        "uploadedAt": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "uploadedBy": uploaded_by,
        "tags": []
    }


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def analyze_duplicates(materials_dir: Path) -> Dict[str, Any]:
    """Analyze duplicate files in materials directory"""
    try:
        file_hashes = defaultdict(list)
        total_files = 0

        for file_path in materials_dir.rglob("*"):
            if file_path.is_file():
                total_files += 1
                try:
                    file_hash = calculate_file_hash(file_path)
                    file_hashes[file_hash].append({
                        "path": str(file_path.relative_to(materials_dir)),
                        "size": file_path.stat().st_size
                    })
                except Exception:
                    continue

        duplicate_groups = 0
        duplicate_files = 0
        wasted_space = 0

        for file_hash, file_list in file_hashes.items():
            if len(file_list) > 1:
                duplicate_groups += 1
                duplicate_files += len(file_list) - 1
                file_size = file_list[0]["size"]
                wasted_space += file_size * (len(file_list) - 1)

        return {
            "total_files_scanned": total_files,
            "unique_files": len(file_hashes),
            "duplicate_groups": duplicate_groups,
            "duplicate_files": duplicate_files,
            "wasted_space_bytes": wasted_space,
            "wasted_space_mb": round(wasted_space / (1024 * 1024), 2),
            "efficiency_percentage": round((1 - duplicate_files / total_files) * 100, 2) if total_files > 0 else 100
        }

    except Exception as e:
        logger.error(f"Error analyzing duplicates: {e}")
        return {"error": str(e)}


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable format"""
    if bytes_value == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(bytes_value)

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    return f"{size:.1f} {units[unit_index]}"

# ========================================
# SYSTEM ENDPOINTS
# ========================================


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "🚀 DNA da Força API v1.4 - Complete Recursive Drive Integration",
        "status": "ok",
        "version": "1.4.0",
        "features": [
            "auth", "chat", "upload", "materials",
            "recursive_drive_sync", "maintenance",
            "analytics", "health_monitoring"
        ]
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    materials_count = len(list(Path("data/materials").rglob("*"))
                          ) if Path("data/materials").exists() else 0

    # Check RAG server status
    rag_status = False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{RAG_SERVER_URL}/health") as response:
                if response.status == 200:
                    rag_data = await response.json()
                    rag_status = rag_data.get("rag_initialized", False)
    except:
        rag_status = False

    status = {
        "status": "ok",
        "version": "1.4.0",
        "rag_initialized": rag_status,
        "drive_authenticated": drive_handler.service is not None,
        "materials_count": materials_count,
        "backend_uptime": "online",
        "timestamp": datetime.now().isoformat(),
        "active_downloads": len(active_downloads),
        "total_download_sessions": len(download_progress)
    }

    return status


@app.get("/status")
async def get_status():
    """Get detailed system status"""
    materials_dir = Path("data/materials")
    chromadb_dir = Path(".chromadb")

    # Check RAG server status
    rag_status = False
    rag_materials_count = 0
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{RAG_SERVER_URL}/status") as response:
                if response.status == 200:
                    rag_data = await response.json()
                    rag_status = rag_data.get("rag_initialized", False)
                    rag_materials_count = rag_data.get("materials_count", 0)
    except:
        rag_status = False
        rag_materials_count = 0

    return {
        "backend": "online",
        "database": "simulated" if not rag_status else "active",
        "ai_enabled": rag_status,
        "materials_count": rag_materials_count,
        "materials_directory_exists": materials_dir.exists(),
        "chromadb_exists": chromadb_dir.exists(),
        "drive_handler_initialized": drive_handler is not None,
        "drive_authenticated": drive_handler.service is not None if drive_handler else False,
        "uptime": "Running",
        "version": "1.4.0",
        "timestamp": datetime.now().isoformat(),
        "message": "Sistema funcionando com funcionalidades recursivas completas."
    }

# ========================================
# INITIALIZATION ENDPOINTS
# ========================================


@app.post("/initialize")
async def initialize_system(
    api_key: str = Form(...),
    drive_folder_id: Optional[str] = Form(None),
    drive_api_key: Optional[str] = Form(None),
    credentials_json: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user)
):
    """Initialize the system with API keys and optional Drive materials"""
    logger.info(f"🚀 System initialization started by: {current_user.username}")
    logger.info(f"🔑 OpenAI API Key provided: {len(api_key) > 0}")
    logger.info(f"📁 Drive folder ID: {drive_folder_id}")
    logger.info(
        f"🔐 Drive API Key provided: {len(drive_api_key) > 0 if drive_api_key else False}")
    logger.info(f"📄 Credentials file uploaded: {credentials_json is not None}")

    try:
        messages = []

        # Initialize RAG handler via RAG server
        logger.info("🤖 Initializing RAG handler via RAG server...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{RAG_SERVER_URL}/initialize", json={"api_key": api_key}) as response:
                    if response.status == 200:
                        messages.append("✓ Initialized RAG handler")
                        logger.info("✅ RAG handler initialized successfully")
                    else:
                        error_detail = await response.text()
                        logger.error(
                            f"❌ RAG initialization failed: {error_detail}")
                        messages.append(
                            f"❌ RAG initialization failed: {error_detail}")
        except aiohttp.ClientError as e:
            logger.error(f"❌ Connection error to RAG server: {str(e)}")
            messages.append(f"❌ RAG server unavailable: {str(e)}")

        # Process Drive materials if provided
        if drive_folder_id:
            logger.info(f"📂 Processing Drive folder: {drive_folder_id}")
            try:
                # Authenticate with Drive
                if credentials_json:
                    logger.info("💾 Saving uploaded credentials file...")
                    creds_path = Path("credentials.json")
                    content = await credentials_json.read()
                    creds_path.write_bytes(content)
                    logger.info(f"✅ Credentials saved to: {creds_path}")

                    auth_success = drive_handler.authenticate(str(creds_path))
                else:
                    logger.info("🔑 Attempting authentication with API key...")
                    auth_success = drive_handler.authenticate(
                        api_key=drive_api_key or "")

                if auth_success:
                    messages.append("✓ Authenticated with Google Drive")
                    logger.info("✅ Google Drive authentication successful")

                    # Test folder access first
                    logger.info("🧪 Testing folder access...")
                    try:
                        # Use the get_folder_structure method to test access
                        structure = drive_handler.get_folder_structure(
                            drive_folder_id)

                        if structure and 'files' in structure:
                            total_files = len(structure['files'])
                            logger.info(
                                f"✅ Folder accessible: {structure.get('name', 'Unknown')} ({total_files} files)")
                            messages.append(
                                f"✓ Folder accessible: {structure.get('name', 'Unknown')} ({total_files} files)")

                            # Process folder recursively
                            logger.info(
                                "📥 Starting recursive download process...")
                            result = drive_handler.download_drive_recursive(
                                drive_folder_id)

                            if result['status'] == 'success':
                                downloaded_count = result['statistics']['downloaded_files']
                                logger.info(
                                    f"🎉 Successfully downloaded {downloaded_count} files")
                                messages.append(
                                    f"✓ Downloaded {downloaded_count} files recursively")
                            else:
                                error_msg = result.get(
                                    'error', 'Unknown error')
                                logger.error(
                                    f"❌ Recursive download failed: {error_msg}")
                                messages.append(
                                    f"❌ Download failed: {error_msg}")
                        else:
                            logger.warning(
                                "⚠️ Folder appears to be empty or inaccessible")
                            messages.append(
                                "⚠️ Folder appears to be empty or inaccessible")
                    except Exception as access_error:
                        logger.error(f"❌ Cannot access folder: {access_error}")
                        messages.append(
                            f"❌ Cannot access folder: {str(access_error)}")
                else:
                    logger.error("❌ Google Drive authentication failed")
                    messages.append(
                        "⚠️ Could not authenticate with Google Drive")

                # Cleanup temporary files
                logger.info("🧹 Cleaning up temporary files...")
                drive_handler.cleanup_temp_files()

            except Exception as e:
                logger.error(f"❌ Drive sync error: {str(e)}")
                messages.append(f"⚠️ Drive sync error: {str(e)}")

        # Process materials via RAG server
        try:
            logger.info("🧠 Starting RAG processing via RAG server...")
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{RAG_SERVER_URL}/process-materials", json={"api_key": api_key, "force_reprocess": False}) as response:
                    if response.status == 200:
                        messages.append("✓ RAG processing initiated")
                        logger.info("✅ RAG processing initiated successfully")
                    else:
                        error_detail = await response.text()
                        logger.error(
                            f"❌ RAG processing failed: {error_detail}")
                        messages.append(
                            f"❌ RAG processing failed: {error_detail}")

        except aiohttp.ClientError as e:
            logger.error(f"❌ Connection error to RAG server: {str(e)}")
            messages.append(f"❌ RAG server unavailable: {str(e)}")

        logger.info("🏁 System initialization completed")
        return {"status": "success", "messages": messages}

    except Exception as e:
        logger.error(f"❌ System initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# CHAT ENDPOINTS
# ========================================


@app.post("/chat", response_model=Response)
async def chat(question: Question):
    """Simplified chat endpoint - forwards to RAG server"""
    logger.info(f"💬 Chat request: {question.content[:50]}...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{RAG_SERVER_URL}/chat", json={"content": question.content}) as response:
                if response.status == 200:
                    data = await response.json()
                    return Response(**data)
                else:
                    error_detail = await response.text()
                    logger.error(f"❌ RAG server error: {error_detail}")
                    raise HTTPException(
                        status_code=response.status, detail=f"RAG server error: {error_detail}")
    except aiohttp.ClientError as e:
        logger.error(f"❌ Connection error to RAG server: {str(e)}")
        raise HTTPException(status_code=503, detail="RAG server unavailable")
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat-auth", response_model=Response)
async def chat_auth(question: Question, current_user: User = Depends(get_current_user)):
    """Process a chat question with authentication - forwards to RAG server"""
    logger.info(
        f"💬 Chat request from {current_user.username}: {question.content[:50]}...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{RAG_SERVER_URL}/chat-auth", json={"content": question.content}) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(
                        f"✅ Chat response generated (time: {data.get('response_time', 0):.2f}s)")
                    return Response(**data)
                else:
                    error_detail = await response.text()
                    logger.error(f"❌ RAG server error: {error_detail}")
                    raise HTTPException(
                        status_code=response.status, detail=f"RAG server error: {error_detail}")
    except aiohttp.ClientError as e:
        logger.error(f"❌ Connection error to RAG server: {str(e)}")
        raise HTTPException(status_code=503, detail="RAG server unavailable")
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/agent")
async def chat_agent_stream(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Endpoint to stream responses from the chat agent - forwards to RAG server"""
    thread_id = request.thread_id or str(uuid4())
    logger.info(
        f"🤖 Agent chat request from {current_user.username} on thread {thread_id}: {request.message[:50]}...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{RAG_SERVER_URL}/chat/agent", json={"message": request.message, "thread_id": thread_id}) as response:
                if response.status == 200:
                    # Forward the streaming response
                    return StreamingResponse(
                        response.content,
                        media_type="text/event-stream"
                    )
                else:
                    error_detail = await response.text()
                    logger.error(f"❌ RAG server error: {error_detail}")
                    raise HTTPException(
                        status_code=response.status, detail=f"RAG server error: {error_detail}")
    except aiohttp.ClientError as e:
        logger.error(f"❌ Connection error to RAG server: {str(e)}")
        raise HTTPException(status_code=503, detail="RAG server unavailable")
    except Exception as e:
        logger.error(f"❌ Agent chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# RECURSIVE DRIVE ENDPOINTS
# ========================================


@asynccontextmanager
async def get_user_drive_handler(username: str, api_key: str = None):
    """Get or create a user-specific drive handler with proper locking and auth caching"""
    # Use a global lock when creating user locks to avoid race conditions
    with user_handler_creation_lock:
        # Create lock for this user if it doesn't exist
        if username not in user_handler_locks:
            user_handler_locks[username] = threading.Lock()

    # Acquire the lock for this user
    with user_handler_locks[username]:
        # Create handler if it doesn't exist
        if username not in user_drive_handlers:
            user_drive_handlers[username] = RecursiveDriveHandler()
            logger.info(f"Created new drive handler for user: {username}")

        # Get the user's handler
        handler = user_drive_handlers[username]

        # Verificar se já autenticamos com sucesso anteriormente
        auth_needed = True
        if username in user_auth_status and user_auth_status[username]['authenticated']:
            # Verificar se o token ainda é válido (verificação a cada 30 minutos)
            last_check = user_auth_status[username]['last_check']
            if time.time() - last_check < 1800:  # 30 minutos
                auth_needed = False
                logger.info(
                    f"Reusing cached authentication for user: {username}")

        # Authenticate if needed
        if auth_needed:
            # Tentar autenticar com OAuth2 primeiro (se api_key não for fornecido)
            # ou com api_key se fornecido
            auth_success = handler.authenticate(api_key=api_key)
            # Armazenar status de autenticação
            user_auth_status[username] = {
                'authenticated': auth_success,
                'last_check': time.time()
            }

        try:
            # Yield the handler for use in the calling function
            yield handler
        finally:
            # Any cleanup if needed
            pass


@app.post("/drive/sync-recursive")
async def sync_drive_recursive(
    data: RecursiveSync,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Start recursive Google Drive sync"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"🔄 Recursive sync requested by: {current_user.username}")
    logger.info(f"📁 Folder ID: {data.folder_id}")

    try:
        # Get user-specific drive handler
        async with get_user_drive_handler(current_user.username, data.api_key) as user_handler:
            # Verify authentication
            if not user_handler.service:
                raise HTTPException(
                    status_code=400, detail="Could not authenticate with Google Drive")

            # Start background download
            download_id = f"download_{current_user.username}_{int(time.time())}"

            # Update download progress with thread safety
            with download_progress_lock:
                download_progress[download_id] = {
                    "status": "starting",
                    "progress": 0,
                    "total_files": 0,
                    "downloaded_files": 0,
                    "current_file": "",
                    "started_at": datetime.now().isoformat(),
                    "folder_id": data.folder_id,
                    "user": current_user.username
                }
                active_downloads[download_id] = True

            # Create an isolated copy of the handler for the background task
            # to avoid concurrency issues with the user's main handler
            task_handler = RecursiveDriveHandler()
            task_handler.authenticate(api_key=data.api_key or "")

            async def run_recursive_download():
                try:
                    # Update status with thread safety
                    with download_progress_lock:
                        download_progress[download_id]["status"] = "analyzing"

                    # Run the download operation
                    result = task_handler.download_drive_recursive(
                        data.folder_id)

                    if result["status"] == "success":
                        # Update progress with thread safety
                        with download_progress_lock:
                            download_progress[download_id].update({
                                "status": "processing",
                                "progress": 95,  # Still processing
                                "total_files": result["statistics"]["total_files"],
                                "downloaded_files": result["statistics"]["downloaded_files"],
                            })

                        # Re-index materials in RAG server
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.post(f"{RAG_SERVER_URL}/process-materials", json={"api_key": "", "force_reprocess": False}) as response:
                                    if response.status == 200:
                                        logger.info("✅ Re-indexing complete.")
                                    else:
                                        logger.warning("⚠️ Re-indexing failed")
                        except Exception as e:
                            logger.warning(
                                f"⚠️ Could not trigger re-indexing: {str(e)}")

                        # Final update with thread safety
                        with download_progress_lock:
                            download_progress[download_id].update({
                                "status": "completed",
                                "progress": 100,
                                "completed_at": datetime.now().isoformat(),
                                "result": result
                            })
                    else:
                        # Error update with thread safety
                        with download_progress_lock:
                            download_progress[download_id].update({
                                "status": "error",
                                "error": result.get("error", "Unknown error"),
                                "completed_at": datetime.now().isoformat()
                            })
                except Exception as e:
                    # Exception update with thread safety
                    with download_progress_lock:
                        download_progress[download_id].update({
                            "status": "error",
                            "error": str(e),
                            "completed_at": datetime.now().isoformat()
                        })
                finally:
                    # Clean up task resources
                    task_handler.cleanup_temp_files()

            # Use asyncio.create_task for better async handling
            background_tasks.add_task(run_recursive_download)

        return {
            "status": "started",
            "download_id": download_id,
            "message": "Recursive download started in background"
        }

    except Exception as e:
        logger.error(f"❌ Recursive sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recursive-drive-analysis")
async def recursive_drive_analysis(
    data: DriveSync,
    current_user: User = Depends(get_current_user)
):
    """Analyze folder structure recursively without downloading"""
    logger.info(
        f"🔍 Recursive drive analysis requested by: {current_user.username}")

    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Use user-specific handler for better concurrency
        async with get_user_drive_handler(current_user.username, data.api_key) as user_handler:
            if not user_handler.service:
                raise HTTPException(
                    status_code=400, detail="Could not authenticate with Google Drive")

            # Get folder structure without downloading
            folder_structure = user_handler.get_folder_structure(
                data.folder_id, max_depth=data.max_depth)

            stats = user_handler.get_download_stats()
        return {
            "status": "success",
            "message": f"Analyzed folder structure with {stats['total_folders']} folders and {stats['total_files']} files",
            "statistics": stats,
            "folder_structure": folder_structure
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Recursive drive analysis error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Drive analysis error: {str(e)}")


@app.post("/recursive-drive-sync")
async def recursive_drive_sync(
    data: DriveSync,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Sync files recursively from the specified Google Drive folder"""
    logger.info(
        f"🔄 Recursive drive sync requested by: {current_user.username}")

    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Use user-specific handler for better concurrency
        async with get_user_drive_handler(current_user.username, data.api_key) as user_handler:
            if not user_handler.service:
                raise HTTPException(
                    status_code=400, detail="Could not authenticate with Google Drive")

            # Create a download ID for tracking
            download_id = f"sync_{current_user.username}_{int(time.time())}"

            # Update download progress with thread safety
            with download_progress_lock:
                download_progress[download_id] = {
                    "status": "starting",
                    "progress": 0,
                    "total_files": 0,
                    "downloaded_files": 0,
                    "current_file": "",
                    "started_at": datetime.now().isoformat(),
                    "folder_id": data.folder_id,
                    "user": current_user.username
                }
                active_downloads[download_id] = True

            # Create an isolated handler for the background task
            task_handler = RecursiveDriveHandler()
            task_handler.authenticate(api_key=data.api_key or "")

            async def run_recursive_download():
                try:
                    # Update status with thread safety
                    with download_progress_lock:
                        download_progress[download_id]["status"] = "analyzing"

                    # Run the download operation
                    result = task_handler.download_drive_recursive(
                        data.folder_id, max_depth=data.max_depth)

                    if result['status'] == 'success':
                        # Update progress with thread safety
                        with download_progress_lock:
                            download_progress[download_id].update({
                                "status": "processing",
                                "progress": 95,  # Still processing
                                "total_files": result["statistics"]["total_files"],
                                "downloaded_files": result["statistics"]["downloaded_files"],
                            })

                        # Re-index materials in RAG server
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.post(f"{RAG_SERVER_URL}/process-materials", json={"api_key": "", "force_reprocess": False}) as response:
                                    if response.status == 200:
                                        logger.info("✅ Re-indexing complete.")
                                    else:
                                        logger.warning("⚠️ Re-indexing failed")
                        except Exception as e:
                            logger.warning(
                                f"⚠️ Could not trigger re-indexing: {str(e)}")

                        # Final update with thread safety
                        with download_progress_lock:
                            download_progress[download_id].update({
                                "status": "completed",
                                "progress": 100,
                                "completed_at": datetime.now().isoformat(),
                                "result": result
                            })
                    else:
                        # Error update with thread safety
                        with download_progress_lock:
                            download_progress[download_id].update({
                                "status": "error",
                                "error": result.get("error", "Unknown error"),
                                "completed_at": datetime.now().isoformat()
                            })
                except Exception as e:
                    logger.error(f"❌ Recursive drive sync error: {str(e)}")
                    # Exception update with thread safety
                    with download_progress_lock:
                        download_progress[download_id].update({
                            "status": "error",
                            "error": str(e),
                            "completed_at": datetime.now().isoformat()
                        })
                finally:
                    # Clean up task resources
                    task_handler.cleanup_temp_files()

            # Use background tasks for better async handling
            background_tasks.add_task(run_recursive_download)

        return {
            "status": "started",
            "download_id": download_id,
            "message": "Recursive download started in background",
            "note": "Check /drive/download-progress for status updates"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Recursive drive sync error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Drive sync error: {str(e)}")


@app.get("/drive/analyze-folder")
async def analyze_folder(
    folder_id: str,
    api_key: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Analyze folder structure without downloading"""
    logger.info(
        f"🔍 Folder analysis requested by {current_user.username}: {folder_id}")

    try:
        # Use user-specific handler for better concurrency
        async with get_user_drive_handler(current_user.username, api_key) as user_handler:
            if not user_handler.service:
                raise HTTPException(
                    status_code=400, detail="Authentication failed")

                structure = user_handler.get_folder_structure(folder_id)
            stats = user_handler.get_download_stats()

            return {
                "status": "success",
                "folder_structure": structure,
                "statistics": stats,
                "analyzed_at": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"❌ Folder analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/drive/download-progress")
async def get_download_progress(
    download_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get download progress status"""
    # Use thread safety when accessing shared resources
    with download_progress_lock:
        if download_id:
            if download_id not in download_progress:
                raise HTTPException(
                    status_code=404, detail="Download not found")

            # Check if this is the user's download or if user is admin
            progress_info = download_progress[download_id]
            if current_user.role != "admin" and progress_info.get("user") != current_user.username:
                raise HTTPException(
                    status_code=403, detail="Not authorized to view this download")

            return progress_info

        # For admins, show all downloads
        if current_user.role == "admin":
            return {
                "active_downloads": list(active_downloads.keys()),
                "download_progress": download_progress
            }

            # For regular users, only show their downloads
            user_downloads = {}
        user_active_downloads = []

        for dl_id, progress in download_progress.items():
            if progress.get("user") == current_user.username:
                user_downloads[dl_id] = progress
                if dl_id in active_downloads:
                    user_active_downloads.append(dl_id)

        return {
            "active_downloads": user_active_downloads,
            "download_progress": user_downloads
        }


@app.post("/drive/cancel-download")
async def cancel_download(
    download_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel active download"""
    # Use thread safety when accessing shared resources
    with download_progress_lock:
        if download_id not in active_downloads:
            raise HTTPException(status_code=404, detail="Download not found")

        # Check if this is the user's download or if user is admin/instructor
        if download_id in download_progress:
            progress_info = download_progress[download_id]
            if current_user.role not in ["admin", "instructor"] and progress_info.get("user") != current_user.username:
                raise HTTPException(
                    status_code=403, detail="Not authorized to cancel this download")

        # Mark as cancelled
        if download_id in download_progress:
            download_progress[download_id]["status"] = "cancelled"
            download_progress[download_id]["cancelled_at"] = datetime.now(
            ).isoformat()

        # Find the appropriate handler to cancel
        if download_progress[download_id].get("user") in user_drive_handlers:
            user = download_progress[download_id].get("user")
            # Set cancel flag on the user's handler
            user_drive_handlers[user].set_cancel_flag(True)
        else:
            # Fallback to global handler
            drive_handler.set_cancel_flag(True)

        # Remove from active downloads
        active_downloads.pop(download_id, None)

    return {"status": "cancelled", "download_id": download_id}


@app.get("/drive/folder-stats")
async def get_folder_stats(current_user: User = Depends(get_current_user)):
    """Get detailed folder statistics"""
    try:
        stats = drive_handler.get_download_stats()

        # Enhanced stats with folder structure analysis
        materials_dir = Path("data/materials")
        if materials_dir.exists():
            folder_structure = {}

            for item in materials_dir.rglob("*"):
                if item.is_dir():
                    rel_path = str(item.relative_to(materials_dir))
                    files_in_folder = [
                        f for f in item.iterdir() if f.is_file()]

                    folder_structure[rel_path] = {
                        "file_count": len(files_in_folder),
                        "total_size": sum(f.stat().st_size for f in files_in_folder),
                        "files": [{"name": f.name, "size": f.stat().st_size, "type": f.suffix[1:] or "unknown"} for f in files_in_folder[:10]]
                    }

            stats["folder_structure"] = folder_structure

        return stats

    except Exception as e:
        logger.error(f"❌ Error getting folder stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/drive-stats-detailed")
async def get_drive_stats_detailed(current_user: User = Depends(get_current_user)):
    """Get detailed Drive statistics with folder structure"""
    logger.info(
        f"📊 Detailed drive stats requested by: {current_user.username}")

    try:
        # Get basic stats from drive handler
        basic_stats = drive_handler.get_download_stats()

        # Build detailed folder structure
        materials_dir = Path("data/materials")
        folder_structure = {}

        if materials_dir.exists():
            # Process root folder
            root_files = [f for f in materials_dir.iterdir() if f.is_file()]
            if root_files:
                folder_structure["root"] = {
                    "file_count": len(root_files),
                    "total_size": sum(f.stat().st_size for f in root_files),
                    "files": [
                        {
                            "name": f.name,
                            "size": f.stat().st_size,
                            "type": f.suffix[1:] or "unknown",
                            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                        }
                        for f in root_files
                    ]
                }

            # Process subdirectories
            for item in materials_dir.rglob("*"):
                if item.is_dir():
                    rel_path = str(item.relative_to(materials_dir))
                    if rel_path and rel_path != ".":  # Skip root
                        files_in_folder = [
                            f for f in item.iterdir() if f.is_file()]

                        if files_in_folder:  # Only include folders with files
                            folder_structure[rel_path] = {
                                "file_count": len(files_in_folder),
                                "total_size": sum(f.stat().st_size for f in files_in_folder),
                                "files": [
                                    {
                                        "name": f.name,
                                        "size": f.stat().st_size,
                                        "type": f.suffix[1:] or "unknown",
                                        "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                                    }
                                    for f in files_in_folder
                                ]
                            }

        # Enhanced stats
        enhanced_stats = {
            **basic_stats,
            "folder_structure": folder_structure,
            "drive_authenticated": drive_handler.service is not None,
            "authentication_method": (
                "API Key" if drive_handler.api_key else
                "OAuth2" if drive_handler.service else
                "None"
            ),
            "recursive_handler_available": True,
            "processed_files_info": {
                "unique_files": len(drive_handler.processed_files) if hasattr(drive_handler, 'processed_files') else 0,
                "hash_tracked_files": len(drive_handler.file_hashes) if hasattr(drive_handler, 'file_hashes') else 0
            },
            "timestamp": datetime.now().isoformat()
        }

        logger.info(
            f"📊 Detailed stats generated with {len(folder_structure)} folders")
        return enhanced_stats

    except Exception as e:
        logger.error(f"❌ Error getting detailed drive stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/drive/test-connection")
async def test_drive_connection(
    api_key: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Test Google Drive connection without performing operations"""
    logger.info(f"🧪 Drive connection test by: {current_user.username}")

    try:
        # Test authentication
        auth_success = drive_handler.authenticate(api_key=api_key or "")

        if auth_success:
            # Try a minimal operation to verify connection
            try:
                # Test with a simple about() call if possible
                if hasattr(drive_handler, 'service') and drive_handler.service:
                    about_info = drive_handler.service.about().get(
                        fields="user,storageQuota").execute()
                    user_email = about_info.get('user', {}).get(
                        'emailAddress', 'Unknown')

                    logger.info(f"Authenticated as: {user_email}")

                    return {
                        "connected": True,
                        "user_email": user_email,
                        "authentication_method": "API Key" if drive_handler.api_key else "OAuth2",
                        "service_available": True,
                        "storage_info": about_info.get('storageQuota', {}),
                        "tested_at": datetime.now().isoformat()
                    }
                else:
                    return {
                        "connected": True,
                        "authentication_method": "Public Access",
                        "service_available": True,
                        "note": "Limited access - may only work with public files",
                        "tested_at": datetime.now().isoformat()
                    }

            except Exception as test_error:
                logger.warning(f"⚠️ Connection test warning: {test_error}")
                return {
                    "connected": True,
                    "authentication_method": "API Key" if drive_handler.api_key else "OAuth2",
                    "service_available": True,
                    "warning": str(test_error),
                    "note": "Authentication successful but limited API access",
                    "tested_at": datetime.now().isoformat()
                }
        else:
            return {
                "connected": False,
                "error": "Authentication failed",
                "tested_at": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"❌ Drive connection test error: {str(e)}")
        return {
            "connected": False,
            "error": str(e),
            "tested_at": datetime.now().isoformat()
        }


@app.post("/drive/clear-cache")
async def clear_drive_cache(current_user: User = Depends(get_current_user)):
    """Clear drive handler cache and reset state"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    logger.info(f"🧹 Drive cache clear requested by: {current_user.username}")

    try:
        # Reset global drive handler state
        if hasattr(drive_handler, 'processed_files'):
            drive_handler.processed_files.clear()
        if hasattr(drive_handler, 'file_hashes'):
            drive_handler.file_hashes.clear()

        # Reset user-specific handlers with thread safety
        for username, lock in user_handler_locks.items():
            with lock:
                if username in user_drive_handlers:
                    handler = user_drive_handlers[username]
                    if hasattr(handler, 'processed_files'):
                        handler.processed_files.clear()
                    if hasattr(handler, 'file_hashes'):
                        handler.file_hashes.clear()
                    handler.cleanup_temp_files()

        # Reset download progress with thread safety
        with download_progress_lock:
            download_progress.clear()
            active_downloads.clear()

        # Clean up temporary files
        drive_handler.cleanup_temp_files()

        return {
            "status": "success",
            "message": "Drive cache and state cleared for all users",
            "cleared_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error clearing drive cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/clear-drive-cache")
async def maintenance_clear_drive_cache(current_user: User = Depends(get_current_user)):
    """Clear the drive handler's file hashes cache to allow redownloading files"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    logger.info(f"🧹 Clear drive cache requested by: {current_user.username}")

    try:
        # Limpar o cache do simple_drive_handler
        simple_result = simple_drive_handler.clear_file_hashes_cache()

        # Limpar também o cache do drive_handler recursivo
        recursive_result = drive_handler.clear_file_hashes_cache()

        return {
            "status": "success",
            "message": "Drive cache cleared successfully",
            "simple_handler": simple_result,
            "recursive_handler": recursive_result
        }

    except Exception as e:
        logger.error(f"❌ Error clearing drive cache: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Cache clearing error: {str(e)}")

# ========================================
# LEGACY DRIVE ENDPOINTS (for backward compatibility)
# ========================================


@app.post("/test-drive-folder")
async def test_drive_folder(
    data: DriveTest,
    current_user: User = Depends(get_current_user)
):
    """Test access to a Google Drive folder (non-recursive)"""
    logger.info(
        f"🧪 Drive folder test requested by: {current_user.username}")

    try:
        # Alterado para usar o simple_drive_handler em vez do drive_handler recursivo
        auth_success = simple_drive_handler.authenticate(
            api_key=data.api_key or "")
        if not auth_success:
            return {"accessible": False, "error": "Authentication failed"}

        # Usar o método list_folder_contents_with_pagination em vez de get_folder_structure
        files = simple_drive_handler.list_folder_contents_with_pagination(
            data.folder_id)

        if files:
            return {
                "accessible": True,
                "folder_name": "Folder",  # Nome básico da pasta
                "file_count": len(files),
                "total_folders": 0,  # Não contamos subpastas no modo não-recursivo
                "public": True,  # Assume public if accessible
                "method": "simple_handler",
                "files_sample": [f.get('name', 'Unknown') for f in files[:5]]
            }
        else:
            return {
                "accessible": False,
                "error": "Folder not found or empty"
            }

    except Exception as e:
        logger.error(f"❌ Legacy drive folder test error: {str(e)}")
        return {"accessible": False, "error": str(e)}


@app.post("/sync-drive")
async def sync_drive(
    data: DriveSync,
    current_user: User = Depends(get_current_user)
):
    """Sync materials from Google Drive (legacy endpoint)"""
    logger.info(f"🔄 Legacy drive sync requested by: {current_user.username}")

    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Use recursive sync for better results
        recursive_data = RecursiveSync(
            folder_id=data.folder_id,
            api_key=data.api_key
        )

        # Authenticate with Drive
        auth_success = drive_handler.authenticate(api_key=data.api_key or "")
        if not auth_success:
            raise HTTPException(
                status_code=400, detail="Could not authenticate with Google Drive")

        # Perform recursive download
        result = drive_handler.download_drive_recursive(data.folder_id)

        if result['status'] == 'success':
            # Re-index materials in RAG server
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{RAG_SERVER_URL}/process-materials", json={"api_key": "", "force_reprocess": False}) as response:
                        if response.status == 200:
                            logger.info("✅ Re-indexing complete.")
                        else:
                            logger.warning("⚠️ Re-indexing failed")
            except Exception as e:
                logger.warning(f"⚠️ Could not trigger re-indexing: {str(e)}")

            stats = drive_handler.get_download_stats()
            return {
                "status": "success",
                "message": f"Processed {result['statistics']['downloaded_files']} files from Google Drive",
                "files": result.get('processed_files', []),
                "statistics": result['statistics'],
                "folder_info": {
                    "accessible": True,
                    "folder_name": result.get('folder_structure', {}).get('name', 'Unknown'),
                    "file_count": result['statistics']['total_files']
                }
            }
        else:
            raise HTTPException(
                status_code=500, detail=result.get('error', 'Unknown error'))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Legacy drive sync error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Drive sync error: {str(e)}")


@app.get("/drive-stats")
async def get_drive_stats(current_user: User = Depends(get_current_user)):
    """Get Drive statistics (legacy endpoint)"""
    logger.info(f"📊 Legacy drive stats requested by: {current_user.username}")

    try:
        stats = drive_handler.get_download_stats()

        # Add additional information for legacy compatibility
        enhanced_stats = {
            **stats,
            "drive_authenticated": drive_handler.service is not None,
            "authentication_method": "API Key" if drive_handler.api_key else "OAuth2" if drive_handler.service else "None",
            "timestamp": datetime.now().isoformat()
        }

        logger.info(
            f"📊 Legacy stats retrieved: {enhanced_stats['total_files']} files, {enhanced_stats['total_size']} bytes")
        return enhanced_stats

    except Exception as e:
        logger.error(f"❌ Error getting legacy drive stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# MAINTENANCE ENDPOINTS
# ========================================


@app.post("/maintenance/cleanup-duplicates")
async def cleanup_duplicate_files(current_user: User = Depends(get_current_user)):
    """Remove duplicate files based on content hash"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    logger.info(f"🧹 Cleanup duplicates requested by: {current_user.username}")

    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {"status": "success", "message": "No materials directory found", "removed_files": 0}

        file_hashes = defaultdict(list)
        total_files = 0

        for file_path in materials_dir.rglob("*"):
            if file_path.is_file():
                total_files += 1
                try:
                    file_hash = calculate_file_hash(file_path)
                    file_hashes[file_hash].append(file_path)
                except Exception as e:
                    logger.warning(f"Could not hash file {file_path}: {e}")

        removed_files = 0
        duplicate_groups = 0
        saved_space = 0

        for file_hash, file_paths in file_hashes.items():
            if len(file_paths) > 1:
                duplicate_groups += 1
                for duplicate_file in file_paths[1:]:
                    try:
                        file_size = duplicate_file.stat().st_size
                        duplicate_file.unlink()
                        removed_files += 1
                        saved_space += file_size
                        logger.info(f"🗑️ Removed duplicate: {duplicate_file}")
                    except Exception as e:
                        logger.error(
                            f"Error removing duplicate {duplicate_file}: {e}")

        return {
            "status": "success",
            "message": f"Cleanup completed",
            "statistics": {
                "total_files_scanned": total_files,
                "duplicate_groups_found": duplicate_groups,
                "files_removed": removed_files,
                "space_saved_bytes": saved_space,
                "space_saved_mb": round(saved_space / (1024 * 1024), 2)
            }
        }

    except Exception as e:
        logger.error(f"❌ Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup error: {str(e)}")


@app.post("/maintenance/cleanup-empty-folders")
async def cleanup_empty_folders(current_user: User = Depends(get_current_user)):
    """Remove empty folders"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {"status": "success", "message": "No materials directory found", "removed_folders": 0}

        removed_folders = 0

        for folder_path in sorted(materials_dir.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if folder_path.is_dir() and folder_path != materials_dir:
                try:
                    if not any(folder_path.iterdir()):
                        folder_path.rmdir()
                        removed_folders += 1
                        logger.info(f"🗑️ Removed empty folder: {folder_path}")
                except Exception as e:
                    logger.warning(
                        f"Could not remove folder {folder_path}: {e}")

        return {
            "status": "success",
            "message": f"Empty folder cleanup completed",
            "removed_folders": removed_folders
        }

    except Exception as e:
        logger.error(f"❌ Error during folder cleanup: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Folder cleanup error: {str(e)}")


@app.post("/maintenance/optimize-storage")
async def optimize_storage(current_user: User = Depends(get_current_user)):
    """Run comprehensive storage optimization"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    logger.info(
        f"⚡ Storage optimization requested by: {current_user.username}")

    try:
        results = {
            "duplicate_cleanup": None,
            "empty_folder_cleanup": None,
            "total_space_saved": 0,
            "optimization_time": 0
        }

        start_time = time.time()

        # Run duplicate cleanup
        try:
            duplicate_response = await cleanup_duplicate_files(current_user)
            results["duplicate_cleanup"] = duplicate_response
            if "statistics" in duplicate_response:
                results["total_space_saved"] += duplicate_response["statistics"]["space_saved_bytes"]
        except Exception as e:
            results["duplicate_cleanup"] = {"error": str(e)}

        # Run empty folder cleanup
        try:
            folder_response = await cleanup_empty_folders(current_user)
            results["empty_folder_cleanup"] = folder_response
        except Exception as e:
            results["empty_folder_cleanup"] = {"error": str(e)}

        results["optimization_time"] = round(time.time() - start_time, 2)
        results["total_space_saved_mb"] = round(
            results["total_space_saved"] / (1024 * 1024), 2)

        return {
            "status": "success",
            "message": "Storage optimization completed",
            "results": results
        }

    except Exception as e:
        logger.error(f"❌ Error during storage optimization: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Storage optimization error: {str(e)}")


@app.post("/maintenance/reset-materials")
async def reset_materials_directory(current_user: User = Depends(get_current_user)):
    """Completely reset the materials directory"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    logger.info(f"🔄 Materials reset requested by: {current_user.username}")

    try:
        materials_dir = Path("data/materials")

        if materials_dir.exists():
            file_count = len(
                [f for f in materials_dir.rglob("*") if f.is_file()])
            folder_count = len(
                [f for f in materials_dir.rglob("*") if f.is_dir()])

            shutil.rmtree(materials_dir)
            logger.info(
                f"🗑️ Removed materials directory with {file_count} files and {folder_count} folders")
        else:
            file_count = 0
            folder_count = 0

        materials_dir.mkdir(parents=True, exist_ok=True)
        logger.info("📁 Created new empty materials directory")

        return {
            "status": "success",
            "message": "Materials directory reset completed",
            "removed_files": file_count,
            "removed_folders": folder_count
        }

    except Exception as e:
        logger.error(f"❌ Error during materials reset: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Materials reset error: {str(e)}")


@app.post("/maintenance/reset-chromadb")
async def reset_chromadb(current_user: User = Depends(get_current_user)):
    """Reset ChromaDB vector database"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    logger.info(f"🗄️ ChromaDB reset requested by: {current_user.username}")

    try:
        # Reset RAG handler via RAG server
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{RAG_SERVER_URL}/reset") as response:
                    if response.status == 200:
                        logger.info("🔄 RAG handler reset via RAG server")
                    else:
                        logger.warning("⚠️ RAG reset failed")
        except Exception as e:
            logger.warning(f"⚠️ Could not reset RAG: {str(e)}")

        chromadb_dir = Path(".chromadb")
        if chromadb_dir.exists():
            try:
                shutil.rmtree(chromadb_dir)
                logger.info("🗑️ Removed ChromaDB directory")
            except Exception as e:
                logger.error(f"❌ Failed to remove ChromaDB directory: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Could not remove ChromaDB directory. It might be locked. Error: {e}")

        return {
            "status": "success",
            "message": "ChromaDB reset completed",
            "note": "You will need to reinitialize the system to use chat functionality"
        }

    except Exception as e:
        logger.error(f"❌ Error during ChromaDB reset: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"ChromaDB reset error: {str(e)}")


@app.post("/maintenance/reset-component")
async def reset_component(
    data: ResetComponent,
    current_user: User = Depends(get_current_user)
):
    """Reset specific system component"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    logger.info(
        f"🔄 Component reset requested by: {current_user.username} - Component: {data.component}")

    if not data.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")

    try:
        if data.component == "materials":
            return await reset_materials_directory(current_user)
        elif data.component == "chromadb":
            return await reset_chromadb(current_user)
        elif data.component == "drive_cache":
            return await clear_drive_cache(current_user)
        elif data.component == "downloads":
            global download_progress, active_downloads
            download_progress.clear()
            active_downloads.clear()
            return {
                "status": "success",
                "message": "Download history cleared",
                "component": "downloads"
            }
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown component: {data.component}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resetting component {data.component}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Component reset error: {str(e)}")


@app.get("/maintenance/system-report")
async def generate_system_report(current_user: User = Depends(get_current_user)):
    """Generate comprehensive system report"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"📊 System report requested by: {current_user.username}")

    try:
        report = {
            "timestamp": datetime.now().isoformat(),
            "generated_by": current_user.username,
            "system_info": {
                "version": "1.4.0",
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": os.name
            },
            "directories": {},
            "drive_status": {},
            "rag_status": {},
            "file_analysis": {},
            "recommendations": []
        }

        # Directory analysis
        materials_dir = Path("data/materials")
        chromadb_dir = Path(".chromadb")

        if materials_dir.exists():
            all_files = list(materials_dir.rglob("*"))
            files = [f for f in all_files if f.is_file()]
            folders = [f for f in all_files if f.is_dir()]

            total_size = sum(f.stat().st_size for f in files)

            file_types = defaultdict(int)
            for file in files:
                ext = file.suffix.lower() or 'no_extension'
                file_types[ext] += 1

            size_ranges = {
                "< 1MB": 0,
                "1MB - 10MB": 0,
                "10MB - 100MB": 0,
                "> 100MB": 0
            }

            for file in files:
                size = file.stat().st_size
                if size < 1024 * 1024:
                    size_ranges["< 1MB"] += 1
                elif size < 10 * 1024 * 1024:
                    size_ranges["1MB - 10MB"] += 1
                elif size < 100 * 1024 * 1024:
                    size_ranges["10MB - 100MB"] += 1
                else:
                    size_ranges["> 100MB"] += 1

            report["directories"]["materials"] = {
                "exists": True,
                "total_files": len(files),
                "total_folders": len(folders),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": dict(file_types),
                "size_distribution": size_ranges
            }
        else:
            report["directories"]["materials"] = {"exists": False}

        report["directories"]["chromadb"] = {
            "exists": chromadb_dir.exists(),
            "size_bytes": sum(f.stat().st_size for f in chromadb_dir.rglob("*") if f.is_file()) if chromadb_dir.exists() else 0
        }

        # Drive status
        report["drive_status"] = {
            "handler_initialized": drive_handler is not None,
            "service_available": drive_handler.service is not None if drive_handler else False,
            "authentication_method": "API Key" if (drive_handler and drive_handler.api_key) else "OAuth2" if (drive_handler and drive_handler.service) else "None",
            "processed_files_count": len(drive_handler.processed_files) if drive_handler and hasattr(drive_handler, 'processed_files') else 0,
            "unique_hashes_count": len(drive_handler.file_hashes) if drive_handler and hasattr(drive_handler, 'file_hashes') else 0
        }

        # RAG status
        rag_status = False
        rag_stats = {}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{RAG_SERVER_URL}/stats") as response:
                    if response.status == 200:
                        rag_stats = await response.json()
                        rag_status = rag_stats.get("rag_initialized", False)
        except:
            rag_stats = {}
            rag_status = False

        report["rag_status"] = {
            "initialized": rag_status,
            "stats": rag_stats
        }

        # Duplicate analysis
        if materials_dir.exists():
            duplicate_analysis = analyze_duplicates(materials_dir)
            report["file_analysis"]["duplicates"] = duplicate_analysis

        # Generate recommendations
        recommendations = []

        if not report["drive_status"]["service_available"]:
            recommendations.append(
                "Configure Google Drive authentication for sync functionality")

        if not report["rag_status"]["initialized"]:
            recommendations.append(
                "Initialize RAG system for chat functionality")

        if report["directories"]["materials"]["exists"]:
            if report["file_analysis"].get("duplicates", {}).get("duplicate_groups", 0) > 0:
                recommendations.append(
                    "Run duplicate cleanup to save storage space")

            if report["directories"]["materials"]["total_files"] == 0:
                recommendations.append(
                    "Sync materials from Google Drive or upload files manually")

        report["recommendations"] = recommendations

        return report

    except Exception as e:
        logger.error(f"❌ Error generating system report: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Report generation error: {str(e)}")


@app.get("/maintenance/health-check")
async def health_check(current_user: User = Depends(get_current_user)):
    """Comprehensive health check"""
    logger.info(f"🏥 Health check requested by: {current_user.username}")

    try:
        checks = {
            "materials_directory": False,
            "chromadb": False,
            "drive_handler": False,
            "rag_handler": False,
            "download_system": False
        }

        issues = []

        # Check materials directory
        materials_dir = Path("data/materials")
        if materials_dir.exists() and materials_dir.is_dir():
            checks["materials_directory"] = True
        else:
            issues.append("Materials directory does not exist")

        # Check ChromaDB
        chromadb_dir = Path(".chromadb")
        if chromadb_dir.exists():
            checks["chromadb"] = True
        else:
            issues.append("ChromaDB directory not found")

        # Check drive handler
        if drive_handler and hasattr(drive_handler, 'service'):
            checks["drive_handler"] = True
        else:
            issues.append("Drive handler not properly initialized")

        # Check RAG handler
        rag_status = False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{RAG_SERVER_URL}/health") as response:
                    if response.status == 200:
                        rag_data = await response.json()
                        rag_status = rag_data.get("rag_initialized", False)
        except:
            rag_status = False

        if rag_status:
            checks["rag_handler"] = True
        else:
            issues.append("RAG handler not initialized")

        # Check download system
        checks["download_system"] = True  # Always available

        overall_health = all(checks.values())

        return {
            "healthy": overall_health,
            "checks": checks,
            "issues": issues,
            "active_downloads": len(active_downloads),
            "total_download_sessions": len(download_progress),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error in health check: {str(e)}")
        return {
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ========================================
# ANALYTICS ENDPOINTS
# ========================================


@app.get("/analytics/folder-structure")
async def get_folder_structure_analysis(current_user: User = Depends(get_current_user)):
    """Get detailed folder structure analysis"""
    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {"structure": {}, "total_folders": 0, "total_files": 0}

        structure = {}
        total_folders = 0
        total_files = 0

        for item in materials_dir.rglob("*"):
            if item.is_dir():
                total_folders += 1
                rel_path = str(item.relative_to(materials_dir)) or "root"
                files_in_folder = [f for f in item.iterdir() if f.is_file()]

                structure[rel_path] = {
                    "file_count": len(files_in_folder),
                    "total_size": sum(f.stat().st_size for f in files_in_folder),
                    "files": [
                        {
                            "name": f.name,
                            "size": f.stat().st_size,
                            "type": f.suffix[1:] or "unknown",
                            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                        }
                        for f in files_in_folder
                    ]
                }
            elif item.is_file():
                total_files += 1

            return {
                "structure": structure,
                "total_folders": total_folders,
                "total_files": total_files,
                "analyzed_at": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"❌ Error in folder structure analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/file-distribution")
async def get_file_distribution_analysis(current_user: User = Depends(get_current_user)):
    """Get file type and size distribution analysis"""
    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {"file_types": {}, "size_distribution": {}, "total_files": 0}

        file_types = defaultdict(lambda: {"count": 0, "total_size": 0})
        size_distribution = {
            "< 1MB": 0,
            "1MB - 10MB": 0,
            "10MB - 100MB": 0,
            "> 100MB": 0
        }

        total_files = 0
        total_size = 0

        for file_path in materials_dir.rglob("*"):
            if file_path.is_file():
                total_files += 1
                file_size = file_path.stat().st_size
                total_size += file_size

                # File type analysis
                ext = file_path.suffix.lower() or 'no_extension'
                file_types[ext]["count"] += 1
                file_types[ext]["total_size"] += file_size

                # Size distribution
                if file_size < 1024 * 1024:
                    size_distribution["< 1MB"] += 1
                elif file_size < 10 * 1024 * 1024:
                    size_distribution["1MB - 10MB"] += 1
                elif file_size < 100 * 1024 * 1024:
                    size_distribution["10MB - 100MB"] += 1
                else:
                    size_distribution["> 100MB"] += 1

        return {
            "file_types": dict(file_types),
            "size_distribution": size_distribution,
            "total_files": total_files,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "analyzed_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error in file distribution analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/storage-efficiency")
async def get_storage_efficiency_analysis(current_user: User = Depends(get_current_user)):
    """Get storage efficiency analysis including duplicates"""
    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {"efficiency": 100, "duplicates": {}, "recommendations": []}

        duplicate_analysis = analyze_duplicates(materials_dir)

        recommendations = []
        if duplicate_analysis.get("duplicate_files", 0) > 0:
            recommendations.append(
                f"Remove {duplicate_analysis['duplicate_files']} duplicate files to save {duplicate_analysis['wasted_space_mb']} MB")

        if duplicate_analysis.get("efficiency_percentage", 100) < 90:
            recommendations.append("Consider running storage optimization")

        return {
            "efficiency": duplicate_analysis.get("efficiency_percentage", 100),
            "duplicates": duplicate_analysis,
            "recommendations": recommendations,
            "analyzed_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error in storage efficiency analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/download-report")
async def get_download_report(current_user: User = Depends(get_current_user)):
    """Get download activity report"""
    try:
        # Combine download progress and completed downloads
        recent_downloads = []

        for download_id, progress in download_progress.items():
            recent_downloads.append({
                "download_id": download_id,
                "folder_id": progress.get("folder_id", "unknown"),
                "status": progress.get("status", "unknown"),
                "started_at": progress.get("started_at"),
                "completed_at": progress.get("completed_at"),
                "total_files": progress.get("total_files", 0),
                "downloaded_files": progress.get("downloaded_files", 0),
                "progress": progress.get("progress", 0)
            })

        # Sort by start time
        recent_downloads.sort(key=lambda x: x.get(
            "started_at", ""), reverse=True)

        # Summary statistics
        total_downloads = len(recent_downloads)
        completed_downloads = len(
            [d for d in recent_downloads if d["status"] == "completed"])
        failed_downloads = len(
            [d for d in recent_downloads if d["status"] == "error"])

        return {
            "summary": {
                "total_downloads": total_downloads,
                "completed_downloads": completed_downloads,
                "failed_downloads": failed_downloads,
                "success_rate": round((completed_downloads / total_downloads * 100), 2) if total_downloads > 0 else 0
            },
            "recent_downloads": recent_downloads[:20],  # Last 20 downloads
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error generating download report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# MATERIALS ENDPOINTS
# ========================================


@app.get("/materials")
async def list_materials(current_user: User = Depends(get_current_user)):
    """List all available materials"""
    logger.info(f"📚 Materials list requested by: {current_user.username}")

    materials_dir = Path("data/materials")
    materials_dir.mkdir(parents=True, exist_ok=True)

    materials = []

    for file_path in materials_dir.rglob("*"):
        if file_path.is_file():
            materials.append(format_file_info(file_path, "user"))

    logger.info(f"📚 Returning {len(materials)} materials")
    return materials


@app.post("/materials/upload")
async def upload_material(
    file: UploadFile = File(...),
    description: str = Form(""),
    tags: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    """Upload a new material"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"📤 File upload by {current_user.username}: {file.filename}")

    if not file.filename:
        raise HTTPException(status_code=400, detail="File has no name")

    allowed_extensions = {'.pdf', '.docx', '.txt',
                          '.pptx'}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported: {', '.join(allowed_extensions)}"
        )

        materials_dir = Path("data/materials")
    materials_dir.mkdir(parents=True, exist_ok=True)

    file_path = materials_dir / file.filename
    counter = 1
    original_path = file_path

    while file_path.exists():
        stem = original_path.stem
        suffix = original_path.suffix
        file_path = materials_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    try:
        content = await file.read()
        max_size = 50 * 1024 * 1024  # 50MB

        if len(content) > max_size:
            raise HTTPException(
                status_code=400, detail="File too large (max 50MB)")

        with file_path.open("wb") as f:
            f.write(content)

        logger.info(f"✅ File uploaded successfully: {file_path}")

        # Re-index materials in RAG server
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{RAG_SERVER_URL}/process-materials", json={"api_key": "", "force_reprocess": False}) as response:
                    if response.status == 200:
                        logger.info("✅ Re-indexing complete.")
                    else:
                        logger.warning("⚠️ Re-indexing failed")
        except Exception as e:
            logger.warning(f"⚠️ Could not trigger re-indexing: {str(e)}")

        return {
            "status": "success",
            "message": "Upload successful",
            "filename": file_path.name,
            "size": len(content),
            "uploaded_by": current_user.username
        }

    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@app.get("/materials/{filename:path}")
async def download_material(filename: str, download: bool = False, current_user: Optional[User] = Depends(get_optional_current_user)):
    """Download a material file with optional authentication"""
    # Verificar se o arquivo deve ser protegido
    requires_auth = should_require_auth(filename)

    # Se o arquivo requer autenticação e o usuário não está autenticado, negar acesso
    if requires_auth and current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Normalizar o caminho do arquivo
    normalized_filename = filename.replace("/", os.path.sep)
    file_path = Path("data/materials") / normalized_filename

    if not file_path.exists() or not file_path.is_file():
        # Try to find file recursively
        materials_dir = Path("data/materials")
        found_files = list(materials_dir.rglob(Path(normalized_filename).name))

        if found_files:
            file_path = found_files[0]
        else:
            raise HTTPException(status_code=404, detail="File not found")

    # Registrar o download (opcional)
    logger.info(
        f"📥 File access: {file_path.name} by {current_user.username if current_user else 'anonymous'}")

    # Determinar o tipo MIME com base na extensão do arquivo
    content_type, _ = mimetypes.guess_type(str(file_path))

    # Se não conseguir determinar o tipo MIME, usar um padrão baseado na extensão
    if not content_type:
        if file_path.name.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif file_path.name.lower().endswith('.txt'):
            content_type = 'text/plain'
        elif file_path.name.lower().endswith('.docx'):
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            # Para outros tipos, forçar o download
            content_type = 'application/octet-stream'

    # Usar o parâmetro download da URL para determinar se deve forçar o download
    force_download = download

    return FileResponse(
        path=str(file_path),
        filename=Path(normalized_filename).name,
        media_type=content_type,
        # Se force_download for True, adicionar o cabeçalho Content-Disposition
        headers={
            'Content-Disposition': f'attachment; filename="{Path(normalized_filename).name}"'} if force_download else None
    )


def should_require_auth(filename: str) -> bool:
    """Determina se um arquivo requer autenticação com base em regras específicas"""
    # Exemplo: arquivos com 'public' no nome não requerem autenticação
    if 'public' in filename.lower():
        return False

    # Exemplo: certos tipos de arquivo não requerem autenticação
    if filename.lower().endswith(('.pdf', '.txt')):
        return False

    # Por padrão, outros arquivos requerem autenticação
    return True


def should_require_auth(filename: str) -> bool:
    """Determina se um arquivo requer autenticação com base em regras específicas"""
    # Exemplo: arquivos com 'public' no nome não requerem autenticação
    if 'public' in filename.lower():
        return False

    # Exemplo: certos tipos de arquivo não requerem autenticação
    if filename.lower().endswith(('.pdf', '.txt')):
        return False

    # Por padrão, outros arquivos requerem autenticação
    return True


@app.delete("/materials/{filename}")
async def delete_material(filename: str, current_user: User = Depends(get_current_user)):
    """Delete a material file"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Handle nested file paths
    file_path = Path("data/materials") / filename

    if not file_path.exists() or not file_path.is_file():
        # Try to find file recursively
        materials_dir = Path("data/materials")
        found_files = list(materials_dir.rglob(filename))

        if found_files:
            file_path = found_files[0]
        else:
            raise HTTPException(status_code=404, detail="File not found")

    try:
        file_path.unlink()
        logger.info(f"🗑️ File deleted by {current_user.username}: {filename}")
        return {"status": "success", "message": f"File deleted: {filename}"}
    except Exception as e:
        logger.error(f"❌ Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")


@app.put("/materials/{filename}/metadata")
async def update_material_metadata(
    filename: str,
    description: str = Form(""),
    tags: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    """Update material metadata"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"✏️ Metadata update by {current_user.username}: {filename}")

    # Handle nested file paths
    file_path = Path("data/materials") / filename

    if not file_path.exists() or not file_path.is_file():
        # Try to find file recursively
        materials_dir = Path("data/materials")
        found_files = list(materials_dir.rglob(filename))
        if found_files:
            file_path = found_files[0]
        else:
            raise HTTPException(status_code=404, detail="File not found")

    try:
        # Atualizar metadados no banco de dados ou em algum arquivo de metadados
        # Aqui você precisaria implementar a lógica para armazenar os metadados
        # Por exemplo, você poderia ter um arquivo JSON com os metadados de todos os materiais

        # Exemplo simplificado (você precisaria adaptar isso ao seu sistema de armazenamento de metadados):
        metadata_file = Path("data/materials_metadata.json")

        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
        else:
            metadata = {}

        # Atualizar metadados do arquivo
        if filename not in metadata:
            metadata[filename] = {}

        metadata[filename]["description"] = description

        if tags:
            try:
                tags_list = json.loads(tags)
                metadata[filename]["tags"] = tags_list
            except:
                metadata[filename]["tags"] = []

        # Salvar metadados atualizados
        with open(metadata_file, "w") as f:
            json.dump(metadata, f)

        logger.info(f"✅ Metadata updated for {filename}")
        return {"status": "success", "message": f"Metadata updated for {filename}"}
    except Exception as e:
        logger.error(f"❌ Update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")

# ========================================
# DEBUG ENDPOINTS
# ========================================


@app.get("/debug/drive")
async def debug_drive(current_user: User = Depends(get_current_user)):
    """Debug endpoint for Drive handler status"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    debug_info = {
        "drive_handler": {
            "service_initialized": drive_handler.service is not None,
            "api_key_set": drive_handler.api_key is not None,
            "materials_dir": str(drive_handler.materials_dir),
            "materials_dir_exists": drive_handler.materials_dir.exists(),
            "scopes": drive_handler.scopes,
            "processed_files_count": len(drive_handler.processed_files) if hasattr(drive_handler, 'processed_files') else 0,
            "file_hashes_count": len(drive_handler.file_hashes) if hasattr(drive_handler, 'file_hashes') else 0
        },
        "environment": {
            "google_drive_api_key": bool(os.getenv('GOOGLE_DRIVE_API_KEY')),
            "credentials_file_exists": os.path.exists('credentials.json'),
            "token_file_exists": os.path.exists('token.json')
        },
        "download_system": {
            "active_downloads": len(active_downloads),
            "download_progress_sessions": len(download_progress),
            "active_download_ids": list(active_downloads.keys()),
            "recent_downloads": list(download_progress.keys())[-5:]
        },
        "materials_directory": drive_handler.get_download_stats()
    }

    logger.info(f"🔍 Debug info requested by: {current_user.username}")
    return debug_info


@app.post("/sync-drive-simple")
async def sync_drive_simple(
    data: DriveSync,
    current_user: User = Depends(get_current_user)
):
    """Sync only files from the specified Google Drive folder (non-recursive)"""
    logger.info(f"🔄 Simple drive sync requested by: {current_user.username}")

    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Autentica com o handler simples, agora com cache de autenticação
        auth_success = simple_drive_handler.authenticate(
            api_key=data.api_key or "")
        if not auth_success:
            raise HTTPException(
                status_code=400, detail="Could not authenticate with Google Drive")

        # Baixa apenas os arquivos da pasta (não recursivo)
        processed_files = simple_drive_handler.process_folder(
            data.folder_id, download_all=data.download_files)

        stats = simple_drive_handler.get_download_stats()
        return {
            "status": "success",
            "message": f"Processed {len(processed_files)} files from Google Drive (non-recursive)",
            "files": processed_files,
            "statistics": stats,
            "folder_info": {
                "accessible": True,
                "folder_id": data.folder_id,
                "file_count": len(processed_files)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Simple drive sync error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Drive sync error: {str(e)}")

# ========================================
# STARTUP EVENT
# ========================================


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(
        "🚀 DNA da Força Backend v1.4 - Complete Recursive Drive Integration Starting...")

    # Create necessary directories
    Path("data/materials").mkdir(parents=True, exist_ok=True)
    logger.info("📁 Materials directory created/verified")

    # Log environment info
    logger.info(f"📊 Environment check:")
    logger.info(
        f"  - OpenAI API Key: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")
    logger.info(
        f"  - Google Drive API Key: {'✅' if os.getenv('GOOGLE_DRIVE_API_KEY') else '❌'}")
    logger.info(
        f"  - Credentials file: {'✅' if os.path.exists('credentials.json') else '❌'}")
    logger.info(
        f"  - Materials directory: {Path('data/materials').absolute()}")
    logger.info(
        f"  - RAG Server URL: {RAG_SERVER_URL}")
    logger.info(
        f"  - Concurrency support: ✅ (User-specific handlers with thread locks)")

    logger.info(
        "✅ Sistema pronto com funcionalidades recursivas completas e suporte a concorrência!")

# ========================================
# ASSISTANT CONFIGURATION ENDPOINTS (Proxy to RAG Server)
# ========================================


@app.get("/assistant/config")
async def get_assistant_config(current_user: User = Depends(get_current_user)):
    """Get current assistant configuration - proxy to RAG server"""
    logger.info(f"⚙️ Assistant config requested by: {current_user.username}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{RAG_SERVER_URL}/assistant/config") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_detail = await response.text()
                    logger.error(f"❌ RAG server error: {error_detail}")
                    raise HTTPException(
                        status_code=response.status, detail=f"RAG server error: {error_detail}")
    except aiohttp.ClientError as e:
        logger.error(f"❌ Connection error to RAG server: {str(e)}")
        raise HTTPException(status_code=503, detail="RAG server unavailable")
    except Exception as e:
        logger.error(f"❌ Error getting assistant config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assistant/config")
async def update_assistant_config(config: dict, current_user: User = Depends(get_current_user)):
    """Update assistant configuration - proxy to RAG server"""
    logger.info(f"⚙️ Assistant config update by: {current_user.username}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{RAG_SERVER_URL}/assistant/config", json=config) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_detail = await response.text()
                    logger.error(f"❌ RAG server error: {error_detail}")
                    raise HTTPException(
                        status_code=response.status, detail=f"RAG server error: {error_detail}")
    except aiohttp.ClientError as e:
        logger.error(f"❌ Connection error to RAG server: {str(e)}")
        raise HTTPException(status_code=503, detail="RAG server unavailable")
    except Exception as e:
        logger.error(f"❌ Error updating assistant config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assistant/templates")
async def get_assistant_templates(current_user: User = Depends(get_current_user)):
    """Get available assistant templates - proxy to RAG server"""
    logger.info(f"📋 Assistant templates requested by: {current_user.username}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{RAG_SERVER_URL}/assistant/templates") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_detail = await response.text()
                    logger.error(f"❌ RAG server error: {error_detail}")
                    raise HTTPException(
                        status_code=response.status, detail=f"RAG server error: {error_detail}")
    except aiohttp.ClientError as e:
        logger.error(f"❌ Connection error to RAG server: {str(e)}")
        raise HTTPException(status_code=503, detail="RAG server unavailable")
    except Exception as e:
        logger.error(f"❌ Error getting assistant templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assistant/config/template/{template_name}")
async def apply_assistant_template(template_name: str, current_user: User = Depends(get_current_user)):
    """Apply a specific assistant template - proxy to RAG server"""
    logger.info(
        f"📋 Applying template '{template_name}' by: {current_user.username}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{RAG_SERVER_URL}/assistant/config/template/{template_name}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_detail = await response.text()
                    logger.error(f"❌ RAG server error: {error_detail}")
                    raise HTTPException(
                        status_code=response.status, detail=f"RAG server error: {error_detail}")
    except aiohttp.ClientError as e:
        logger.error(f"❌ Connection error to RAG server: {str(e)}")
        raise HTTPException(status_code=503, detail="RAG server unavailable")
    except Exception as e:
        logger.error(f"❌ Error applying assistant template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assistant/config/reset")
async def reset_assistant_config(current_user: User = Depends(get_current_user)):
    """Reset assistant configuration to default - proxy to RAG server"""
    logger.info(f"🔄 Assistant config reset by: {current_user.username}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{RAG_SERVER_URL}/assistant/config/reset") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_detail = await response.text()
                    logger.error(f"❌ RAG server error: {error_detail}")
                    raise HTTPException(
                        status_code=response.status, detail=f"RAG server error: {error_detail}")
    except aiohttp.ClientError as e:
        logger.error(f"❌ Connection error to RAG server: {str(e)}")
        raise HTTPException(status_code=503, detail="RAG server unavailable")
    except Exception as e:
        logger.error(f"❌ Error resetting assistant config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# SYSTEM SETTINGS ENDPOINTS
# ========================================

@app.get("/settings")
async def get_system_settings(current_user: User = Depends(get_current_user)):
    """Get system settings"""
    logger.info("⚙️ System settings requested")

    # Verificar se o usuário é admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Apenas administradores podem acessar configurações do sistema")

    # Carregar configurações do sistema
    load_system_settings()

    # Se não há configurações salvas, retornar padrão
    if system_settings is None:
        default_settings = get_default_system_settings()
        logger.info("✅ Returning default system settings")
        return {
            "status": "success",
            "settings": default_settings
        }

    logger.info("✅ Returning saved system settings")
    return {
        "status": "success",
        "settings": system_settings
    }


@app.post("/settings")
async def update_system_settings(settings: SystemSettings, current_user: User = Depends(get_current_user)):
    """Update system settings"""
    logger.info("⚙️ System settings update requested")

    # Verificar se o usuário é admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Apenas administradores podem modificar configurações do sistema")

    try:
        # Atualizar configurações globais
        global system_settings
        system_settings = settings.dict()

        # Salvar configurações
        save_system_settings()

        logger.info("✅ System settings updated successfully")
        return {
            "status": "success",
            "message": "Configurações do sistema atualizadas com sucesso",
            "settings": system_settings
        }
    except Exception as e:
        logger.error(f"❌ Error updating system settings: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao atualizar configurações: {str(e)}")


@app.post("/settings/reset")
async def reset_system_settings(current_user: User = Depends(get_current_user)):
    """Reset system settings to default"""
    logger.info("🔄 System settings reset requested")

    # Verificar se o usuário é admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Apenas administradores podem resetar configurações do sistema")

    try:
        # Resetar para configurações padrão
        global system_settings
        system_settings = get_default_system_settings()

        # Salvar configurações
        save_system_settings()

        logger.info("✅ System settings reset to default")
        return {
            "status": "success",
            "message": "Configurações do sistema resetadas para padrão",
            "settings": system_settings
        }
    except Exception as e:
        logger.error(f"❌ Error resetting system settings: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao resetar configurações: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    logger.info(
        "🚀 DNA da Força Backend v1.4 - Complete Recursive Drive Integration")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
