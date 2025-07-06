from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
from dotenv import load_dotenv
import os
import shutil

# Import RAG handler
from rag_handler import RAGHandler, ProcessingConfig, AssistantConfigModel
from conversational_agent import graph as conversational_graph
from drive_handler import DriveHandler

# Import auth functionality
from auth import (
    User,
    Token,
    get_current_user,
    create_access_token,
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# Load environment variables
load_dotenv()

# Simple working backend for Chatbot Educacional
app = FastAPI(title="Chatbot Educacional API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "x-auth-token"],
)

# RAG Handler Initialization
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

rag_config = ProcessingConfig()
rag_handler = RAGHandler(api_key=API_KEY, config=rag_config)


# Models

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    agent_config: Optional[AssistantConfigModel] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: Optional[List[dict]] = None


class IndexResponse(BaseModel):
    success: bool
    message: str
    details: Optional[List[str]] = None



# Drive Handler Initialization
drive_handler = DriveHandler()

class Material(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    type: str
    path: str
    size: int
    uploadedAt: datetime
    uploadedBy: str
    tags: Optional[List[str]] = None

@app.get("/materials", response_model=List[Material])
async def get_materials_list():
    """
    Lists all materials currently available in the data/materials directory.
    """
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    materials_dir = os.path.join(backend_dir, "data", "materials")
    
    if not os.path.isdir(materials_dir):
        os.makedirs(materials_dir, exist_ok=True)
        return []
    
    materials = []
    for filename in os.listdir(materials_dir):
        file_path = os.path.join(materials_dir, filename)
        if os.path.isfile(file_path):
            file_stat = os.stat(file_path)
            file_type = os.path.splitext(filename)[1].replace('.', '') or 'file'
            
            materials.append(Material(
                id=filename,
                title=filename,
                description=f"Arquivo {filename} localizado no servidor.",
                type=file_type,
                path=file_path,
                size=file_stat.st_size,
                uploadedAt=datetime.fromtimestamp(file_stat.st_ctime),
                uploadedBy="system",
                tags=[file_type, "local"],
            ))
    return materials

@app.post("/materials/upload", response_model=List[Material])
async def upload_material(file: UploadFile = File(...)):
    """
    Uploads a new material to the data/materials directory and returns the updated list.
    """
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    materials_dir = os.path.join(backend_dir, "data", "materials")
    os.makedirs(materials_dir, exist_ok=True)
    
    # Sanitize filename to prevent security issues
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(materials_dir, safe_filename)
    
    # Security check: ensure the final path is within the intended directory
    if not os.path.abspath(file_path).startswith(os.path.abspath(materials_dir)):
        raise HTTPException(status_code=400, detail="Invalid file path")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
        
    # Return the updated list of materials
    materials = []
    for filename_loop in os.listdir(materials_dir):
        file_path_loop = os.path.join(materials_dir, filename_loop)
        if os.path.isfile(file_path_loop):
            file_stat = os.stat(file_path_loop)
            file_type = os.path.splitext(filename_loop)[1].replace('.', '') or 'file'
            
            materials.append(Material(
                id=filename_loop,
                title=filename_loop,
                description=f"Arquivo {filename_loop} localizado no servidor.",
                type=file_type,
                path=file_path_loop,
                size=file_stat.st_size,
                uploadedAt=datetime.fromtimestamp(file_stat.st_ctime),
                uploadedBy="system",
                tags=[file_type, "local"],
            ))
    return materials

@app.get("/drive-stats-detailed")
async def get_drive_stats_detailed():
    """
    Returns statistics about the local materials directory.
    The name is a legacy from a previous implementation.
    """
    stats = drive_handler.get_download_stats()
    return stats


@app.get("/")
def read_root():
    return {"message": "Chatbot Educacional Backend", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Login endpoint using OAuth2PasswordRequestForm (FormData)
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handles a chat request by generating a response using the RAG system.
    """
    if not rag_handler:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    try:
        # Generate a response using the RAG handler
        result = rag_handler.generate_response(
            question=request.message,
            config=request.agent_config
        )
        
        # The conversation_id can be managed based on your application's needs.
        # For now, we'll just pass it through if provided.
        conversation_id = request.conversation_id or f"thread_{datetime.now().timestamp()}"

        return ChatResponse(
            response=result.get("answer", "No answer found."),
            conversation_id=conversation_id,
            sources=result.get("sources", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during chat processing: {e}")


@app.get("/assistant/config", response_model=AssistantConfigModel)
async def get_assistant_config():
    """
    Retrieves the current assistant configuration.
    """
    if not rag_handler:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    current_config = rag_handler.config
    return AssistantConfigModel(
        name="Assistente de Treino",  # Name and description can be customized
        description="Configuração atual do assistente de treino",
        prompt="Prompt atual",  # The prompt is not stored in the config object
        model=current_config.model_name,
        temperature=current_config.temperature,
        chunkSize=current_config.chunk_size,
        chunkOverlap=current_config.chunk_overlap,
        retrievalSearchType="mmr",  # This is not part of the backend config
        embeddingModel=current_config.embedding_model,
    )


@app.post("/assistant/config", response_model=AssistantConfigModel)
async def update_assistant_config(
    config: AssistantConfigModel
):
    """
    Updates the assistant's configuration.
    """
    if not rag_handler:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    try:
        new_config = ProcessingConfig(
            chunk_size=config.chunkSize,
            chunk_overlap=config.chunkOverlap,
            model_name=config.model,
            embedding_model=config.embeddingModel,
            temperature=config.temperature,
        )
        rag_handler.update_config(new_config)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {e}")


@app.post("/index", response_model=IndexResponse)
async def index_documents():
    """
    Scans the 'data/materials' directory, processes all documents,
    and adds them to the ChromaDB 'materials' collection.
    This is a full re-indexing operation.
    """
    # The directory containing the documents to be indexed
    docs_dir = "data/materials"

    # Get the absolute path for file system operations
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_docs_dir = os.path.join(backend_dir, docs_dir)

    if not os.path.isdir(absolute_docs_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Materials directory not found at {absolute_docs_dir}"
        )

    try:
        # Reset handler state before processing to ensure a clean index
        rag_handler.reset()
        
        # Process documents and initialize the chain
        success, messages = rag_handler.process_and_initialize(absolute_docs_dir)
        
        if success:
            return IndexResponse(
                success=True,
                message=f"Documents from '{docs_dir}' indexed successfully.",
                details=messages
            )
        else:
            # Handle the case where no documents are found as a success
            if messages and "No documents found" in messages[0]:
                 return IndexResponse(
                    success=True,
                    message=f"No documents found in '{docs_dir}' to index.",
                    details=messages
                )
            return IndexResponse(
                success=False,
                message=f"Failed to index documents from '{docs_dir}'.",
                details=messages
            )
    except Exception as e:
        # In a real app, you'd want to log this exception
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during indexing: {str(e)}"
        )

