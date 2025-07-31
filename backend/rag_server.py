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
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from dotenv import load_dotenv

# Importar componentes RAG
from rag_system.rag_handler import RAGHandler, ProcessingConfig, AssistantConfigModel

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar FastAPI
app = FastAPI(
    title="DNA da Força RAG Server",
    description="Servidor RAG para processamento de materiais e treinamento de modelos",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variáveis globais
rag_handler = None
materials_dir = os.getenv("MATERIALS_DIR", "/app/data/materials")
chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", "/app/data/.chromadb")

# Modelos Pydantic


class ProcessMaterialsRequest(BaseModel):
    """Request para processar materiais"""
    api_key: str
    force_reprocess: bool = False


class QueryRequest(BaseModel):
    """Request para consulta RAG"""
    question: str
    material_ids: Optional[List[str]] = None
    config: Optional[AssistantConfigModel] = None


class ProcessResponse(BaseModel):
    """Response do processamento"""
    success: bool
    message: str
    processed_files: List[str] = []
    errors: List[str] = []


class QueryResponse(BaseModel):
    """Response da consulta RAG"""
    answer: str
    sources: List[Dict[str, Any]]
    response_time: float


@app.on_event("startup")
async def startup_event():
    """Inicializar o servidor RAG"""
    global rag_handler

    logger.info("🚀 Iniciando servidor RAG...")

    # Verificar se o diretório de materiais existe
    materials_path = Path(materials_dir)
    if not materials_path.exists():
        logger.warning(
            f"⚠️ Diretório de materiais não encontrado: {materials_dir}")
        materials_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Diretório criado: {materials_dir}")

    logger.info(f"📁 Diretório de materiais: {materials_dir}")
    logger.info(f"📁 Diretório ChromaDB: {chroma_persist_dir}")


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
        "materials_directory": materials_dir,
        "chroma_persist_dir": chroma_persist_dir,
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
    """Processar materiais em background"""
    global rag_handler

    try:
        logger.info("🔄 Iniciando processamento de materiais...")

        # Inicializar RAG handler se necessário
        if not rag_handler:
            rag_handler = RAGHandler(
                api_key=request.api_key,
                persist_dir=chroma_persist_dir
            )
            logger.info("✅ RAG handler inicializado")

        # Processar materiais em background
        background_tasks.add_task(
            process_materials_task, request.api_key, request.force_reprocess)

        return ProcessResponse(
            success=True,
            message="Processamento de materiais iniciado em background"
        )

    except Exception as e:
        logger.error(f"❌ Erro ao iniciar processamento: {e}")
        return ProcessResponse(
            success=False,
            message=f"Erro ao iniciar processamento: {str(e)}"
        )


async def process_materials_task(api_key: str, force_reprocess: bool = False):
    """Task em background para processar materiais"""
    global rag_handler

    try:
        logger.info("🔄 Processando materiais em background...")

        # Inicializar RAG handler se necessário
        if not rag_handler:
            rag_handler = RAGHandler(
                api_key=api_key,
                persist_dir=chroma_persist_dir
            )

        # Processar materiais
        success, processed_files = rag_handler.process_and_initialize(
            materials_dir)

        if success:
            logger.info(
                f"✅ Processamento concluído. Arquivos processados: {len(processed_files)}")
        else:
            logger.error("❌ Erro no processamento de materiais")

    except Exception as e:
        logger.error(f"❌ Erro no processamento em background: {e}")


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
            material_ids=request.material_ids,
            config=request.config
        )

        end_time = asyncio.get_event_loop().time()
        response_time = end_time - start_time

        return QueryResponse(
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
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
            persist_dir=chroma_persist_dir
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
    logger.info("🚀 Iniciando servidor RAG na porta 8001...")
    uvicorn.run(
        "rag_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False,  # Não usar reload em produção
        log_level="info"
    )
