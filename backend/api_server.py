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
from pathlib import Path
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
        materials_dir = Path("data/materials")
        if not materials_dir.exists():
            return {"materials": []}

        materials = []
        for file_path in materials_dir.iterdir():
            if file_path.is_file():
                materials.append({
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime
                })

        return {"materials": materials}
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

if __name__ == "__main__":
    logger.info("🚀 Iniciando servidor API Geral na porta 8000...")
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
