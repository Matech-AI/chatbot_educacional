from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import os
import json
from datetime import datetime, timedelta
import logging

from auth import (
    create_access_token,
    get_current_user,
    authenticate_user,
    User,
    Token
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Chatbot Educacional API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Question(BaseModel):
    content: str

class Response(BaseModel):
    answer: str
    sources: List[dict] = []
    response_time: float = 0.0

class LoginRequest(BaseModel):
    username: str
    password: str

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Chatbot Educacional API está funcionando!", "status": "online"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Authentication endpoint
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Chat endpoint (simplified)
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
                "source": "backend/main_simple_fixed.py",
                "page": 1,
                "relevance": 0.9
            }
        ],
        response_time=0.1
    )

# Materials endpoints
@app.get("/materials")
async def list_materials():
    """List available materials"""
    materials_dir = Path("data/materials")
    materials_dir.mkdir(parents=True, exist_ok=True)
    
    files = []
    if materials_dir.exists():
        for file_path in materials_dir.glob("*"):
            if file_path.is_file():
                files.append({
                    "id": file_path.name,
                    "title": file_path.name,
                    "path": f"/materials/{file_path.name}",
                    "type": file_path.suffix[1:] if file_path.suffix else "unknown",
                    "size": file_path.stat().st_size,
                    "uploadedAt": file_path.stat().st_mtime,
                    "uploadedBy": "system",
                    "tags": []
                })
    
    return files

@app.post("/materials/upload")
async def upload_material(file: UploadFile = File(...)):
    """Upload a material file"""
    materials_dir = Path("data/materials")
    materials_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = materials_dir / file.filename
    
    try:
        with file_path.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "status": "success",
            "message": f"Arquivo '{file.filename}' carregado com sucesso",
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar arquivo: {str(e)}")

@app.get("/materials/{filename}")
async def get_material(filename: str):
    """Download a material file"""
    file_path = Path("data/materials") / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(str(file_path), filename=filename)

@app.delete("/materials/{filename}")
async def delete_material(filename: str):
    """Delete a material file"""
    file_path = Path("data/materials") / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    try:
        file_path.unlink()
        return {
            "status": "success",
            "message": f"Arquivo '{filename}' removido com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover arquivo: {str(e)}")

# System status endpoint
@app.get("/status")
async def get_status():
    """Get system status"""
    return {
        "backend": "online",
        "database": "simulated",
        "ai_enabled": False,
        "materials_count": len(list(Path("data/materials").glob("*")) if Path("data/materials").exists() else []),
        "uptime": "Running",
        "message": "Sistema funcionando em modo simplificado. Configure OpenAI para funcionalidades completas."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_simple_fixed:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )

