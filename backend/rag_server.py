#!/usr/bin/env python3
"""
Servidor RAG Independente - DNA da Força AI
Este servidor fica sempre rodando para processamento de materiais e treinamento do modelo.
"""

import os
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from dotenv import load_dotenv
import time

# Importar componentes RAG
from rag_system.rag_handler import RAGHandler, RAGConfig, Source
import chromadb
from chromadb.config import Settings
# ========================================
# MODELS PYDANTIC
# ========================================


class ProcessMaterialsRequest(BaseModel):
    force_reprocess: bool = False
    enable_educational_features: bool = True


class ProcessResponse(BaseModel):
    success: bool
    message: str


class QueryRequest(BaseModel):
    question: str
    user_level: str = "intermediate"


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    response_time: float




# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Variáveis globais
rag_handler = None
chroma_persist_dir = None
materials_dir = None



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager para inicializar e limpar recursos"""
    global rag_handler, chroma_persist_dir, materials_dir

    logger.info("🚀 Iniciando servidor RAG...")

    # Configurar diretórios
    chroma_persist_dir = Path("data/chromadb")
    materials_dir = Path("data/materials")

    # Criar diretórios se não existirem
    chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    materials_dir.mkdir(parents=True, exist_ok=True)


    logger.info(f"📁 Diretórios configurados:")
    logger.info(f"   - ChromaDB: {chroma_persist_dir}")
    logger.info(f"   - Materiais: {materials_dir}")

    # Tentar inicializar RAG handler automaticamente se OPENAI_API_KEY estiver disponível
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key and openai_api_key != "your_openai_api_key_here":
        try:
            logger.info("🔧 Inicializando RAG handler automaticamente...")
            rag_handler = RAGHandler(
                api_key=openai_api_key,
                persist_dir=str(chroma_persist_dir)
            )
            logger.info("✅ RAG handler inicializado automaticamente")
        except Exception as e:
            logger.warning(
                f"⚠️  Não foi possível inicializar RAG handler automaticamente: {e}")
            logger.info(
                "💡 Use a rota /initialize para inicializar manualmente")
    else:
        logger.info(
            "💡 OPENAI_API_KEY não configurada. Use a rota /initialize para inicializar o RAG handler")

    logger.info("✅ Servidor RAG iniciado com sucesso")

    yield

    logger.info("🛑 Encerrando servidor RAG...")

# Inicializar FastAPI
app = FastAPI(
    title="DNA da Força RAG Server",
    description="Servidor RAG para processamento de materiais e treinamento de modelos",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS para permitir o frontend no Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chatbot-educacional.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://dna-forca-frontend.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Verificar saúde do servidor RAG"""
    return {
        "status": "healthy",
        "service": "rag-server",
        "version": "1.0.0",
        "rag_initialized": rag_handler is not None
    }


@app.get("/status")
async def get_status():
    """Obter status detalhado do servidor RAG"""
    global rag_handler

    status = {
        "service": "rag-server",
        "version": "1.0.0",
        "rag_initialized": rag_handler is not None,
        "materials_directory": str(materials_dir) if materials_dir else None,
        "chroma_persist_dir": str(chroma_persist_dir) if chroma_persist_dir else None,
        "materials_count": 0,
        "vector_store_ready": False
    }

    if rag_handler:
        try:
            stats = rag_handler.get_system_stats()
            status.update(stats)
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")

    return status


@app.post("/process-materials", response_model=ProcessResponse)
async def process_materials(request: ProcessMaterialsRequest, background_tasks: BackgroundTasks):
    """Process materials in the background with configurable educational features."""
    global rag_handler
    if not rag_handler:
        raise HTTPException(status_code=503, detail="RAG handler not initialized.")

    try:
        logger.info(f"🔄 Starting material processing with educational features: {request.enable_educational_features}")
        
        # Update the handler's config for this task
        rag_handler.config.enable_educational_features = request.enable_educational_features
        
        background_tasks.add_task(rag_handler.process_documents, force_reprocess=request.force_reprocess)

        return ProcessResponse(
            success=True,
            message="Material processing started in the background."
        )
    except Exception as e:
        logger.error(f"❌ Error starting processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reprocess-enhanced-materials", response_model=ProcessResponse)
async def reprocess_enhanced_materials(background_tasks: BackgroundTasks):
    """
    Reprocess all materials using the enhanced RAG system.

    This endpoint forces reprocessing of all documents with educational features enabled,
    such as extracting key concepts, assessing difficulty, and creating summaries.
    """
    global rag_handler
    if not rag_handler:
        raise HTTPException(status_code=503, detail="RAG handler not initialized.")

    try:
        logger.info("🚀 Starting enhanced material reprocessing...")

        # Forçar a ativação de recursos educacionais para este processo
        rag_handler.config.enable_educational_features = True

        # Adicionar a tarefa de reprocessamento em segundo plano
        background_tasks.add_task(rag_handler.process_documents, force_reprocess=True)

        return ProcessResponse(
            success=True,
            message="Enhanced material reprocessing started in the background."
        )
    except Exception as e:
        logger.error(f"❌ Error starting enhanced reprocessing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Realizar consulta RAG"""
    global rag_handler

    if not rag_handler:
        raise HTTPException(
            status_code=503, detail="RAG handler não inicializado")

    try:
        start_time = asyncio.get_event_loop().time()

        # Realizar consulta
        result = rag_handler.generate_response(
            question=request.question,
            user_level=request.user_level
        )

        end_time = asyncio.get_event_loop().time()
        response_time = end_time - start_time

        return QueryResponse(
            answer=result.get("answer", ""),
            sources=[
                {
                    **source,
                    "chunk": source["chunk"][:200] + "..." if len(source["chunk"]) > 200 else source["chunk"],
                    "title": None  # Remove the title
                }
                for source in result.get("sources", [])
            ],
            response_time=response_time
        )

    except Exception as e:
        logger.error(f"❌ Erro na consulta RAG: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro na consulta: {str(e)}")


@app.post("/initialize")
async def initialize_rag(api_key: str):
    """Inicializar RAG handler"""
    global rag_handler

    try:
        logger.info("🔧 Inicializando RAG handler...")

        rag_handler = RAGHandler(
            api_key=api_key,
            persist_dir=str(chroma_persist_dir)
        )

        logger.info("✅ RAG handler inicializado com sucesso")
        return {"success": True, "message": "RAG handler inicializado"}

    except Exception as e:
        logger.error(f"❌ Erro ao inicializar RAG: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro na inicialização: {str(e)}")


@app.post("/reset")
async def reset_rag():
    """Resetar RAG handler"""
    global rag_handler

    try:
        if rag_handler:
            rag_handler.reset()
            logger.info("🔄 RAG handler resetado")

        return {"success": True, "message": "RAG handler resetado"}

    except Exception as e:
        logger.error(f"❌ Erro ao resetar RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no reset: {str(e)}")


@app.get("/stats")
async def get_rag_stats():
    """Obter estatísticas do RAG"""
    global rag_handler

    if not rag_handler:
        raise HTTPException(
            status_code=503, detail="RAG handler não inicializado")

    try:
        stats = rag_handler.get_system_stats()
        return stats

    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")




if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DNA da Força RAG Server")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host para o servidor")
    parser.add_argument("--port", type=int, default=8001,
                        help="Porta para o servidor")
    parser.add_argument("--reload", action="store_true",
                        help="Habilitar reload automático")

    args = parser.parse_args()

    logger.info(f"🚀 Iniciando servidor RAG em {args.host}:{args.port}...")
    uvicorn.run(
        "rag_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
