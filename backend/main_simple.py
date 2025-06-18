from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Request # Added Request
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
import asyncio
import tempfile
import mimetypes
import logging
from dotenv import load_dotenv

from rag_handler import RAGHandler
from drive_handler import DriveHandler
from auth import (
    create_access_token,
    get_current_user,
    authenticate_user as auth_authenticate_user,
    User,
    Token,
    load_users as auth_load_users,
    get_password_hash,
    USERS_FILE
)
import logging
from dotenv import load_dotenv

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("🚀 Application starting up...")
    
    # Create data directories if they don't exist
    Path("data/materials").mkdir(parents=True, exist_ok=True)
    
    # Initialize users from auth module
    auth_load_users(force_reload=True)
    
    logger.info("✅ Startup complete")
    yield
    logger.info("👋 Application shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="DNA da Força AI API",
    description="Sistema educacional com IA para treinamento físico - Versão Melhorada",
    version="1.3.0",
    lifespan=lifespan
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
    knowledge_base_ids: Optional[List[str]] = None


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
# USER MANAGEMENT (Now handled by auth.py)
# ========================================

def save_users_to_json(users_dict):
    """Saves the user dictionary back to the users.json file."""
    users_list = [
        {
            "username": u["username"],
            "password": u["password"], # Store plain text, will be hashed on load
            "role": u["role"],
            "disabled": u.get("disabled", False)
        }
        for u in users_dict.values()
    ]
    with open(USERS_FILE, "w") as f:
        json.dump(users_list, f, indent=2)
    logger.info(f"💾 Saved {len(users_list)} users to '{USERS_FILE}'")

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

    # Use the centralized authentication logic
    user = auth_authenticate_user(current_user.username, current_password)
    if not user:
        logger.warning(f"❌ Incorrect current password for: {current_user.username}")
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    # Load all users to update the specific user's password
    with open(USERS_FILE, "r") as f:
        users_list = json.load(f)

    user_found = False
    for user_record in users_list:
        if user_record["username"] == current_user.username:
            user_record["password"] = new_password
            user_found = True
            break
    
    if not user_found:
        raise HTTPException(status_code=404, detail="User not found in JSON file")

    # Save the updated list back to the file
    with open(USERS_FILE, "w") as f:
        json.dump(users_list, f, indent=2)

    # Force a reload of the user cache
    auth_load_users(force_reload=True)

    logger.info(f"✅ Password changed successfully for: {current_user.username}")
    return {"status": "success", "message": "Password changed successfully"}


@app.post("/reset-password")
async def reset_password(data: dict):
    """Reset user password (admin function)"""
    username = data.get("username")
    new_password = data.get("new_password")

    logger.info(f"🔄 Password reset request for: {username}")

    if not username or not new_password:
        raise HTTPException(status_code=400, detail="Missing required fields")

    with open(USERS_FILE, "r") as f:
        users_list = json.load(f)

    user_found = False
    for user_record in users_list:
        if user_record["username"] == username:
            user_record["password"] = new_password
            user_found = True
            break

    if not user_found:
        raise HTTPException(status_code=404, detail="User not found in JSON file")

    with open(USERS_FILE, "w") as f:
        json.dump(users_list, f, indent=2)

    # Force a reload of the user cache
    auth_load_users(force_reload=True)
    
    logger.info(f"✅ Password reset successfully for: {username}")
    return {"status": "success", "message": "Password reset successfully"}

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
        if not api_key:
            messages.append("⚠️ OpenAI API Key is missing. RAG handler not initialized.")
            logger.warning("⚠️ OpenAI API Key is missing. RAG handler not initialized.")
        else:
            try:
                rag_handler = RAGHandler(api_key=api_key)
                messages.append("✓ Initialized RAG handler")
                logger.info("✅ RAG handler initialized successfully")
            except Exception as e:
                logger.error(f"❌ RAG handler initialization failed: {str(e)}")
                messages.append(f"❌ RAG handler initialization failed: {str(e)}")

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
                docs_dir="data/materials",
                knowledge_base_id="material_de_treino"
            )
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


