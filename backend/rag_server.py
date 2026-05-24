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
from datetime import datetime

# Importar componentes RAG
from rag_system.rag_handler import RAGHandler, RAGConfig, Source
import chromadb
from chromadb.config import Settings
from chat_agents.educational_agent import router as educational_agent_router
from config.render_config import is_render_environment, get_chromadb_path, get_materials_path
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


class ReprocessRequest(BaseModel):
    training_dirs: Optional[List[str]] = None  # subfolder names inside materials dir


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


class CompressLocalRequest(BaseModel):
    source_path: str = ".chromadb"
    output_filename: Optional[str] = None


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
   - Padrão DNA-only: basear suas respostas exclusivamente nos materiais do DNA da Força quando disponíveis
   - Citar no formato: "Módulo X, Aula Y — 'Título' (PDF), p. N" (não inventar página; omitir quando não existir metadado)
   - Nunca exibir caminhos de arquivos nem códigos internos (ex.: M13A52)
   - Nunca inventar informações que não estejam nos materiais do curso

2. ESTILO DE RESPOSTA:
   - Usar linguagem clara, técnica mas acessível
   - Relacionar teoria com aplicação prática no treinamento
   - Fornecer exemplos de exercícios e progressões quando apropriado
   - Explicar os princípios fisiológicos por trás dos conceitos

