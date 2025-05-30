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

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="DNA da Força AI API",
    description="Sistema educacional com IA para treinamento físico",
    version="1.2.0"
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
        return users

    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def authenticate_user(username: str, password: str):
    """Authenticate user credentials"""
    users = load_users()
    for user in users:
        if user["username"] == username and user["password"] == password:
            return user
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
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
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

    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Missing required fields")

    users = load_users()
    for user in users:
        if user["username"] == current_user.username:
            if user["password"] != current_password:
                raise HTTPException(
                    status_code=401, detail="Current password is incorrect")

            user["password"] = new_password
            save_users(users)
            return {"status": "success", "message": "Password changed successfully"}

    raise HTTPException(status_code=404, detail="User not found")


@app.post("/reset-password")
async def reset_password(data: dict):
    """Reset user password (admin function)"""
    username = data.get("username")
    new_password = data.get("new_password")

    if not username or not new_password:
        raise HTTPException(status_code=400, detail="Missing required fields")

    users = load_users()
    for user in users:
        if user["username"] == username:
            user["password"] = new_password
            save_users(users)
            return {"status": "success", "message": "Password reset successfully"}

    raise HTTPException(status_code=404, detail="User not found")

# ========================================
# SYSTEM ENDPOINTS
# ========================================


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "🚀 DNA da Força API v1.2",
        "status": "ok",
        "version": "1.2.0",
        "features": ["auth", "chat", "upload", "materials", "drive_sync"]
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    materials_count = len(list(Path("data/materials").glob("*"))
                          ) if Path("data/materials").exists() else 0

    return SystemStatus(
        status="ok",
        version="1.2.0",
        rag_initialized=rag_handler is not None,
        drive_authenticated=drive_handler.service is not None,
        materials_count=materials_count,
        backend_uptime="online"
    )


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

    try:
        messages = []

        # Initialize RAG handler
        rag_handler = RAGHandler(api_key)
        messages.append("✓ Initialized RAG handler")

        # Process Drive materials if provided
        if drive_folder_id:
            try:
                # Authenticate with Drive
                if credentials_json:
                    # Save credentials temporarily
                    creds_path = Path("credentials.json")
                    content = await credentials_json.read()
                    creds_path.write_bytes(content)

                    auth_success = drive_handler.authenticate(str(creds_path))
                else:
                    auth_success = drive_handler.authenticate(
                        api_key=drive_api_key)

                if auth_success:
                    messages.append("✓ Authenticated with Google Drive")

                    # Process folder
                    downloaded_files = drive_handler.process_folder(
                        drive_folder_id)
                    messages.append(
                        f"✓ Downloaded {len(downloaded_files)} files from Drive")
                else:
                    messages.append(
                        "⚠️ Could not authenticate with Google Drive")

                # Cleanup temporary files
                drive_handler.cleanup_temp_files()

            except Exception as e:
                messages.append(f"⚠️ Drive sync error: {str(e)}")

        # Process materials and initialize RAG
        try:
            success, rag_messages = rag_handler.process_and_initialize(
                "data/materials")
            messages.extend(rag_messages)
        except Exception as e:
            messages.append(f"⚠️ RAG initialization error: {str(e)}")
            success = False

        return {"status": "success", "messages": messages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# CHAT ENDPOINTS
# ========================================


@app.post("/chat", response_model=Response)
async def chat(question: Question, current_user: User = Depends(get_current_user)):
    """Process a chat question and return response"""
    if not rag_handler:
        raise HTTPException(status_code=400, detail="System not initialized")

    try:
        response = rag_handler.generate_response(question.content)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# MATERIALS ENDPOINTS
# ========================================


@app.get("/materials")
async def list_materials(current_user: User = Depends(get_current_user)):
    """List all available materials"""
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

    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.txt',
                          '.mp4', '.avi', '.mov', '.pptx', '.webm'}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
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
            raise HTTPException(
                status_code=400, detail="File too large (max 50MB)")

        # Save file
        with file_path.open("wb") as f:
            f.write(content)

        return {
            "status": "success",
            "message": "Upload successful",
            "filename": file_path.name,
            "size": len(content),
            "uploaded_by": current_user.username
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@app.get("/materials/{filename}")
async def download_material(filename: str, current_user: User = Depends(get_current_user)):
    """Download a material file"""
    file_path = Path("data/materials") / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

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
        return {"status": "success", "message": f"File deleted: {filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")


@app.get("/materials-zip")
async def download_all_materials(current_user: User = Depends(get_current_user)):
    """Download all materials as a ZIP file"""
    materials_dir = Path("data/materials")

    if not materials_dir.exists() or not any(materials_dir.iterdir()):
        raise HTTPException(status_code=404, detail="No materials found")

    # Create temporary ZIP file
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    zip_path = temp_zip.name
    temp_zip.close()

    try:
        shutil.make_archive(zip_path.replace('.zip', ''),
                            'zip', str(materials_dir))

        return FileResponse(
            path=zip_path,
            filename="materiais_dna_forca.zip",
            media_type="application/zip"
        )
    except Exception as e:
        # Cleanup on error
        if os.path.exists(zip_path):
            os.unlink(zip_path)
        raise HTTPException(
            status_code=500, detail=f"ZIP creation error: {str(e)}")

# ========================================
# GOOGLE DRIVE ENDPOINTS
# ========================================


@app.post("/sync-drive")
async def sync_drive(
    data: DriveSync,
    current_user: User = Depends(get_current_user)
):
    """Sync materials from Google Drive"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        # Authenticate with Drive
        auth_success = drive_handler.authenticate(api_key=data.api_key)
        if not auth_success:
            raise HTTPException(
                status_code=400, detail="Could not authenticate with Google Drive")

        # Test folder access first
        access_test = drive_handler.test_folder_access(data.folder_id)
        if not access_test['accessible']:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot access folder: {access_test.get('error', 'Unknown error')}"
            )

        # Process folder
        if data.download_files:
            files = drive_handler.process_folder(
                data.folder_id, download_all=True)
        else:
            files = drive_handler.process_folder(
                data.folder_id, download_all=False)

        return {
            "status": "success",
            "message": f"Processed {len(files)} files from Google Drive",
            "files": files,
            "folder_info": access_test
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Drive sync error: {str(e)}")


@app.post("/test-drive-folder")
async def test_drive_folder(
    data: dict,
    current_user: User = Depends(get_current_user)
):
    """Test access to a Google Drive folder"""
    folder_id = data.get("folder_id")
    api_key = data.get("api_key")

    if not folder_id:
        raise HTTPException(status_code=400, detail="Folder ID is required")

    try:
        # Authenticate with Drive
        auth_success = drive_handler.authenticate(api_key=api_key)
        if not auth_success:
            return {"accessible": False, "error": "Authentication failed"}

        # Test folder access
        result = drive_handler.test_folder_access(folder_id)
        return result

    except Exception as e:
        return {"accessible": False, "error": str(e)}


@app.get("/drive-stats")
async def get_drive_stats(current_user: User = Depends(get_current_user)):
    """Get statistics about downloaded Drive materials"""
    stats = drive_handler.get_download_stats()
    return stats

# ========================================
# STARTUP EVENT
# ========================================


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print("🚀 DNA da Força Backend v1.2 - Iniciando...")

    # Create necessary directories
    Path("data/materials").mkdir(parents=True, exist_ok=True)

    print("✅ Diretórios criados")
    print("✅ Sistema pronto para uso!")

if __name__ == "__main__":
    import uvicorn
    print("🚀 DNA da Força Backend v1.2 - Com Google Drive e Upload Completo")
    uvicorn.run(app, host="0.0.0.0", port=8000)
