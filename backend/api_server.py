#!/usr/bin/env python3
"""
Servidor API Geral - DNA da Força AI
Este servidor gerencia autenticação, chatbot, sincronização do Drive e outras funcionalidades.
Comunica-se com o servidor RAG para consultas.
"""

import os
import logging
import asyncio
import aiohttp
import sys
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from dotenv import load_dotenv

# Importar componentes
from auth.auth import get_current_user, User, router as auth_router
from auth.auth import get_optional_current_user
from auth.user_management import router as user_management_router
from chat_agents.educational_agent import router as educational_agent_router
from drive_sync.drive_handler import DriveHandler
from drive_sync.drive_handler_recursive import RecursiveDriveHandler
from video_processing.video_handler import get_video_handler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
RAG_SERVER_URL = os.getenv("RAG_SERVER_URL", "http://localhost:8001")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Inicializar FastAPI
app = FastAPI(
    title="DNA da Força API Geral",
    description="API para autenticação, chatbot, Drive sync e outras funcionalidades",
    version="1.0.0"
)

# Configurar CORS
cors_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(user_management_router)
app.include_router(auth_router)
app.include_router(educational_agent_router)

# Inicializar handlers
drive_handler = RecursiveDriveHandler()
simple_drive_handler = DriveHandler()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Modelos Pydantic


class Question(BaseModel):
    content: str


class Response(BaseModel):
    answer: str
    sources: List[dict]
    response_time: float


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class DriveSync(BaseModel):
    folder_id: str
    api_key: Optional[str] = None
    download_files: bool = True
    root_folder_id: Optional[str] = None
    max_depth: Optional[int] = None


class RecursiveSync(BaseModel):
    folder_id: str
    api_key: Optional[str] = None
    credentials_json: Optional[str] = None


class DriveTest(BaseModel):
    folder_id: str
    api_key: Optional[str] = None


class SystemStatus(BaseModel):
    status: str
    version: str
    rag_server_status: str
    drive_authenticated: bool
    materials_count: int
    backend_uptime: str


class ResetComponent(BaseModel):
    component: str
    confirm: bool = False


# Funções auxiliares para manutenção
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


def get_file_type(filename: str) -> str:
    """Determine file type based on extension"""
    ext = Path(filename).suffix.lower()
    if ext in ['.pdf']:
        return 'pdf'
    elif ext in ['.docx', '.doc']:
        return 'docx'
    elif ext in ['.txt', '.md']:
        return 'txt'
    elif ext in ['.mp4', '.avi', '.mov', '.webm']:
        return 'video'
    else:
        return 'txt'  # Default to txt for unknown types


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


# Variáveis globais
startup_time = None
download_progress = {}
active_downloads = {}
download_progress_lock = asyncio.Lock()


@app.on_event("startup")
async def startup_event():
    """Inicializar o servidor API"""
    global startup_time
    startup_time = asyncio.get_event_loop().time()

    logger.info("🚀 Iniciando servidor API Geral...")
    logger.info(f"🔗 Servidor RAG: {RAG_SERVER_URL}")

    # Verificar conexão com servidor RAG
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{RAG_SERVER_URL}/health") as response:
                if response.status == 200:
                    logger.info("✅ Conexão com servidor RAG estabelecida")
                else:
                    logger.warning(
                        "⚠️ Servidor RAG não está respondendo corretamente")
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível conectar ao servidor RAG: {e}")


@app.get("/")
def root():
    """Endpoint raiz"""
    return {
        "message": "DNA da Força AI - API Geral",
        "version": "1.0.0",
        "services": {
            "authentication": "/auth",
            "chatbot": "/chat",
            "drive_sync": "/drive",
            "materials": "/materials",
            "maintenance": "/maintenance"
        },
        "rag_server": RAG_SERVER_URL
    }


@app.get("/health")
def health():
    """Verificar saúde do servidor"""
    return {
        "status": "healthy",
        "service": "api-server",
        "version": "1.0.0",
        "rag_server_url": RAG_SERVER_URL
    }


