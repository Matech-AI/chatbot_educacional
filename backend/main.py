from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
from dotenv import load_dotenv
import os

# Import RAG handler
from rag_handler import RAGHandler, ProcessingConfig

# Import auth functionality
from passlib.context import CryptContext
from jose import JWTError, jwt

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
    allow_headers=["*"],
)

# RAG Handler Initialization
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

rag_config = ProcessingConfig()
rag_handler = RAGHandler(api_key=API_KEY, config=rag_config)

# Security configuration (from auth.py)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mock users database from auth.py
USERS_DB = {
    "admin": {
        "username": "admin",
        "role": "admin",
        "hashed_password": pwd_context.hash("adminpass"),
        "disabled": False
    },
    "instrutor": {
        "username": "instrutor",
        "role": "instructor",
        "hashed_password": pwd_context.hash("instrutorpass"),
        "disabled": False
    },
    "aluno": {
        "username": "aluno",
        "role": "student",
        "hashed_password": pwd_context.hash("alunopass"),
        "disabled": False
    }
}

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class User(BaseModel):
    username: str
    role: str
    disabled: Optional[bool] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: Optional[List[dict]] = None


class IndexResponse(BaseModel):
    success: bool
    message: str
    details: Optional[List[str]] = None

# Auth helper functions (from auth.py)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    if username in USERS_DB:
        user_dict = USERS_DB[username]
        return User(**user_dict)
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, USERS_DB[username]["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

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
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    if not rag_handler:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    response_data = rag_handler.generate_response(request.message)
    
    return ChatResponse(
        response=response_data["answer"],
        conversation_id=request.conversation_id or "default-conversation",
        sources=response_data.get("sources", [])
    )

@app.post("/index", response_model=IndexResponse)
async def index_documents(current_user: User = Depends(get_current_user)):
    """
    Scans the 'data/materials' directory, processes all documents,
    and adds them to the ChromaDB 'materials' collection.
    This is a full re-indexing operation.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can index documents")

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

