from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Body, Request, BackgroundTasks
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
from langchain_core.runnables import RunnableConfig

# Import RAG handler
from rag_handler import RAGHandler, ProcessingConfig, AssistantConfigModel
from chat_agent import graph as chat_agent_graph
from drive_handler import DriveHandler
from drive_handler_recursive import RecursiveDriveHandler
from auth import (
    create_access_token,
    get_current_user,
    authenticate_user as auth_authenticate_user,
    User,
    Token
)
from drive_handler import DriveHandler

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
    version="1.4.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize handlers
rag_handler = None
drive_handler = RecursiveDriveHandler()
simple_drive_handler = DriveHandler()

# Global state for download tracking
download_progress = {}
active_downloads = {}

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

logger.info("🚀 DNA da Força API v1.4.0 - Complete Recursive Drive Integration")

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

# ========================================
# USER MANAGEMENT
# ========================================


USERS_FILE = "users.json"


def load_users():
    """Load users from JSON file"""
    if not os.path.exists(USERS_FILE):
        users = [
            {"username": "admin", "password": "admin123", "role": "admin"},
            {"username": "instrutor", "password": "instrutor123", "role": "instructor"},
            {"username": "aluno", "password": "aluno123", "role": "student"}
        ]
        save_users(users)
        logger.info("👥 Created default users file")
        return users

    with open(USERS_FILE, "r") as f:
        users = json.load(f)
        logger.info(f"👥 Loaded {len(users)} users from file")
        return users


def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)
    logger.info(f"💾 Saved {len(users)} users to file")

# ========================================
# UTILITY FUNCTIONS
# ========================================


