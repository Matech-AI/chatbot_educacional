from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import json
from datetime import datetime, timedelta
import shutil
import tempfile
import mimetypes
import logging
from dotenv import load_dotenv

from rag_handler import RAGHandler
from drive_handler import DriveHandler
from auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
    User,
    Token
)

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
    description="Sistema educacional com IA para treinamento físico - Versão Melhorada",
    version="1.3.0"
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
drive_handler = DriveHandler()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

logger.info("🚀 DNA da Força API v1.3.0 - Enhanced Drive Integration")

# ========================================
# MODELS
# ========================================


class Question(BaseModel):
    content: str


class Response(BaseModel):
    answer: str
    sources: List[dict]
    response_time: float


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


class SystemStatus(BaseModel):
    status: str
    version: str
    rag_initialized: bool
    drive_authenticated: bool
    materials_count: int
    backend_uptime: str

# ========================================
# USER MANAGEMENT
# ========================================


USERS_FILE = "users.json"


def load_users():
    """Load users from JSON file"""
    if not os.path.exists(USERS_FILE):
        # Initialize with default users
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


def authenticate_user(username: str, password: str):
    """Authenticate user credentials"""
    logger.info(f"🔐 Authenticating user: {username}")
    users = load_users()
    for user in users:
        if user["username"] == username and user["password"] == password:
            logger.info(
                f"✅ Authentication successful for: {username} (role: {user['role']})")
            return user
    logger.warning(f"❌ Authentication failed for: {username}")
    return None

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

    # Fallback to extension
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

# ========================================
# AUTHENTICATION ENDPOINTS
# ========================================


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """User login endpoint"""
    logger.info(f"🔐 Login attempt for: {form_data.username}")

    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"❌ Failed login attempt for: {form_data.username}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    logger.info(f"✅ Login successful for: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/change-password")
async def change_password(
    request: Request,
    data: dict = None,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    if data is None:
        data = await request.json()

    current_password = data.get("current_password")
    new_password = data.get("new_password")

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


@app.post("/reset-password")
async def reset_password(data: dict):
    """Reset user password (admin function)"""
    username = data.get("username")
    new_password = data.get("new_password")

    logger.info(f"🔄 Password reset request for: {username}")

    if not username or not new_password:
        raise HTTPException(status_code=400, detail="Missing required fields")

    users = load_users()
    for user in users:
        if user["username"] == username:
            user["password"] = new_password
            save_users(users)
            logger.info(f"✅ Password reset successfully for: {username}")
            return {"status": "success", "message": "Password reset successfully"}

    raise HTTPException(status_code=404, detail="User not found")

# ========================================
# SYSTEM ENDPOINTS
# ========================================


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "🚀 DNA da Força API v1.3 - Enhanced Drive Integration",
        "status": "ok",
        "version": "1.3.0",
        "features": ["auth", "chat", "upload", "materials", "drive_sync", "enhanced_logging"]
    }


@app.get("/health")
def health():
    """Health check endpoint with enhanced information"""
    materials_count = len(list(Path("data/materials").glob("*"))
                          ) if Path("data/materials").exists() else 0

    # Check drive handler status
    drive_status = {
        "authenticated": drive_handler.service is not None,
        "service_type": "API Key" if drive_handler.api_key else "OAuth2" if drive_handler.service else "None",
        "materials_directory": str(drive_handler.materials_dir),
        "materials_directory_exists": drive_handler.materials_dir.exists()
    }

    status = SystemStatus(
        status="ok",
        version="1.3.0",
        rag_initialized=rag_handler is not None,
        drive_authenticated=drive_handler.service is not None,
        materials_count=materials_count,
        backend_uptime="online"
    )

    logger.info(
        f"🏥 Health check: RAG={status.rag_initialized}, Drive={status.drive_authenticated}, Materials={materials_count}")

    return {
        **status.dict(),
        "drive_details": drive_status,
        "timestamp": datetime.now().isoformat()
    }


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
                    # Save credentials temporarily
                    logger.info("💾 Saving uploaded credentials file...")
                    creds_path = Path("credentials.json")
                    content = await credentials_json.read()
                    creds_path.write_bytes(content)
                    logger.info(f"✅ Credentials saved to: {creds_path}")

                    auth_success = drive_handler.authenticate(str(creds_path))
                else:
                    logger.info("🔑 Attempting authentication with API key...")
                    auth_success = drive_handler.authenticate(
                        api_key=drive_api_key)

                if auth_success:
                    messages.append("✓ Authenticated with Google Drive")
                    logger.info("✅ Google Drive authentication successful")

                    # Test folder access first
                    logger.info("🧪 Testing folder access...")
                    access_test = drive_handler.test_folder_access(
                        drive_folder_id)

                    if access_test['accessible']:
                        logger.info(
                            f"✅ Folder accessible: {access_test['folder_name']} ({access_test['file_count']} files)")
                        messages.append(
                            f"✓ Folder accessible: {access_test['folder_name']} ({access_test['file_count']} files)")

                        # Process folder
                        logger.info("📥 Starting file download process...")
                        downloaded_files = drive_handler.process_folder(
                            drive_folder_id)

                        if downloaded_files:
                            logger.info(
                                f"🎉 Successfully downloaded {len(downloaded_files)} files")
                            messages.append(
                                f"✓ Downloaded {len(downloaded_files)} files from Drive")

                            # Log details about downloaded files
                            # Log first 5 files
                            for file in downloaded_files[:5]:
                                logger.info(
                                    f"✅ Downloaded: {file.get('name')} ({file.get('size', 0)} bytes)")
                        else:
                            logger.warning("⚠️ No files were downloaded")
                            messages.append(
                                "⚠️ No files were downloaded from Drive")
                    else:
                        error_msg = access_test.get('error', 'Unknown error')
                        logger.error(f"❌ Cannot access folder: {error_msg}")
                        messages.append(f"❌ Cannot access folder: {error_msg}")
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
async def chat(question: Question, current_user: User = Depends(get_current_user)):
    """Process a chat question and return response"""
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

# ========================================
# GOOGLE DRIVE ENDPOINTS - ENHANCED
# ========================================


@app.post("/test-drive-folder")
async def test_drive_folder(
    data: DriveTest,
    current_user: User = Depends(get_current_user)
):
    """Test access to a Google Drive folder with detailed logging"""
    logger.info(f"🧪 Drive folder test requested by: {current_user.username}")
    logger.info(f"📁 Folder ID: {data.folder_id}")
    logger.info(
        f"🔑 API Key provided: {len(data.api_key) > 0 if data.api_key else False}")

    if not data.folder_id:
        logger.error("❌ No folder ID provided")
        raise HTTPException(status_code=400, detail="Folder ID is required")

    try:
        # Authenticate with Drive
        logger.info("🔐 Attempting Drive authentication for test...")
        auth_success = drive_handler.authenticate(api_key=data.api_key)

        if not auth_success:
            logger.error("❌ Authentication failed for folder test")
            return {"accessible": False, "error": "Authentication failed"}

        logger.info("✅ Authentication successful, testing folder access...")

        # Test folder access
        result = drive_handler.test_folder_access(data.folder_id)

        logger.info(f"🏁 Folder test completed: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ Drive folder test error: {str(e)}")
        return {"accessible": False, "error": str(e)}


@app.post("/sync-drive")
async def sync_drive(
    data: DriveSync,
    current_user: User = Depends(get_current_user)
):
    """Sync materials from Google Drive with enhanced logging"""
    logger.info(f"🔄 Drive sync requested by: {current_user.username}")
    logger.info(f"📁 Folder ID: {data.folder_id}")
    logger.info(f"📥 Download files: {data.download_files}")
    logger.info(
        f"🔑 API Key provided: {len(data.api_key) > 0 if data.api_key else False}")

    if current_user.role not in ["admin", "instructor"]:
        logger.warning(
            f"❌ Unauthorized sync attempt by: {current_user.username} (role: {current_user.role})")
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Authenticate with Drive
        logger.info("🔐 Authenticating with Google Drive...")
        auth_success = drive_handler.authenticate(api_key=data.api_key)

        if not auth_success:
            logger.error("❌ Google Drive authentication failed")
            raise HTTPException(
                status_code=400, detail="Could not authenticate with Google Drive")

        logger.info("✅ Google Drive authentication successful")

        # Test folder access first
        logger.info("🧪 Testing folder access before sync...")
        access_test = drive_handler.test_folder_access(data.folder_id)

        if not access_test['accessible']:
            error_msg = access_test.get('error', 'Unknown error')
            logger.error(f"❌ Folder not accessible: {error_msg}")
            raise HTTPException(
                status_code=400, detail=f"Cannot access folder: {error_msg}")

        logger.info(
            f"✅ Folder accessible: {access_test['folder_name']} ({access_test['file_count']} files)")

        # Process folder
        logger.info(
            f"🚀 Starting folder processing (download: {data.download_files})...")
        files = drive_handler.process_folder(
            data.folder_id, download_all=data.download_files)

        # Get final statistics
        stats = drive_handler.get_download_stats()

        logger.info(f"🎉 Drive sync completed successfully!")
        logger.info(f"📊 Files processed: {len(files)}")
        logger.info(f"📊 Total files in materials: {stats['total_files']}")

        return {
            "status": "success",
            "message": f"Processed {len(files)} files from Google Drive",
            "files": files,
            "folder_info": access_test,
            "statistics": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Drive sync error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Drive sync error: {str(e)}")


@app.get("/drive-stats")
async def get_drive_stats(current_user: User = Depends(get_current_user)):
    """Get detailed statistics about downloaded Drive materials"""
    logger.info(f"📊 Drive stats requested by: {current_user.username}")

    try:
        stats = drive_handler.get_download_stats()

        # Add additional information
        enhanced_stats = {
            **stats,
            "drive_authenticated": drive_handler.service is not None,
            "authentication_method": "API Key" if drive_handler.api_key else "OAuth2" if drive_handler.service else "None",
            "timestamp": datetime.now().isoformat()
        }

        logger.info(
            f"📊 Stats retrieved: {enhanced_stats['total_files']} files, {enhanced_stats['total_size']} bytes")
        return enhanced_stats

    except Exception as e:
        logger.error(f"❌ Error getting drive stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
            "scopes": drive_handler.scopes
        },
        "environment": {
            "google_drive_api_key": bool(os.getenv('GOOGLE_DRIVE_API_KEY')),
            "credentials_file_exists": os.path.exists('credentials.json'),
            "token_file_exists": os.path.exists('token.json')
        },
        "materials_directory": drive_handler.get_download_stats()
    }

    logger.info(f"🔍 Debug info requested by: {current_user.username}")
    return debug_info


