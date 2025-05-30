from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from datetime import datetime
from pathlib import Path
import json

# Criar app FastAPI
app = FastAPI(
    title="DNA da Força API",
    description="Sistema educacional v1.1 com upload",
    version="1.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modelos


class Token(BaseModel):
    access_token: str
    token_type: str


class Question(BaseModel):
    content: str


class Response(BaseModel):
    answer: str
    sources: List[dict]
    response_time: float


# Usuários
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "instrutor": {"password": "instrutor123", "role": "instructor"},
    "aluno": {"password": "aluno123", "role": "student"}
}


def create_token(username: str, role: str):
    timestamp = int(datetime.now().timestamp() * 1000)
    return f"{username}-{role}-{timestamp}"


def validate_token(token: str):
    try:
        parts = token.split('-')
        if len(parts) >= 3:
            username = parts[0]
            role = parts[1]
            if username in USERS:
                return {"username": username, "role": role}
    except:
        pass
    raise HTTPException(status_code=401, detail="Token inválido")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    return validate_token(token)

# ROTAS


@app.get("/")
def root():
    return {
        "message": "🚀 DNA da Força API v1.1",
        "status": "ok",
        "version": "1.1.0",
        "features": ["auth", "chat", "upload", "materials"]
    }


@app.get("/health")
def health():
    print("🏥 Health check v1.1")
    return {
        "status": "ok",
        "message": "Backend v1.1 funcionando com upload",
        "version": "1.1.0",
        "users_available": list(USERS.keys())
    }


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password

    print(f"🔐 Login: {username}")

    if username not in USERS or USERS[username]["password"] != password:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = create_token(username, USERS[username]["role"])
    print(f"✅ Login OK: {username}")

    return {"access_token": token, "token_type": "bearer"}


@app.post("/chat", response_model=Response)
async def chat(question: Question, user: dict = Depends(get_current_user)):
    print(f"💬 {user['username']}: {question.content[:30]}...")

    # Respostas expandidas
    respostas = {
        "treino": "O treinamento de força é fundamental para desenvolvimento muscular. Princípios: sobrecarga progressiva, especificidade, individualidade. Recomendo 3-4 sessões semanais com exercícios compostos como agachamento, supino e levantamento terra.",

        "nutrição": "Nutrição otimizada: 1.6-2.2g proteína/kg, carboidratos 3-7g/kg, gorduras 20-35% VET. Timing: proteína pós-treino, carboidratos pré-treino. Hidratação: 35-40ml/kg peso corporal diariamente.",

        "recuperação": "Recuperação ativa: sono 7-9h (pico GH), descanso 48-72h entre sessões do mesmo grupo. Métodos: alongamento dinâmico, liberação miofascial, contraste térmico, nutrição pós-exercício adequada.",

        "força": "Força máxima: 1-5 reps, 85-100% 1RM, descanso 3-5min, exercícios compostos. Periodização linear para iniciantes, ondulatória para avançados. Técnica sempre priorizada sobre carga.",

        "hipertrofia": "Hipertrofia: 6-12 reps, 65-85% 1RM, volume 10-20 séries/grupo/semana, tempo sob tensão 40-70s, frequência 2-3x/semana/grupo. Variação previne estagnação.",
    }

    pergunta_lower = question.content.lower()
    resposta = "Assistente DNA da Força v1.1. Pergunte sobre: treino, nutrição, recuperação, força, hipertrofia para respostas detalhadas."

    for palavra, resp in respostas.items():
        if palavra in pergunta_lower:
            resposta = resp
            break

    return {
        "answer": resposta,
        "sources": [{"title": "Manual DNA v1.1", "source": "/materials/manual.pdf", "page": 1, "chunk": "Conteúdo científico..."}],
        "response_time": 0.5
    }


@app.get("/materials")
async def list_materials(user: dict = Depends(get_current_user)):
    print(f"📚 Materiais para {user['username']}")

    # Pasta real
    materials_dir = Path("data/materials")
    materials_dir.mkdir(parents=True, exist_ok=True)

    materiais = []

    # Arquivos reais
    for file_path in materials_dir.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            materiais.append({
                "id": file_path.name,
                "title": file_path.stem.replace('_', ' ').title(),
                "description": f"Material: {file_path.name}",
                "type": file_path.suffix[1:].lower(),
                "size": stat.st_size,
                "uploadedAt": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "uploadedBy": "usuario",
                "tags": ["educacional"]
            })

    # Materiais exemplo
    materiais.extend([
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

    return materiais


@app.post("/materials/upload")
async def upload_material(
    file: UploadFile = File(...),
    description: str = Form(""),
    tags: str = Form(""),
    user: dict = Depends(get_current_user)
):
    # Só admin e instrutor podem fazer upload
    if user["role"] not in ["admin", "instructor"]:
        raise HTTPException(
            status_code=403, detail="Sem permissão para upload")

    print(f"📤 Upload: {file.filename} por {user['username']}")

    # Tipos permitidos
    allowed = {'.pdf', '.docx', '.txt', '.mp4', '.avi', '.mov', '.pptx'}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed:
        raise HTTPException(
            status_code=400, detail=f"Tipo não permitido. Use: {', '.join(allowed)}")

    # Criar pasta
    materials_dir = Path("data/materials")
    materials_dir.mkdir(parents=True, exist_ok=True)

    # Evitar sobrescrever
    file_path = materials_dir / file.filename
    counter = 1
    original = file_path

    while file_path.exists():
        stem = original.stem
        suffix = original.suffix
        file_path = materials_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    # Salvar
    try:
        content = await file.read()

        # Max 50MB
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=400, detail="Arquivo muito grande (máx 50MB)")

        with file_path.open("wb") as f:
            f.write(content)

        print(f"✅ Salvo: {file_path}")

        return {
            "status": "success",
            "message": "Upload realizado com sucesso",
            "filename": file_path.name,
            "size": len(content),
            "uploaded_by": user["username"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@app.get("/materials/{filename}")
async def download_material(filename: str, user: dict = Depends(get_current_user)):
    print(f"📥 Download: {filename}")

    file_path = Path("data/materials") / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    return FileResponse(path=str(file_path), filename=filename)


@app.delete("/materials/{filename}")
async def delete_material(filename: str, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Sem permissão")

    print(f"🗑️ Delete: {filename}")

    file_path = Path("data/materials") / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    file_path.unlink()
    return {"status": "success", "message": f"Arquivo removido: {filename}"}


@app.post("/initialize")
async def initialize_system(api_key: str = Form("")):
    return {
        "status": "success",
        "messages": [
            "✅ Sistema v1.1 inicializado",
            "✅ Upload de materiais ativo",
            "✅ Chat expandido funcionando"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 DNA da Força Backend v1.1 - Com Upload")
    uvicorn.run(app, host="0.0.0.0", port=8000)