def get_file_type(filename: str) -> str:
    """Get file type from filename"""
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        if mime_type.startswith('video/'):
            return 'video'
        elif mime_type == 'application/pdf':
            return 'pdf'
        elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            return 'docx'
        elif mime_type == 'text/plain':
            return 'txt'

    ext = Path(filename).suffix.lower()
    if ext in ['.mp4', '.avi', '.mov', '.webm']:
        return 'video'
    elif ext == '.pdf':
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
    return {
        "id": file_path.name,
        "title": file_path.stem.replace('_', ' ').title(),
        "description": f"Material: {file_path.name}",
        "type": get_file_type(file_path.name),
        "path": f"/api/materials/{file_path.name}",
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
# AUTHENTICATION ENDPOINTS
# ========================================


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """User login endpoint"""
    logger.info(f"🔐 Login attempt for: {form_data.username}")

    user = auth_authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"❌ Failed login attempt for: {form_data.username}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )

    logger.info(f"✅ Login successful for: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/change-password")
async def change_password(
    request: Request,
    data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    request_data = data
    if request_data is None:
        request_data = await request.json()

    if not isinstance(request_data, dict):
        raise HTTPException(status_code=400, detail="Invalid request body")

    current_password = request_data.get("current_password")
    new_password = request_data.get("new_password")

    logger.info(f"🔑 Password change request for: {current_user.username}")

    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Missing required fields")

    users = load_users()
    for user in users:
        if user["username"] == current_user.username:
            if user["password"] != current_password:
                logger.warning(
                    f"❌ Incorrect current password for: {current_user.username}")
                raise HTTPException(
                    status_code=401, detail="Current password is incorrect")

            user["password"] = new_password
            save_users(users)
            logger.info(
                f"✅ Password changed successfully for: {current_user.username}")
            return {"status": "success", "message": "Password changed successfully"}

    raise HTTPException(status_code=404, detail="User not found")

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
def health():
    """Health check endpoint"""
    materials_count = len(list(Path("data/materials").rglob("*"))
                          ) if Path("data/materials").exists() else 0

    status = {
        "status": "ok",
        "version": "1.4.0",
        "rag_initialized": rag_handler is not None,
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

    return {
        "backend": "online",
        "database": "simulated" if not rag_handler else "active",
        "ai_enabled": rag_handler is not None,
        "materials_count": len(list(materials_dir.rglob("*")) if materials_dir.exists() else []),
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
    global rag_handler, drive_handler

    logger.info(f"🚀 System initialization started by: {current_user.username}")
    logger.info(f"🔑 OpenAI API Key provided: {len(api_key) > 0}")
    logger.info(f"📁 Drive folder ID: {drive_folder_id}")
    logger.info(
        f"🔐 Drive API Key provided: {len(drive_api_key) > 0 if drive_api_key else False}")
    logger.info(f"📄 Credentials file uploaded: {credentials_json is not None}")

    try:
        messages = []

        # Initialize RAG handler
        logger.info("🤖 Initializing RAG handler...")
        rag_handler = RAGHandler(api_key)
        messages.append("✓ Initialized RAG handler")
        logger.info("✅ RAG handler initialized successfully")

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

        # Process materials and initialize RAG
        try:
            logger.info("🧠 Starting RAG processing and initialization...")
            success, rag_messages = rag_handler.process_and_initialize(
                "data/materials")
            messages.extend(rag_messages)

            if success:
                logger.info(
                    "✅ RAG processing and initialization completed successfully")
            else:
                logger.error("❌ RAG processing failed")

        except Exception as e:
            logger.error(f"❌ RAG initialization error: {str(e)}")
            messages.append(f"⚠️ RAG initialization error: {str(e)}")
            success = False

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
    """Simplified chat endpoint"""
    logger.info(f"💬 Chat request: {question.content[:50]}...")

    if not rag_handler:
        simulated_answer = f"Sistema não inicializado. Esta é uma resposta simulada para: '{question.content}'. Configure uma chave OpenAI válida para funcionalidades completas."
        return Response(
            answer=simulated_answer,
            sources=[{"title": "Sistema de Teste",
                      "source": "backend/main_simple.py", "page": 1, "relevance": 0.9}],
            response_time=0.1
        )

    try:
        response = rag_handler.generate_response(question.content)
        return response
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat-auth", response_model=Response)
async def chat_auth(question: Question, current_user: User = Depends(get_current_user)):
    """Process a chat question with authentication"""
    logger.info(
        f"💬 Chat request from {current_user.username}: {question.content[:50]}...")

    if not rag_handler:
        logger.error("❌ RAG handler not initialized")
        raise HTTPException(status_code=400, detail="System not initialized")

    try:
        response = rag_handler.generate_response(question.content)
        logger.info(
            f"✅ Chat response generated (time: {response.get('response_time', 0):.2f}s)")
        return response
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def stream_agent_response(message: str, thread_id: str):
    """Generator function to stream agent responses."""
    config = RunnableConfig(configurable={"thread_id": thread_id})
    async for event in chat_agent_graph.astream_events(
        {"messages": [("user", message)]},
        config=config,
        version="v1"
    ):
        kind = event["event"]
        if kind == "on_chat_model_stream" and "chunk" in event["data"] and event["data"]["chunk"].content:
            content = event["data"]["chunk"].content
            data = {
                "thread_id": thread_id,
                "event": "stream",
                "data": content,
            }
            yield f"data: {json.dumps(data)}\n\n"
        elif kind == "on_tool_start":
            data = {
                "thread_id": thread_id,
                "event": "tool_start",
                "data": {
                    "name": event["name"],
                    "input": event["data"].get("input"),
                },
            }
            yield f"data: {json.dumps(data)}\n\n"
        elif kind == "on_tool_end":
            data = {
                "thread_id": thread_id,
                "event": "tool_end",
                "data": {
                    "name": event["name"],
                    "output": event["data"].get("output"),
                },
            }
            yield f"data: {json.dumps(data)}\n\n"


@app.post("/chat/agent")
async def chat_agent_stream(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Endpoint to stream responses from the chat agent."""
    thread_id = request.thread_id or str(uuid4())
    logger.info(f"🤖 Agent chat request from {current_user.username} on thread {thread_id}: {request.message[:50]}...")

    if not rag_handler:
        logger.error("❌ RAG handler not initialized for agent chat")
        raise HTTPException(status_code=400, detail="System not initialized. Cannot use agent.")

    return StreamingResponse(
        stream_agent_response(request.message, thread_id),
        media_type="text/event-stream"
    )


# ========================================
# RECURSIVE DRIVE ENDPOINTS
# ========================================


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
        # Authenticate with Drive
        auth_success = drive_handler.authenticate(api_key=data.api_key or "")
        if not auth_success:
            raise HTTPException(
                status_code=400, detail="Could not authenticate with Google Drive")

        # Start background download
        download_id = f"download_{int(time.time())}"
        download_progress[download_id] = {
            "status": "starting",
            "progress": 0,
            "total_files": 0,
            "downloaded_files": 0,
            "current_file": "",
            "started_at": datetime.now().isoformat(),
            "folder_id": data.folder_id
        }

        def run_recursive_download():
            try:
                download_progress[download_id]["status"] = "analyzing"
                result = drive_handler.download_drive_recursive(data.folder_id)

                if result["status"] == "success":
                    download_progress[download_id].update({
                        "status": "completed",
                        "progress": 100,
                        "total_files": result["statistics"]["total_files"],
                        "downloaded_files": result["statistics"]["downloaded_files"],
                        "completed_at": datetime.now().isoformat(),
                        "result": result
                    })
                else:
                    download_progress[download_id].update({
                        "status": "error",
                        "error": result.get("error", "Unknown error"),
                        "completed_at": datetime.now().isoformat()
                    })
            except Exception as e:
                download_progress[download_id].update({
                    "status": "error",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                })

        background_tasks.add_task(run_recursive_download)
        active_downloads[download_id] = True

        return {
            "status": "started",
            "download_id": download_id,
            "message": "Recursive download started in background"
        }

    except Exception as e:
        logger.error(f"❌ Recursive sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/drive/analyze-folder")
async def analyze_folder(
    folder_id: str,
    api_key: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Analyze folder structure without downloading"""
    logger.info(f"🔍 Folder analysis requested: {folder_id}")

    try:
        auth_success = drive_handler.authenticate(api_key=api_key or "")
        if not auth_success:
            raise HTTPException(
                status_code=400, detail="Authentication failed")

        structure = drive_handler.get_folder_structure(folder_id)
        stats = drive_handler.download_stats

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
    if download_id:
        if download_id not in download_progress:
            raise HTTPException(status_code=404, detail="Download not found")
        return download_progress[download_id]

    return {
        "active_downloads": list(active_downloads.keys()),
        "download_progress": download_progress
    }


@app.post("/drive/cancel-download")
async def cancel_download(
    download_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel active download"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if download_id not in active_downloads:
        raise HTTPException(status_code=404, detail="Download not found")

    # Mark as cancelled
    if download_id in download_progress:
        download_progress[download_id]["status"] = "cancelled"
        download_progress[download_id]["cancelled_at"] = datetime.now(
        ).isoformat()

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
        # Reset drive handler state
        if hasattr(drive_handler, 'processed_files'):
            drive_handler.processed_files.clear()
        if hasattr(drive_handler, 'file_hashes'):
            drive_handler.file_hashes.clear()

        # Reset download progress
        global download_progress, active_downloads
        download_progress.clear()
        active_downloads.clear()

        # Clean up temporary files
        drive_handler.cleanup_temp_files()

        return {
            "status": "success",
            "message": "Drive cache and state cleared",
            "cleared_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error clearing drive cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# LEGACY DRIVE ENDPOINTS (for backward compatibility)
# ========================================


@app.post("/test-drive-folder")
async def test_drive_folder(
    data: DriveTest,
    current_user: User = Depends(get_current_user)
):
    """Test access to a Google Drive folder (legacy endpoint)"""
    logger.info(
        f"🧪 Legacy drive folder test requested by: {current_user.username}")

    try:
        auth_success = drive_handler.authenticate(api_key=data.api_key or "")
        if not auth_success:
            return {"accessible": False, "error": "Authentication failed"}

        # Use the new analyze_folder functionality
        structure = drive_handler.get_folder_structure(data.folder_id)

        if structure and 'files' in structure:
            return {
                "accessible": True,
                "folder_name": structure.get('name', 'Unknown'),
                "file_count": len(structure['files']),
                "total_folders": len(structure.get('subfolders', {})),
                "public": True,  # Assume public if accessible
                "method": "recursive_handler"
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
        global rag_handler

        if rag_handler:
            rag_handler.reset()
            logger.info("🔄 RAG handler reset")

        chromadb_dir = Path(".chromadb")
        if chromadb_dir.exists():
            shutil.rmtree(chromadb_dir)
            logger.info("🗑️ Removed ChromaDB directory")

        rag_handler = None

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
        report["rag_status"] = {
            "initialized": rag_handler is not None,
            "stats": rag_handler.get_system_stats() if rag_handler else {}
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
        if rag_handler:
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
                          '.mp4', '.avi', '.mov', '.pptx', '.webm'}
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


@app.get("/materials/{filename}")
async def download_material(filename: str, current_user: User = Depends(get_current_user)):
    """Download a material file"""
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

    logger.info(f"📥 File download by {current_user.username}: {filename}")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )


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
        # Autentica com o handler simples
        auth_success = simple_drive_handler.authenticate(api_key=data.api_key or "")
        if not auth_success:
            raise HTTPException(
                status_code=400, detail="Could not authenticate with Google Drive")

        # Baixa apenas os arquivos da pasta (não recursivo)
        processed_files = simple_drive_handler.process_folder(
            data.folder_id, download_all=True)

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
    global rag_handler
    logger.info(
        "🚀 DNA da Força Backend v1.4 - Complete Recursive Drive Integration Starting...")

    # Create necessary directories
    Path("data/materials").mkdir(parents=True, exist_ok=True)
    logger.info("📁 Materials directory created/verified")

    # Initialize RAG handler if API key is available
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        logger.info("🔑 OpenAI API key found, initializing RAG handler...")
        try:
            rag_handler = RAGHandler(api_key=openai_api_key)
            rag_handler.process_and_initialize("data/materials")
            logger.info("✅ RAG handler initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG handler: {e}")
    else:
        logger.warning("⚠️ OpenAI API key not found. RAG handler not initialized.")

    # Log environment info
    logger.info(f"📊 Environment check:")
    logger.info(
        f"  - OpenAI API Key: {'✅' if openai_api_key else '❌'}")
    logger.info(
        f"  - Google Drive API Key: {'✅' if os.getenv('GOOGLE_DRIVE_API_KEY') else '❌'}")
    logger.info(
        f"  - Credentials file: {'✅' if os.path.exists('credentials.json') else '❌'}")
    logger.info(
        f"  - Materials directory: {Path('data/materials').absolute()}")

    logger.info("✅ Sistema pronto com funcionalidades recursivas completas!")

if __name__ == "__main__":
    import uvicorn
    logger.info(
        "🚀 DNA da Força Backend v1.4 - Complete Recursive Drive Integration")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
