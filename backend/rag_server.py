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
from uuid import uuid4
import time

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

# Importar o router corretamente
from chat_agents.educational_agent import router as educational_router

# Incluir router do educational agent
app.include_router(educational_router, prefix="/chat", tags=["educational"])

# Comente ou remova a implementação direta do endpoint
# @app.post("/chat/educational")
# async def educational_chat(request: dict):
#     """Enhanced educational chat with learning features"""
#     logger.info(
#         f"🎓 Educational chat request: {request.get('content', '')[:50]}...")

#     try:
#         # Simulate educational response
#         response_data = {
#             "response": f"Resposta educacional para: {request.get('content', '')}. Este é um sistema de IA educacional focado em treinamento físico e educação esportiva.",
#             "sources": [
#                 {
#                     "title": "Material de Treinamento",
#                     "source": "rag_server.py",
#                     "chunk": "Conteúdo educacional sobre treinamento físico...",
#                     "page": 1
#                 }
#             ],
#             "follow_up_questions": [
#                 "Como posso aplicar esse conhecimento na prática?",
#                 "Quais são os benefícios principais?",
#                 "Existe alguma contraindicação?"
#             ],
#             "learning_suggestions": [
#                 "Considere praticar os exercícios demonstrados",
#                 "Mantenha um diário de treino",
#                 "Consulte um profissional se necessário"
#             ],
#             "related_topics": ["treinamento", "fitness", "saúde"],
#             "educational_metadata": {
#                 "difficulty_level": request.get('user_level', 'intermediate'),
#                 "estimated_reading_time": 2.5,
#                 "complexity_score": 0.6
#             },
#             "learning_context": {
#                 "user_id": "default_user",
#                 "session_id": request.get('session_id') or f"session_{int(time.time())}",
#                 "current_topic": request.get('current_topic') or "treinamento",
#                 "learning_objectives": request.get('learning_objectives', []),
#                 "topics_covered": ["treinamento", "fitness"],
#                 "difficulty_level": request.get('user_level', 'intermediate'),
#                 "preferred_learning_style": request.get('learning_style', 'mixed')
#             },
#             "video_suggestions": [],
#             "response_time": 0.1
#         }

#         return response_data

#     except Exception as e:
#         logger.error(f"❌ Educational chat error: {str(e)}")
#         raise HTTPException(
#             status_code=500, detail=f"Educational chat error: {str(e)}")


@app.get("/chat/session/{session_id}/context")
async def get_session_context(session_id: str):
    """Get learning context for a chat session"""
    logger.info(f"📚 Session context request: {session_id}")

    try:
        return {
            "session_id": session_id,
            "learning_context": {
                "user_id": "default_user",
                "session_id": session_id,
                "current_topic": None,
                "learning_objectives": [],
                "topics_covered": [],
                "difficulty_level": "beginner",
                "preferred_learning_style": "mixed",
                "knowledge_gaps": [],
                "follow_up_questions": []
            },
            "summary": {
                "topics_covered": 0,
                "current_focus": None,
                "difficulty_level": "beginner",
                "objectives_count": 0
            }
        }

    except Exception as e:
        logger.error(f"❌ Session context error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Session context error: {str(e)}")


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


class Question(BaseModel):
    content: str


class Response(BaseModel):
    answer: str
    sources: List[dict]
    response_time: float


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


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


# ========================================
# CHAT ENDPOINTS
# ========================================

@app.post("/chat", response_model=Response)
async def chat(question: Question):
    """Simplified chat endpoint"""
    logger.info(f"💬 Chat request: {question.content[:50]}...")

    if not rag_handler:
        simulated_answer = f"Sistema não inicializado. Esta é uma resposta simulada para: '{question.content}'. Configure uma chave OpenAI válida para funcionalidades completas."
        return Response(
            answer=simulated_answer,
            sources=[{"title": "Sistema de Teste",
                      "source": "rag_server.py", "page": 1, "relevance": 0.9}],
            response_time=0.1
        )

    try:
        response = rag_handler.generate_response(question.content)
        return response
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat-auth", response_model=Response)
async def chat_auth(question: Question):
    """Process a chat question with authentication"""
    logger.info(f"💬 Chat request: {question.content[:50]}...")

    if not rag_handler:
        logger.error("❌ RAG handler not initialized")
        raise HTTPException(status_code=400, detail="System not initialized")

    try:
        response = rag_handler.generate_response(question.content)
        logger.info(
            f"✅ Chat response generated (time: {response.get('response_time', 0):.2f}s)")
        return response
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/agent")
async def chat_agent_stream(request: ChatRequest):
    """Endpoint to stream responses from the chat agent."""
    thread_id = request.thread_id or str(uuid4())
    logger.info(
        f"🤖 Agent chat request on thread {thread_id}: {request.message[:50]}...")

    if not rag_handler:
        logger.error("❌ RAG handler not initialized for agent chat")
        raise HTTPException(
            status_code=400, detail="System not initialized. Cannot use agent.")

    try:
        # For now, return a simple response since we don't have the full agent setup
        response = rag_handler.generate_response(request.message)
        return response
    except Exception as e:
        logger.error(f"❌ Agent chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DNA da Força RAG Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host para o servidor")
    parser.add_argument("--port", type=int, default=8001, help="Porta para o servidor")
    parser.add_argument("--reload", action="store_true", help="Habilitar reload automático")
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Iniciando servidor RAG em {args.host}:{args.port}...")
    uvicorn.run(
        "rag_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
