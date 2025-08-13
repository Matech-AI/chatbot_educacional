#!/usr/bin/env python3
"""
Servidor RAG Independente - DNA da Força AI
Este servidor fica sempre rodando para processamento de materiais e treinamento do modelo.
"""

import os
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, UploadFile, File, Form
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
import zipfile
import tarfile
import tempfile
import aiohttp

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

    # Configurar diretórios (usar variáveis de ambiente se definidas; caso contrário, relativos ao diretório deste arquivo)
    base_dir = Path(__file__).parent
    default_chroma = base_dir / "data" / "chromadb"
    default_materials = base_dir / "data" / "materials"

    env_chroma = os.getenv("CHROMA_PERSIST_DIR")
    env_materials = os.getenv("MATERIALS_DIR")

    chroma_persist_dir = Path(env_chroma) if env_chroma else default_chroma
    materials_dir = Path(env_materials) if env_materials else default_materials

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
                persist_dir=str(chroma_persist_dir),
                materials_dir=str(materials_dir)
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
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS (permitir origem do frontend no Render e locais; também suportar regex e env var)
cors_origins_env = os.getenv(
    "CORS_ORIGINS",
    "https://dna-forca-frontend.onrender.com,http://localhost:3000,http://127.0.0.1:3000",
)
cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
cors_origin_regex = os.getenv(
    "CORS_ORIGIN_REGEX", r"https://.*\\.onrender\\.com$")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(educational_agent_router, prefix="/chat")


# Banner de funcionamento ao iniciar (semelhante ao api_server.py)
@app.on_event("startup")
async def startup_banner():
    try:
        port = int(os.getenv("PORT", "8001"))
    except Exception:
        port = 8001
    logger.info("====================================================")
    logger.info(
        f"🚀 DNA da Força RAG Server v1.0.0 funcionando na porta {port}")
    logger.info("Rotas: GET /health | GET /status | POST /process-materials | POST /reprocess-enhanced-materials | POST /query | /chat/*")
    logger.info("====================================================")


def _apply_config_to_rag_handler(cfg: Dict[str, Any]):
    """Atualiza o RAGHandler com a configuração recebida do frontend, se estiver inicializado."""
    global rag_handler
    if not rag_handler:
        return
    try:
        # Mapear campos do frontend para o RAGConfig
        if 'chunkSize' in cfg and isinstance(cfg['chunkSize'], int):
            rag_handler.config.chunk_size = cfg['chunkSize']
        if 'chunkOverlap' in cfg and isinstance(cfg['chunkOverlap'], int):
            rag_handler.config.chunk_overlap = cfg['chunkOverlap']
        if 'model' in cfg and isinstance(cfg['model'], str):
            rag_handler.config.model_name = cfg['model']
        if 'embeddingModel' in cfg and isinstance(cfg['embeddingModel'], str):
            rag_handler.config.embedding_model = cfg['embeddingModel']
            try:
                # Reinitialize embeddings and vector store to ensure new embedding model is used
                rag_handler._initialize_embeddings()
                rag_handler._initialize_vector_store()
            except Exception as reinit_err:
                logger.warning(
                    f"Falha ao reinicializar embeddings/vector store: {reinit_err}")
        if 'temperature' in cfg:
            try:
                rag_handler.config.temperature = float(cfg['temperature'])
            except Exception:
                pass
        if 'retrievalSearchType' in cfg and isinstance(cfg['retrievalSearchType'], str):
            rag_handler.config.retrieval_search_type = cfg['retrievalSearchType']
        # Reconfigurar retriever após mudanças
        rag_handler._setup_retriever()
    except Exception as e:
        logger.warning(
            f"Não foi possível aplicar configuração ao RAG handler: {e}")


def _get_effective_templates() -> Dict[str, Any]:
    """Retorna templates carregados ou os padrões se vazio."""
    global assistant_configs
    load_assistant_configs()
    if not assistant_configs:
        assistant_configs = get_default_templates()
    return assistant_configs


@app.get("/assistant/config")
async def get_assistant_config_rag():
    """Obter configuração atual do assistente e templates disponíveis."""
    global current_assistant_config
    load_assistant_configs()
    templates = _get_effective_templates()
    # Se não há current, usar primeiro template disponível
    if current_assistant_config is None and templates:
        first_name = next(iter(templates.keys()))
        current_assistant_config = templates[first_name]
    return {
        "status": "success",
        "config": current_assistant_config or {},
        "templates": templates,
    }


