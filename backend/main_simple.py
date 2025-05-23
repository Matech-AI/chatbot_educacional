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

# Initialize FastAPI app
app = FastAPI(title="DNA da Força AI API - Windows")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models


class Token(BaseModel):
    access_token: str
    token_type: str


class Question(BaseModel):
    content: str


class Response(BaseModel):
    answer: str
    sources: List[dict]
    response_time: float


# Simple user database
USERS_DB = {
    "admin": {"username": "admin", "password": "admin123", "role": "admin"},
    "instrutor": {"username": "instrutor", "password": "instrutor123", "role": "instructor"},
    "aluno": {"username": "aluno", "password": "aluno123", "role": "student"}
}


def authenticate_user(username: str, password: str):
    user = USERS_DB.get(username)
    if user and user["password"] == password:
        return user
    return None


def create_access_token(data: dict):
    # Simplified token (not JWT for testing)
    token_data = {
        "sub": data["sub"],
        "role": data["role"],
        "exp": (datetime.utcnow() + timedelta(hours=24)).timestamp()
    }
    # In production, use proper JWT encoding
    token = f"{data['sub']}-{data['role']}-{datetime.now().timestamp()}"
    return token


async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Simplified token validation
    try:
        username = token.split('-')[0]
        role = token.split('-')[1]

        if username in USERS_DB:
            return {
                "username": username,
                "role": role
            }
    except:
        pass

    raise HTTPException(
        status_code=401,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Routes


@app.get("/")
def read_root():
    return {"message": "DNA da Força AI API funcionando!", "status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend conectado"}


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
        data={"sub": user["username"], "role": user["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/chat", response_model=Response)
async def chat(question: Question, current_user: dict = Depends(get_current_user)):
    """Process a chat question and return mock response"""

    # Mock responses based on question content
    mock_responses = {
        "treino": "O treinamento de força é fundamental para o desenvolvimento muscular. Recomenda-se treinar 3-4 vezes por semana com exercícios compostos.",
        "nutrição": "A nutrição adequada inclui proteínas (1.6-2.2g/kg), carboidratos complexos e gorduras saudáveis. Hidratação é essencial.",
        "recuperação": "A recuperação muscular ocorre durante o descanso. Durma 7-9 horas por noite e permita 48-72h entre treinos do mesmo grupo muscular.",
        "default": f"Obrigado pela pergunta sobre '{question.content}'. Esta é uma resposta de teste do assistente DNA da Força."
    }

    # Simple keyword matching
    response_text = mock_responses["default"]
    for keyword, response in mock_responses.items():
        if keyword in question.content.lower():
            response_text = response
            break

    return {
        "answer": response_text,
        "sources": [
            {
                "title": "Manual DNA da Força",
                "source": "/materials/manual.pdf",
                "page": 1,
                "chunk": "Conteúdo de exemplo do material de treino..."
            }
        ],
        "response_time": 0.5
    }


@app.post("/materials/upload")
async def upload_material(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Create materials directory
    materials_dir = Path("data/materials")
    materials_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = materials_dir / file.filename
    with file_path.open("wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return {"status": "success", "filename": file.filename}


@app.get("/materials")
def list_materials(current_user: dict = Depends(get_current_user)):
    materials_dir = Path("data/materials")
    materials_dir.mkdir(parents=True, exist_ok=True)

    files = []
    for file_path in materials_dir.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            files.append({
                "id": file_path.name,
                "title": file_path.stem,
                "description": f"Material de treino: {file_path.name}",
                "type": file_path.suffix[1:].lower(),
                "path": f"/api/materials/{file_path.name}",
                "size": stat.st_size,
                "uploadedAt": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "uploadedBy": "system",
                "tags": ["treino", "educacao"]
            })

    # Add mock materials if directory is empty
    if not files:
        files = [
            {
                "id": "fundamentos-treino",
                "title": "Fundamentos do Treinamento de Força",
                "description": "Guia completo sobre os princípios básicos do treinamento de força",
                "type": "pdf",
                "path": "/api/materials/fundamentos.pdf",
                "size": 2500000,
                "uploadedAt": datetime.now().isoformat(),
                "uploadedBy": "system",
                "tags": ["força", "fundamentos", "treino"]
            },
            {
                "id": "periodizacao",
                "title": "Periodização do Treinamento",
                "description": "Metodologia detalhada para periodização de treinos",
                "type": "pdf",
                "path": "/api/materials/periodizacao.pdf",
                "size": 1800000,
                "uploadedAt": datetime.now().isoformat(),
                "uploadedBy": "system",
                "tags": ["periodização", "planejamento"]
            }
        ]

    return files


@app.get("/materials/{filename}")
def get_material(filename: str, current_user: dict = Depends(get_current_user)):
    file_path = Path("data/materials") / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path), filename=filename)
    else:
        # Return mock response for demo
        raise HTTPException(
            status_code=404, detail="Arquivo não encontrado (modo demo)")


@app.delete("/materials/{filename}")
def delete_material(filename: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    file_path = Path("data/materials") / filename
    if file_path.exists():
        file_path.unlink()
        return {"status": "success", "message": f"{filename} removido com sucesso"}
    else:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")


@app.post("/sync-drive")
def sync_drive(data: dict, current_user: dict = Depends(get_current_user)):
    # Mock Drive sync for testing
    folder_id = data.get("folder_id", "")

    return {
        "status": "success",
        "files": [
            {"name": "material1.pdf", "size": 1024000},
            {"name": "material2.pdf", "size": 2048000}
        ],
        "message": f"Simulação: sincronizado pasta {folder_id}"
    }


@app.post("/initialize")
async def initialize_system(api_key: str = Form(...)):
    """Mock system initialization"""
    return {
        "status": "success",
        "messages": [
            "✓ Sistema inicializado (modo demo)",
            "✓ Pronto para responder perguntas"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