# Chat endpoint (simplified) - No authentication required
@app.post("/chat", response_model=Response)
async def chat(question: Question):
    """Simplified chat endpoint for testing"""
    logger.info(f"Received question: {question.content}")
    
    # Simulated response for testing
    simulated_answer = f"Esta é uma resposta simulada para: '{question.content}'. O sistema está funcionando corretamente, mas as funcionalidades de IA precisam ser configuradas com uma chave OpenAI válida."
    
    return Response(
        answer=simulated_answer,
        sources=[
            {
                "title": "Sistema de Teste",
                "source": "backend/main_simple.py",
                "page": 1,
                "relevance": 0.9
            }
        ],
        response_time=0.1
    )

# Chat endpoint with authentication (original)
@app.post("/chat-auth", response_model=Response)
async def chat_auth(question: Question, current_user: User = Depends(get_current_user)):
    """Process a chat question and return response with authentication"""
    logger.info(
        f"💬 Chat request from {current_user.username}: {question.content[:50]}...")
    logger.info(f"🔎 Knowledge bases: {question.knowledge_base_ids}")

    if not rag_handler:
        logger.error("❌ RAG handler not initialized")
        raise HTTPException(status_code=400, detail="System not initialized")

    try:
        response = rag_handler.generate_response(
            question.content,
            allowed_knowledge_base_ids=question.knowledge_base_ids
        )
        logger.info(
            f"✅ Chat response generated (time: {response.get('response_time', 0):.2f}s)")
        return response
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge-bases", response_model=List[str])
async def get_knowledge_bases(current_user: User = Depends(get_current_user)):
    """Get a list of available knowledge bases"""
    if not rag_handler:
        raise HTTPException(status_code=400, detail="System not initialized")
    
    try:
        return rag_handler.get_available_knowledge_bases()
    except Exception as e:
        logger.error(f"❌ Error getting knowledge bases: {str(e)}")
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

    try:
        # Authenticate with Drive
        if data.api_key:
            logger.info("🔑 Authenticating with provided API key...")
            auth_success = drive_handler.authenticate(api_key=data.api_key)
        else:
            logger.info("🔑 Authenticating with existing credentials...")
            auth_success = drive_handler.authenticate()

        if auth_success:
            logger.info("✅ Google Drive authentication successful")
            access_test = drive_handler.test_folder_access(data.folder_id)
            return access_test
        else:
            logger.error("❌ Google Drive authentication failed")
            raise HTTPException(
                status_code=401, detail="Google Drive authentication failed")

    except Exception as e:
        logger.error(f"❌ Drive folder test error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sync-drive")
async def sync_drive(
    data: DriveSync,
    current_user: User = Depends(get_current_user)
):
    """Sync materials from Google Drive with enhanced logging"""
    logger.info(f"🔄 Drive sync requested by: {current_user.username}")
    logger.info(f"📁 Folder ID: {data.folder_id}")
    logger.info(f"📥 Download files: {data.download_files}")

    if not rag_handler:
        raise HTTPException(status_code=400, detail="System not initialized")

    try:
        messages = []

        # Authenticate with Drive
        if data.api_key:
            logger.info("🔑 Authenticating with provided API key...")
            auth_success = drive_handler.authenticate(api_key=data.api_key)
        else:
            logger.info("🔑 Authenticating with existing credentials...")
            auth_success = drive_handler.authenticate()

        if auth_success:
            messages.append("✓ Authenticated with Google Drive")
            logger.info("✅ Google Drive authentication successful")

            # Process folder
            if data.download_files:
                logger.info("📥 Starting file download process...")
                downloaded_files = drive_handler.process_folder(data.folder_id)
                
                if downloaded_files:
                    logger.info(
                        f"🎉 Successfully downloaded {len(downloaded_files)} files")
                    messages.append(
                        f"✓ Downloaded {len(downloaded_files)} files from Drive")
                else:
                    logger.warning("⚠️ No files were downloaded")
                    messages.append("⚠️ No files were downloaded from Drive")
            else:
                logger.info("ℹ️ Skipping file download as requested")
                messages.append("✓ Skipping file download")

            # Process materials and initialize RAG
            logger.info("🧠 Starting RAG processing and initialization...")
            success, rag_messages = rag_handler.process_and_initialize(
                "data/materials", "material_de_treino")
            messages.extend(rag_messages)

            if success:
                logger.info(
                    "✅ RAG processing and initialization completed successfully")
            else:
                logger.error("❌ RAG processing failed")

            return {"status": "success", "messages": messages}
        else:
            logger.error("❌ Google Drive authentication failed")
            raise HTTPException(
                status_code=401, detail="Google Drive authentication failed")

    except Exception as e:
        logger.error(f"❌ Drive sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/drive-stats")