3. CITAÇÕES E FONTES:
   - Sempre indicar a origem no formato DNA e usar aspas para citações diretas
   - Se a pergunta não puder ser respondida com os materiais disponíveis, informar isto explicitamente e, se útil, adicionar bloco "Informação complementar (fora do acervo)"

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
            "embeddingModel": "text-embedding-3-large"
        },
        "Nutrição Esportiva": {
            "name": "Assistente Educacional de Nutrição Esportiva",
            "description": "Especializado em nutrição aplicada ao esporte, suplementação e estratégias alimentares para performance",
            "prompt": """Você é um ASSISTENTE EDUCACIONAL especializado em NUTRIÇÃO ESPORTIVA. Seu objetivo é auxiliar estudantes a compreender conceitos de nutrição aplicada ao esporte, metabolismo energético, suplementação e estratégias alimentares. Siga estas diretrizes:

1. CONTEXTO DO CURSO:
   - Padrão DNA-only
   - Citar no formato DNA (página apenas com metadado real)
   - Nunca exibir caminhos de arquivos nem códigos internos

2. ESTILO DE RESPOSTA:
   - Usar linguagem científica mas didática
   - Relacionar conceitos nutricionais com performance esportiva
   - Fornecer exemplos práticos de aplicação nutricional
   - Explicar os mecanismos bioquímicos quando relevante

3. CITAÇÕES E FONTES:
   - Sempre indicar a origem no formato DNA e usar aspas para citações diretas
   - Se a pergunta não puder ser respondida com os materiais disponíveis, informar explicitamente e, se útil, adicionar "Informação complementar (fora do acervo)"

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
            "embeddingModel": "text-embedding-3-large"
        },
        "Anatomia Humana": {
            "name": "Assistente Educacional de Anatomia Humana",
            "description": "Especializado em anatomia sistêmica, cinesiologia e biomecânica do movimento humano",
            "prompt": """Você é um ASSISTENTE EDUCACIONAL especializado em ANATOMIA HUMANA. Seu objetivo é auxiliar estudantes a compreender a estrutura do corpo humano, cinesiologia e biomecânica do movimento. Siga estas diretrizes:

1. CONTEXTO DO CURSO:
   - Padrão DNA-only
   - Citar no formato DNA (página apenas com metadado real)
   - Nunca exibir caminhos de arquivos nem códigos internos

2. ESTILO DE RESPOSTA:
   - Usar terminologia anatômica precisa e correta
   - Relacionar estrutura anatômica com função
   - Fornecer exemplos de movimentos e posições
   - Explicar a biomecânica quando relevante

3. CITAÇÕES E FONTES:
   - Sempre indicar a origem no formato DNA e usar aspas para citações diretas
   - Se a pergunta não puder ser respondida com os materiais disponíveis, informar explicitamente e, se útil, adicionar "Informação complementar (fora do acervo)"

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
            "embeddingModel": "text-embedding-3-large"
        }
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager para inicializar e limpar recursos"""
    global rag_handler, chroma_persist_dir, materials_dir

    logger.info("🚀 Iniciando servidor RAG...")

    # Configurar diretórios (usar variáveis de ambiente se definidas; caso contrário, relativos ao diretório deste arquivo)
    base_dir = Path(__file__).parent

    # 🎯 CORREÇÃO: CAMINHOS DINÂMICOS para Render vs Local
    # Detectar se está rodando no Render ou localmente
    is_render = (
        os.getenv("RENDER") or
        os.getenv("RENDER_ENVIRONMENT") or
        "onrender.com" in str(base_dir).lower() or
        "app" in str(base_dir).lower() or
        "\\app\\" in str(base_dir) or
        "/app/" in str(base_dir)
    )

    if is_render:
        # 🚀 RENDER: app/data (sem .chromadb automático) e app/data/materials
        default_chroma = None  # Não criar .chromadb automaticamente
        default_materials = base_dir / "data" / "materials"
        logger.info("🌐 Ambiente detectado: RENDER")
    else:
        # 💻 LOCAL: backend/data/.chromadb e backend/data/materials
        default_chroma = base_dir / "data" / ".chromadb"
        default_materials = base_dir / "data" / "materials"
        logger.info("💻 Ambiente detectado: LOCAL")

    # 🚨 CORREÇÃO CRÍTICA: Garantir que os caminhos sejam absolutos e corretos
    logger.info(f"🔍 Caminhos base:")
    logger.info(f"   - Base dir: {base_dir}")
    logger.info(f"   - Ambiente: {'RENDER' if is_render else 'LOCAL'}")
    logger.info(f"   - Default ChromaDB: {default_chroma}")
    logger.info(f"   - Default Materials: {default_materials}")
    logger.info(f"   - Base dir exists: {base_dir.exists()}")
    logger.info(f"   - Data dir exists: {(base_dir / 'data').exists()}")

    # Verificar ChromaDB apenas se existir
    if default_chroma:
        logger.info(f"   - ChromaDB dir exists: {default_chroma.exists()}")
        logger.info(f"   - ChromaDB path resolved: {default_chroma.resolve()}")
    else:
        logger.info(f"   - ChromaDB: Não configurado (ambiente RENDER)")

    logger.info(f"   - Materials dir exists: {default_materials.exists()}")
    logger.info(f"   - Materials path resolved: {default_materials.resolve()}")

    # 🚨 VERIFICAÇÃO ADICIONAL: Usar configuração do Render
    if is_render_environment():
        logger.info("🚨 Configuração do Render detectada:")
        logger.info("   - Auto-create ChromaDB: False")
        logger.info("   - ChromaDB será criado apenas via upload")
        logger.info("   - Diretório /app/data será mantido limpo")

    env_chroma = os.getenv("CHROMA_PERSIST_DIR")
    env_materials = os.getenv("MATERIALS_DIR")

    # 🎯 CORREÇÃO: Não criar .chromadb automaticamente no Render
    if env_chroma:
        chroma_persist_dir = Path(env_chroma)
    elif default_chroma:
        chroma_persist_dir = default_chroma
    else:
        chroma_persist_dir = None  # Render: deixar None até ser necessário

    materials_dir = Path(env_materials) if env_materials else default_materials

    # Criar diretórios se não existirem (apenas estrutura básica, sem .chromadb)
    materials_dir.mkdir(parents=True, exist_ok=True)
    Path("/app/logs").mkdir(parents=True, exist_ok=True)

    # 🚨 IMPORTANTE: NÃO criar .chromadb automaticamente no Render
    if chroma_persist_dir and not str(chroma_persist_dir).endswith('.chromadb'):
        # Verificar se estamos no Render
        is_render = os.getenv("RENDER", "").lower() == "true"
        if not is_render:
            chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        else:
            logger.info(
                "🚨 Render detectado - NÃO criando diretório .chromadb automaticamente")
            logger.info(
                "💡 Use a interface para fazer upload de um arquivo .chromadb existente")

    # 🎯 VERIFICAÇÃO: Garantir que o caminho está correto
    logger.info(f"🔍 Verificando caminhos:")
    logger.info(f"   - Base dir: {base_dir}")
    logger.info(f"   - ChromaDB path: {chroma_persist_dir}")
    if chroma_persist_dir:
        logger.info(f"   - ChromaDB exists: {chroma_persist_dir.exists()}")
        logger.info(f"   - ChromaDB is_dir: {chroma_persist_dir.is_dir()}")
    else:
        logger.info(
            f"   - ChromaDB: Não configurado (será criado quando necessário)")

    # Carregar configurações do assistente
    load_assistant_configs()

    logger.info(f"📁 Diretórios configurados:")
    logger.info(f"   - ChromaDB: {chroma_persist_dir}")
    logger.info(f"   - Materiais: {materials_dir}")

    # Verificar integridade do ChromaDB existente (se houver)
    if chroma_persist_dir:
        chromadb_status = check_chromadb_integrity(chroma_persist_dir)
        logger.info(f"🔍 Status do ChromaDB: {chromadb_status['reason']}")

        if chromadb_status['valid']:
            logger.info(
                f"✅ ChromaDB válido encontrado com {chromadb_status['total_documents']} documentos")
            for col_info in chromadb_status['collections']:
                logger.info(
                    f"   - Coleção '{col_info['name']}': {col_info['count']} documentos")
        else:
            logger.info(
                f"ℹ️ ChromaDB não encontrado ou vazio: {chromadb_status['reason']}")
            logger.info(
                f"💡 Use a interface para fazer upload de um arquivo .chromadb existente")
    else:
        logger.info(
            f"ℹ️ ChromaDB não configurado - será criado quando necessário")
        chromadb_status = {"valid": False,
                           "reason": "Not configured", "collections": []}

    # 🎯 CORREÇÃO: Inicializar RAG handler com NVIDIA_API_KEY (prioridade) ou OPENAI_API_KEY
    nvidia_api_key = os.getenv("NVIDIA_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # 🚨 IMPORTANTE: Só inicializar RAG handler se chroma_persist_dir estiver configurado
    if not chroma_persist_dir:
        logger.info(
            "💡 ChromaDB não configurado - RAG handler será inicializado quando necessário")
        logger.info("💡 Use a rota /initialize para configurar manualmente")
    else:
        # Tentar inicializar com múltiplas APIs se disponíveis
        if nvidia_api_key and nvidia_api_key != "your_nvidia_api_key_here" and openai_api_key and openai_api_key != "your_openai_api_key_here":
            try:
                logger.info("🚀 Inicializando RAG handler com OpenAI e NVIDIA API...")
                rag_handler = RAGHandler(
                    api_key=openai_api_key,
                    nvidia_api_key=nvidia_api_key,
                    persist_dir=str(chroma_persist_dir),
                    materials_dir=str(materials_dir)
                )
                logger.info("✅ RAG handler inicializado com OpenAI + NVIDIA API")
            except Exception as e:
                logger.warning(f"⚠️  Falha ao inicializar com OpenAI + NVIDIA: {e}")
                # Fallback para apenas OpenAI
                try:
                    logger.info("🔄 Fallback: Inicializando apenas com OpenAI...")
                    rag_handler = RAGHandler(
                        api_key=openai_api_key,
                        persist_dir=str(chroma_persist_dir),
                        materials_dir=str(materials_dir)
                    )
                    logger.info("✅ RAG handler inicializado com OpenAI")
                except Exception as e2:
                    logger.error(f"❌ Falha ao inicializar com OpenAI: {e2}")
        elif openai_api_key and openai_api_key != "your_openai_api_key_here":
            try:
                logger.info("🔧 Inicializando RAG handler com OpenAI API...")
                rag_handler = RAGHandler(
                    api_key=openai_api_key,
                    persist_dir=str(chroma_persist_dir),
                    materials_dir=str(materials_dir)
                )

                # Verificar se o RAG handler carregou dados existentes
                if rag_handler.vector_store:
                    try:
                        current_count = rag_handler.vector_store._collection.count()
                        if current_count > 0:
                            logger.info(
                                f"✅ RAG handler carregou automaticamente {current_count} documentos do ChromaDB existente")
                            logger.info(
                                f"📚 Coleção ativa: '{rag_handler.config.collection_name}'")
                        else:
                            logger.info(
                                "📝 RAG handler inicializado com ChromaDB vazio - pronto para receber novos materiais")
                    except Exception as e:
                        logger.warning(
                            f"⚠️  Não foi possível verificar contagem de documentos: {e}")

                logger.info("✅ RAG handler inicializado com OpenAI")
            except Exception as e:
                logger.warning(f"⚠️  Falha ao inicializar com OpenAI: {e}")
                logger.info(
                    "💡 Use a rota /initialize para inicializar manualmente")
        else:
            logger.info(
                "💡 Nenhuma API key configurada. Use a rota /initialize para inicializar o RAG handler")

    logger.info("✅ Servidor RAG iniciado com sucesso")

    # Exibir banner de funcionamento
    startup_banner()

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
    "https://iadnadaforca.com.br,https://www.iadnadaforca.com.br,http://localhost:3000,http://127.0.0.1:3000",
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


# Banner de funcionamento ao iniciar (movido para dentro do lifespan)
def startup_banner():
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


@app.get("/materials/subfolders")
async def list_materials_subfolders():
    """List immediate subfolders inside the materials directory."""
    global rag_handler
    materials_dir = rag_handler.materials_dir if rag_handler else Path(
        os.getenv("MATERIALS_DIR", "data/materials"))
    try:
        subfolders = sorted([
            {"name": d.name, "file_count": sum(1 for f in d.rglob("*") if f.is_file())}
            for d in Path(materials_dir).iterdir()
            if d.is_dir()
        ], key=lambda x: x["name"])
        return {"subfolders": subfolders, "materials_dir": str(materials_dir)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reprocess-enhanced-materials", response_model=ProcessResponse)
async def reprocess_enhanced_materials(
    background_tasks: BackgroundTasks,
    request: ReprocessRequest = ReprocessRequest()
):
    """
    Reprocess materials using the enhanced RAG system.
    Accepts optional list of subfolder names to restrict training scope.
    """
    global rag_handler
    if not rag_handler:
        raise HTTPException(status_code=503, detail="RAG handler not initialized.")

    try:
        logger.info("🚀 Starting enhanced material reprocessing...")

        # Update training dirs if specified
        if request.training_dirs:
            rag_handler.training_dirs = [
                rag_handler.materials_dir / d for d in request.training_dirs
            ]
            logger.info(f"🎯 Training restricted to: {request.training_dirs}")
        else:
            rag_handler.training_dirs = [rag_handler.materials_dir]
            logger.info("📂 Training on full materials directory")

        rag_handler.config.enable_educational_features = True

        background_tasks.add_task(rag_handler.process_documents, force_reprocess=True)
        logger.info("✅ Background task added successfully")

        dirs_label = ", ".join(request.training_dirs) if request.training_dirs else "todos os materiais"
        return ProcessResponse(
            success=True,
            message=f"Reprocessamento iniciado em background para: {dirs_label}."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting enhanced reprocessing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


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
    global rag_handler, chroma_persist_dir

    try:
        logger.info("🔧 Inicializando RAG handler...")

        # 🚨 CORREÇÃO: Verificar se chroma_persist_dir está configurado
        if not chroma_persist_dir:
            # No Render, NÃO definir caminho padrão automaticamente
            is_render = os.getenv("RENDER", "").lower() == "true"
            if is_render:
                # 🚨 IMPORTANTE: NÃO criar .chromadb automaticamente no Render
                logger.info(
                    "🚨 Render detectado - NÃO criando .chromadb automaticamente")
                logger.info(
                    "💡 Use a interface para fazer upload de um arquivo .chromadb existente")
                logger.info("💡 Ou configure CHROMA_PERSIST_DIR manualmente")

                # Verificar se o diretório /app/data existe (apenas para logs)
                data_dir = Path("/app/data")
                if not data_dir.exists():
                    logger.info(
                        "ℹ️ Diretório /app/data não existe - será criado apenas quando necessário")
                else:
                    logger.info(f"ℹ️ Diretório /app/data existe: {data_dir}")
                    # Listar conteúdo para debug
                    try:
                        contents = list(data_dir.iterdir())
                        logger.info(
                            f"📁 Conteúdo de /app/data: {[item.name for item in contents]}")
                    except Exception as e:
                        logger.warning(
                            f"⚠️ Não foi possível listar conteúdo de /app/data: {e}")

                # NÃO definir chroma_persist_dir automaticamente
                raise HTTPException(
                    status_code=400,
                    detail="ChromaDB não configurado no Render. Faça upload de um arquivo .chromadb existente ou configure CHROMA_PERSIST_DIR manualmente."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="ChromaDB não configurado. Configure CHROMA_PERSIST_DIR ou use a rota /initialize"
                )

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


@app.post("/chromadb/upload")
async def upload_chromadb_archive(
    archive: UploadFile = File(...),
    replace_existing: bool = Form(True)
):
    """Upload e substituição do banco ChromaDB treinado."""
    global rag_handler, chroma_persist_dir

    try:
        # Validar parâmetros
        logger.info(
            f"🔍 Parâmetros recebidos: replace_existing={replace_existing}")
        if not isinstance(replace_existing, bool):
            logger.error(
                f"❌ Parâmetro replace_existing inválido: {replace_existing}")
            raise HTTPException(
                status_code=400,
                detail="Parâmetro replace_existing deve ser um booleano"
            )
        # 🚨 CORREÇÃO: Verificar se chroma_persist_dir está configurado
        if not chroma_persist_dir:
            # No Render, NÃO definir caminho padrão automaticamente
            is_render = os.getenv("RENDER", "").lower() == "true"
            if is_render:
                # 🚨 IMPORTANTE: NÃO criar .chromadb automaticamente no Render
                logger.info(
                    "🚨 Render detectado - NÃO criando .chromadb automaticamente")
                logger.info(
                    "💡 Use a interface para fazer upload de um arquivo .chromadb existente")
                logger.info("💡 Ou configure CHROMA_PERSIST_DIR manualmente")

                # Verificar se o diretório /app/data existe (apenas para logs)
                data_dir = Path("/app/data")
                if not data_dir.exists():
                    logger.info(
                        "ℹ️ Diretório /app/data não existe - será criado apenas quando necessário")
                else:
                    logger.info(f"ℹ️ Diretório /app/data existe: {data_dir}")
                    # Listar conteúdo para debug
                    try:
                        contents = list(data_dir.iterdir())
                        logger.info(
                            f"📁 Conteúdo de /app/data: {[item.name for item in contents]}")
                    except Exception as e:
                        logger.warning(
                            f"⚠️ Não foi possível listar conteúdo de /app/data: {e}")

                # NÃO definir chroma_persist_dir automaticamente
                raise HTTPException(
                    status_code=400,
                    detail="ChromaDB não configurado no Render. Faça upload de um arquivo .chromadb existente ou configure CHROMA_PERSIST_DIR manualmente."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="ChromaDB não configurado. Configure CHROMA_PERSIST_DIR ou use a rota /initialize"
                )

        # Verificar se o arquivo é um .tar.gz válido
        logger.info(f"🔍 Validando arquivo: {archive.filename}")
        if not archive.filename:
            logger.error("❌ Nome do arquivo não fornecido")
            raise HTTPException(
                status_code=400,
                detail="Nome do arquivo não fornecido"
            )

        if not archive.filename.lower().endswith(('.tar.gz', '.tgz')):
            logger.error(f"❌ Formato de arquivo inválido: {archive.filename}")
            raise HTTPException(
                status_code=400,
                detail="Arquivo deve ser .tar.gz contendo o diretório .chromadb"
            )

        # Ler o conteúdo do arquivo
        logger.info("📖 Lendo conteúdo do arquivo...")
        content = await archive.read()
        if len(content) == 0:
            logger.error("❌ Arquivo vazio")
            raise HTTPException(status_code=400, detail="Arquivo vazio")

        logger.info(f"✅ Arquivo lido com sucesso: {len(content)} bytes")

        # Backup do ChromaDB atual se existir
        chroma_path = Path(chroma_persist_dir)
        backup_path = None

        if chroma_path.exists() and replace_existing:
            backup_path = chroma_path.parent / \
                f".chromadb_backup_{int(time.time())}"
            logger.info(
                f"📦 Fazendo backup do ChromaDB atual para {backup_path}")
            import shutil
            shutil.move(str(chroma_path), str(backup_path))

        # Criar diretório temporário para extração
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_archive = tmp_dir / archive.filename
        tmp_archive.write_bytes(content)

        # Extrair o arquivo
        logger.info(f"📂 Extraindo ChromaDB para {chroma_path}")
        # 🚨 CORREÇÃO: NÃO criar diretório automaticamente no Render
        is_render = os.getenv("RENDER", "").lower() == "true"
        if not is_render:
            chroma_path.mkdir(parents=True, exist_ok=True)
        else:
            logger.info(
                "🚨 Render detectado - NÃO criando diretório .chromadb automaticamente")
            logger.info(
                "💡 Use a interface para fazer upload de um arquivo .chromadb existente")
            # Verificar se o diretório pai existe e criar apenas se necessário
            parent_dir = chroma_path.parent
            if not parent_dir.exists():
                logger.info(f"📁 Criando diretório pai: {parent_dir}")
                parent_dir.mkdir(parents=True, exist_ok=True)
            else:
                logger.info(f"📁 Diretório pai já existe: {parent_dir}")

        # Validar se o arquivo é um tar.gz válido
        logger.info("🔍 Validando arquivo tar.gz...")
        try:
            with tarfile.open(tmp_archive, 'r:gz') as tf:
                logger.info(
                    f"✅ Arquivo tar.gz válido, {len(tf.getmembers())} membros encontrados")
                tf.extractall(chroma_path)
                logger.info("✅ Arquivo extraído com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao extrair arquivo tar.gz: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo tar.gz inválido ou corrompido: {str(e)}"
            )

        # Limpeza do arquivo temporário
        try:
            tmp_archive.unlink(missing_ok=True)
            tmp_dir.rmdir()
        except Exception:
            pass

        # Verificar integridade do ChromaDB carregado
        logger.info("🔍 Iniciando verificação de integridade do ChromaDB...")

        # Verificar se os arquivos foram extraídos corretamente
        if chroma_path.exists():
            extracted_files = list(chroma_path.rglob("*"))
            logger.info(f"📁 Arquivos extraídos: {len(extracted_files)}")
            # Mostrar apenas os primeiros 5
            for file_path in extracted_files[:5]:
                logger.info(f"   - {file_path.relative_to(chroma_path)}")
            if len(extracted_files) > 5:
                logger.info(
                    f"   ... e mais {len(extracted_files) - 5} arquivos")
        else:
            logger.error("❌ Diretório ChromaDB não foi criado após extração")
            raise HTTPException(
                status_code=400,
                detail="Falha na criação do diretório ChromaDB"
            )

        # Aguardar um pouco para garantir que os arquivos estejam completamente escritos
        import time
        logger.info(
            "⏳ Aguardando 2 segundos para estabilização dos arquivos...")
        time.sleep(2)

        integrity_check = check_chromadb_integrity(chroma_path)
        logger.info(f"🔍 Resultado da verificação: {integrity_check}")

        if not integrity_check["valid"]:
            # Restaurar backup se a verificação falhar
            if backup_path and backup_path.exists():
                logger.error(f"❌ ChromaDB inválido, restaurando backup")
                if chroma_path.exists():
                    import shutil
                    shutil.rmtree(chroma_path)
                shutil.move(str(backup_path), str(chroma_path))

            raise HTTPException(
                status_code=400,
                detail=f"ChromaDB inválido: {integrity_check['reason']}"
            )

        # Reinicializar o RAG handler se estiver ativo
        if rag_handler:
            logger.info("🔄 Reinicializando RAG handler com novo ChromaDB")
            try:
                old_api_key = rag_handler.config.api_key
                rag_handler = RAGHandler(
                    api_key=old_api_key,
                    persist_dir=str(chroma_path)
                )
                logger.info("✅ RAG handler reinicializado com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao reinicializar RAG handler: {e}")

        # Remover backup se tudo deu certo
        if backup_path and backup_path.exists():
            import shutil
            shutil.rmtree(backup_path)
            logger.info("🗑️ Backup removido após sucesso")

        return {
            "status": "success",
            "message": "ChromaDB carregado com sucesso",
            "collections": integrity_check.get("collections", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no upload do ChromaDB: {e}")
        import traceback
        logger.error(f"📋 Traceback completo: {traceback.format_exc()}")

        # Informações adicionais para debug
        debug_info = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "chroma_persist_dir": str(chroma_persist_dir) if chroma_persist_dir else None,
            "is_render": os.getenv("RENDER", "").lower() == "true",
            "current_working_directory": str(Path.cwd()),
            "timestamp": time.time()
        }

        # Verificar se é um problema de permissões
        if "Permission denied" in str(e) or "PermissionError" in str(type(e).__name__):
            logger.error("🚨 Problema de permissões detectado!")
            debug_info["permission_issue"] = True

            # Tentar verificar permissões
            try:
                if chroma_persist_dir and chroma_persist_dir.parent.exists():
                    test_file = chroma_persist_dir.parent / "debug_permission_test"
                    test_file.touch()
                    test_file.unlink()
                    debug_info["parent_dir_writable"] = True
                else:
                    debug_info["parent_dir_writable"] = False
            except Exception as perm_e:
                debug_info["parent_dir_writable"] = False
                debug_info["permission_error"] = str(perm_e)

        # Verificar se é um problema de espaço em disco
        if "No space left on device" in str(e) or "OSError: [Errno 28]" in str(e):
            logger.error("🚨 Problema de espaço em disco detectado!")
            debug_info["disk_space_issue"] = True

            try:
                import shutil
                if chroma_persist_dir and chroma_persist_dir.parent.exists():
                    total, used, free = shutil.disk_usage(
                        str(chroma_persist_dir.parent))
                    debug_info["disk_usage"] = {
                        "total_gb": round(total / (1024**3), 2),
                        "used_gb": round(used / (1024**3), 2),
                        "free_gb": round(free / (1024**3), 2),
                        "free_percent": round((free / total) * 100, 2)
                    }
            except Exception as disk_e:
                debug_info["disk_usage_error"] = str(disk_e)

        logger.error(f"🔍 Informações de debug: {debug_info}")

        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Erro interno no upload: {str(e)}",
                "error_type": type(e).__name__,
                "debug_info": debug_info
            }
        )


@app.get("/chromadb/download")
async def download_chromadb_archive():
    """Download do banco ChromaDB completo em formato .tar.gz"""
    global chroma_persist_dir

    try:
        # 🚨 CORREÇÃO: Verificar se chroma_persist_dir está configurado
        if not chroma_persist_dir:
            raise HTTPException(
                status_code=404,
                detail="ChromaDB não configurado. Configure CHROMA_PERSIST_DIR ou use a rota /initialize"
            )

        chroma_path = Path(chroma_persist_dir)

        if not chroma_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Diretório ChromaDB não encontrado"
            )

        # Verificar se há dados no ChromaDB
        try:
            client = chromadb.PersistentClient(path=str(chroma_path))
            collections = client.list_collections()

            if not collections:
                raise HTTPException(
                    status_code=404,
                    detail="ChromaDB está vazio - não há dados para baixar"
                )

            total_documents = sum(col.count() for col in collections)
            logger.info(
                f"📊 ChromaDB contém {len(collections)} coleções com {total_documents} documentos")

        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar ChromaDB: {e}")
            # Continuar mesmo com erro de verificação

        # Criar arquivo temporário para o tar.gz
        import tempfile
        import shutil

        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Criar o arquivo tar.gz
            logger.info(
                f"📦 Criando arquivo .tar.gz do ChromaDB: {chroma_path}")

            with tarfile.open(tmp_path, 'w:gz') as tar:
                tar.add(chroma_path, arcname='.chromadb')

            # Verificar tamanho do arquivo
            file_size = tmp_path.stat().st_size
            logger.info(
                f"✅ Arquivo .tar.gz criado: {file_size / (1024*1024):.2f} MB")

            # Retornar o arquivo para download
            def generate_file():
                try:
                    with open(tmp_path, 'rb') as f:
                        while chunk := f.read(8192):
                            yield chunk
                finally:
                    # Limpar arquivo temporário após download
                    try:
                        tmp_path.unlink(missing_ok=True)
                    except Exception:
                        pass

            filename = f"chromadb_complete_{int(time.time())}.tar.gz"

            return StreamingResponse(
                generate_file(),
                media_type="application/gzip",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )

        except Exception as e:
            # Limpar arquivo temporário em caso de erro
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise e

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao criar download do ChromaDB: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao criar arquivo de download: {str(e)}"
        )


@app.post("/chromadb/compress")
async def compress_chromadb_folder():
    """Compactar pasta .chromadb não compactada em arquivo .tar.gz"""
    global chroma_persist_dir

    try:
        logger.info("📦 Iniciando compressão do ChromaDB...")

        if not chroma_persist_dir:
            raise HTTPException(
                status_code=500,
                detail="ChromaDB persist directory não configurado"
            )

        chroma_path = Path(chroma_persist_dir)
        logger.info(f"🔍 Caminho do ChromaDB: {chroma_path}")

        if not chroma_path.exists():
            logger.error(f"❌ Diretório ChromaDB não encontrado: {chroma_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Diretório ChromaDB não encontrado: {chroma_path}"
            )

        # Verificar se já existe arquivo compactado
        parent_dir = chroma_path.parent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"chromadb_backup_{timestamp}.tar.gz"
        archive_path = parent_dir / archive_name

        logger.info(f"📁 Pasta pai: {parent_dir}")
        logger.info(f"📦 Arquivo será salvo em: {archive_path}")

        if archive_path.exists():
            logger.warning(f"⚠️ Arquivo já existe, removendo: {archive_path}")
            archive_path.unlink()

        # Criar arquivo tar.gz na pasta do ChromaDB
        logger.info("🔧 Criando arquivo tar.gz...")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(chroma_path, arcname=chroma_path.name)

        file_size = archive_path.stat().st_size
        logger.info(f"✅ Arquivo criado com sucesso: {archive_path}")
        logger.info(
            f"📏 Tamanho: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")

        # Retornar informações do arquivo criado
        return {
            "status": "success",
            "message": "ChromaDB compactado com sucesso",
            "file_path": str(archive_path),
            "file_name": archive_name,
            "file_size": file_size,
            "file_size_mb": round(file_size / (1024*1024), 2),
            "created_at": timestamp,
            "location": "local_folder"
        }

    except Exception as e:
        logger.error(f"❌ Erro durante compressão: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro durante compressão: {str(e)}"
        )


@app.post("/chromadb/compress-local")
async def compress_local_chromadb_folder(request: CompressLocalRequest):
    """Compactar pasta .chromadb local em arquivo .tar.gz"""
    try:
        # Extrair parâmetros da requisição
        source_path = request.source_path
        output_filename = request.output_filename or f"chromadb_local_{int(time.time())}.tar.gz"

        logger.info(f"📦 Compactando pasta local: {source_path}")

        # Resolver o caminho da pasta .chromadb local
        # Se for caminho relativo, tentar diferentes localizações
        local_chroma_path = None

        # Tentar diferentes caminhos possíveis
        possible_paths = [
            Path(source_path),  # Caminho exato fornecido
            Path.cwd() / source_path,  # Caminho relativo ao diretório atual
            Path.cwd().parent / source_path,  # Um nível acima
            Path.cwd().parent.parent / source_path,  # Dois níveis acima
        ]

        for path in possible_paths:
            if path.exists() and path.is_dir():
                local_chroma_path = path
                logger.info(
                    f"✅ Pasta .chromadb encontrada em: {local_chroma_path.absolute()}")
                break

        if not local_chroma_path:
            # Listar diretórios disponíveis para debug
            current_dir = Path.cwd()
            logger.error(
                f"❌ Pasta .chromadb não encontrada. Diretório atual: {current_dir}")
            logger.error(f"❌ Tentou os seguintes caminhos:")
            for path in possible_paths:
                logger.error(
                    f"   - {path.absolute()} (existe: {path.exists()}, é_dir: {path.is_dir() if path.exists() else 'N/A'})")

            raise HTTPException(
                status_code=404,
                detail=f"Pasta .chromadb não encontrada. Verifique se está no diretório correto."
            )

        # Verificar se há dados na pasta local
        try:
            # Tentar conectar ao ChromaDB local para verificar integridade
            client = chromadb.PersistentClient(path=str(local_chroma_path))
            collections = client.list_collections()

            if not collections:
                raise HTTPException(
                    status_code=404,
                    detail="Pasta local está vazia - não há dados para compactar"
                )

            total_documents = sum(col.count() for col in collections)
            logger.info(
                f"📊 Pasta local contém {len(collections)} coleções com {total_documents} documentos")

        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar pasta local: {e}")
            # Continuar mesmo com erro de verificação

        # Criar arquivo temporário para o tar.gz
        import tempfile
        import shutil

        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Criar o arquivo tar.gz
            logger.info(
                f"📦 Compactando pasta local {source_path} em .tar.gz: {local_chroma_path}")

            with tarfile.open(tmp_path, 'w:gz') as tar:
                # Compactar a pasta inteira .chromadb
                tar.add(local_chroma_path, arcname='.chromadb')

            # Verificar tamanho do arquivo
            file_size = tmp_path.stat().st_size
            logger.info(
                f"✅ Arquivo .tar.gz criado: {file_size / (1024*1024):.2f} MB")

            # Retornar o arquivo para download
            def generate_file():
                try:
                    with open(tmp_path, 'rb') as f:
                        while chunk := f.read(8192):
                            yield chunk
                finally:
                    # Limpar arquivo temporário após download
                    try:
                        tmp_path.unlink(missing_ok=True)
                    except Exception:
                        pass

            return StreamingResponse(
                generate_file(),
                media_type="application/gzip",
                headers={
                    "Content-Disposition": f"attachment; filename={output_filename}"
                }
            )

        except Exception as e:
            # Limpar arquivo temporário em caso de erro
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise e

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao compactar pasta local: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao compactar pasta local: {str(e)}"
        )


@app.post("/chromadb/compress-local-path")
async def compress_local_chromadb_folder_by_path(request: CompressLocalRequest):
    """Compactar pasta .chromadb local especificando caminho completo"""
    try:
        # Extrair parâmetros da requisição
        source_path = request.source_path
        output_filename = request.output_filename or f"chromadb_local_{int(time.time())}.tar.gz"

        logger.info(f"📦 Compactando pasta local por caminho: {source_path}")

        # Usar o caminho exato fornecido
        local_chroma_path = Path(source_path)

        if not local_chroma_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Pasta não encontrada: {source_path}"
            )

        if not local_chroma_path.is_dir():
            raise HTTPException(
                status_code=400,
                detail=f"Caminho não é uma pasta válida: {source_path}"
            )

        # Verificar se é realmente uma pasta .chromadb
        if not local_chroma_path.name == ".chromadb":
            logger.warning(
                f"⚠️ Pasta não se chama '.chromadb': {local_chroma_path.name}")

        # Verificar se há dados na pasta local
        try:
            # Tentar conectar ao ChromaDB local para verificar integridade
            client = chromadb.PersistentClient(path=str(local_chroma_path))
            collections = client.list_collections()

            if not collections:
                raise HTTPException(
                    status_code=404,
                    detail="Pasta local está vazia - não há dados para compactar"
                )

            total_documents = sum(col.count() for col in collections)
            logger.info(
                f"📊 Pasta local contém {len(collections)} coleções com {total_documents} documentos")

        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar pasta local: {e}")
            # Continuar mesmo com erro de verificação

        # Criar arquivo temporário para o tar.gz
        import tempfile
        import shutil

        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Criar o arquivo tar.gz
            logger.info(
                f"📦 Compactando pasta local {source_path} em .tar.gz: {local_chroma_path}")

            with tarfile.open(tmp_path, 'w:gz') as tar:
                # Compactar a pasta inteira .chromadb
                tar.add(local_chroma_path, arcname='.chromadb')

            # Verificar tamanho do arquivo
            file_size = tmp_path.stat().st_size
            logger.info(
                f"✅ Arquivo .tar.gz criado: {file_size / (1024*1024):.2f} MB")

            # Retornar o arquivo para download
            def generate_file():
                try:
                    with open(tmp_path, 'rb') as f:
                        while chunk := f.read(8192):
                            yield chunk
                finally:
                    # Limpar arquivo temporário após download
                    try:
                        tmp_path.unlink(missing_ok=True)
                    except Exception:
                        pass

            return StreamingResponse(
                generate_file(),
                media_type="application/gzip",
                headers={
                    "Content-Disposition": f"attachment; filename={output_filename}"
                }
            )

        except Exception as e:
            # Limpar arquivo temporário em caso de erro
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise e

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao compactar pasta local por caminho: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao compactar pasta local: {str(e)}"
        )


@app.post("/chromadb/upload-folder")
async def upload_chromadb_folder(
    folder: UploadFile = File(...),
    replace_existing: bool = Form(True)
):
    """Upload de pasta .chromadb não compactada (zipada)"""
    global rag_handler, chroma_persist_dir

    try:
        # Validar parâmetros
        logger.info(
            f"🔍 Parâmetros recebidos: replace_existing={replace_existing}")
        if not isinstance(replace_existing, bool):
            logger.error(
                f"❌ Parâmetro replace_existing inválido: {replace_existing}")
            raise HTTPException(
                status_code=400,
                detail="Parâmetro replace_existing deve ser um booleano"
            )
        # 🚨 CORREÇÃO: Verificar se chroma_persist_dir está configurado
        if not chroma_persist_dir:
            # No Render, NÃO definir caminho padrão automaticamente
            is_render = os.getenv("RENDER", "").lower() == "true"
            if is_render:
                # 🚨 IMPORTANTE: NÃO criar .chromadb automaticamente no Render
                logger.info(
                    "🚨 Render detectado - NÃO criando .chromadb automaticamente")
                logger.info(
                    "💡 Use a interface para fazer upload de um arquivo .chromadb existente")
                logger.info("💡 Ou configure CHROMA_PERSIST_DIR manualmente")

                # Verificar se o diretório /app/data existe (apenas para logs)
                data_dir = Path("/app/data")
                if not data_dir.exists():
                    logger.info(
                        "ℹ️ Diretório /app/data não existe - será criado apenas quando necessário")
                else:
                    logger.info(f"ℹ️ Diretório /app/data existe: {data_dir}")
                    # Listar conteúdo para debug
                    try:
                        contents = list(data_dir.iterdir())
                        logger.info(
                            f"📁 Conteúdo de /app/data: {[item.name for item in contents]}")
                    except Exception as e:
                        logger.warning(
                            f"⚠️ Não foi possível listar conteúdo de /app/data: {e}")

                # NÃO definir chroma_persist_dir automaticamente
                raise HTTPException(
                    status_code=400,
                    detail="ChromaDB não configurado no Render. Faça upload de um arquivo .chromadb existente ou configure CHROMA_PERSIST_DIR manualmente."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="ChromaDB não configurado. Configure CHROMA_PERSIST_DIR ou use a rota /initialize"
                )

        # Verificar se é um arquivo zip válido
        logger.info(f"🔍 Validando arquivo: {folder.filename}")
        if not folder.filename:
            logger.error("❌ Nome do arquivo não fornecido")
            raise HTTPException(
                status_code=400,
                detail="Nome do arquivo não fornecido"
            )

        if not folder.filename.lower().endswith('.zip'):
            logger.error(f"❌ Formato de arquivo inválido: {folder.filename}")
            raise HTTPException(
                status_code=400,
                detail="Arquivo deve ser .zip contendo o diretório .chromadb"
            )

        # Ler o conteúdo do arquivo
        logger.info("📖 Lendo conteúdo do arquivo...")
        content = await folder.read()
        if len(content) == 0:
            logger.error("❌ Arquivo vazio")
            raise HTTPException(status_code=400, detail="Arquivo vazio")

        logger.info(f"✅ Arquivo lido com sucesso: {len(content)} bytes")

        # Backup do ChromaDB atual se existir
        chroma_path = Path(chroma_persist_dir)
        backup_path = None

        if chroma_path.exists() and replace_existing:
            backup_path = chroma_path.parent / \
                f".chromadb_backup_{int(time.time())}"
            logger.info(
                f"📦 Fazendo backup do ChromaDB atual para {backup_path}")
            import shutil
            shutil.move(str(chroma_path), str(backup_path))

        # Criar diretório temporário para extração
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_archive = tmp_dir / folder.filename
        tmp_archive.write_bytes(content)

        # Extrair o arquivo zip
        logger.info(f"📂 Extraindo pasta .chromadb do zip para {chroma_path}")
        # 🚨 CORREÇÃO: NÃO criar diretório automaticamente no Render
        is_render = os.getenv("RENDER", "").lower() == "true"
        if not is_render:
            chroma_path.mkdir(parents=True, exist_ok=True)
        else:
            logger.info(
                "🚨 Render detectado - NÃO criando diretório .chromadb automaticamente")
            logger.info(
                "💡 Use a interface para fazer upload de um arquivo .chromadb existente")
            # Verificar se o diretório pai existe e criar apenas se necessário
            parent_dir = chroma_path.parent
            if not parent_dir.exists():
                logger.info(f"📁 Criando diretório pai: {parent_dir}")
                parent_dir.mkdir(parents=True, exist_ok=True)
            else:
                logger.info(f"📁 Diretório pai já existe: {parent_dir}")

        # Validar se o arquivo é um zip válido
        logger.info("🔍 Validando arquivo zip...")
        try:
            with zipfile.ZipFile(tmp_archive, 'r') as zf:
                logger.info(
                    f"✅ Arquivo zip válido, {len(zf.namelist())} arquivos encontrados")
                zf.extractall(chroma_path)
                logger.info("✅ Arquivo extraído com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao extrair arquivo zip: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo zip inválido ou corrompido: {str(e)}"
            )

        # Limpeza do arquivo temporário
        try:
            tmp_archive.unlink(missing_ok=True)
            tmp_dir.rmdir()
        except Exception:
            pass

        # Verificar integridade do ChromaDB carregado
        logger.info("🔍 Iniciando verificação de integridade do ChromaDB...")

        # Verificar se os arquivos foram extraídos corretamente
        if chroma_path.exists():
            extracted_files = list(chroma_path.rglob("*"))
            logger.info(f"📁 Arquivos extraídos: {len(extracted_files)}")
            # Mostrar apenas os primeiros 5
            for file_path in extracted_files[:5]:
                logger.info(f"   - {file_path.relative_to(chroma_path)}")
            if len(extracted_files) > 5:
                logger.info(
                    f"   ... e mais {len(extracted_files) - 5} arquivos")
        else:
            logger.error("❌ Diretório ChromaDB não foi criado após extração")
            raise HTTPException(
                status_code=400,
                detail="Falha na criação do diretório ChromaDB"
            )

        # Aguardar um pouco para garantir que os arquivos estejam completamente escritos
        import time
        logger.info(
            "⏳ Aguardando 2 segundos para estabilização dos arquivos...")
        time.sleep(2)

        integrity_check = check_chromadb_integrity(chroma_path)
        logger.info(f"🔍 Resultado da verificação: {integrity_check}")

        if not integrity_check["valid"]:
            # Restaurar backup se a verificação falhar
            if backup_path and backup_path.exists():
                logger.error(f"❌ ChromaDB inválido, restaurando backup")
                if chroma_path.exists():
                    import shutil
                    shutil.rmtree(chroma_path)
                shutil.move(str(backup_path), str(chroma_path))

            raise HTTPException(
                status_code=400,
                detail=f"ChromaDB inválido: {integrity_check['reason']}"
            )

        # Reinicializar o RAG handler se estiver ativo
        if rag_handler:
            logger.info("🔄 Reinicializando RAG handler com novo ChromaDB")
            try:
                old_api_key = rag_handler.config.api_key
                rag_handler = RAGHandler(
                    api_key=old_api_key,
                    persist_dir=str(chroma_path)
                )
                logger.info("✅ RAG handler reinicializado com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao reinicializar RAG handler: {e}")

        # Remover backup se tudo deu certo
        if backup_path and backup_path.exists():
            import shutil
            shutil.rmtree(backup_path)
            logger.info("🗑️ Backup removido após sucesso")

        return {
            "status": "success",
            "message": "Pasta .chromadb carregada com sucesso",
            "collections": integrity_check.get("collections", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no upload da pasta .chromadb: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/system")
async def debug_system():
    """Debug detalhado do sistema para troubleshooting"""
    try:
        # Verificar variáveis de ambiente
        env_vars = {
            "RENDER": os.getenv("RENDER"),
            "RENDER_ENVIRONMENT": os.getenv("RENDER_ENVIRONMENT"),
            "CHROMA_PERSIST_DIR": os.getenv("CHROMA_PERSIST_DIR"),
            "MATERIALS_DIR": os.getenv("MATERIALS_DIR"),
            "PORT": os.getenv("PORT"),
            "CORS_ORIGINS": os.getenv("CORS_ORIGINS"),
            "NVIDIA_API_KEY": "***" if os.getenv("NVIDIA_API_KEY") else None,
            "OPENAI_API_KEY": "***" if os.getenv("OPENAI_API_KEY") else None,
            "GEMINI_API_KEY": "***" if os.getenv("GEMINI_API_KEY") else None,
        }

        # Verificar diretórios
        dir_status = {}
        if chroma_persist_dir:
            dir_status["chroma_persist_dir"] = {
                "path": str(chroma_persist_dir),
                "exists": chroma_persist_dir.exists(),
                "is_dir": chroma_persist_dir.is_dir() if chroma_persist_dir.exists() else False,
                "size": sum(f.stat().st_size for f in chroma_persist_dir.rglob('*') if f.is_file()) if chroma_persist_dir.exists() else 0
            }

        if materials_dir:
            dir_status["materials_dir"] = {
                "path": str(materials_dir),
                "exists": materials_dir.exists(),
                "is_dir": materials_dir.is_dir() if materials_dir.exists() else False,
                "file_count": len(list(materials_dir.rglob('*'))) if materials_dir.exists() else 0
            }

        # Verificar RAG handler
        rag_status = {
            "initialized": rag_handler is not None,
            "vector_store_ready": rag_handler.vector_store is not None if rag_handler else False,
            "embeddings_ready": rag_handler.embeddings is not None if rag_handler else False,
            "llm_ready": rag_handler.llm is not None if rag_handler else False
        }

        if rag_handler:
            try:
                rag_status["vector_store_count"] = rag_handler.vector_store._collection.count(
                ) if rag_handler.vector_store else 0
            except Exception as e:
                rag_status["vector_store_count_error"] = str(e)

        return {
            "status": "success",
            "timestamp": time.time(),
            "environment_variables": env_vars,
            "directory_status": dir_status,
            "rag_handler_status": rag_status,
            "system_info": {
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "platform": os.sys.platform,
                "current_working_directory": str(Path.cwd()),
                "script_location": str(Path(__file__).parent)
            }
        }
    except Exception as e:
        logger.error(f"❌ Erro no debug do sistema: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": time.time()
        }


@app.get("/test-connection")
async def test_connection():
    """Teste de conectividade e status básico do servidor"""
    try:
        return {
            "status": "success",
            "message": "Servidor RAG funcionando",
            "timestamp": time.time(),
            "chroma_persist_dir": str(chroma_persist_dir) if chroma_persist_dir else None,
            "materials_dir": str(materials_dir) if materials_dir else None,
            "rag_handler_active": rag_handler is not None,
            "environment": "RENDER" if os.getenv("RENDER") else "LOCAL"
        }
    except Exception as e:
        logger.error(f"❌ Erro no teste de conexão: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": time.time()
        }


@app.get("/chromadb/status")
async def get_chromadb_status():
    """Verificar status e integridade do ChromaDB atual."""
    try:
        # 🚨 CORREÇÃO: Verificar se chroma_persist_dir está configurado
        if not chroma_persist_dir:
            return {
                "status": "not_configured",
                "message": "ChromaDB não configurado. Configure CHROMA_PERSIST_DIR ou use a rota /initialize",
                "path": None
            }

        chroma_path = Path(chroma_persist_dir)

        if not chroma_path.exists():
            return {
                "status": "not_found",
                "message": "ChromaDB não encontrado",
                "path": str(chroma_path)
            }

        integrity_check = check_chromadb_integrity(chroma_path)

        return {
            "status": "found" if integrity_check["valid"] else "invalid",
            "path": str(chroma_path),
            "is_valid": integrity_check["valid"],
            "reason": integrity_check.get("reason"),
            "collections": integrity_check.get("collections", []),
            "total_documents": sum(c.get("count", 0) for c in integrity_check.get("collections", [])),
            "rag_handler_active": rag_handler is not None
        }

    except Exception as e:
        logger.error(f"❌ Erro ao verificar status do ChromaDB: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/initialize")
async def initialize_rag(api_key: str):
    """Inicializar RAG handler"""
    global rag_handler, chroma_persist_dir

    try:
        logger.info("🔧 Inicializando RAG handler...")

        # 🚨 CORREÇÃO: Verificar se chroma_persist_dir está configurado
        if not chroma_persist_dir:
            # No Render, NÃO definir caminho padrão automaticamente
            is_render = os.getenv("RENDER", "").lower() == "true"
            if is_render:
                # 🚨 IMPORTANTE: NÃO criar .chromadb automaticamente no Render
                logger.info(
                    "🚨 Render detectado - NÃO criando .chromadb automaticamente")
                logger.info(
                    "💡 Use a interface para fazer upload de um arquivo .chromadb existente")
                logger.info("💡 Ou configure CHROMA_PERSIST_DIR manualmente")

                # Verificar se o diretório /app/data existe (apenas para logs)
                data_dir = Path("/app/data")
                if not data_dir.exists():
                    logger.info(
                        "ℹ️ Diretório /app/data não existe - será criado apenas quando necessário")
                else:
                    logger.info(f"ℹ️ Diretório /app/data existe: {data_dir}")
                    # Listar conteúdo para debug
                    try:
                        contents = list(data_dir.iterdir())
                        logger.info(
                            f"📁 Conteúdo de /app/data: {[item.name for item in contents]}")
                    except Exception as e:
                        logger.warning(
                            f"⚠️ Não foi possível listar conteúdo de /app/data: {e}")

                # NÃO definir chroma_persist_dir automaticamente
                raise HTTPException(
                    status_code=400,
                    detail="ChromaDB não configurado no Render. Faça upload de um arquivo .chromadb existente ou configure CHROMA_PERSIST_DIR manualmente."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="ChromaDB não configurado. Configure CHROMA_PERSIST_DIR ou use a rota /initialize"
                )

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


@app.get("/chromadb/backups")
async def list_chromadb_backups():
    """Listar arquivos de backup do ChromaDB"""
    global chroma_persist_dir

    try:
        if not chroma_persist_dir:
            raise HTTPException(
                status_code=500,
                detail="ChromaDB persist directory não configurado"
            )

        chroma_path = Path(chroma_persist_dir)
        parent_dir = chroma_path.parent

        # Buscar arquivos .tar.gz de backup
        backup_files = []
        for file_path in parent_dir.glob("chromadb_backup_*.tar.gz"):
            stat = file_path.stat()
            backup_files.append({
                "filename": file_path.name,
                "file_path": str(file_path),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024*1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })

        # Ordenar por data de criação (mais recente primeiro)
        backup_files.sort(key=lambda x: x["created_at"], reverse=True)

        return {
            "status": "success",
            "backup_dir": str(parent_dir),
            "total_backups": len(backup_files),
            "backups": backup_files
        }

    except Exception as e:
        logger.error(f"❌ Erro ao listar backups: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar backups: {str(e)}"
        )


@app.get("/debug/upload-test")
async def debug_upload_test():
    """Debug específico para problemas de upload do ChromaDB"""
    try:
        debug_info = {
            "timestamp": time.time(),
            "environment": {
                "is_render": os.getenv("RENDER", "").lower() == "true",
                "render_environment": os.getenv("RENDER_ENVIRONMENT"),
                "current_working_directory": str(Path.cwd()),
                "script_location": str(Path(__file__).parent)
            },
            "chroma_persist_dir": {
                "configured": chroma_persist_dir is not None,
                "path": str(chroma_persist_dir) if chroma_persist_dir else None,
                "exists": chroma_persist_dir.exists() if chroma_persist_dir else False,
                "is_dir": chroma_persist_dir.is_dir() if chroma_persist_dir and chroma_persist_dir.exists() else False
            },
            "app_data_directory": {
                "path": "/app/data",
                "exists": Path("/app/data").exists(),
                "is_dir": Path("/app/data").is_dir() if Path("/app/data").exists() else False
            },
            "permissions_test": {},
            "disk_space": {},
            "python_environment": {
                "version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "platform": os.sys.platform,
                "executable": os.sys.executable
            }
        }

        # Testar permissões em /app/data
        app_data = Path("/app/data")
        if app_data.exists():
            try:
                test_file = app_data / "upload_test_permissions"
                test_file.touch()
                test_file.unlink()
                debug_info["permissions_test"]["app_data_writable"] = True
            except Exception as e:
                debug_info["permissions_test"]["app_data_writable"] = False
                debug_info["permissions_test"]["app_data_error"] = str(e)

        # Testar permissões no diretório ChromaDB se existir
        if chroma_persist_dir and chroma_persist_dir.exists():
            try:
                test_file = chroma_persist_dir / "upload_test_permissions"
                test_file.touch()
                test_file.unlink()
                debug_info["permissions_test"]["chroma_dir_writable"] = True
            except Exception as e:
                debug_info["permissions_test"]["chroma_dir_writable"] = False
                debug_info["permissions_test"]["chroma_dir_error"] = str(e)

        # Verificar espaço em disco
        try:
            import shutil
            total, used, free = shutil.disk_usage(
                "/app/data" if app_data.exists() else "/")
            debug_info["disk_space"] = {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "free_percent": round((free / total) * 100, 2)
            }
        except Exception as e:
            debug_info["disk_space"]["error"] = str(e)

        # Verificar se há arquivos temporários ou backups
        if chroma_persist_dir and chroma_persist_dir.parent.exists():
            try:
                backup_files = list(
                    chroma_persist_dir.parent.glob("*.backup*"))
                debug_info["backup_files"] = {
                    "count": len(backup_files),
                    "files": [str(f.relative_to(chroma_persist_dir.parent)) for f in backup_files[:5]]
                }
            except Exception as e:
                debug_info["backup_files"] = {"error": str(e)}

        return {
            "status": "success",
            "debug_info": debug_info
        }

    except Exception as e:
        logger.error(f"❌ Erro no debug de upload: {e}")
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


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


def check_chromadb_integrity(persist_dir: Path) -> Dict[str, Any]:
    """Verificar integridade e conteúdo do ChromaDB"""
    try:
        logger.info(f"🔍 Verificando integridade do ChromaDB em: {persist_dir}")

        if not persist_dir.exists():
            logger.error(f"❌ Diretório não existe: {persist_dir}")
            return {"valid": False, "reason": "Directory does not exist", "collections": []}

        # Listar todos os arquivos no diretório para debug
        all_files = list(persist_dir.rglob("*"))
        logger.info(f"📁 Arquivos encontrados no diretório: {len(all_files)}")
        # Mostrar apenas os primeiros 10 arquivos
        for file_path in all_files[:10]:
            logger.info(f"   - {file_path.relative_to(persist_dir)}")
        if len(all_files) > 10:
            logger.info(f"   ... e mais {len(all_files) - 10} arquivos")

        # Verificar se há arquivos do ChromaDB
        chromadb_files = list(persist_dir.rglob("*.sqlite*")) + \
            list(persist_dir.rglob("chroma.sqlite3"))

        logger.info(f"🔍 Arquivos ChromaDB encontrados: {len(chromadb_files)}")
        for db_file in chromadb_files:
            logger.info(f"   - {db_file.relative_to(persist_dir)}")

        if not chromadb_files:
            logger.error("❌ Nenhum arquivo ChromaDB encontrado")
            return {"valid": False, "reason": "No ChromaDB files found", "collections": []}

        # Verificar se o diretório tem permissões corretas
        try:
            test_file = persist_dir / "test_permissions"
            test_file.touch()
            test_file.unlink()
            logger.info("✅ Permissões de escrita verificadas")
        except Exception as e:
            logger.warning(f"⚠️ Problema com permissões: {e}")

        # Tentar conectar e listar coleções
        logger.info("🔌 Tentando conectar ao ChromaDB...")
        client = chromadb.PersistentClient(path=str(persist_dir))

        logger.info("📋 Listando coleções...")
        collections = client.list_collections()
        logger.info(f"✅ {len(collections)} coleções encontradas")

        collections_info = []
        total_documents = 0

        for collection in collections:
            try:
                logger.info(f"🔍 Verificando coleção: {collection.name}")
                count = collection.count()
                logger.info(
                    f"   - Documentos na coleção {collection.name}: {count}")

                collections_info.append({
                    "name": collection.name,
                    "count": count,
                    "metadata": getattr(collection, 'metadata', {})
                })
                total_documents += count
            except Exception as e:
                logger.warning(
                    f"⚠️ Erro ao verificar coleção {collection.name}: {e}")
                collections_info.append({
                    "name": collection.name,
                    "count": 0,
                    "error": str(e)
                })

        logger.info(f"📊 Total de documentos: {total_documents}")

        # Ser mais flexível na validação - aceitar ChromaDBs com pelo menos uma coleção
        is_valid = len(collections) > 0

        if is_valid:
            logger.info("✅ ChromaDB validado com sucesso")
        else:
            logger.warning("⚠️ ChromaDB não tem coleções")

        return {
            "valid": is_valid,
            "reason": f"Found {len(collections)} collections with {total_documents} total documents",
            "collections": collections_info,
            "total_documents": total_documents
        }

    except Exception as e:
        logger.error(f"❌ Erro ao verificar integridade do ChromaDB: {e}")
        import traceback
        logger.error(f"📋 Traceback completo: {traceback.format_exc()}")
        return {"valid": False, "reason": f"Error checking ChromaDB: {str(e)}", "collections": []}