@app.get("/status")
async def get_status():
    """Obter status detalhado do sistema"""
    global startup_time

    # Verificar status do servidor RAG
    rag_status = "unknown"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{RAG_SERVER_URL}/status") as response:
                if response.status == 200:
                    rag_data = await response.json()
                    rag_status = "healthy" if rag_data.get(
                        "rag_initialized") else "not_initialized"
                else:
                    rag_status = "unavailable"
    except Exception:
        rag_status = "unavailable"

    # Calcular uptime
    uptime = "unknown"
    if startup_time:
        uptime_seconds = asyncio.get_event_loop().time() - startup_time
        uptime = f"{int(uptime_seconds)}s"

    return SystemStatus(
        status="running",
        version="1.0.0",
        rag_server_status=rag_status,
        drive_authenticated=False,  # Implementar verificação se necessário
        materials_count=0,  # Implementar contagem se necessário
        backend_uptime=uptime
    )

# Endpoints de Chat que se comunicam com o servidor RAG


@app.post("/chat", response_model=Response)
async def chat(question: Question):
    """Chat básico usando servidor RAG"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{RAG_SERVER_URL}/query",
                json={
                    "question": question.content,
                    "material_ids": None,
                    "config": None
                }
            ) as response:
                if response.status == 200:
                    rag_response = await response.json()
                    return Response(
                        answer=rag_response.get("answer", ""),
                        sources=rag_response.get("sources", []),
                        response_time=rag_response.get("response_time", 0.0)
                    )
                else:
                    raise HTTPException(
                        status_code=503, detail="Servidor RAG indisponível")
    except Exception as e:
        logger.error(f"Erro na comunicação com servidor RAG: {e}")
        raise HTTPException(
            status_code=503, detail="Erro na comunicação com servidor RAG")


@app.post("/chat-auth", response_model=Response)
async def chat_auth(question: Question, current_user: User = Depends(get_current_user)):
    """Chat autenticado usando servidor RAG"""
    return await chat(question)

# Endpoints de Drive Sync (mantidos do original)


@app.post("/drive/sync-recursive")
async def sync_drive_recursive(
    data: RecursiveSync,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Sincronizar Drive recursivamente"""
    try:
        # Implementar lógica de sincronização
        # Esta é uma versão simplificada
        return {
            "success": True,
            "message": "Sincronização iniciada",
            "folder_id": data.folder_id
        }
    except Exception as e:
        logger.error(f"Erro na sincronização: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/drive/analyze-folder")
