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
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from dotenv import load_dotenv
from uuid import uuid4
import time
import json

# Importar componentes RAG
from rag_system.rag_handler import RAGHandler, RAGConfig, Source
import chromadb
from chromadb.config import Settings
from chat_agents.educational_agent import router as educational_agent_router
# ========================================
# MODELS PYDANTIC
# ========================================


class Question(BaseModel):
    content: str


class Response(BaseModel):
    answer: str
    sources: List[dict]
    response_time: float


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


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


class AssistantConfigRequest(BaseModel):
    prompt: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    temperature: Optional[float] = None
    title: Optional[str] = None


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

# Sistema de persistência para configurações do assistente
assistant_configs_file = Path("data/assistant_configs.json")
assistant_configs = {}
current_assistant_config = None


def load_assistant_configs():
    """Carregar configurações do assistente do arquivo"""
    global assistant_configs, current_assistant_config

    if assistant_configs_file.exists():
        try:
            with open(assistant_configs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assistant_configs = data.get('configs', {})
                current_assistant_config = data.get('current', None)
                logger.info(
                    f"✅ Configurações do assistente carregadas: {len(assistant_configs)} templates")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar configurações: {e}")
            assistant_configs = {}
            current_assistant_config = None


def save_assistant_configs():
    """Salvar configurações do assistente no arquivo"""
    global assistant_configs, current_assistant_config

    try:
        # Criar diretório se não existir
        assistant_configs_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'configs': assistant_configs,
            'current': current_assistant_config,
            'last_updated': time.time()
        }

        with open(assistant_configs_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"✅ Configurações do assistente salvas: {len(assistant_configs)} templates")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar configurações: {e}")


def get_default_templates():
    """Retornar templates padrão"""
    return {
        "Educação Física": {
            "name": "Assistente Educacional de Educação Física",
            "description": "Especializado em responder dúvidas sobre treinamento, fisiologia do exercício e metodologia do ensino",
            "prompt": """Você é um ASSISTENTE EDUCACIONAL especializado em EDUCAÇÃO FÍSICA. Seu objetivo é auxiliar estudantes a compreender conceitos de treinamento, fisiologia do exercício, biomecânica e metodologia do ensino. Siga estas diretrizes:

1. CONTEXTO DO CURSO:
   - Basear suas respostas exclusivamente nos materiais do curso fornecidos
   - Citar a fonte específica (aula, página, vídeo) de onde a informação foi extraída
   - Nunca inventar informações que não estejam nos materiais do curso

2. ESTILO DE RESPOSTA:
   - Usar linguagem clara, técnica mas acessível
   - Relacionar teoria com aplicação prática no treinamento
   - Fornecer exemplos de exercícios e progressões quando apropriado
   - Explicar os princípios fisiológicos por trás dos conceitos

3. CITAÇÕES E FONTES:
   - Sempre indicar a origem da informação (ex: "Conforme a Aula 3, página 7...")
   - Para citações diretas, usar aspas e referenciar a fonte exata
   - Se a pergunta não puder ser respondida com os materiais disponíveis, informar isto claramente

4. ESTRATÉGIAS PEDAGÓGICAS:
   - Conectar conceitos teóricos com aplicações práticas no treinamento
   - Usar analogias relacionadas ao movimento humano
   - Incentivar análise crítica de métodos de treinamento
   - Sugerir progressões e adaptações para diferentes níveis

Use {context}, {chat_history} e {question} como variáveis no template.""",
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "chunkSize": 2000,
            "chunkOverlap": 100,
            "retrievalSearchType": "mmr",
            "embeddingModel": "text-embedding-ada-002"
        },
        "Nutrição Esportiva": {
            "name": "Assistente Educacional de Nutrição Esportiva",
            "description": "Especializado em nutrição aplicada ao esporte, suplementação e estratégias alimentares para performance",
            "prompt": """Você é um ASSISTENTE EDUCACIONAL especializado em NUTRIÇÃO ESPORTIVA. Seu objetivo é auxiliar estudantes a compreender conceitos de nutrição aplicada ao esporte, metabolismo energético, suplementação e estratégias alimentares. Siga estas diretrizes:

1. CONTEXTO DO CURSO:
   - Basear suas respostas exclusivamente nos materiais do curso fornecidos
   - Citar a fonte específica (aula, página, vídeo) de onde a informação foi extraída
   - Nunca inventar informações que não estejam nos materiais do curso

2. ESTILO DE RESPOSTA:
   - Usar linguagem científica mas didática
   - Relacionar conceitos nutricionais com performance esportiva
   - Fornecer exemplos práticos de aplicação nutricional
   - Explicar os mecanismos bioquímicos quando relevante

3. CITAÇÕES E FONTES:
   - Sempre indicar a origem da informação (ex: "Conforme a Aula 5, página 12...")
   - Para citações diretas, usar aspas e referenciar a fonte exata
   - Se a pergunta não puder ser respondida com os materiais disponíveis, informar isto claramente

4. ESTRATÉGIAS PEDAGÓGICAS:
   - Conectar bioquímica nutricional com aplicações práticas
   - Usar exemplos de diferentes modalidades esportivas
   - Incentivar análise crítica de estratégias nutricionais
   - Sugerir adequações nutricionais para diferentes objetivos

Use {context}, {chat_history} e {question} como variáveis no template.""",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "chunkSize": 2200,
            "chunkOverlap": 150,
            "retrievalSearchType": "mmr",
            "embeddingModel": "text-embedding-ada-002"
        },
        "Anatomia Humana": {
            "name": "Assistente Educacional de Anatomia Humana",
            "description": "Especializado em anatomia sistêmica, cinesiologia e biomecânica do movimento humano",
            "prompt": """Você é um ASSISTENTE EDUCACIONAL especializado em ANATOMIA HUMANA. Seu objetivo é auxiliar estudantes a compreender a estrutura do corpo humano, cinesiologia e biomecânica do movimento. Siga estas diretrizes:

1. CONTEXTO DO CURSO:
   - Basear suas respostas exclusivamente nos materiais do curso fornecidos
   - Citar a fonte específica (aula, página, atlas, vídeo) de onde a informação foi extraída
   - Nunca inventar informações que não estejam nos materiais do curso

2. ESTILO DE RESPOSTA:
   - Usar terminologia anatômica precisa e correta
   - Relacionar estrutura anatômica com função
   - Fornecer exemplos de movimentos e posições
   - Explicar a biomecânica quando relevante

3. CITAÇÕES E FONTES:
   - Sempre indicar a origem da informação (ex: "Conforme o Atlas de Anatomia, página 45...")
   - Para citações diretas, usar aspas e referenciar a fonte exata
   - Se a pergunta não puder ser respondida com os materiais disponíveis, informar isto claramente

4. ESTRATÉGIAS PEDAGÓGICAS:
   - Conectar anatomia com movimento e função
   - Usar exemplos práticos de palpação e identificação
   - Incentivar análise crítica de estruturas anatômicas
   - Sugerir exercícios de memorização e identificação

Use {context}, {chat_history} e {question} como variáveis no template.""",
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "chunkSize": 2000,
            "chunkOverlap": 100,
            "retrievalSearchType": "mmr",
            "embeddingModel": "text-embedding-ada-002"
        }
    }


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

    # Carregar configurações do assistente
    load_assistant_configs()

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
    # Salvar configurações do assistente ao encerrar
    save_assistant_configs()

