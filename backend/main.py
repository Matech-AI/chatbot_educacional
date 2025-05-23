from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import os
import json
from datetime import datetime, timedelta
import shutil
import tempfile
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

# Initialize FastAPI app
app = FastAPI(title="DNA da Força AI API")

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

# Models


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


USERS_FILE = "users.json"


def load_users():
    if not os.path.exists(USERS_FILE):
        # Inicializa com os usuários padrão
        users = [
            {"username": "admin", "password": "admin123", "role": "admin"},
            {"username": "instrutor", "password": "instrutor123", "role": "instructor"},
            {"username": "aluno", "password": "aluno123", "role": "student"}
        ]
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)
        return users
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


def authenticate_user(username: str, password: str):
    users = load_users()
    for user in users:
        if user["username"] == username and user["password"] == password:
            return user
    return None


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


@app.post("/initialize")
async def initialize_system(
    api_key: str = Form(...),
    drive_folder_id: Optional[str] = Form(None),
    credentials_json: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user)
):
    """Initialize the system with OpenAI API key and optional Drive materials"""
    global rag_handler, drive_handler

    try:
        messages = []

        # Initialize RAG handler
        rag_handler = RAGHandler(api_key)
        messages.append("✓ Initialized RAG handler")

        # Process Drive materials if provided
        if drive_folder_id and credentials_json:
            # Save credentials temporarily
            creds_path = Path("credentials.json")
            content = await credentials_json.read()
            creds_path.write_bytes(content)

            try:
                # Authenticate and process folder
                drive_handler.authenticate(str(creds_path))
                messages.append("✓ Authenticated with Google Drive")

                downloaded_files = drive_handler.process_folder(
                    drive_folder_id)
                messages.append(
                    f"✓ Downloaded {len(downloaded_files)} files from Drive")

                # Process downloaded materials
                success, rag_messages = rag_handler.process_and_initialize(
                    "data/materials")
                messages.extend(rag_messages)

            finally:
                # Cleanup credentials
                creds_path.unlink(missing_ok=True)
                Path("token.json").unlink(missing_ok=True)
        else:
            # Just process local materials
            success, rag_messages = rag_handler.process_and_initialize(
                "data/materials")
            messages.extend(rag_messages)

        if success:
            return {"status": "success", "messages": messages}
        else:
            raise HTTPException(status_code=500, detail=messages[-1])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/materials/upload")
async def upload_material(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    save_dir = Path("data/materials")
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / file.filename
    with file_path.open("wb") as buffer:
        content = await file.read()
        buffer.write(content)
    return {"status": "success", "filename": file.filename}


@app.get("/materials")
def list_materials():
    files = []
    for fname in os.listdir("data/materials"):
        fpath = os.path.join("data/materials", fname)
        if os.path.isfile(fpath):
            files.append({
                "id": fname,
                "title": fname,
                "path": f"/api/materials/{fname}",
                "type": fname.split('.')[-1],
                "size": os.path.getsize(fpath),
                "uploadedAt": os.path.getmtime(fpath),
                "uploadedBy": "backend",
                "tags": []
            })
    return files


@app.get("/materials/{filename}")
def get_material(filename: str):
    file_path = Path("data/materials") / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(str(file_path), filename=filename)


@app.delete("/materials/{filename}")
def delete_material(filename: str, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    file_path = Path("data/materials") / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    file_path.unlink()
    return {"status": "success", "message": f"{filename} removido com sucesso"}


@app.get("/materials-zip")
def download_all_materials():
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    zip_path = temp_zip.name
    temp_zip.close()
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', "data/materials")
    return FileResponse(zip_path, filename="materiais.zip", media_type="application/zip")


@app.post("/sync-drive")
def sync_drive(data: dict = Body(...)):
    folder_id = data.get("folder_id")
    drive_handler.authenticate('credentials.json')
    files = drive_handler.process_folder(folder_id)
    return {"files": files}


@app.post("/change-password")
async def change_password(request: Request, data: dict = None, current_user: User = Depends(get_current_user)):
    if data is None:
        data = await request.json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    if not current_password or not new_password:
        raise HTTPException(
            status_code=400, detail="Campos obrigatórios ausentes.")
    users = load_users()
    for user in users:
        if user["username"] == current_user.username:
            if user["password"] != current_password:
                raise HTTPException(
                    status_code=401, detail="Senha atual incorreta.")
            user["password"] = new_password
            save_users(users)
            return {"status": "success", "message": "Senha alterada com sucesso."}
    raise HTTPException(status_code=404, detail="Usuário não encontrado.")


@app.post("/reset-password")
async def reset_password(data: dict):
    username = data.get("username")
    new_password = data.get("new_password")
    if not username or not new_password:
        raise HTTPException(
            status_code=400, detail="Campos obrigatórios ausentes.")
    users = load_users()
    for user in users:
        if user["username"] == username:
            user["password"] = new_password
            save_users(users)
            return {"status": "success", "message": "Senha redefinida com sucesso."}
    raise HTTPException(status_code=404, detail="Usuário não encontrado.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