async def analyze_folder(
    folder_id: str,
    api_key: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Analisar pasta do Drive"""
    try:
        # Implementar análise de pasta
        return {
            "folder_id": folder_id,
            "files_count": 0,
            "total_size": 0
        }
    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Materiais


@app.get("/materials")
async def list_materials(current_user: User = Depends(get_current_user)):
    """Listar materiais"""
    try:
        logger.info(f"📚 Materials list requested by: {current_user.username}")

        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            logger.info(
                "📚 Materials directory does not exist, returning empty array")
            return []

        materials = []
        for file_path in materials_dir.iterdir():
            if file_path.is_file():
                material_info = {
                    "id": file_path.name,  # Usar nome como ID
                    "title": file_path.name,
                    "description": "",
                    "type": get_file_type(file_path.name),
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "uploadedAt": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "uploadedBy": "system",
                    "tags": []
                }
                materials.append(material_info)
                logger.debug(f"📚 Added material: {file_path.name}")

        logger.info(f"📚 Returning {len(materials)} materials as array")
        return materials
    except Exception as e:
        logger.error(f"Erro ao listar materiais: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/materials/upload")
async def upload_material(
    file: UploadFile = File(...),
    description: str = Form(""),
    tags: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    """Upload de material"""
    try:
        materials_dir = Path("data/materials")
        materials_dir.mkdir(parents=True, exist_ok=True)

        file_path = materials_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return {
            "success": True,
            "filename": file.filename,
            "size": len(content)
        }
    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de inicialização do RAG


@app.post("/initialize-rag")
async def initialize_rag_system(
    api_key: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Inicializar sistema RAG"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{RAG_SERVER_URL}/initialize",
                json={"api_key": api_key}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    raise HTTPException(
                        status_code=503, detail="Erro na inicialização do RAG")
    except Exception as e:
        logger.error(f"Erro na inicialização do RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test-drive-folder")
async def test_drive_folder(
    data: DriveTest,
    current_user: User = Depends(get_current_user)
):
    """Test access to a Google Drive folder (non-recursive)"""
    logger.info(f"🧪 Drive folder test requested by: {current_user.username}")

    try:
        # Usar o simple_drive_handler para teste não-recursivo
        auth_success = simple_drive_handler.authenticate(
            api_key=data.api_key or "")
        if not auth_success:
            return {"accessible": False, "error": "Authentication failed"}

        # Usar o método list_folder_contents_with_pagination
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
        logger.error(f"❌ Drive folder test error: {str(e)}")
        return {"accessible": False, "error": str(e)}


@app.post("/sync-drive-simple")
async def sync_drive_simple(
    data: DriveSync,
    current_user: User = Depends(get_current_user)
):
    """Sync only files from the specified Google Drive folder (non-recursive)"""
    logger.info(f"🔄 Simple drive sync requested by: {current_user.username}")

    try:
        # Autentica com o handler simples
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


@app.post("/process-materials")
async def process_materials(
    api_key: str = Form(...),
    force_reprocess: bool = Form(False),
    current_user: User = Depends(get_current_user)
):
    """Processar materiais no servidor RAG"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{RAG_SERVER_URL}/process-materials",
                json={
                    "api_key": api_key,
                    "force_reprocess": force_reprocess
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    raise HTTPException(
                        status_code=503, detail="Erro no processamento")
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# DRIVE ENDPOINTS
# ========================================


@app.get("/drive/download-progress")
async def get_download_progress(
    download_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get download progress for recursive sync"""
    logger.info(f"📊 Download progress requested by: {current_user.username}")

    try:
        # This would need to be implemented with actual progress tracking
        # For now, return a basic structure
        return {
            "status": "completed",
            "progress": 100,
            "message": "No active downloads",
            "download_id": download_id
        }
    except Exception as e:
        logger.error(f"❌ Error getting download progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/drive/cancel-download")
async def cancel_download(
    download_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel an active download"""
    logger.info(
        f"❌ Download cancellation requested by: {current_user.username}")

    try:
        # This would need to be implemented with actual cancellation logic
        return {
            "status": "success",
            "message": f"Download {download_id} cancelled successfully"
        }
    except Exception as e:
        logger.error(f"❌ Error cancelling download: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/drive/folder-stats")
async def get_folder_stats(current_user: User = Depends(get_current_user)):
    """Get folder statistics"""
    logger.info(f"📊 Folder stats requested by: {current_user.username}")

    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {
                "total_folders": 0,
                "total_files": 0,
                "total_size": 0
            }

        folders = [f for f in materials_dir.rglob("*") if f.is_dir()]
        files = [f for f in materials_dir.rglob("*") if f.is_file()]
        total_size = sum(f.stat().st_size for f in files)

        return {
            "total_folders": len(folders),
            "total_files": len(files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    except Exception as e:
        logger.error(f"❌ Error getting folder stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/drive/test-connection")
async def test_drive_connection(
    api_key: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Test Google Drive connection"""
    logger.info(f"🧪 Drive connection test by: {current_user.username}")

    try:
        # Test authentication
        auth_success = drive_handler.authenticate(api_key=api_key or "")

        if auth_success:
            return {
                "status": "success",
                "message": "Google Drive connection successful",
                "authenticated": True
            }
        else:
            return {
                "status": "error",
                "message": "Failed to authenticate with Google Drive",
                "authenticated": False
            }
    except Exception as e:
        logger.error(f"❌ Error testing drive connection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/drive/clear-cache")
async def clear_drive_cache(current_user: User = Depends(get_current_user)):
    """Clear Drive cache"""
    logger.info(f"🧹 Drive cache clear requested by: {current_user.username}")

    try:
        # Clear any cached data
        if hasattr(drive_handler, 'processed_files'):
            drive_handler.processed_files.clear()
        if hasattr(drive_handler, 'file_hashes'):
            drive_handler.file_hashes.clear()

        return {
            "status": "success",
            "message": "Drive cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"❌ Error clearing drive cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recursive-drive-analysis")
async def recursive_drive_analysis(
    data: DriveSync,
    current_user: User = Depends(get_current_user)
):
    """Analyze Google Drive folder recursively"""
    logger.info(
        f"📊 Recursive drive analysis requested by: {current_user.username}")

    try:
        # Authenticate
        auth_success = drive_handler.authenticate(api_key=data.api_key or "")
        if not auth_success:
            raise HTTPException(
                status_code=400, detail="Could not authenticate with Google Drive")

        # Analyze folder structure
        analysis = drive_handler.analyze_folder_recursive(data.folder_id)

        return {
            "status": "success",
            "message": "Recursive analysis completed",
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"❌ Error in recursive drive analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recursive-drive-sync")
async def recursive_drive_sync(
    data: DriveSync,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Sync Google Drive folder recursively"""
    logger.info(
        f"🔄 Recursive drive sync requested by: {current_user.username}")

    try:
        # Authenticate
        auth_success = drive_handler.authenticate(api_key=data.api_key or "")
        if not auth_success:
            raise HTTPException(
                status_code=400, detail="Could not authenticate with Google Drive")

        # Start background sync
        background_tasks.add_task(
            drive_handler.sync_folder_recursive, data.folder_id)

        return {
            "status": "success",
            "message": "Recursive sync started in background",
            "folder_id": data.folder_id
        }
    except Exception as e:
        logger.error(f"❌ Error in recursive drive sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/drive-stats")
async def get_drive_stats(current_user: User = Depends(get_current_user)):
    """Get basic Drive statistics"""
    logger.info(f"📊 Drive stats requested by: {current_user.username}")

    try:
        stats = drive_handler.get_download_stats()
        return {
            **stats,
            "authenticated": drive_handler.service is not None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting drive stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/materials/{filename}")
async def delete_material(filename: str, current_user: User = Depends(get_current_user)):
    """Delete a material file"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"🗑️ Material deletion requested by: {current_user.username}")

    try:
        materials_dir = Path("data/materials")
        file_path = materials_dir / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        file_path.unlink()
        logger.info(f"✅ Material deleted: {filename}")

        return {
            "status": "success",
            "message": f"Material {filename} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting material: {str(e)}")
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

# ========================================
# MAINTENANCE ENDPOINTS
# ========================================


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
                "version": "1.0.0",
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

        # RAG status - verificar se o servidor RAG está rodando
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{RAG_SERVER_URL}/health") as response:
                    rag_healthy = response.status == 200
        except:
            rag_healthy = False

        report["rag_status"] = {
            "initialized": rag_healthy,
            "server_url": RAG_SERVER_URL,
            "status": "healthy" if rag_healthy else "unavailable"
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
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"🏥 Health check requested by: {current_user.username}")

    try:
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {},
            "issues": []
        }

        # Check materials directory
        materials_dir = Path("data/materials")
        if materials_dir.exists():
            health_status["components"]["materials_directory"] = {
                "status": "healthy",
                "exists": True,
                "file_count": len(list(materials_dir.rglob("*")))
            }
        else:
            health_status["components"]["materials_directory"] = {
                "status": "warning",
                "exists": False,
                "message": "Materials directory does not exist"
            }
            health_status["issues"].append("Materials directory missing")

        # Check ChromaDB
        chromadb_dir = Path(".chromadb")
        if chromadb_dir.exists():
            health_status["components"]["chromadb"] = {
                "status": "healthy",
                "exists": True
            }
        else:
            health_status["components"]["chromadb"] = {
                "status": "warning",
                "exists": False,
                "message": "ChromaDB directory does not exist"
            }
            health_status["issues"].append("ChromaDB directory missing")

        # Check RAG server
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{RAG_SERVER_URL}/health") as response:
                    if response.status == 200:
                        health_status["components"]["rag_server"] = {
                            "status": "healthy",
                            "url": RAG_SERVER_URL
                        }
                    else:
                        health_status["components"]["rag_server"] = {
                            "status": "unhealthy",
                            "url": RAG_SERVER_URL,
                            "status_code": response.status
                        }
                        health_status["issues"].append("RAG server unhealthy")
        except Exception as e:
            health_status["components"]["rag_server"] = {
                "status": "unavailable",
                "url": RAG_SERVER_URL,
                "error": str(e)
            }
            health_status["issues"].append("RAG server unavailable")

        # Check drive handler
        if drive_handler:
            health_status["components"]["drive_handler"] = {
                "status": "healthy",
                "initialized": True
            }
        else:
            health_status["components"]["drive_handler"] = {
                "status": "warning",
                "initialized": False
            }
            health_status["issues"].append("Drive handler not initialized")

        # Update overall status
        if health_status["issues"]:
            health_status["overall_status"] = "unhealthy"

        return health_status

    except Exception as e:
        logger.error(f"❌ Error in health check: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Health check error: {str(e)}")


@app.post("/maintenance/cleanup-duplicates")
async def cleanup_duplicate_files(current_user: User = Depends(get_current_user)):
    """Clean up duplicate files"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"🧹 Duplicate cleanup requested by: {current_user.username}")

    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            raise HTTPException(
                status_code=404, detail="Materials directory not found")

        duplicate_analysis = analyze_duplicates(materials_dir)

        if duplicate_analysis.get("duplicate_groups", 0) == 0:
            return {
                "status": "success",
                "message": "No duplicates found",
                "removed_files": 0,
                "saved_space": 0
            }

        # Remove duplicates (keep the first file in each group)
        removed_files = 0
        saved_space = 0

        file_hashes = defaultdict(list)
        for file_path in materials_dir.rglob("*"):
            if file_path.is_file():
                try:
                    file_hash = calculate_file_hash(file_path)
                    file_hashes[file_hash].append(file_path)
                except Exception:
                    continue

        for file_hash, file_list in file_hashes.items():
            if len(file_list) > 1:
                # Keep the first file, remove the rest
                for duplicate_file in file_list[1:]:
                    try:
                        file_size = duplicate_file.stat().st_size
                        duplicate_file.unlink()
                        removed_files += 1
                        saved_space += file_size
                        logger.info(f"Removed duplicate: {duplicate_file}")
                    except Exception as e:
                        logger.error(
                            f"Error removing duplicate {duplicate_file}: {e}")

        return {
            "status": "success",
            "message": f"Removed {removed_files} duplicate files",
            "removed_files": removed_files,
            "saved_space_bytes": saved_space,
            "saved_space_mb": round(saved_space / (1024 * 1024), 2)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in duplicate cleanup: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Cleanup error: {str(e)}")


@app.post("/maintenance/reset-materials")
async def reset_materials_directory(current_user: User = Depends(get_current_user)):
    """Reset materials directory"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"🔄 Materials reset requested by: {current_user.username}")

    try:
        materials_dir = Path("data/materials")
        if materials_dir.exists():
            shutil.rmtree(materials_dir)
            logger.info("Materials directory removed")

        materials_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Materials directory recreated")

        return {
            "status": "success",
            "message": "Materials directory reset successfully"
        }

    except Exception as e:
        logger.error(f"❌ Error resetting materials: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Reset error: {str(e)}")


@app.post("/maintenance/clear-drive-cache")
async def maintenance_clear_drive_cache(current_user: User = Depends(get_current_user)):
    """Clear Drive cache (maintenance endpoint)"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"🧹 Drive cache clear requested by: {current_user.username}")

    try:
        # Clear any cached data
        if hasattr(drive_handler, 'processed_files'):
            drive_handler.processed_files.clear()
        if hasattr(drive_handler, 'file_hashes'):
            drive_handler.file_hashes.clear()

        return {
            "status": "success",
            "message": "Drive cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"❌ Error clearing drive cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/cleanup-empty-folders")
async def cleanup_empty_folders(current_user: User = Depends(get_current_user)):
    """Clean up empty folders"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(
        f"🧹 Empty folder cleanup requested by: {current_user.username}")

    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {
                "status": "success",
                "message": "Materials directory does not exist",
                "removed_folders": 0
            }

        removed_folders = 0
        for folder in materials_dir.rglob("*"):
            if folder.is_dir() and not any(folder.iterdir()):
                try:
                    folder.rmdir()
                    removed_folders += 1
                    logger.info(f"Removed empty folder: {folder}")
                except Exception as e:
                    logger.error(f"Error removing folder {folder}: {e}")

        return {
            "status": "success",
            "message": f"Removed {removed_folders} empty folders",
            "removed_folders": removed_folders
        }

    except Exception as e:
        logger.error(f"❌ Error in empty folder cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/optimize-storage")
async def optimize_storage(current_user: User = Depends(get_current_user)):
    """Optimize storage usage"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(
        f"⚡ Storage optimization requested by: {current_user.username}")

    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {
                "status": "success",
                "message": "Materials directory does not exist",
                "optimizations": []
            }

        optimizations = []

        # Remove duplicates
        duplicate_analysis = analyze_duplicates(materials_dir)
        if duplicate_analysis.get("duplicate_groups", 0) > 0:
            optimizations.append(
                "Duplicate files detected - run cleanup-duplicates")

        # Remove empty folders
        empty_folders = [f for f in materials_dir.rglob(
            "*") if f.is_dir() and not any(f.iterdir())]
        if empty_folders:
            optimizations.append(
                f"Empty folders detected - run cleanup-empty-folders")

        # Check for large files
        large_files = []
        for file in materials_dir.rglob("*"):
            if file.is_file() and file.stat().st_size > 100 * 1024 * 1024:  # > 100MB
                large_files.append(str(file.relative_to(materials_dir)))

        if large_files:
            optimizations.append(
                f"Large files detected: {len(large_files)} files > 100MB")

        return {
            "status": "success",
            "message": "Storage analysis completed",
            "optimizations": optimizations,
            "duplicate_analysis": duplicate_analysis,
            "empty_folders_count": len(empty_folders),
            "large_files_count": len(large_files)
        }

    except Exception as e:
        logger.error(f"❌ Error in storage optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/reset-chromadb")
async def reset_chromadb(current_user: User = Depends(get_current_user)):
    """Reset ChromaDB"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"🔄 ChromaDB reset requested by: {current_user.username}")

    try:
        chromadb_dir = Path(".chromadb")
        if chromadb_dir.exists():
            shutil.rmtree(chromadb_dir)
            logger.info("ChromaDB directory removed")

        return {
            "status": "success",
            "message": "ChromaDB reset successfully"
        }

    except Exception as e:
        logger.error(f"❌ Error resetting ChromaDB: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/reset-component")
async def reset_component(
    data: ResetComponent,
    current_user: User = Depends(get_current_user)
):
    """Reset a specific component"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not data.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")

    logger.info(f"🔄 Component reset requested by: {current_user.username}")

    try:
        if data.component == "materials":
            materials_dir = Path("data/materials")
            if materials_dir.exists():
                shutil.rmtree(materials_dir)
            materials_dir.mkdir(parents=True, exist_ok=True)
            message = "Materials directory reset successfully"

        elif data.component == "chromadb":
            chromadb_dir = Path(".chromadb")
            if chromadb_dir.exists():
                shutil.rmtree(chromadb_dir)
            message = "ChromaDB reset successfully"

        elif data.component == "drive_cache":
            if hasattr(drive_handler, 'processed_files'):
                drive_handler.processed_files.clear()
            if hasattr(drive_handler, 'file_hashes'):
                drive_handler.file_hashes.clear()
            message = "Drive cache reset successfully"

        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown component: {data.component}")

        return {
            "status": "success",
            "message": message,
            "component": data.component
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resetting component {data.component}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# ANALYTICS ENDPOINTS
# ========================================

@app.get("/analytics/folder-structure")
async def get_folder_structure_analysis(current_user: User = Depends(get_current_user)):
    """Analyze folder structure"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(
        f"📊 Folder structure analysis requested by: {current_user.username}")

    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {
                "status": "success",
                "message": "Materials directory does not exist",
                "analysis": {}
            }

        analysis = {
            "total_folders": 0,
            "total_files": 0,
            "folder_depth": {},
            "file_types": defaultdict(int),
            "size_distribution": {
                "< 1MB": 0,
                "1MB - 10MB": 0,
                "10MB - 100MB": 0,
                "> 100MB": 0
            }
        }

        for item in materials_dir.rglob("*"):
            if item.is_dir():
                analysis["total_folders"] += 1
                depth = len(item.relative_to(materials_dir).parts)
                analysis["folder_depth"][depth] = analysis["folder_depth"].get(
                    depth, 0) + 1
            elif item.is_file():
                analysis["total_files"] += 1
                ext = item.suffix.lower() or 'no_extension'
                analysis["file_types"][ext] += 1

                size = item.stat().st_size
                if size < 1024 * 1024:
                    analysis["size_distribution"]["< 1MB"] += 1
                elif size < 10 * 1024 * 1024:
                    analysis["size_distribution"]["1MB - 10MB"] += 1
                elif size < 100 * 1024 * 1024:
                    analysis["size_distribution"]["10MB - 100MB"] += 1
                else:
                    analysis["size_distribution"]["> 100MB"] += 1

        analysis["file_types"] = dict(analysis["file_types"])

        return {
            "status": "success",
            "message": "Folder structure analysis completed",
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"❌ Error in folder structure analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/file-distribution")
async def get_file_distribution_analysis(current_user: User = Depends(get_current_user)):
    """Analyze file distribution"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(
        f"📊 File distribution analysis requested by: {current_user.username}")

    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {
                "status": "success",
                "message": "Materials directory does not exist",
                "analysis": {}
            }

        analysis = {
            "file_types": defaultdict(int),
            "size_ranges": {
                "< 1MB": 0,
                "1MB - 10MB": 0,
                "10MB - 100MB": 0,
                "> 100MB": 0
            },
            "total_files": 0,
            "total_size": 0
        }

        for file in materials_dir.rglob("*"):
            if file.is_file():
                analysis["total_files"] += 1
                size = file.stat().st_size
                analysis["total_size"] += size

                ext = file.suffix.lower() or 'no_extension'
                analysis["file_types"][ext] += 1

                if size < 1024 * 1024:
                    analysis["size_ranges"]["< 1MB"] += 1
                elif size < 10 * 1024 * 1024:
                    analysis["size_ranges"]["1MB - 10MB"] += 1
                elif size < 100 * 1024 * 1024:
                    analysis["size_ranges"]["10MB - 100MB"] += 1
                else:
                    analysis["size_ranges"]["> 100MB"] += 1

        analysis["file_types"] = dict(analysis["file_types"])
        analysis["total_size_mb"] = round(
            analysis["total_size"] / (1024 * 1024), 2)

        return {
            "status": "success",
            "message": "File distribution analysis completed",
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"❌ Error in file distribution analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/storage-efficiency")
async def get_storage_efficiency_analysis(current_user: User = Depends(get_current_user)):
    """Analyze storage efficiency"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(
        f"📊 Storage efficiency analysis requested by: {current_user.username}")

    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {
                "status": "success",
                "message": "Materials directory does not exist",
                "analysis": {}
            }

        # Analyze duplicates
        duplicate_analysis = analyze_duplicates(materials_dir)

        # Calculate efficiency metrics
        total_files = duplicate_analysis.get("total_files_scanned", 0)
        unique_files = duplicate_analysis.get("unique_files", 0)
        duplicate_files = duplicate_analysis.get("duplicate_files", 0)
        wasted_space = duplicate_analysis.get("wasted_space_bytes", 0)

        efficiency = {
            "total_files": total_files,
            "unique_files": unique_files,
            "duplicate_files": duplicate_files,
            "wasted_space_bytes": wasted_space,
            "wasted_space_mb": round(wasted_space / (1024 * 1024), 2),
            "efficiency_percentage": duplicate_analysis.get("efficiency_percentage", 100),
            "duplicate_groups": duplicate_analysis.get("duplicate_groups", 0)
        }

        return {
            "status": "success",
            "message": "Storage efficiency analysis completed",
            "analysis": efficiency
        }

    except Exception as e:
        logger.error(f"❌ Error in storage efficiency analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/download-report")
async def get_download_report(current_user: User = Depends(get_current_user)):
    """Generate download report"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"📊 Download report requested by: {current_user.username}")

    try:
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {
                "status": "success",
                "message": "Materials directory does not exist",
                "report": {}
            }

        report = {
            "total_files": 0,
            "total_size": 0,
            "file_types": defaultdict(int),
            "folders": defaultdict(int),
            "recent_downloads": []
        }

        for file in materials_dir.rglob("*"):
            if file.is_file():
                report["total_files"] += 1
                size = file.stat().st_size
                report["total_size"] += size

                ext = file.suffix.lower() or 'no_extension'
                report["file_types"][ext] += 1

                # Count files per folder
                folder = str(file.parent.relative_to(materials_dir))
                report["folders"][folder] += 1

                # Get modification time
                mtime = file.stat().st_mtime
                report["recent_downloads"].append({
                    "file": str(file.relative_to(materials_dir)),
                    "size": size,
                    "modified": datetime.fromtimestamp(mtime).isoformat()
                })

        # Sort recent downloads by modification time
        report["recent_downloads"].sort(
            key=lambda x: x["modified"], reverse=True)
        report["recent_downloads"] = report["recent_downloads"][:10]  # Top 10

        report["file_types"] = dict(report["file_types"])
        report["folders"] = dict(report["folders"])
        report["total_size_mb"] = round(
            report["total_size"] / (1024 * 1024), 2)

        return {
            "status": "success",
            "message": "Download report generated",
            "report": report
        }

    except Exception as e:
        logger.error(f"❌ Error generating download report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# DEBUG ENDPOINTS
# ========================================

@app.get("/debug/drive")
async def debug_drive(current_user: User = Depends(get_current_user)):
    """Debug Drive handler"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    logger.info(f"🐛 Drive debug requested by: {current_user.username}")

    try:
        debug_info = {
            "handler_type": type(drive_handler).__name__,
            "handler_initialized": drive_handler is not None,
            "service_available": drive_handler.service is not None if drive_handler else False,
            "api_key_configured": bool(drive_handler.api_key) if drive_handler else False,
            "processed_files_count": len(drive_handler.processed_files) if drive_handler and hasattr(drive_handler, 'processed_files') else 0,
            "file_hashes_count": len(drive_handler.file_hashes) if drive_handler and hasattr(drive_handler, 'file_hashes') else 0,
            "handler_attributes": list(drive_handler.__dict__.keys()) if drive_handler else []
        }

        return {
            "status": "success",
            "message": "Drive debug information",
            "debug_info": debug_info
        }

    except Exception as e:
        logger.error(f"❌ Error in drive debug: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DNA da Força API Server")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host para o servidor")
    parser.add_argument("--port", type=int, default=8000,
                        help="Porta para o servidor")
    parser.add_argument("--reload", action="store_true",
                        help="Habilitar reload automático")

    args = parser.parse_args()

    logger.info(
        f"🚀 Iniciando servidor API Geral em {args.host}:{args.port}...")
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