# Inicializar FastAPI
app = FastAPI(
    title="DNA da Força RAG Server",
    description="Servidor RAG para processamento de materiais e treinamento de modelos",
    version="1.7.0",
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

app.include_router(educational_agent_router, prefix="/chat")

@app.get("/health")
async def health_check():
    """Verificar saúde do servidor RAG"""
    return {
        "status": "healthy",
        "service": "rag-server",
        "version": "1.7.0",
        "rag_initialized": rag_handler is not None
    }


@app.get("/status")
async def get_status():
    """Obter status detalhado do servidor RAG"""
    global rag_handler

    status = {
        "service": "rag-server",
        "version": "1.7.0",
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


@app.post("/chat/explore-topic")
async def explore_topic(request: dict):
    """Explore a topic with the educational agent"""
    try:
        topic = request.get("topic")
        user_level = request.get("user_level", "intermediate")
        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required")

        from chat_agents.educational_agent import get_educational_agent
        agent = get_educational_agent()

        if not agent.rag_handler:
            raise HTTPException(
                status_code=503, detail="RAG handler not initialized in Educational Agent.")

        # This would ideally be a more sophisticated method in the agent
        # For now, we can simulate a response or use a simple RAG query
        response = agent.rag_handler.generate_response(
            question=f"Explique o tópico '{topic}' para um aluno de nível {user_level}.",
            user_level=user_level
        )
        return response

    except Exception as e:
        logger.error(f"❌ Error exploring topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/learning-path/{topic}")
async def get_learning_path(topic: str, user_level: str = "intermediate"):
    """Get a learning path for a topic"""
    try:
        from chat_agents.educational_agent import get_educational_agent
        agent = get_educational_agent()

        # This would ideally be a more sophisticated method in the agent
        # For now, we can simulate a response or use a simple RAG query
        learning_path = [
            {"step": 1, "title": f"Fundamentos de {topic}",
                "description": "Conceitos básicos e terminologia"},
            {"step": 2, "title": f"Aplicação prática de {topic}",
                "description": "Como aplicar na prática"},
            {"step": 3, "title": f"Progressão em {topic}",
                "description": "Níveis avançados e variações"},
            {"step": 4, "title": f"Troubleshooting {topic}",
                "description": "Solucionando problemas comuns"}
        ]

        return {
            "topic": topic,
            "user_level": user_level,
            "learning_path": learning_path,
            "estimated_time": "2-4 semanas",
            "prerequisites": [],
            "resources_available": True
        }

    except Exception as e:
        logger.error(f"❌ Error getting learning path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