async def get_drive_stats(current_user: User = Depends(get_current_user)):
    """Get detailed statistics about downloaded Drive materials"""
    logger.info(f"📊 Drive stats requested by: {current_user.username}")

    try:
        stats = drive_handler.get_folder_stats()
        return stats
    except Exception as e:
        logger.error(f"❌ Error getting Drive stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# DEBUG ENDPOINTS
# ========================================


@app.get("/debug/drive")
async def debug_drive(current_user: User = Depends(get_current_user)):
    """Get debug information about the Drive handler"""
    if not drive_handler:
        return {"status": "Drive handler not initialized"}

    return {
        "service_initialized": drive_handler.service is not None,
        "credentials_path": str(drive_handler.credentials_path),
        "credentials_exist": drive_handler.credentials_path.exists(),
        "materials_directory": str(drive_handler.materials_dir),
        "materials_directory_exists": drive_handler.materials_dir.exists(),
    }


@app.post("/debug/test-specific-folder")
async def test_specific_folder(current_user: User = Depends(get_current_user)):
    """Test the specific folder mentioned in the request"""
    folder_id = "12345"  # Replace with a valid folder ID for testing
    logger.info(f"🧪 Testing specific folder: {folder_id}")

    try:
        # This assumes drive_handler is already authenticated
        if not drive_handler.service:
            raise HTTPException(
                status_code=400, detail="Drive handler not authenticated")

        access_test = drive_handler.test_folder_access(folder_id)
        return access_test
    except Exception as e:
        logger.error(f"❌ Specific folder test error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# MATERIAL MANAGEMENT ENDPOINTS
# ========================================


@app.get("/materials")
async def list_materials(current_user: User = Depends(get_current_user)):
    """List all available materials"""
    materials_dir = Path("data/materials")
    if not materials_dir.exists():
        return []

    materials = [
        format_file_info(f)
        for f in materials_dir.iterdir()
        if f.is_file()
    ]
    
    # Sort by upload date, newest first
    materials.sort(key=lambda x: x['uploadedAt'], reverse=True)
    
    logger.info(f"📚 Listed {len(materials)} materials for {current_user.username}")
    return materials


@app.post("/materials/upload")
async def upload_material(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Receive tags as a JSON string
    current_user: User = Depends(get_current_user)
):
    """Upload a new material"""
    materials_dir = Path("data/materials")
    materials_dir.mkdir(exist_ok=True)

    # Sanitize filename
    filename = Path(file.filename).name
    file_path = materials_dir / filename

    logger.info(
        f"📥 Uploading material: {filename} by {current_user.username}")

    try:
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Process tags
        tag_list = []
        if tags:
            try:
                tag_list = json.loads(tags)
                if not isinstance(tag_list, list):
                    tag_list = []
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Invalid JSON for tags: {tags}")
                tag_list = []
        
        # Create metadata file
        metadata = {
            "title": Path(filename).stem.replace('_', ' ').title(),
            "description": description or "",
            "tags": tag_list,
            "original_filename": file.filename,
            "uploaded_by": current_user.username,
            "uploaded_at": datetime.now().isoformat()
        }
        
        meta_path = materials_dir / f"{filename}.meta.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"✅ Material uploaded successfully: {filename}")
        
        # Return formatted file info
        return format_file_info(file_path, current_user.username)

    except Exception as e:
        logger.error(f"❌ Error uploading material: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/materials/{filename}")
async def download_material(filename: str, current_user: User = Depends(get_current_user)):
    """Download a material file"""
    file_path = Path("data/materials") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    logger.info(
        f"🔽 Downloading material: {filename} for {current_user.username}")
    return FileResponse(file_path)


@app.post("/materials/embed")
async def embed_material(
    data: dict,
    current_user: User = Depends(get_current_user)
):
    """Embed a single material into a knowledge base"""
    filename = data.get("filename")
    knowledge_base_id = data.get("knowledge_base_id")

    if not filename or not knowledge_base_id:
        raise HTTPException(status_code=400, detail="Missing filename or knowledge_base_id")

    if not rag_handler:
        raise HTTPException(status_code=400, detail="System not initialized")

    file_path = Path("data/materials") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        success, messages = rag_handler.process_single_file(str(file_path), knowledge_base_id)
        if not success:
            raise HTTPException(status_code=500, detail=messages[0])
        return {"status": "success", "messages": messages}
    except Exception as e:
        logger.error(f"❌ Error embedding material: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/materials/{filename}")
async def delete_material(filename: str, current_user: User = Depends(get_current_user)):
    """Delete a material file"""
    logger.info(
        f"🗑️ Deleting material: {filename} by {current_user.username}")
    
    file_path = Path("data/materials") / filename
    meta_path = Path("data/materials") / f"{filename}.meta.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_path.unlink()
        if meta_path.exists():
            meta_path.unlink()
            
        logger.info(f"✅ Material deleted successfully: {filename}")
        return {"status": "success", "message": "Material deleted"}
    except Exception as e:
        logger.error(f"❌ Error deleting material: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/documents")
async def get_documents(
    knowledge_base_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List documents in the vector store."""
    if not rag_handler:
        raise HTTPException(status_code=400, detail="System not initialized")
    
    documents = rag_handler.list_documents(knowledge_base_id=knowledge_base_id)
    return documents

@app.delete("/documents")
async def remove_documents(
    knowledge_base_id: Optional[str] = None,
    filename: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Delete documents from the vector store."""
    if not rag_handler:
        raise HTTPException(status_code=400, detail="System not initialized")
    
    if not knowledge_base_id and not filename:
        raise HTTPException(status_code=400, detail="Either knowledge_base_id or filename must be provided")

    result = rag_handler.delete_documents(knowledge_base_id=knowledge_base_id, filename=filename)
    return result


@app.get("/materials-zip")
async def download_all_materials():
    """Download all materials as a ZIP file"""
    logger.info("📦 Creating ZIP of all materials...")
    
    materials_dir = Path("data/materials")
    zip_path = Path("data/materials.zip")

    if zip_path.exists():
        zip_path.unlink()

    try:
        shutil.make_archive(
            base_name=str(zip_path).replace('.zip', ''),
            format='zip',
            root_dir=materials_dir
        )
        
        logger.info("✅ ZIP file created successfully")
        return FileResponse(zip_path, filename="materials.zip")
    except Exception as e:
        logger.error(f"❌ Error creating ZIP file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# GENERAL STATUS
# ========================================


@app.get("/status")
async def get_status():
    """Get system status"""
    return {
        "status": "ok",
        "version": "1.3.0",
        "rag_initialized": rag_handler is not None,
        "drive_authenticated": drive_handler.service is not None,
        "timestamp": datetime.now().isoformat()
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_simple:app", host="0.0.0.0", port=8000, reload=True)