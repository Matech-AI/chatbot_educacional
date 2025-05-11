from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import os
import json
from datetime import datetime, timedelta

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
                
                downloaded_files = drive_handler.process_folder(drive_folder_id)
                messages.append(f"✓ Downloaded {len(downloaded_files)} files from Drive")
                
                # Process downloaded materials
                success, rag_messages = rag_handler.process_and_initialize("data/materials")
                messages.extend(rag_messages)
                
            finally:
                # Cleanup credentials
                creds_path.unlink(missing_ok=True)
                Path("token.json").unlink(missing_ok=True)
        else:
            # Just process local materials
            success, rag_messages = rag_handler.process_and_initialize("data/materials")
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

@app.post("/upload")
async def upload_material(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: str = Form("[]"),
    current_user: User = Depends(get_current_user)
):
    """Upload a new material"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Parse tags
        tags_list = json.loads(tags)
        
        # Save file
        save_dir = Path("data/materials")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = save_dir / file.filename
        with file_path.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Reinitialize RAG system with new material
        if rag_handler:
            success, messages = rag_handler.process_and_initialize("data/materials")
            if not success:
                raise Exception("Failed to update RAG system")
        
        return {
            "status": "success",
            "file_info": {
                "filename": file.filename,
                "size": len(content),
                "type": file.content_type
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/materials")
async def list_materials(current_user: User = Depends(get_current_user)):
    """List all available materials"""
    try:
        materials_dir = Path("data/materials")
        materials = []
        
        for file_path in materials_dir.glob("**/*"):
            if file_path.is_file():
                materials.append({
                    "id": str(file_path.stem),
                    "title": file_path.name,
                    "path": str(file_path.relative_to(materials_dir)),
                    "size": file_path.stat().st_size,
                    "type": file_path.suffix[1:],
                    "uploadedAt": datetime.fromtimestamp(file_path.stat().st_mtime)
                })
        
        return materials
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)