@app.post("/assistant/config")
async def update_assistant_config_rag(request: Request):
    """Atualizar configuração do assistente (merge simples) e aplicar no RAG se possível."""
    global current_assistant_config
    payload = await request.json()
    load_assistant_configs()
    if current_assistant_config is None:
        current_assistant_config = {}
    try:
        # Merge raso
        current_assistant_config.update(payload or {})
        _apply_config_to_rag_handler(current_assistant_config)
        save_assistant_configs()
        return {"status": "success", "config": current_assistant_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assistant/templates")
async def get_assistant_templates_rag():
    """Listar templates disponíveis (persistidos + padrão)."""
    templates = _get_effective_templates()
    return {"status": "success", "templates": templates}


@app.post("/assistant/config/template/{template_name}")
async def apply_assistant_template_rag(template_name: str):
    """Aplicar um template existente como configuração atual e refletir no RAG."""
    global current_assistant_config
    templates = _get_effective_templates()
    if template_name not in templates:
        raise HTTPException(status_code=404, detail="Template not found")
    current_assistant_config = templates[template_name]
    _apply_config_to_rag_handler(current_assistant_config)
    save_assistant_configs()
    return {"status": "success", "config": current_assistant_config}


@app.post("/assistant/config/save-template")
async def save_assistant_template_rag(template_name: str, request: Request):
    """Salvar/atualizar um template com o corpo enviado."""
    global assistant_configs
    payload = await request.json()
    load_assistant_configs()
    assistant_configs[template_name] = payload or {}
    save_assistant_configs()
    return {"status": "success", "config": assistant_configs.get(template_name, {})}


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
        raise HTTPException(
            status_code=503, detail="RAG handler not initialized.")

    try:
        logger.info(
            f"🔄 Starting material processing with educational features: {request.enable_educational_features}")

        # Update the handler's config for this task
        rag_handler.config.enable_educational_features = request.enable_educational_features

        background_tasks.add_task(
            rag_handler.process_documents, force_reprocess=request.force_reprocess)

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
        raise HTTPException(
            status_code=503, detail="RAG handler not initialized.")

    try:
        logger.info("🚀 Starting enhanced material reprocessing...")

        # Forçar a ativação de recursos educacionais para este processo
        rag_handler.config.enable_educational_features = True

        # Adicionar a tarefa de reprocessamento em segundo plano
        background_tasks.add_task(
            rag_handler.process_documents, force_reprocess=True)

        return ProcessResponse(
            success=True,
            message="Enhanced material reprocessing started in the background."
        )
    except Exception as e:
        logger.error(f"❌ Error starting enhanced reprocessing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# MATERIALS MANAGEMENT (RAG-SIDE)
# ========================================

@app.get("/materials/list")
async def list_rag_materials():
    """Listar materiais que o servidor RAG enxerga (debug)."""
    try:
        root = Path(materials_dir)
        root.mkdir(parents=True, exist_ok=True)
        files = []
        for p in root.rglob("*"):
            if p.is_file():
                files.append(str(p.relative_to(root)))
        return {
            "root": str(root),
            "count": len(files),
            "files": files[:200],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/materials/upload-archive")
async def upload_materials_archive_rag(
    archive: UploadFile = File(...),
    destination_subdir: Optional[str] = Form(None),
):
    """Enviar um .zip ou .tar.gz com materiais diretamente para o RAG e extrair em MATERIALS_DIR."""
    try:
        root = Path(materials_dir)
        root.mkdir(parents=True, exist_ok=True)

        # Salvar temporariamente
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_path = tmp_dir / archive.filename
        content = await archive.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty archive")
        tmp_path.write_bytes(content)

        # Destino final
        dest_dir = root / destination_subdir if destination_subdir else root
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Extrair
        name_lower = archive.filename.lower()
        extracted_files = []
        if name_lower.endswith(".zip"):
            with zipfile.ZipFile(tmp_path, 'r') as zf:
                zf.extractall(dest_dir)
                extracted_files = zf.namelist()
        elif name_lower.endswith(".tar.gz") or name_lower.endswith(".tgz"):
            with tarfile.open(tmp_path, 'r:gz') as tf:
                tf.extractall(dest_dir)
                extracted_files = [
                    m.name for m in tf.getmembers() if m.isfile()]
        else:
            raise HTTPException(
                status_code=400, detail="Unsupported archive format. Use .zip or .tar.gz")

        # Limpeza
        try:
            tmp_path.unlink(missing_ok=True)  # type: ignore
            tmp_dir.rmdir()
        except Exception:
            pass

        return {
            "status": "success",
            "message": "Archive extracted to RAG materials",
            "destination": str(dest_dir),
            "files_count": len(extracted_files),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/materials/sync-from-api")
async def sync_materials_from_api(api_base_url: str = Form(...), token: Optional[str] = Form(None)):
    """Baixa materials.tar.gz do API e extrai em MATERIALS_DIR (server-to-server)."""
    try:
        root = Path(materials_dir)
        root.mkdir(parents=True, exist_ok=True)

        archive_url = f"{api_base_url.rstrip('/')}/materials/archive"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with aiohttp.ClientSession() as session:
            async with session.get(archive_url, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise HTTPException(
                        status_code=resp.status, detail=f"API error: {text}")
                content = await resp.read()

        # Salvar temporário e extrair
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_path = tmp_dir / "materials.tar.gz"
        tmp_path.write_bytes(content)

        with tarfile.open(tmp_path, 'r:gz') as tf:
            tf.extractall(root)

        try:
            tmp_path.unlink(missing_ok=True)  # type: ignore
            tmp_dir.rmdir()
        except Exception:
            pass

        return {"status": "success", "message": "Materials synced from API"}
    except HTTPException:
        raise
    except Exception as e:
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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DNA da Força RAG Server")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host para o servidor")
    # Permitir que o Render defina a PORT
    default_port = int(os.getenv("PORT", "8001"))
    parser.add_argument("--port", type=int, default=default_port,
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