@app.post("/debug/test-specific-folder")
async def test_specific_folder(current_user: User = Depends(get_current_user)):
    """Test the specific folder mentioned in the request"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    folder_id = "1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ"
    logger.info(f"🎯 Testing specific folder: {folder_id}")

    try:
        # Try without API key first (public access)
        logger.info("🔓 Testing public access...")
        auth_success = drive_handler.authenticate()

        if auth_success:
            result = drive_handler.test_folder_access(folder_id)
            logger.info(f"🎯 Specific folder test result: {result}")
            return {
                "folder_id": folder_id,
                "test_result": result,
                "authentication_method": "OAuth2/Public"
            }
        else:
            logger.error("❌ Could not authenticate for specific folder test")
            return {
                "folder_id": folder_id,
                "error": "Authentication failed",
                "suggestion": "Try providing an API key or check credentials.json"
            }

    except Exception as e:
        logger.error(f"❌ Specific folder test error: {str(e)}")
        return {
            "folder_id": folder_id,
            "error": str(e)
        }

# ========================================
# MATERIALS ENDPOINTS (keeping existing ones)
# ========================================


@app.get("/materials")
async def list_materials(current_user: User = Depends(get_current_user)):
    """List all available materials"""
    logger.info(f"📚 Materials list requested by: {current_user.username}")

    materials_dir = Path("data/materials")
    materials_dir.mkdir(parents=True, exist_ok=True)

    materials = []

    # Add real files
    for file_path in materials_dir.iterdir():
        if file_path.is_file():
            materials.append(format_file_info(file_path, "user"))

    # Add example materials if no real files
    if not materials:
        materials.extend([
            {
                "id": "fundamentos-v2",
                "title": "Fundamentos do Treinamento v2.0",
                "description": "Princípios científicos do treinamento de força",
                "type": "pdf",
                "size": 3200000,
                "uploadedAt": datetime.now().isoformat(),
                "uploadedBy": "sistema",
                "tags": ["fundamentos", "força"]
            },
            {
                "id": "nutricao-avancada",
                "title": "Nutrição Esportiva Avançada",
                "description": "Estratégias nutricionais para performance",
                "type": "pdf",
                "size": 2800000,
                "uploadedAt": datetime.now().isoformat(),
                "uploadedBy": "sistema",
                "tags": ["nutrição", "performance"]
            }
        ])

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

    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.txt',
                          '.mp4', '.avi', '.mov', '.pptx', '.webm'}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        logger.warning(f"❌ Invalid file type: {file_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported: {', '.join(allowed_extensions)}"
        )

    # Create materials directory
    materials_dir = Path("data/materials")
    materials_dir.mkdir(parents=True, exist_ok=True)

    # Handle filename conflicts
    file_path = materials_dir / file.filename
    counter = 1
    original_path = file_path

    while file_path.exists():
        stem = original_path.stem
        suffix = original_path.suffix
        file_path = materials_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    try:
        # Read and validate file size
        content = await file.read()
        max_size = 50 * 1024 * 1024  # 50MB

        if len(content) > max_size:
            logger.warning(f"❌ File too large: {len(content)} bytes")
            raise HTTPException(
                status_code=400, detail="File too large (max 50MB)")

        # Save file
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
    file_path = Path("data/materials") / filename

    if not file_path.exists() or not file_path.is_file():
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

    file_path = Path("data/materials") / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_path.unlink()
        logger.info(f"🗑️ File deleted by {current_user.username}: {filename}")
        return {"status": "success", "message": f"File deleted: {filename}"}
    except Exception as e:
        logger.error(f"❌ Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")

# ========================================
# STARTUP EVENT
# ========================================


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(
        "🚀 DNA da Força Backend v1.3 - Enhanced Drive Integration Starting...")

    # Create necessary directories
    Path("data/materials").mkdir(parents=True, exist_ok=True)
    logger.info("📁 Materials directory created/verified")

    # Log environment info
    logger.info(f"📊 Environment check:")
    logger.info(
        f"  - Google Drive API Key: {'✅' if os.getenv('GOOGLE_DRIVE_API_KEY') else '❌'}")
    logger.info(
        f"  - Credentials file: {'✅' if os.path.exists('credentials.json') else '❌'}")
    logger.info(
        f"  - Materials directory: {Path('data/materials').absolute()}")

    logger.info("✅ Sistema pronto para uso com logging aprimorado!")

if __name__ == "__main__":
    import uvicorn
    logger.info(
        "🚀 DNA da Força Backend v1.3 - Enhanced Drive Integration with Detailed Logging")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
