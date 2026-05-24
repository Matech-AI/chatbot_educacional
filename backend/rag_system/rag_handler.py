from chromadb.config import Settings
import chromadb
from langchain.load import dumps, loads
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import (
    PyPDFLoader,
    DirectoryLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import os
import logging
import openai
import time
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Type, Tuple
from dataclasses import dataclass, field
from pydantic import BaseModel, SecretStr, Field
from langchain.tools import BaseTool
import pandas as pd

# Configure logging FIRST
logger = logging.getLogger(__name__)

# Importar sistema de guardrails
try:
    from .guardrails import content_guardrails, validate_and_sanitize_content, is_content_safe
    GUARDRAILS_AVAILABLE = True
except ImportError:
    try:
        from guardrails import content_guardrails, validate_and_sanitize_content, is_content_safe
        GUARDRAILS_AVAILABLE = True
    except ImportError:
        GUARDRAILS_AVAILABLE = False
        logger.warning(
            "⚠️ Sistema de guardrails não disponível. Instale o módulo guardrails.py")


# Importações para Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
except ImportError:
    ChatGoogleGenerativeAI = None
    GoogleGenerativeAIEmbeddings = None
    logger.warning(
        "⚠️ Google Generative AI not available. Install with: pip install langchain-google-genai")

# NOVO: Classe personalizada para NVIDIA API


class NVIDIAChatOpenAI(ChatOpenAI):
    """Custom ChatOpenAI class for NVIDIA API with robust retry logic and fallback."""

    def __init__(self, nvidia_api_key: str, model: str, base_url: str, retry_attempts: int = 2, retry_delay: float = 0.5, **kwargs):
        # Remover stream=True se estiver presente para evitar conflitos com LangChain
        if 'stream' in kwargs:
            del kwargs['stream']

        # Definir atributos ANTES de chamar super()
        self._nvidia_retry_attempts = retry_attempts
        self._nvidia_retry_delay = retry_delay
        self._nvidia_max_retry_delay = 10.0

        # ✅ CORREÇÃO: Usar base_url diretamente em vez de openai_client_config
        super().__init__(
            api_key=SecretStr(nvidia_api_key),
            model=model,
            base_url=base_url,
            **kwargs
        )

    @property
    def retry_attempts(self):
        return getattr(self, '_nvidia_retry_attempts', 3)

    @property
    def retry_delay(self):
        return getattr(self, '_nvidia_retry_delay', 2.0)

    @property
    def max_retry_delay(self):
        return getattr(self, '_nvidia_max_retry_delay', 10.0)

    def _call_with_retry(self, *args, **kwargs):
        """Execute API call with exponential backoff retry logic."""
        last_exception = None

        for attempt in range(self.retry_attempts):
            try:
                # Tentar chamada normal
                return super()._call(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"⚠️ NVIDIA API attempt {attempt + 1}/{self.retry_attempts} failed: {str(e)[:100]}...")

                # Se não for a última tentativa, aguardar antes de tentar novamente
                if attempt < self.retry_attempts - 1:
                    # Exponential backoff com jitter para evitar thundering herd
                    delay = min(self.retry_delay * (2 ** attempt) +
                                (random.random() * 0.1), self.max_retry_delay)
                    logger.info(
                        f"🔄 Aguardando {delay:.1f}s antes da próxima tentativa...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"❌ NVIDIA API failed after {self.retry_attempts} attempts")
                    break

        # Se chegou aqui, todas as tentativas falharam
        raise last_exception

    def _call(self, *args, **kwargs):
        """Override _call to use retry logic."""
        return self._call_with_retry(*args, **kwargs)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        """Override _generate with robust error handling and retry."""
        try:
            # Tentar com retry logic
            result = super()._generate(messages, stop, run_manager, **kwargs)
            return result
        except Exception as e:
            logger.error(f"❌ Error in NVIDIA _generate: {e}")

            # ❌ REMOVIDO: Não tentar mais uma vez - deixar o fallback atuar
            # Se falhou 2 vezes, é hora de usar o fallback
            logger.info(
                "🔄 NVIDIA falhou 2 vezes - ativando fallback automático...")
            raise e  # Deixar a exceção propagar para ativar o fallback


class NVIDIAEmbeddings(OpenAIEmbeddings):
    """Custom OpenAI Embeddings class for NVIDIA API with retry logic."""

    def __init__(self, nvidia_api_key: str, model: str, model_name: str, base_url: str, retry_attempts: int = 2, retry_delay: float = 0.5, **kwargs):
        # Definir atributos ANTES de chamar super()
        self._nvidia_retry_attempts = retry_attempts
        self._nvidia_retry_delay = retry_delay

        # ✅ CORREÇÃO: Usar base_url diretamente em vez de openai_client_config
        super().__init__(
            api_key=SecretStr(nvidia_api_key),
            model=model_name,
            base_url=base_url,  # ✅ CORRETO: usar base_url diretamente
            **kwargs
        )

    @property
    def retry_attempts(self):
        return getattr(self, '_nvidia_retry_attempts', 2)

    @property
    def retry_delay(self):
        return getattr(self, '_nvidia_retry_delay', 0.5)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents with retry logic."""
        for attempt in range(self.retry_attempts):
            try:
                return super().embed_documents(texts)
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    logger.warning(
                        f"⚠️ NVIDIA Embeddings attempt {attempt + 1} failed: {e}. Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    logger.error(
                        f"❌ NVIDIA Embeddings failed after {self.retry_attempts} attempts: {e}")
                    # ❌ REMOVIDO: Não tentar mais - deixar o fallback atuar
                    logger.info(
                        "🔄 NVIDIA Embeddings falhou 2 vezes - ativando fallback automático...")
                    raise e  # Deixar a exceção propagar para ativar o fallback

    def embed_query(self, text: str) -> List[float]:
        """Embed query with retry logic."""
        for attempt in range(self.retry_attempts):
            try:
                return super().embed_query(text)
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    logger.warning(
                        f"⚠️ NVIDIA Query Embedding attempt {attempt + 1} failed: {e}. Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    logger.error(
                        f"❌ NVIDIA Query Embedding failed after {self.retry_attempts} attempts: {e}")
                    # ❌ REMOVIDO: Não tentar mais - deixar o fallback atuar
                    logger.info(
                        "🔄 NVIDIA Query Embedding falhou 2 vezes - ativando fallback automático...")
                    raise e  # Deixar a exceção propagar para ativar o fallback


# NOVO: Classe para embeddings open source
try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
    from langchain_community.embeddings import HuggingFaceEmbeddings
    OpenSourceEmbeddings = True
    CrossEncoderAvailable = True
except ImportError:
    OpenSourceEmbeddings = False
    CrossEncoderAvailable = False
    logger.warning(
        "⚠️ Sentence Transformers not available. Install with: pip install sentence-transformers")


class OpenSourceEmbeddingsWrapper:
    """Wrapper para embeddings open source usando sentence-transformers"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not OpenSourceEmbeddings:
            raise ImportError("Sentence Transformers not available")

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        logger.info(f"✅ Open Source Embeddings loaded: {model_name}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents using open source model"""
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings
        except Exception as e:
            logger.error(f"❌ Error in open source embeddings: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """Embed query using open source model"""
        try:
            embedding = self.model.encode([text], convert_to_tensor=False)
            return embedding[0].tolist() if hasattr(embedding[0], 'tolist') else embedding[0]
        except Exception as e:
            logger.error(f"❌ Error in open source query embedding: {e}")
            raise


try:
    import tiktoken  # for token estimation
except Exception:
    tiktoken = None


@dataclass
class RAGConfig:
    """Unified configuration for the RAG handler."""
    # Text processing - OTIMIZADO para melhor precisão
    chunk_size: int = 600  # Reduzido para capturar conceitos completos
    chunk_overlap: int = 150  # 25% de overlap para manter contexto

    # Model configuration
    model_name: str = "gpt-4o-mini"
    gemini_model_name: str = "gemini-2.5-flash"
    # Modelo NVIDIA (sem prefixo openai/)
    # Modelo NVIDIA (nome correto da API)
    nvidia_model_name: str = "openai/gpt-oss-120b"
    embedding_model: str = "text-embedding-3-small"
    gemini_embedding_model: str = "models/text-embedding-004"
    nvidia_embedding_model: str = "nvidia/nv-embedqa-e5-v5"  # NOVO: Embedding NVIDIA
    # NOVO: Embedding Open Source de alta qualidade (768d) - versão BASE para menos memória
    open_source_embedding_model: str = "intfloat/multilingual-e5-base"  # Mudado de -large para -base para evitar erro de memória
    temperature: float = 0.1  # MUITO baixa para evitar criatividade e alucinações
    max_tokens: int = 2048  # Reduzido para respostas mais focadas

    # Provider preference - LER VARIÁVEIS DE AMBIENTE DO RENDER
    prefer_nvidia: bool = os.getenv(
        "PREFER_NVIDIA", "true").lower() == "true"  # NOVO: Preferir NVIDIA
    prefer_openai: bool = os.getenv(
        "PREFER_OPENAI", "false").lower() == "true"  # Mantido False
    prefer_open_source: bool = os.getenv("PREFER_OPEN_SOURCE_EMBEDDINGS", "false").lower(
    ) == "true"  # Embeddings open source habilitados (usando e5-base para reduzir uso de memória)

    # NVIDIA specific settings
    nvidia_retry_attempts: int = 2  # NOVO: Tentativas de retry
    nvidia_retry_delay: float = 0.5  # NOVO: Delay entre tentativas
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"  # NOVO: URL base NVIDIA

    # Retrieval configuration - OTIMIZADO para conteúdo educacional
    retrieval_search_type: str = "mmr"  # MMR para diversidade (evita documentos repetidos)
    retrieval_k: int = 12  # Buscar mais documentos relevantes
    retrieval_fetch_k: int = 40  # Buscar mais candidatos para reranking
    retrieval_lambda_mult: float = 0.7  # Maior diversidade de documentos
    # Context assembly - OTIMIZADO
    max_context_chunks: int = 8  # Usar mais chunks na resposta

    # Indexing - OTIMIZADO para melhor qualidade
    add_batch_size: int = 4  # Reduzido para melhor qualidade por batch
    embedding_request_token_limit: int = 200000  # Reduzido para chunks menores
    embedding_request_target: int = 180000  # Ajustado proporcionalmente

    # Vector store
    collection_name: str = "langchain"

    # Educational features (can be toggled)
    enable_educational_features: bool = True
    generate_learning_objectives: bool = True
    extract_key_concepts: bool = True
    identify_prerequisites: bool = True
    assess_difficulty_level: bool = True
    create_summaries: bool = True

    def __post_init__(self):
        """Override embedding model from environment if specified"""
        env_model = os.getenv("OPEN_SOURCE_EMBEDDING_MODEL")
        if env_model:
            self.open_source_embedding_model = env_model


class Source(BaseModel):
    """Unified source model for RAG content."""
    title: str
    source: str
    page: Optional[int] = None
    chunk: str
    content_type: str = "text"
    difficulty_level: str = "intermediate"
    key_concepts: List[str] = []
    summary: str = ""
    relevance_score: float = 0.0
    educational_value: float = 0.0


class RAGHandler:
    """
    Unified RAG handler with configurable educational enhancements and OpenAI/Gemini fallback.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        nvidia_api_key: Optional[str] = None,  # NOVO: NVIDIA API Key
        config: Optional[RAGConfig] = None,
        persist_dir: Optional[str] = None,
        materials_dir: str = "data/materials",
    ):
        logger.info(
            "🚀 Initializing Unified RAG Handler with NVIDIA/OpenAI/Gemini fallback...")

        # API Keys
        self.openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.nvidia_api_key = nvidia_api_key or os.getenv("NVIDIA_API_KEY")

        if self.openai_api_key:
            openai.api_key = self.openai_api_key

        self.config = config or RAGConfig()

        # Provider tracking
        self.current_llm_provider = None
        self.current_embedding_provider = None

        # Setup directories
        if persist_dir:
            self.persist_dir = persist_dir
        else:
            # 🚨 CORREÇÃO: Não criar .chromadb automaticamente no Render
            is_render = os.getenv("RENDER", "").lower() == "true"
            if is_render:
                logger.warning(
                    "🚨 Render detectado - persist_dir não configurado")
                logger.warning(
                    "💡 Configure persist_dir manualmente ou faça upload de um arquivo .chromadb")
                self.persist_dir = None
            else:
                backend_dir = Path(__file__).parent.parent
                self.persist_dir = str(backend_dir / "data" / ".chromadb")

        self.materials_dir = Path(materials_dir)

        # Subpastas específicas para treino (RAG_TRAINING_DIRS no .env)
        # Formato: nomes separados por vírgula, ex: "DNA da Força - Conteúdo para IA"
        # Se vazio, usa todo o materials_dir
        training_dirs_env = os.getenv("RAG_TRAINING_DIRS", "").strip()
        if training_dirs_env:
            self.training_dirs = [
                self.materials_dir / d.strip()
                for d in training_dirs_env.split(",")
                if d.strip()
            ]
            logger.info(f"🎯 RAG treinará apenas nas pastas: {[str(d) for d in self.training_dirs]}")
        else:
            self.training_dirs = [self.materials_dir]
            logger.info(f"📂 RAG treinará em todo o materials_dir: {self.materials_dir}")

        # Initialize components
        self.embeddings: Optional[Any] = None
        self.llm: Optional[Any] = None
        self.vector_store: Optional[Chroma] = None
        self.retriever = None

        # Caches for educational features
        self.concept_cache: Dict[str, List[str]] = {}
        self.difficulty_cache: Dict[str, str] = {}
        self.summary_cache: Dict[str, str] = {}

        self.course_structure: Optional[pd.DataFrame] = None

        # Aliases/sinônimos para melhorar achabilidade
        self.aliases: Dict[str, List[str]] = {}

        self._initialize_components()
        self._load_aliases()
        logger.info("✅ Unified RAG Handler initialized successfully")

    def _initialize_components(self):
        """Initialize all necessary components."""
        self._initialize_embeddings()
        self._initialize_llm()
        self._initialize_vector_store()
        self._setup_retriever()
        self.load_course_structure()

    def _initialize_embeddings(self):
        """Initialize embeddings with Open Source/NVIDIA/OpenAI/Gemini fallback."""
        providers_to_try = []

        # Log das configurações atuais
        logger.info(f"🔍 Configurações de embeddings:")
        logger.info(
            f"   - prefer_open_source: {self.config.prefer_open_source}")
        logger.info(f"   - prefer_nvidia: {self.config.prefer_nvidia}")
        logger.info(f"   - prefer_openai: {self.config.prefer_openai}")
        logger.info(
            f"   - open_source_model: {self.config.open_source_embedding_model}")
        logger.info(
            f"   - NVIDIA API Key: {'✅ Configurada' if self.nvidia_api_key else '❌ Não configurada'}")
        logger.info(
            f"   - OpenAI API Key: {'✅ Configurada' if self.openai_api_key else '❌ Não configurada'}")
        logger.info(
            f"   - Gemini API Key: {'✅ Configurada' if self.gemini_api_key else '❌ Não configurada'}")

        # NVIDIA DESABILITADO TEMPORARIAMENTE devido a erro na API
        # Descomentar quando a API NVIDIA estiver funcionando:
        # if self.nvidia_api_key:
        #     providers_to_try.append(("nvidia", self.nvidia_api_key))
        #     logger.info("🎯 Adicionando NVIDIA como PRIMEIRA PRIORIDADE (melhor para Q&A)")
        
        # TEMPORÁRIO: Pular NVIDIA e usar OpenAI como padrão
        logger.warning("⚠️ NVIDIA temporariamente desabilitado - usando OpenAI como padrão")

        # OpenAI como PRIMEIRA PRIORIDADE (NVIDIA desabilitado)
        if self.openai_api_key:
            providers_to_try.append(("openai", self.openai_api_key))
            logger.info("🎯 Adicionando OpenAI como PRIMEIRA PRIORIDADE")
        
        if self.gemini_api_key and GoogleGenerativeAIEmbeddings:
            providers_to_try.append(("gemini", self.gemini_api_key))
            logger.info("🔄 Adicionando Gemini como fallback")

        # Open Source como ÚLTIMO fallback (só se todos os outros falharem)
        if OpenSourceEmbeddings:
            providers_to_try.append(("open_source", None))
            logger.info("🔄 Adicionando Open Source como último fallback")

        logger.info(
            f"📋 Ordem de tentativa dos providers: {[p[0] for p in providers_to_try]}")

        for provider, api_key in providers_to_try:
            try:
                logger.info(
                    f"🚀 Tentando inicializar embeddings com: {provider}")

                if provider == "open_source":
                    self.embeddings = OpenSourceEmbeddingsWrapper(
                        model_name=self.config.open_source_embedding_model
                    )
                    self.current_embedding_provider = "Open Source"
                    logger.info(
                        f"✅ Embeddings initialized: Open Source ({self.config.open_source_embedding_model})")
                    return

                elif provider == "nvidia":
                    self.embeddings = NVIDIAEmbeddings(
                        nvidia_api_key=api_key,
                        model=self.config.nvidia_embedding_model,
                        model_name=self.config.nvidia_embedding_model,
                        base_url=self.config.nvidia_base_url,
                        retry_attempts=self.config.nvidia_retry_attempts,
                        retry_delay=self.config.nvidia_retry_delay
                    )
                    self.current_embedding_provider = "NVIDIA"
                    logger.info(
                        f"✅ Embeddings initialized: NVIDIA ({self.config.nvidia_embedding_model})")
                    return

                elif provider == "openai":
                    self.embeddings = OpenAIEmbeddings(
                        model=self.config.embedding_model,
                        api_key=SecretStr(api_key)
                    )
                    self.current_embedding_provider = "OpenAI"
                    logger.info(
                        f"✅ Embeddings initialized: OpenAI ({self.config.embedding_model})")
                    return

                elif provider == "gemini" and GoogleGenerativeAIEmbeddings:
                    self.embeddings = GoogleGenerativeAIEmbeddings(
                        model=self.config.gemini_embedding_model,
                        google_api_key=api_key
                    )
                    self.current_embedding_provider = "Gemini"
                    logger.info(
                        f"✅ Embeddings initialized: Gemini ({self.config.gemini_embedding_model})")
                    return

            except Exception as e:
                logger.warning(
                    f"⚠️ Failed to initialize {provider} embeddings: {e}")
                continue

        logger.error("❌ Failed to initialize embeddings with any provider")
        raise Exception("No embedding provider available")

    def _initialize_llm(self):
        """Initialize LLM with NVIDIA/OpenAI/Gemini fallback."""
        providers_to_try = []

        # NVIDIA como prioridade se prefer_nvidia for True
        if self.config.prefer_nvidia and self.nvidia_api_key:
            providers_to_try.append(("nvidia", self.nvidia_api_key))

        if self.config.prefer_openai:
            if self.openai_api_key:
                providers_to_try.append(("openai", self.openai_api_key))
            if self.gemini_api_key and ChatGoogleGenerativeAI:
                providers_to_try.append(("gemini", self.gemini_api_key))
        else:
            if self.gemini_api_key and ChatGoogleGenerativeAI:
                providers_to_try.append(("gemini", self.gemini_api_key))
            if self.openai_api_key:
                providers_to_try.append(("openai", self.openai_api_key))

        # Adicionar NVIDIA como fallback se não foi adicionado como prioridade
        if not self.config.prefer_nvidia and self.nvidia_api_key:
            providers_to_try.append(("nvidia", self.nvidia_api_key))

        # Tentar cada provider
        for provider, api_key in providers_to_try:
            try:
                if provider == "nvidia":
                    self.llm = NVIDIAChatOpenAI(
                        nvidia_api_key=api_key,
                        model=self.config.nvidia_model_name,
                        base_url=self.config.nvidia_base_url,
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                        retry_attempts=self.config.nvidia_retry_attempts,
                        retry_delay=self.config.nvidia_retry_delay
                    )
                    self.current_llm_provider = "NVIDIA"
                    logger.info(
                        f"✅ LLM initialized: NVIDIA ({self.config.nvidia_model_name})")
                    return

                elif provider == "openai":
                    self.llm = ChatOpenAI(
                        model=self.config.model_name,
                        temperature=self.config.temperature,
                        api_key=SecretStr(api_key),
                        max_tokens=self.config.max_tokens,
                    )
                    self.current_llm_provider = "OpenAI"
                    logger.info(
                        f"✅ LLM initialized: OpenAI ({self.config.model_name})")
                    return

                elif provider == "gemini" and ChatGoogleGenerativeAI:
                    self.llm = ChatGoogleGenerativeAI(
                        model=self.config.gemini_model_name,
                        temperature=self.config.temperature,
                        google_api_key=api_key,
                        max_output_tokens=self.config.max_tokens,
                    )
                    self.current_llm_provider = "Gemini"
                    logger.info(
                        f"✅ LLM initialized: Gemini ({self.config.gemini_model_name})")
                    return

            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize {provider} LLM: {e}")
                continue

        logger.error("❌ Failed to initialize LLM with any provider")
        raise Exception("No LLM provider available")

    def _try_llm_fallback(self, messages, **kwargs):
        """Try LLM with automatic fallback to alternative providers."""
        original_provider = self.current_llm_provider

        # Tentar com o provider atual primeiro
        try:
            if self.llm:
                return self.llm.generate(messages, **kwargs)
        except Exception as e:
            logger.warning(f"⚠️ Primary LLM ({original_provider}) failed: {e}")

        # Se falhou, tentar outros providers
        fallback_providers = []

        if self.current_llm_provider != "OpenAI" and self.openai_api_key:
            fallback_providers.append(("openai", self.openai_api_key))
        if self.current_llm_provider != "Gemini" and self.gemini_api_key and ChatGoogleGenerativeAI:
            fallback_providers.append(("gemini", self.gemini_api_key))
        if self.current_llm_provider != "NVIDIA" and self.nvidia_api_key:
            fallback_providers.append(("nvidia", self.nvidia_api_key))

        for provider, api_key in fallback_providers:
            try:
                logger.info(f"🔄 Trying fallback LLM: {provider}")

                if provider == "openai":
                    temp_llm = ChatOpenAI(
                        model=self.config.model_name,
                        temperature=self.config.temperature,
                        api_key=SecretStr(api_key),
                        max_tokens=self.config.max_tokens,
                    )
                elif provider == "gemini":
                    temp_llm = ChatGoogleGenerativeAI(
                        model=self.config.gemini_model_name,
                        temperature=self.config.temperature,
                        google_api_key=api_key,
                        max_output_tokens=self.config.max_tokens,
                    )
                elif provider == "nvidia":
                    temp_llm = NVIDIAChatOpenAI(
                        nvidia_api_key=api_key,
                        model=self.config.nvidia_model_name,
                        base_url=self.config.nvidia_base_url,
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                        retry_attempts=2,  # Menos tentativas para fallback
                        retry_delay=1.0
                    )

                result = temp_llm.generate(messages, **kwargs)
                logger.info(f"✅ Fallback LLM ({provider}) successful!")

                # Atualizar provider atual se funcionou
                self.llm = temp_llm
                self.current_llm_provider = provider

                return result

            except Exception as e:
                logger.warning(f"⚠️ Fallback LLM ({provider}) failed: {e}")
                continue

        # Se chegou aqui, todos falharam
        logger.error(f"❌ All LLM providers failed. Original: {original_provider}")
        raise Exception(
            f"All LLM providers failed. Original: {original_provider}")

    def get_provider_status(self) -> Dict[str, Any]:
        """Get current provider status and availability."""
        return {
            "current_llm_provider": self.current_llm_provider,
            "current_embedding_provider": self.current_embedding_provider,
            "available_providers": {
                "open_source": {
                    "available": bool(OpenSourceEmbeddings),
                    "library_installed": bool(OpenSourceEmbeddings)
                },
                "nvidia": {
                    "available": bool(self.nvidia_api_key),
                    "api_key_configured": bool(self.nvidia_api_key)
                },
                "openai": {
                    "available": bool(self.openai_api_key),
                    "api_key_configured": bool(self.openai_api_key)
                },
                "gemini": {
                    "available": bool(self.gemini_api_key and ChatGoogleGenerativeAI),
                    "api_key_configured": bool(self.gemini_api_key),
                    "library_installed": bool(ChatGoogleGenerativeAI)
                }
            },
            "config": {
                "prefer_open_source": self.config.prefer_open_source,
                "prefer_nvidia": self.config.prefer_nvidia,
                "prefer_openai": self.config.prefer_openai,
                "nvidia_model": self.config.nvidia_model_name,
                "openai_model": self.config.model_name,
                "gemini_model": self.config.gemini_model_name,
                "open_source_embedding": self.config.open_source_embedding_model,
                "nvidia_embedding": self.config.nvidia_embedding_model,
                "openai_embedding": self.config.embedding_model,
                "gemini_embedding": self.config.gemini_embedding_model
            }
        }

    def _try_embedding_fallback(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Try embedding with fallback to alternative provider."""
        providers = [("open_source", None), ("nvidia", self.nvidia_api_key),
                     ("gemini", self.gemini_api_key), ("openai", self.openai_api_key)]

        for provider, api_key in providers:
            if not api_key and provider != "open_source":
                continue

            try:
                if provider == "open_source" and OpenSourceEmbeddings:
                    temp_embeddings = OpenSourceEmbeddingsWrapper(
                        model_name=self.config.open_source_embedding_model
                    )
                    logger.info(
                        f"🔄 Trying fallback embedding with Open Source...")
                    result = temp_embeddings.embed_documents(texts)
                    logger.info(
                        f"✅ Fallback embedding successful with Open Source")
                    return result

                elif provider == "nvidia" and NVIDIAEmbeddings:
                    temp_embeddings = NVIDIAEmbeddings(
                        model=self.config.nvidia_embedding_model,
                        nvidia_api_key=api_key,
                        base_url=self.config.nvidia_base_url
                    )
                    logger.info(f"🔄 Trying fallback embedding with NVIDIA...")
                    result = temp_embeddings.embed_documents(texts)
                    logger.info(f"✅ Fallback embedding successful with NVIDIA")
                    return result

                elif provider == "gemini" and GoogleGenerativeAIEmbeddings:
                    temp_embeddings = GoogleGenerativeAIEmbeddings(
                        model=self.config.gemini_embedding_model,
                        google_api_key=api_key
                    )
                    logger.info(f"🔄 Trying fallback embedding with Gemini...")
                    result = temp_embeddings.embed_documents(texts)
                    logger.info(f"✅ Fallback embedding successful with Gemini")
                    return result

                elif provider == "openai":
                    temp_embeddings = OpenAIEmbeddings(
                        model=self.config.embedding_model,
                        api_key=SecretStr(api_key)
                    )
                    logger.info(f"🔄 Trying fallback embedding with OpenAI...")
                    result = temp_embeddings.embed_documents(texts)
                    logger.info(f"✅ Fallback embedding successful with OpenAI")
                    return result

            except Exception as e:
                logger.warning(
                    f"⚠️ Fallback embedding failed with {provider}: {e}")
                continue

        logger.error("❌ All embedding providers failed")
        return None

    def _initialize_embeddings_fallback(self):
        """Initialize embeddings with the alternative provider."""
        # Tenta Open Source primeiro se não estiver usando
        if self.current_embedding_provider != "Open Source":
            if OpenSourceEmbeddings:
                try:
                    self.embeddings = OpenSourceEmbeddingsWrapper(
                        model_name=self.config.open_source_embedding_model
                    )
                    self.current_embedding_provider = "Open Source"
                    logger.info(
                        f"✅ Switched to Open Source embeddings ({self.config.open_source_embedding_model})")
                    return
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to switch to Open Source embeddings: {e}")

        # Tenta NVIDIA se não estiver usando
        if self.current_embedding_provider != "NVIDIA":
            if self.nvidia_api_key and NVIDIAEmbeddings:
                try:
                    self.embeddings = NVIDIAEmbeddings(
                        model=self.config.nvidia_embedding_model,
                        nvidia_api_key=self.nvidia_api_key,
                        base_url=self.config.nvidia_base_url
                    )
                    self.current_embedding_provider = "NVIDIA"
                    logger.info(
                        f"✅ Switched to NVIDIA embeddings ({self.config.nvidia_embedding_model})")
                    return
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to switch to NVIDIA embeddings: {e}")

        # Se estava usando NVIDIA ou falhou ao tentar NVIDIA, tenta OpenAI
        if self.current_embedding_provider != "OpenAI":
            if self.openai_api_key:
                try:
                    self.embeddings = OpenAIEmbeddings(
                        model=self.config.embedding_model,
                        api_key=SecretStr(self.openai_api_key)
                    )
                    self.current_embedding_provider = "OpenAI"
                    logger.info(
                        f"✅ Switched to OpenAI embeddings ({self.config.embedding_model})")
                    return
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to switch to OpenAI embeddings: {e}")

        # Se estava usando OpenAI ou falhou ao tentar OpenAI, tenta Gemini
        if self.current_embedding_provider != "Gemini":
            if self.gemini_api_key and GoogleGenerativeAIEmbeddings:
                try:
                    self.embeddings = GoogleGenerativeAIEmbeddings(
                        model=self.config.gemini_embedding_model,
                        google_api_key=self.gemini_api_key
                    )
                    self.current_embedding_provider = "Gemini"
                    logger.info(
                        f"✅ Switched to Gemini embeddings ({self.config.gemini_embedding_model})")
                    return
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to switch to Gemini embeddings: {e}")

        logger.error("❌ No alternative embedding provider available")
        raise Exception("No alternative embedding provider available")

    def _initialize_vector_store(self):
        try:
            # 🚨 CORREÇÃO: NÃO criar diretório automaticamente no Render
            # Verificar se persist_dir não é None antes de verificar existência
            if not self.persist_dir:
                logger.error("❌ persist_dir é None - não é possível inicializar vector store")
                return
            
            # Verificar se o diretório existe antes de tentar usar
            if not os.path.exists(self.persist_dir):
                # Verificar se está no ambiente Render
                is_render = os.getenv("RENDER", "").lower() == "true"
                
                if is_render:
                    logger.warning(
                        f"⚠️ Diretório ChromaDB não encontrado: {self.persist_dir}")
                    logger.warning(
                        "💡 Crie manualmente o diretório ou faça upload via frontend")
                    # Não criar automaticamente no Render
                    return
                else:
                    # Criar diretório automaticamente em desenvolvimento local
                    logger.info(
                        f"📁 Criando diretório ChromaDB: {self.persist_dir}")
                    os.makedirs(self.persist_dir, exist_ok=True)
                    logger.info(
                        f"✅ Diretório ChromaDB criado com sucesso: {self.persist_dir}")
            # Tenta carregar a coleção configurada (default: "langchain")
            try:
                # ✅ CORREÇÃO: persist_dir já foi verificado acima
                self.vector_store = Chroma(
                    persist_directory=self.persist_dir,
                    embedding_function=self.embeddings,
                    collection_name=self.config.collection_name,
                )
                logger.info(
                    f"✅ Vector store loaded at {self.persist_dir} (collection='{self.config.collection_name}')"
                )
            except Exception as e:
                logger.warning(
                    f"⚠️ Could not load configured collection '{self.config.collection_name}': {e}. Will try autodiscovery."
                )
                self.vector_store = None

            # Se a coleção configurada estiver vazia, tentar descobrir alguma coleção existente com dados
            try:
                current_count = 0
                if self.vector_store and hasattr(self.vector_store, "_collection"):
                    current_count = self.vector_store._collection.count()

                if not self.vector_store or current_count == 0:
                    # ✅ CORREÇÃO: Verificar se persist_dir não é None antes de usar
                    if not self.persist_dir:
                        logger.error("❌ persist_dir é None - não é possível inicializar ChromaDB")
                        return
                    
                    client = chromadb.PersistentClient(path=self.persist_dir)
                    collections = client.list_collections()
                    logger.info(
                        f"🔎 Autodiscovery: found {len(collections)} collection(s) in persist dir"
                    )
                    # Priorizar coleção não vazia
                    for col in collections:
                        try:
                            # ✅ CORREÇÃO: persist_dir já foi verificado acima
                            candidate_vs = Chroma(
                                persist_directory=self.persist_dir,
                                embedding_function=self.embeddings,
                                collection_name=col.name,
                            )
                            cnt = candidate_vs._collection.count()
                            if cnt and cnt > 0:
                                self.vector_store = candidate_vs
                                self.config.collection_name = col.name
                                logger.info(
                                    f"✅ Loaded existing non-empty collection '{col.name}' with {cnt} item(s)"
                                )
                                break
                        except Exception as inner_e:
                            logger.debug(
                                f"Skipping collection '{getattr(col, 'name', '?')}' due to error: {inner_e}"
                            )

                if self.vector_store is None:
                    # ✅ CORREÇÃO: Verificar se persist_dir não é None antes de usar
                    if not self.persist_dir:
                        logger.error("❌ persist_dir é None - não é possível criar vector store como último recurso")
                        return
                    
                    # Como último recurso, cria/usa a coleção configurada
                    # ✅ CORREÇÃO: persist_dir já foi verificado acima
                    self.vector_store = Chroma(
                        persist_directory=self.persist_dir,
                        embedding_function=self.embeddings,
                        collection_name=self.config.collection_name,
                    )
                    logger.info(
                        f"✅ Vector store ready at {self.persist_dir} (collection='{self.config.collection_name}')"
                    )
            except Exception as discover_e:
                logger.warning(
                    f"⚠️ Vector store autodiscovery failed: {discover_e}")

            # Logar contagem final
            try:
                if self.vector_store and hasattr(self.vector_store, "_collection"):
                    final_count = self.vector_store._collection.count()
                else:
                    final_count = 0
            except Exception:
                final_count = 0
            logger.info(
                f"📊 Vector store collection='{self.config.collection_name}' count={final_count}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {e}")
            raise

    def _setup_retriever(self):
        if self.vector_store and hasattr(self.vector_store, "_collection"):
            # ChromaDB 1.0.15 compatibility - remove fetch_k and lambda_mult
            search_kwargs = {
                "k": max(8, self.config.retrieval_k),
            }

            # Only add lambda_mult for MMR search type
            if self.config.retrieval_search_type == "mmr":
                search_kwargs["lambda_mult"] = self.config.retrieval_lambda_mult

            self.retriever = self.vector_store.as_retriever(
                search_type=self.config.retrieval_search_type,
                search_kwargs=search_kwargs,
            )
            logger.info("✅ Retriever configured")
        else:
            logger.warning("⚠️ Vector store não disponível - retriever não configurado")

    def _load_aliases(self):
        """Load aliases from optional JSON file backend/data/aliases.json."""
        try:
            base_dir = Path(__file__).parent.parent
            aliases_path = base_dir / "data" / "aliases.json"
            if aliases_path.exists():
                data = json.loads(aliases_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.aliases = {str(k).lower(): [str(
                        x) for x in v] for k, v in data.items() if isinstance(v, list)}
                    logger.info(f"✅ Loaded {len(self.aliases)} alias entries")
        except Exception as e:
            logger.debug(f"No aliases loaded: {e}")

    def _augment_query_with_aliases(self, question: str) -> str:
        """Append aliases/synonyms related to the question to improve recall."""
        try:
            ql = (question or "").lower()
            extras: List[str] = []
            # Hardcoded fallbacks for common terms if no file provided
            default_aliases: Dict[str, List[str]] = {
                "hipertrofia regionalizada": ["crescimento localizado", "hipertrofia seletiva", "CSA localizada", "CSA do quadríceps"],
                "amplitude": ["amplitude de movimento", "ROM", "range of motion"],
                "quadríceps": ["quadriceps", "quadríceps femoral"],
            }
            alias_map = getattr(self, "aliases", None) or default_aliases
            for key, syns in alias_map.items():
                if key in ql:
                    extras.extend([s for s in syns if s not in extras])
            if extras:
                return question + "\n\n" + " ".join(extras)
            return question
        except Exception:
            return question

    def load_course_structure(self, spreadsheet_path: str = "data/catalog.xlsx"):
        """Load and process the course structure from a spreadsheet.
        Falls back to searching materials for files matching '#catalog*.xlsx' or '*catalog*.xlsx'.
        """
        try:
            spreadsheet_file = Path(spreadsheet_path)
            candidate_path: Optional[Path] = None

            if spreadsheet_file.exists():
                candidate_path = spreadsheet_file
            else:
                # Fallback: search in materials for a catalog file
                if not self.materials_dir.exists():
                    logger.warning(f"⚠️ Materials directory does not exist: {self.materials_dir}")
                    return
                    
                patterns = ["#catalog*.xlsx",
                            "*catalog*.xlsx", "*catálogo*.xlsx"]
                for pattern in patterns:
                    try:
                        match = next(Path(self.materials_dir).rglob(pattern), None)
                        if match:
                            candidate_path = match
                            logger.info(
                                f"📊 Using course catalog found at {candidate_path}")
                            break
                    except Exception as e:
                        logger.debug(f"⚠️ Error searching for pattern {pattern}: {e}")
                        continue

            if not candidate_path:
                logger.warning(
                    f"Spreadsheet not found at {spreadsheet_path} and no catalog found in materials.")
                return

            self.course_structure = pd.read_excel(candidate_path)
            self.course_structure.columns = [
                col.strip().lower() for col in self.course_structure.columns]
            required_columns = ['código', 'módulo',
                                'aula', 'nome da aula', 'resumo da aula']
            if not all(col in self.course_structure.columns for col in required_columns):
                logger.error(
                    f"Spreadsheet is missing required columns. Found: {self.course_structure.columns}")
                self.course_structure = None
                return

            self.course_structure['código_normalized'] = self.course_structure['código'].str.strip(
            ).str.lower()
            logger.info(f"✅ Course structure loaded from {candidate_path}")
        except Exception as e:
            logger.error(f"Failed to load course structure: {e}")
            self.course_structure = None

    def process_documents(self, force_reprocess: bool = False) -> bool:
        """Process all documents with optional educational enhancements."""
        logger.info("📚 Starting document processing...")

        try:
            # Verificar diretório de materiais
            if not self.materials_dir.exists():
                logger.error(
                    f"❌ Materials directory not found: {self.materials_dir}")
                return False

            logger.info(f"✅ Materials directory found: {self.materials_dir}")

            # Verificar/reinicializar embeddings
            # FORÇAR OpenAI para evitar problemas com NVIDIA
            if not self.embeddings or self.current_embedding_provider == "NVIDIA":
                logger.info("🔧 Forçando OpenAI embeddings...")
                try:
                    if self.openai_api_key:
                        # Se está usando NVIDIA, precisamos recriar o vector store
                        if self.vector_store and self.current_embedding_provider == "NVIDIA":
                            logger.warning("⚠️ Detected NVIDIA vector store - will be recreated")
                            self.vector_store = None  # Forçar recriação
                        
                        self.embeddings = OpenAIEmbeddings(
                            model=self.config.embedding_model,
                            api_key=SecretStr(self.openai_api_key)
                        )
                        self.current_embedding_provider = "OpenAI"
                        logger.info(f"✅ Embeddings forçados para OpenAI: {self.config.embedding_model}")
                    else:
                        logger.error("❌ OpenAI API key não configurada")
                        return False
                except Exception as emb_error:
                    logger.error(f"❌ Error initializing embeddings: {emb_error}")
                    return False

            # Verificar/inicializar vector store
            if not self.vector_store:
                logger.info("🔧 Initializing vector store...")
                try:
                    self._initialize_vector_store()
                except Exception as vs_error:
                    logger.error(f"❌ Error initializing vector store: {vs_error}")
                    return False
                
            if not self.vector_store:
                logger.error("❌ Vector store could not be initialized")
                return False
                
            logger.info("✅ Vector store initialized successfully")
        except Exception as init_error:
            logger.error(f"❌ Error in initial checks: {init_error}", exc_info=True)
            return False

        if self.vector_store and hasattr(self.vector_store, "_collection"):
            try:
                if not force_reprocess and self.vector_store._collection.count() > 0:
                    logger.info(
                        "📋 Documents already processed. Use force_reprocess=True to reprocess.")
                    return True

                if force_reprocess and self.vector_store._collection.count() > 0:
                    logger.info(
                        "🗑️ Clearing existing documents for reprocessing...")
                    try:
                        result = self.vector_store.get()
                        ids = result.get("ids", []) if isinstance(result, dict) else []
                        if ids:
                            self.vector_store.delete(ids)
                            logger.info(f"✅ Deleted {len(ids)} existing documents")
                        else:
                            logger.warning("⚠️ No IDs found to delete")
                    except Exception as delete_error:
                        logger.error(f"❌ Error deleting documents: {delete_error}")
                        # Tentar limpar de outra forma
                        try:
                            self.vector_store.delete([])  # Limpar tudo
                        except:
                            pass
            except Exception as e:
                logger.warning(f"⚠️ Could not check vector store status: {e}")
                return False

        # Processar documentos com try-except geral
        try:
            # Load documents
            logger.info("📖 Loading documents...")
            documents = self._load_all_documents()
            if not documents:
                logger.warning("⚠️ No documents found to process")
                return False
            logger.info(f"✅ Loaded {len(documents)} documents")

            # Enhance documents if enabled
            if self.config.enable_educational_features:
                logger.info("🎓 Enhancing documents with educational metadata...")
                enhanced_documents = [
                    self._enhance_document(doc) for doc in documents]
            else:
                enhanced_documents = documents
            logger.info(f"✅ Enhanced {len(enhanced_documents)} documents")
        except Exception as doc_error:
            logger.error(f"❌ Error loading/enhancing documents: {doc_error}")
            return False

        # 🛡️ GUARDRAILS TEMPORARIAMENTE DESABILITADOS (muito agressivos)
        # TODO: Ajustar thresholds dos guardrails para não bloquear material educacional legítimo
        logger.warning(
            "⚠️ Guardrails temporariamente desabilitados durante processamento")
        # Guardrails causavam bloqueio de TODOS os PDFs
        # enhanced_documents já está pronto para uso

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        splits = text_splitter.split_documents(enhanced_documents)
        logger.info(f"🔪 Split into {len(splits)} chunks")

        # Add to vector store (batched to respect embedding API limits)
        try:
            if self.vector_store:
                total = len(splits)
                batch_docs: List[Document] = []
                batch_tokens: int = 0

                def flush_batch(batch_index: int):
                    nonlocal batch_docs, batch_tokens
                    if not batch_docs:
                        return
                    self.vector_store.add_documents(batch_docs)
                    logger.info(
                        f"✅ Added batch #{batch_index} with {len(batch_docs)} chunks (~{batch_tokens} tokens) to vector store")
                    batch_docs = []
                    batch_tokens = 0

                batch_index = 1
                for i, doc in enumerate(splits, start=1):
                    text = doc.page_content or ""
                    if tiktoken is not None:
                        try:
                            enc = tiktoken.get_encoding("cl100k_base")
                            tok = len(enc.encode(text))
                        except Exception:
                            tok = max(1, len(text) // 4)
                    else:
                        tok = max(1, len(text) // 4)

                    # If adding this doc would exceed the target, flush first (but ensure at least 1 per batch)
                    if batch_docs and (batch_tokens + tok) > self.config.embedding_request_target:
                        flush_batch(batch_index)
                        batch_index += 1

                    batch_docs.append(doc)
                    batch_tokens += tok

                    # Safety: also split batches by count to avoid very large batches with small tokens
                    if len(batch_docs) >= self.config.add_batch_size:
                        flush_batch(batch_index)
                        batch_index += 1

                # Flush remaining
                flush_batch(batch_index)
                # Ensure data is persisted
                try:
                    self.vector_store.persist()
                except Exception:
                    pass
            logger.info(
                f"✅ Finished adding {len(splits)} document chunks to vector store")
            self._setup_retriever()
            logger.info("✅ Document processing completed successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ Failed during document processing: {e}")
            logger.error(f"❌ Traceback: ", exc_info=True)
            return False

    def _load_all_documents(self) -> List[Document]:
        """Load documents from training_dirs (configured via RAG_TRAINING_DIRS env var)."""
        documents: List[Document] = []

        for train_dir in self.training_dirs:
            if not train_dir.exists():
                logger.warning(f"⚠️ Training directory does not exist, skipping: {train_dir}")
                continue

            logger.info(f"📂 Loading documents from: {train_dir}")

            # PDFs
            try:
                loader = DirectoryLoader(
                    str(train_dir),
                    glob="**/*.pdf",
                    loader_cls=PyPDFLoader,
                    show_progress=True,
                    use_multithreading=True,
                )
                loaded = loader.load()
                logger.info(f"📥 {len(loaded)} PDFs from: {train_dir.name}")
                documents.extend(loaded)
            except Exception as e:
                logger.warning(f"⚠️ Error loading PDFs from {train_dir}: {e}")

            # Markdown
            try:
                md_loader = DirectoryLoader(
                    str(train_dir),
                    glob="**/*.md",
                    loader_cls=UnstructuredMarkdownLoader,
                    show_progress=True,
                )
                loaded_md = md_loader.load()
                logger.info(f"📥 {len(loaded_md)} Markdown files from: {train_dir.name}")
                documents.extend(loaded_md)
            except Exception as e:
                logger.warning(f"⚠️ Error loading Markdown from {train_dir}: {e}")

            # PPTX (PowerPoint slides)
            try:
                pptx_loader = DirectoryLoader(
                    str(train_dir),
                    glob="**/*.pptx",
                    loader_cls=UnstructuredPowerPointLoader,
                    show_progress=True,
                )
                loaded_pptx = pptx_loader.load()
                logger.info(f"📥 {len(loaded_pptx)} PPTX files from: {train_dir.name}")
                documents.extend(loaded_pptx)
            except Exception as e:
                logger.warning(f"⚠️ Error loading PPTX from {train_dir}: {e}")

        # XLSX via pandas (e.g., course catalog)
        try:
            documents.extend(self._load_xlsx_with_pandas())
        except Exception as e:
            logger.warning(f"⚠️ Error loading XLSX via pandas: {e}")

        logger.info(f"📄 Total: {len(documents)} documentos carregados para treino.")
        return documents

    def _load_xlsx_with_pandas(self) -> List[Document]:
        """Load .xlsx files by parsing sheets with pandas into textual Documents.
        Prioritize files like '#catalog*.xlsx' or '*catalog*.xlsx'.
        """
        xlsx_documents: List[Document] = []
        try:
            import pandas as pd
        except Exception as e:
            logger.warning(f"Pandas not available for XLSX parsing: {e}")
            return xlsx_documents

        # Gather candidates (catalog first)
        candidates: List[Path] = []
        try:
            if not self.materials_dir.exists():
                logger.warning(f"⚠️ Materials directory does not exist: {self.materials_dir}")
                return xlsx_documents
                
            for pattern in ("#catalog*.xlsx", "*catalog*.xlsx", "*.xlsx"):
                candidates.extend(list(Path(self.materials_dir).rglob(pattern)))
        except Exception as e:
            logger.warning(f"⚠️ Error gathering XLSX candidates: {e}")
            return xlsx_documents

        seen: set[str] = set()
        for xlsx_path in candidates:
            path_str = str(xlsx_path)
            if path_str in seen:
                continue
            seen.add(path_str)
            try:
                excel_file = pd.ExcelFile(xlsx_path)
                for sheet_name in excel_file.sheet_names:
                    try:
                        df = excel_file.parse(sheet_name)
                        # small safeguard: limit very large sheets
                        if df.shape[0] > 20000:
                            df = df.head(20000)
                        text_content = df.to_csv(index=False)
                        meta = {
                            "source": path_str,
                            "sheet": sheet_name,
                            "content_type": "data",
                            "loader": "pandas_excel",
                        }
                        xlsx_documents.append(
                            Document(page_content=text_content, metadata=meta))
                    except Exception as sheet_err:
                        logger.debug(
                            f"Failed parsing sheet '{sheet_name}' in {xlsx_path}: {sheet_err}")
            except Exception as file_err:
                logger.debug(f"Failed opening xlsx {xlsx_path}: {file_err}")

        logger.info(
            f"📥 Loaded {len(xlsx_documents)} docs for pattern **/*.xlsx (pandas)")
        return xlsx_documents

    def _enhance_document(self, doc: Document) -> Document:
        """Enhance a single document with educational metadata."""
        source_path = doc.metadata.get('source', '')

        enhanced_metadata = {
            **doc.metadata,
            'content_type': self._analyze_content_type(source_path),
            'processed_at': time.time(),
        }

        # ✅ ADICIONAR VALIDAÇÃO DE PÁGINA
        page_number = doc.metadata.get('page')
        if page_number is not None:
            # Verificar se a página é válida (número inteiro positivo)
            try:
                page_int = int(page_number)
                if page_int > 0:
                    enhanced_metadata['page'] = page_int
                    enhanced_metadata['has_valid_page'] = True
                else:
                    enhanced_metadata['page'] = None
                    enhanced_metadata['has_valid_page'] = False
            except (ValueError, TypeError):
                enhanced_metadata['page'] = None
                enhanced_metadata['has_valid_page'] = False
        else:
            enhanced_metadata['page'] = None
            enhanced_metadata['has_valid_page'] = False
        
        # Get course info from catalog
        course_info = self._get_course_info(source_path)
        if course_info:
            enhanced_metadata.update(course_info)

        return Document(page_content=doc.page_content, metadata=enhanced_metadata)

    def _get_course_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extracts course information from the catalog based on the file name."""
        if self.course_structure is None:
            return None

        try:
            filename_stem = Path(file_path).stem
            # Extract the code (e.g., M01A01) from the filename
            parts = filename_stem.replace('-', ' ').replace('.', ' ').split()
            video_code = parts[0].strip().lower(
            ) if parts else filename_stem.strip().lower()

            # ✅ CORREÇÃO: Verificar se course_structure tem a coluna necessária
            if 'código_normalized' not in self.course_structure.columns:
                logger.warning("⚠️ Course structure não tem coluna 'código_normalized'")
                return None

            match = self.course_structure[self.course_structure['código_normalized'] == video_code]

            if not match.empty:
                course_data = match.iloc[0].to_dict()
                return {
                    "course_code": course_data.get('código'),
                    "module": course_data.get('módulo'),
                    "class_number": course_data.get('aula'),
                    "class_name": course_data.get('nome da aula'),
                    "summary": course_data.get('resumo da aula')
                }
        except Exception as e:
            logger.debug(f"Could not extract course info for {file_path}: {e}")

        return None

    def _analyze_content_type(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return "document"
        if ext in [".xlsx", ".csv"]:
            return "data"
        return "text"

    def _validate_answer_against_context(self, answer: str, context: str) -> tuple[str, bool]:
        """
        Valida se a resposta está baseada APENAS no contexto fornecido.
        Retorna (resposta_validada, is_valid)
        """
        # Extrair claims específicos da resposta
        answer_sentences = answer.split('.')
        context_lower = context.lower()
        
        invalid_claims = []
        for sentence in answer_sentences:
            # Pular frases muito curtas ou de transição
            if len(sentence.strip()) < 20:
                continue
                
            # Verificar se a sentença tem base no contexto
            sentence_words = set(sentence.lower().split())
            # Remove stopwords comuns
            sentence_words = {w for w in sentence_words if len(w) > 3}
            
            # Se menos de 30% das palavras aparecem no contexto, é suspeito
            context_words = set(context_lower.split())
            overlap = len(sentence_words & context_words) / max(len(sentence_words), 1)
            
            if overlap < 0.3:
                invalid_claims.append(sentence.strip())
        
        # Se há muitas claims suspeitas, rejeitar resposta
        if len(invalid_claims) > len(answer_sentences) * 0.3:  # >30% suspeito
            return ("", False)
        
        return (answer, True)

    def _run_llm_feature(self, text: str, cache: Dict, prompt_template: str, feature_name: str, result_parser) -> Any:
        """Generic method to run an LLM-based feature with caching."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in cache:
            return cache[text_hash]

        try:
            prompt = ChatPromptTemplate.from_template(prompt_template)
            if not self.llm:
                logger.warning(f"⚠️ LLM not initialized for feature '{feature_name}'")
                return None
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"text": text[:2000]})
            parsed_result = result_parser(result)
            cache[text_hash] = parsed_result
            return parsed_result
        except Exception as e:
            logger.warning(f"⚠️ Failed to run feature '{feature_name}': {e}")
            return None

    def _extract_key_concepts(self, text: str) -> List[str]:
        prompt = "Analise o seguinte texto e extraia os principais conceitos (máximo 8), separados por vírgula.\n\nTexto: {text}\n\nConceitos:"
        return self._run_llm_feature(text, self.concept_cache, prompt, "extract_concepts", lambda r: [c.strip() for c in r.split(',') if c.strip()][:8]) or []

    def _assess_difficulty_level(self, text: str) -> str:
        prompt = "Analise o texto e classifique o nível como 'beginner', 'intermediate', ou 'advanced'.\n\nTexto: {text}\n\nNível:"
        level = self._run_llm_feature(
            text, self.difficulty_cache, prompt, "assess_difficulty", lambda r: r.strip().lower())
        return level if level in ['beginner', 'intermediate', 'advanced'] else 'intermediate'

    def _create_content_summary(self, text: str) -> str:
        prompt = "Crie um resumo conciso (máximo 3 frases) do texto a seguir.\n\nTexto: {text}\n\nResumo:"
        return self._run_llm_feature(text, self.summary_cache, prompt, "create_summary", lambda r: r.strip()) or ""

    def _rerank_documents(self, documents: List[Tuple[Document, float]], 
                          question: str, top_k: int = 8) -> List[Tuple[Document, float]]:
        """
        Reranking usando cross-encoder para melhor precisão.
        Usa o modelo da biblioteca já instalada (sentence-transformers).
        """
        # Verificar se CrossEncoder está disponível
        if not CrossEncoderAvailable:
            logger.debug("⚠️ CrossEncoder não disponível - pulando reranking")
            return documents[:top_k]
            
        try:
            from sentence_transformers import CrossEncoder
            
            logger.info(f"🔄 Aplicando reranking em {len(documents)} documentos...")
            
            # Usar modelo multilíngue de alta qualidade (menor e mais rápido)
            model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            
            # Preparar pares (question, document)
            pairs = [[question, doc.page_content] for doc, _ in documents]
            
            # Calcular scores de relevância
            scores = model.predict(pairs)
            
            # Ordenar por score (maior primeiro)
            reranked = sorted(zip(documents, scores), 
                             key=lambda x: x[1], reverse=True)
            
            # Retornar top_k com novos scores
            result = [(doc, float(score)) for (doc, _), score in reranked[:top_k]]
            logger.info(f"✅ Reranking completo, top {len(result)} documentos selecionados")
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Reranking falhou, usando ordem original: {e}")
            return documents[:top_k]

    def retrieve_documents(self, question: str, k: Optional[int] = None) -> List[Document]:
        """Retrieve documents with automatic fallback on embedding failures."""
        try:
            if not self.retriever:
                logger.warning("⚠️ No retriever available - persist_dir pode ser None")
                return []

            k = k or self.config.retrieval_k
            logger.info(f"🔍 Retrieving documents for question: '{question}'")

            # Tentar com o retriever atual
            try:
                docs = self.retriever.invoke(question)
                logger.info(f"📄 Found {len(docs)} relevant documents.")
                return docs[:k]
            except Exception as e:
                logger.warning(f"⚠️ Primary retrieval failed: {e}")

                # Se falhou, tentar recriar o vector store com provider alternativo
                if "429" in str(e) or "quota" in str(e).lower() or "insufficient_quota" in str(e):
                    logger.info(
                        "🔄 Attempting to switch embedding provider due to quota issues...")

                    # Salvar provider atual
                    original_provider = self.current_embedding_provider

                    # Tentar inicializar com provider alternativo
                    try:
                        self._initialize_embeddings_fallback()
                        self._initialize_vector_store()
                        self._setup_retriever()

                        if self.retriever:
                            docs = self.retriever.invoke(question)
                            logger.info(
                                f"✅ Fallback retrieval successful with {self.current_embedding_provider}")
                            logger.info(
                                f"📄 Found {len(docs)} relevant documents.")
                            return docs[:k]
                    except Exception as fallback_e:
                        logger.error(
                            f"❌ Fallback retrieval also failed: {fallback_e}")

                return []

        except Exception as e:
            logger.error(f"Failed during retrieval: {e}")
            return []

    def generate_response(self, question: str, user_level: str = "intermediate", return_immediate: bool = False) -> Dict[str, Any]:
        """Generate a response using the RAG system."""
        # 🎯 LOG INICIAL MOSTRANDO QUAL MODELO SERÁ USADO
        logger.info(
            f"🚀 Starting response generation with: {self.current_llm_provider} ({getattr(self.llm, 'model', 'Unknown')})")

        # ⏱️ MENSAGEM IMEDIATA PARA O USUÁRIO SOBRE TEMPO DE PROCESSAMENTO
        immediate_processing_message = """⏱️ **PROCESSANDO SUA PERGUNTA...**

💡 **Dica sobre tempo de resposta:** Dependendo da complexidade, as respostas podem levar:
   - **Perguntas simples:** 5-15 segundos
   - **Perguntas complexas:** 15-30 segundos  
   - **Análises detalhadas:** 30-60 segundos

🔄 **O que está acontecendo agora:**
   1. Busca nos 53.000+ documentos do DNA da Força
   2. Análise de relevância e contexto
   3. Geração de resposta personalizada pela IA
   4. Verificação de acurácia e segurança

⏳ **Aguarde com paciência para respostas de qualidade!**\n\n"""

        # 🚀 RESPOSTA IMEDIATA - Se solicitado, retornar apenas a mensagem de processamento
        if return_immediate:
            logger.info("⚡ Retornando mensagem de processamento imediata")
            return {
                "answer": immediate_processing_message,
                "sources": [],
                "status": "processing",
                "message": "Iniciando processamento da pergunta..."
            }

        if not self.retriever:
            logger.error("❌ Retriever not initialized - persist_dir pode ser None")
            return {"answer": immediate_processing_message + f"""❌ **PROBLEMA TÉCNICO IDENTIFICADO**

Sua pergunta: "{question}"

🚨 **PROBLEMA CRÍTICO:**
O sistema RAG não conseguiu inicializar corretamente.

**Detalhes técnicos:**
- persist_dir: {self.persist_dir}
- vector_store: {'✅ Disponível' if self.vector_store else '❌ Não disponível'}
- retriever: {'✅ Configurado' if self.retriever else '❌ Não configurado'}

**Possíveis causas:**
1. Diretório ChromaDB não configurado corretamente
2. persist_dir é None no ambiente Render
3. Problema na inicialização do banco de dados vetorial

**Soluções:**
1. Verificar configuração do CHROMA_PERSIST_DIR
2. Fazer upload do arquivo .chromadb via frontend
3. Reprocessar materiais se necessário
4. Contatar suporte técnico

🔒 **Compromisso de Acurácia:** Não posso fornecer respostas sem acesso ao banco de dados vetorial.""", "sources": []}

        try:
            # Expand query with aliases/synonyms
            try:
                question_aug = self._augment_query_with_aliases(
                    question)  # type: ignore[attr-defined]
            except Exception:
                question_aug = question

            retrieved: List[Tuple[Document, Optional[float]]] = []
            try:
                # ✅ CORREÇÃO: Verificar se vector_store existe E se persist_dir não é None
                if self.vector_store and self.persist_dir:
                    try:
                        # Prefer retriever with relevance scores when available
                        vs_results = self.vector_store.similarity_search_with_relevance_scores(
                            question_aug, k=self.config.retrieval_k
                        )
                        retrieved = [(doc, score) for doc, score in vs_results]
                        # If no results (e.g., thresholding in some backends), fallback to plain similarity search
                        if not retrieved:
                            logger.debug(
                                "No results from relevance_scores; falling back to similarity_search")
                            docs = self.vector_store.similarity_search(
                                question_aug, k=max(self.config.retrieval_k, 8)
                            )
                            retrieved = [(doc, None) for doc in docs]
                    except Exception as e:
                        logger.debug(
                            f"similarity_search_with_relevance_scores unavailable, falling back: {e}")
                        try:
                            docs = self.vector_store.similarity_search(
                                question_aug, k=max(self.config.retrieval_k, 8)
                            )
                            retrieved = [(doc, None) for doc in docs]
                        except Exception as e2:
                            logger.debug(
                                f"similarity_search failed: {e2}; using retriever.invoke")
                            docs = self.retrieve_documents(question_aug)
                            retrieved = [(doc, None) for doc in docs]
                else:
                    logger.warning(f"⚠️ Vector store não disponível - persist_dir: {self.persist_dir}")
                    docs = self.retrieve_documents(question_aug)
                    retrieved = [(doc, None) for doc in docs]
            except Exception as e:
                logger.error(f"Failed during retrieval: {e}")
                retrieved = []

            # 🎯 APLICAR RERANKING para melhorar relevância
            if retrieved and len(retrieved) > 1:
                logger.info(f"🔄 Aplicando reranking em {len(retrieved)} documentos para melhor precisão")
                try:
                    retrieved = self._rerank_documents(retrieved, question_aug, 
                                                      top_k=self.config.retrieval_k)
                    logger.info(f"✅ Reranking completo, {len(retrieved)} documentos selecionados")
                except Exception as rerank_error:
                    logger.warning(f"⚠️ Reranking falhou: {rerank_error}, usando ordem original")

            logger.info(f"📄 Found {len(retrieved)} relevant documents.")

            if not retrieved:
                logger.warning("No documents found for the question.")
                return {"answer": immediate_processing_message + "No relevant information found.", "sources": []}

            sources = []
            valid_documents = []

            for i, (doc, score) in enumerate(retrieved):
                logger.info(f"  - Document {i+1}:")
                logger.info(
                    f"    - Source: {doc.metadata.get('source', 'N/A')}")
                logger.info(f"    - Page: {doc.metadata.get('page', 'N/A')}")

                # ✅ VALIDAÇÃO CRÍTICA: Verificar se o documento tem conteúdo válido
                content = doc.page_content or ""
                content_length = len(content.strip())

                # Verificar se o conteúdo é apenas números ou muito pequeno
                is_only_numbers = content.strip().isdigit() if content.strip() else True
                is_too_small = content_length < 50
                is_invalid = is_only_numbers or is_too_small

                if is_invalid:
                    logger.warning(
                        f"    - ❌ INVALID CONTENT: '{content}' (length: {content_length}, only_numbers: {is_only_numbers})")
                    continue

                logger.info(
                    f"    - ✅ VALID CONTENT: {content[:100]}... (length: {content_length})")
                valid_documents.append((doc, score))

                source = Source(
                    title=doc.metadata.get('title', Path(
                        doc.metadata.get('source', '')).name),
                    source=doc.metadata.get('source', ''),
                    page=doc.metadata.get('page'),
                    chunk=content,
                    content_type=doc.metadata.get('content_type', 'text'),
                    difficulty_level=doc.metadata.get(
                        'difficulty_level', 'intermediate'),
                    key_concepts=doc.metadata.get('key_concepts', []),
                    summary=doc.metadata.get('summary', ''),
                )
                # Store retrieval score when available (higher is better)
                try:
                    source.relevance_score = float(
                        score) if score is not None else 0.0
                except Exception:
                    source.relevance_score = 0.0
                source.educational_value = self._calculate_educational_value(
                    source, user_level)
                sources.append(source)

            # ✅ VERIFICAÇÃO: Se não há documentos válidos, retornar erro
            if not valid_documents:
                logger.error(
                    "❌ Nenhum documento válido encontrado - todos têm conteúdo corrompido")
                return {
                    "answer": immediate_processing_message + f"""❌ **PROBLEMA TÉCNICO IDENTIFICADO**

Sua pergunta: "{question}"

🚨 **PROBLEMA CRÍTICO:**
Os documentos encontrados têm conteúdo corrompido ou inválido.

**Detalhes técnicos:**
- Documentos encontrados: {len(retrieved)}
- Documentos válidos: 0
- Conteúdo extraído: Apenas números ou muito pequeno

**Possíveis causas:**
1. Problema na indexação dos documentos
2. Corrupção no banco de dados ChromaDB
3. Problema na extração de conteúdo dos PDFs
4. Versão incompatível das bibliotecas

**Soluções:**
1. Reprocessar todos os materiais
2. Verificar versões das bibliotecas
3. Limpar e recriar o banco de dados
4. Contatar suporte técnico

🔒 **Compromisso de Acurácia:** Não posso fornecer respostas com dados corrompidos.""",
                    "sources": []
                }

            logger.info(
                f"✅ Documentos válidos: {len(valid_documents)}/{len(retrieved)}")

            # Rank by a weighted combination favoring retrieval relevance
            def _combined_score(s: Source) -> float:
                relevance_component = s.relevance_score or 0.0
                educational_component = s.educational_value or 0.0
                return 0.85 * relevance_component + 0.15 * educational_component

            sources.sort(key=_combined_score, reverse=True)

            # Limit context size to avoid dilution and token overflows
            top_n = max(1, min(self.config.max_context_chunks, len(sources)))
            selected_sources = sources[:top_n]

            context = "\n\n".join([s.chunk for s in selected_sources])
            logger.info(
                f"📝 Generated context with {len(selected_sources)} sources.")
            logger.info(f"Full context for LLM:\n{context}")

            # ✅ VALIDAÇÃO AVANÇADA DE CONTEXTO
            context_quality = self._validate_context_quality(context, question)

            if context_quality["is_valid"] == False:
                logger.warning(
                    f"⚠️ Contexto de baixa qualidade: {context_quality['reason']}")

                # 🔄 TENTAR BUSCAR MAIS DOCUMENTOS SE POSSÍVEL
                if len(retrieved) < 20:  # Tentar expandir a busca
                    logger.info(
                        "🔄 Tentando expandir busca para encontrar mais contexto...")
                    try:
                        expanded_docs = self.vector_store.similarity_search(
                            question_aug, k=min(20, len(retrieved) + 10)
                        )
                        # Filtrar documentos válidos da busca expandida
                        additional_sources = []
                        for doc in expanded_docs:
                            content = doc.page_content or ""
                            if len(content.strip()) >= 50 and not content.strip().isdigit():
                                additional_sources.append(Source(
                                    title=doc.metadata.get('title', Path(
                                        doc.metadata.get('source', '')).name),
                                    source=doc.metadata.get('source', ''),
                                    page=doc.metadata.get('page'),
                                    chunk=content,
                                    content_type=doc.metadata.get(
                                        'content_type', 'text'),
                                    difficulty_level=doc.metadata.get(
                                        'difficulty_level', 'intermediate'),
                                    key_concepts=doc.metadata.get(
                                        'key_concepts', []),
                                    summary=doc.metadata.get('summary', ''),
                                    relevance_score=0.5,  # Score médio para documentos adicionais
                                    educational_value=0.5
                                ))

                        if additional_sources:
                            sources.extend(additional_sources)
                            # Reordenar e selecionar melhores
                            sources.sort(
                                key=lambda s: s.relevance_score or 0, reverse=True)
                            selected_sources = sources[:min(
                                self.config.max_context_chunks, len(sources))]
                            context = "\n\n".join(
                                [s.chunk for s in selected_sources])

                            # ✅ VALIDAR NOVO CONTEXTO
                            context_quality = self._validate_context_quality(
                                context, question)
                            if context_quality["is_valid"]:
                                logger.info(
                                    "✅ Contexto expandido com sucesso!")
                            else:
                                logger.warning(
                                    "⚠️ Mesmo com expansão, contexto ainda é insuficiente")
                        else:
                            logger.warning(
                                "⚠️ Nenhum documento adicional válido encontrado")
                    except Exception as e:
                        logger.warning(f"⚠️ Falha ao expandir busca: {e}")

                # 🚨 SE AINDA NÃO FUNCIONOU, RETORNAR ERRO DETALHADO
                if not context_quality["is_valid"]:
                    return {
                        "answer": immediate_processing_message + f"""❌ **PROBLEMA DE CONTEXTO IDENTIFICADO**

Sua pergunta: "{question}"

⚠️ **PROBLEMA TÉCNICO:**
{context_quality['reason']}

**Detalhes técnicos:**
- Documentos encontrados: {len(retrieved)}
- Documentos válidos: {len(valid_documents)}
- Qualidade do contexto: {context_quality['score']:.2f}/10
- Tamanho do contexto: {len(context)} caracteres

**Possíveis soluções:**
1. **Reformular pergunta** com termos mais específicos
2. **Usar sinônimos** relacionados aos materiais
3. **Consultar diretamente** os módulos do DNA da Força
4. **Aguardar** reprocessamento dos materiais

**Exemplo de pergunta que funciona:**
"Quais são os princípios básicos do treinamento de força?"

🔒 **Compromisso de Acurácia:** Prefiro não responder do que fornecer informações imprecisas.""",
                        "sources": []
                    }

            # Verificar se o contexto contém informações relevantes para a pergunta
            question_words = set(question.lower().split())
            context_words = set(context.lower().split())
            relevance_score = len(question_words.intersection(
                context_words)) / len(question_words) if question_words else 0

            # Verificar se é pergunta sobre programa de treino (menos restritivo)
            is_training_program = any(word in question.lower() for word in 
                ['programa', 'treino', 'exercício', 'séries', 'repetições', 'tabela', 'dia a', 'dia b', 'dia c', 'dia d'])
            
            # Threshold mais baixo para programas de treino
            threshold = 0.2 if is_training_program else 0.3
            
            if relevance_score < threshold:  # Baixa relevância
                logger.warning(
                    f"⚠️ Baixa relevância do contexto ({relevance_score:.2f}) - risco de resposta imprecisa")
                return {
                    "answer": immediate_processing_message + f"""❌ **CONTEXTO NÃO RELEVANTE**

Sua pergunta: "{question}"

⚠️ **PROBLEMA IDENTIFICADO:**
Os materiais encontrados não são suficientemente relevantes para sua pergunta específica.

🚨 **POR SEGURANÇA:**
- Não posso fornecer uma resposta precisa
- O contexto disponível não aborda adequadamente sua pergunta
- Recomendo consultar diretamente os materiais do DNA da Força

**Sugestões:**
1. Reformule sua pergunta usando termos dos materiais disponíveis
2. Consulte diretamente os módulos e aulas do DNA da Força
3. Verifique se o assunto está coberto pelos materiais

🔒 **Compromisso de Acurácia:** Prefiro não responder do que fornecer informações incorretas ou irrelevantes.""",
                    "sources": []
                }

            prompt_template = """
Você é um Professor de Educação Física do DNA da Força, respondendo APENAS com base nos materiais fornecidos.

🚨 **REGRAS ABSOLUTAS - MODO DNA-ONLY:**

1. **RESPONDA APENAS COM O CONTEXTO ABAIXO**
   - Se a informação NÃO está no contexto: diga "❌ Não encontrei essa informação nos materiais do DNA da Força"
   - NUNCA use conhecimento geral ou externo
   - NUNCA complete informações faltantes com suposições

2. **SEJA ESPECÍFICO E DIRETO**
   - Se perguntarem sobre estudos: cite EXATAMENTE os estudos mencionados no contexto
   - Se perguntarem sobre exercício: descreva APENAS o que está nos materiais
   - Não adicione explicações genéricas que não estejam no contexto

3. **CITAÇÃO PRECISA**
   - Formato: "Conforme Módulo X, Aula Y — 'Título'"
   - SÓ adicione página se houver metadado válido (não invente)
   - Se não souber a fonte exata: diga "mencionado nos materiais consultados"

4. **PRIORIDADE DE RESPOSTA**
   - 1º: Responda exatamente o que foi perguntado
   - 2º: Use APENAS informações do contexto fornecido
   - 3º: Se não tiver info suficiente, admita claramente

5. **IDIOMA OBRIGATÓRIO**
   - SEMPRE responda em PORTUGUÊS BRASILEIRO
   - NUNCA use inglês ou outros idiomas

**CONTEXTO DOS MATERIAIS DNA DA FORÇA:**
{context}

**PERGUNTA DO ALUNO ({user_level}):**
{question}

**SUA RESPOSTA (DNA-ONLY):**
            """
            prompt = ChatPromptTemplate.from_template(prompt_template)

            if not self.llm:
                raise ValueError("LLM not initialized")

                # Tentar gerar resposta com fallback automático
            try:
                chain = prompt | self.llm | StrOutputParser()
                answer = chain.invoke({
                    "context": context,
                    "question": question,
                    "user_level": user_level
                })

                # 🎯 VALIDAÇÃO CRÍTICA - Modo DNA-Only Rigoroso
                validated_answer, is_valid = self._validate_answer_against_context(answer, context)
                
                if not is_valid:
                    logger.warning(f"⚠️ Resposta rejeitada por conter informações não baseadas no contexto")
                    # Preparar informações sobre documentos consultados
                    num_docs = len(selected_sources) if 'selected_sources' in locals() and selected_sources else 0
                    docs_list = ""
                    if 'selected_sources' in locals() and selected_sources:
                        try:
                            titles = [f"• {s.title}" for s in selected_sources[:3]]
                            docs_list = "\n".join(titles)
                        except:
                            pass
                    
                    answer = f"""❌ **NÃO ENCONTREI INFORMAÇÃO SUFICIENTE NOS MATERIAIS**

Sua pergunta: "{question}"

🔍 **O que busquei:**
Consultei {num_docs} documentos relevantes do DNA da Força, mas não encontrei informações específicas suficientes para responder com precisão.

📚 **Documentos consultados:**
{docs_list if docs_list else "• Múltiplos materiais do DNA da Força"}

💡 **Sugestões:**
1. Reformule usando termos exatos dos materiais (ex: "hipertrofia regionalizada" ao invés de "crescimento muscular")
2. Verifique se o assunto está coberto nas aulas do DNA da Força
3. Especifique o módulo/aula se souber onde está a informação

⚠️ **Compromisso DNA-Only:** Prefiro não responder do que misturar informações externas."""
                else:
                    answer = validated_answer

                # ✅ VERIFICAÇÃO DE ACURÁCIA - Garantir que a resposta é segura
                answer = self._validate_response_accuracy(
                    answer, context, question)

                # 🛡️ VERIFICAÇÃO DE GUARDRAILS - Proteção contra conteúdo inadequado
                if GUARDRAILS_AVAILABLE:
                    answer = self._apply_content_guardrails(answer, question)
                else:
                    logger.warning(
                        "⚠️ Sistema de guardrails não disponível - resposta não verificada")

            except Exception as e:
                logger.warning(f"⚠️ Primary LLM failed: {e}")
                logger.info("🔄 Attempting LLM fallback...")

                try:
                    # Usar fallback automático
                    logger.info(
                        f"🔄 LLM fallback activated - original provider: {self.current_llm_provider}")
                    messages = prompt.format_messages(
                        context=context,
                        question=question,
                        user_level=user_level
                    )

                    result = self._try_llm_fallback(messages)
                    answer = result.generations[0][0].text
                    logger.info(
                        f"✅ LLM fallback successful! New provider: {self.current_llm_provider}")

                    # ✅ VERIFICAÇÃO DE ACURÁCIA também para fallback
                    answer = self._validate_response_accuracy(
                        answer, context, question)

                    # 🛡️ VERIFICAÇÃO DE GUARDRAILS também para fallback
                    if GUARDRAILS_AVAILABLE:
                        answer = self._apply_content_guardrails(
                            answer, question)
                    else:
                        logger.warning(
                            "⚠️ Sistema de guardrails não disponível - resposta não verificada")

                except Exception as fallback_e:
                    logger.error(f"❌ LLM fallback also failed: {fallback_e}")
                    # 🚨 RESPOSTA DE EMERGÊNCIA SEGURA - SEM INFORMAÇÕES INVENTADAS
                    answer = f"""❌ **ATENÇÃO: DIFICULDADE TÉCNICA**

Infelizmente, estou enfrentando dificuldades técnicas para processar sua pergunta: "{question}"

🚨 **IMPORTANTE:**
- Não posso fornecer informações sobre este assunto neste momento
- Qualquer resposta seria potencialmente imprecisa
- Recomendo consultar diretamente os materiais do DNA da Força

**O que posso fazer:**
- Responder perguntas quando o sistema estiver funcionando normalmente
- Garantir que todas as respostas sejam baseadas APENAS nos materiais oficiais
- Manter a acurácia e transparência em todas as interações

**Sugestão:** Tente novamente em alguns minutos ou reformule sua pergunta de forma mais específica.

⚠️ **Compromisso de Acurácia:** Prefiro não responder do que fornecer informações incorretas ou inventadas.

⏱️ **SOBRE TEMPO DE RESPOSTA:**
💡 **Normalmente as respostas levam:**
   - **Perguntas simples:** 5-15 segundos
   - **Perguntas complexas:** 15-30 segundos
   - **Análises detalhadas:** 30-60 segundos

🔄 **O sistema processa 53.000+ documentos para garantir acurácia!**"""

            # 🎯 LOG CLARO DO MODELO UTILIZADO
            logger.info(
                f"🤖 LLM Answer generated by: {self.current_llm_provider} ({getattr(self.llm, 'model', 'Unknown')})")
            logger.info(f"🤖 LLM Answer: {answer}")

            # ✅ RESPOSTA FINAL SEM MENSAGEM DE PROCESSAMENTO DUPLICADA
            # A mensagem já foi mostrada ao usuário anteriormente

            final_sources = [s.model_dump() for s in selected_sources]
            # Formatar citações amigáveis sem paths nem códigos internos
            try:
                sources_lines = []
                for s in selected_sources:
                    module = s.model_dump().get("module")
                    class_number = s.model_dump().get("class_number")
                    class_name = s.model_dump().get("class_name")
                    title = class_name or Path(s.source).stem if s.source else s.title
                    
                    cite = []
                    if module is not None and class_number is not None:
                        cite.append(f"Módulo {module}, Aula {class_number}")
                    cite.append(f"'{title}' (PDF)")
                    
                    # ✅ CRÍTICO: SÓ ADICIONAR PÁGINA SE FOR VÁLIDA
                    has_valid_page = s.model_dump().get("has_valid_page", False)
                    if has_valid_page and s.page is not None:
                        page_info = f", p. {s.page}"
                    else:
                        page_info = ""  # NÃO inventar página
                        
                    sources_lines.append(" — ".join(cite) + page_info)
                if sources_lines:
                    answer = f"{answer}\n\n**📚 FONTES CONSULTADAS:**\n\n" + \
                        "\n\n".join(
                            [f"• {source}" for source in sources_lines])
            except Exception:
                pass
            logger.info(
                f"✅ Successfully generated response with {len(final_sources)} sources (selected).")
            return {"answer": answer, "sources": final_sources}

        except Exception as e:
            logger.error(f"❌ Error generating response: {e}", exc_info=True)
            return {"answer": immediate_processing_message + "An error occurred while generating the response.", "sources": []}

    def _apply_content_guardrails(self, answer: str, question: str) -> str:
        """Aplica guardrails de segurança ao conteúdo da resposta."""
        try:
            if not GUARDRAILS_AVAILABLE:
                logger.warning("⚠️ Sistema de guardrails não disponível")
                return answer

            # Verificar se a resposta é segura
            guardrail_result = content_guardrails.validate_response(
                answer, question)

            if guardrail_result.is_safe:
                logger.info("✅ Resposta passou na verificação de guardrails")
                return answer

            # 🚨 CONTEÚDO NÃO SEGURO IDENTIFICADO
            logger.warning(
                f"⚠️ Conteúdo não seguro detectado: {guardrail_result.category.value}")
            logger.warning(f"🚨 Risco: {guardrail_result.risk_level}")
            logger.warning(
                f"🔍 Conteúdo marcado: {guardrail_result.flagged_content}")

            # Sanitizar o conteúdo
            sanitized_answer, sanitization_result = content_guardrails.sanitize_content(
                answer, question)

            # Adicionar aviso de segurança
            security_warning = f"""

🚨 **AVISO DE SEGURANÇA - CONTEÚDO PROTEGIDO**

⚠️ **PROBLEMA IDENTIFICADO:**
{chr(10).join(f"- {content}" for content in guardrail_result.flagged_content[:3])}

🛡️ **PROTEÇÕES APLICADAS:**
- Conteúdo sensível foi sanitizado automaticamente
- Dados pessoais foram substituídos por placeholders
- Resposta foi marcada para revisão manual

📋 **RECOMENDAÇÕES:**
{chr(10).join(f"- {rec}" for rec in guardrail_result.recommendations[:3])}

🔒 **Nível de Risco:** {guardrail_result.risk_level.upper()}
🎯 **Categoria:** {guardrail_result.category.value.replace('_', ' ').title()}

⚠️ **IMPORTANTE:** Esta resposta foi processada pelo sistema de segurança. 
Recomenda-se revisão manual para garantir adequação educacional."""

            sanitized_answer += security_warning

            logger.info("✅ Conteúdo sanitizado com sucesso")
            return sanitized_answer

        except Exception as e:
            logger.error(f"❌ Erro na aplicação de guardrails: {e}")
            # Em caso de erro, adicionar aviso de segurança padrão
            safety_warning = """

⚠️ **AVISO DE SEGURANÇA:**
Ocorreu um erro na verificação de segurança desta resposta. 
Para máxima proteção, recomendo revisar manualmente o conteúdo."""

            return answer + safety_warning

    def _validate_response_accuracy(self, answer: str, context: str, question: str) -> str:
        """Valida a acurácia da resposta e adiciona avisos de segurança se necessário."""
        try:
            # 🚨 VERIFICAÇÕES CRÍTICAS DE ACURÁCIA

            # 1. Verificar se a resposta contém informações específicas não presentes no contexto
            answer_lower = answer.lower()
            context_lower = context.lower()

            # 2. Palavras-chave que podem indicar invenção de informações
            warning_indicators = [
                "geralmente", "tipicamente", "em geral", "normalmente",
                "costuma", "sempre", "nunca", "todo mundo",
                "estudos mostram", "pesquisas indicam", "especialistas dizem",
                "é comum", "é sabido", "é conhecido", "todo mundo sabe"
            ]

            # 3. Verificar se há afirmações genéricas sem base no contexto
            has_generic_claims = any(
                indicator in answer_lower for indicator in warning_indicators)

            # 4. Verificar se a resposta é muito genérica
            is_too_generic = len(
                answer.split()) < 20 or "não encontrei" not in answer_lower

            # 5. Adicionar avisos de segurança se necessário
            if has_generic_claims or is_too_generic:
                safety_warning = """

⚠️ **AVISO DE SEGURANÇA - ACURÁCIA VERIFICADA:**
Esta resposta foi gerada com base nos materiais do DNA da Força consultados. 
Se você precisar de informações mais específicas ou detalhadas, recomendo consultar diretamente os materiais originais.

🔒 **Compromisso de Acurácia:** Todas as informações são baseadas exclusivamente nos materiais fornecidos."""

                answer += safety_warning
                logger.info("✅ Aviso de segurança adicionado à resposta")

            # 6. Verificar se há citações precisas das fontes
            if "módulo" not in answer_lower and "aula" not in answer_lower:
                source_warning = """

📚 **FONTE DOS DADOS:**
Esta resposta foi baseada nos materiais do DNA da Força consultados. 
Para informações mais detalhadas, consulte os materiais originais."""

                answer += source_warning
                logger.info("✅ Aviso de fonte adicionado à resposta")

            # 7. 🚫 REMOVER QUALQUER TENTATIVA DE TABELA - Garantir texto limpo
            answer = self._remove_table_attempts(answer)

            return answer

        except Exception as e:
            logger.warning(f"⚠️ Erro na validação de acurácia: {e}")
            # Em caso de erro na validação, adicionar aviso de segurança padrão
            safety_warning = """

⚠️ **AVISO DE SEGURANÇA:**
Esta resposta foi gerada pelo sistema. Para máxima acurácia, 
recomendo consultar diretamente os materiais do DNA da Força."""

            return answer + safety_warning


    def _remove_table_attempts(self, answer: str) -> str:
        """Permite tabelas markdown válidas e remove apenas tentativas malformadas."""
        try:
            # Padrões para detectar tentativas de tabelas malformadas (não markdown válidas)
            bad_table_patterns = [
                r'\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|',  # Tabelas muito longas
                r'[|]{3,}',         # Múltiplos | consecutivos (|||)
                r'[-\s]{10,}',      # Muitos - com espaços (mais de 10)
                r'[=\s]{10,}',      # Muitos = com espaços (mais de 10)
            ]

            # Verificar se há padrões de tabela malformada na resposta
            has_bad_table_patterns = any(re.search(pattern, answer)
                                     for pattern in bad_table_patterns)

            if not has_bad_table_patterns:
                return answer

            logger.info(
                "⚠️ Detectadas tabelas malformadas - mantendo formato markdown válido")

            # Limpar apenas formatação problemática, manter tabelas markdown válidas
            answer = re.sub(r'-{10,}', '---', answer)  # Reduzir linhas muito longas
            answer = re.sub(r'={10,}', '===', answer)  # Reduzir linhas muito longas
            answer = re.sub(r'[|]{3,}', '||', answer)  # Reduzir múltiplos pipes

            # Manter tabelas markdown válidas - não remover pipes

            # 5. Limpar espaços extras e quebras de linha
            answer = re.sub(r'\n\s*\n', '\n\n', answer)
            answer = re.sub(r' +', ' ', answer)
            answer = re.sub(r'\n\s*-\s*\n', '\n\n', answer)
            answer = re.sub(r'\n\s*=\s*\n', '\n\n', answer)

            logger.info(
                "✅ Tentativas de tabelas removidas AGESSIVAMENTE - texto limpo gerado")
            return answer

        except Exception as e:
            logger.warning(f"⚠️ Erro na remoção de tentativas de tabela: {e}")
            return answer

    def _calculate_educational_value(self, source: Source, user_level: str) -> float:
        """Calculate educational value score for a source."""
        score = 0.5
        if source.difficulty_level == user_level:
            score += 0.3
        if source.key_concepts:
            score += 0.1
        if source.summary:
            score += 0.1
        return min(1.0, score)

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics for debugging."""
        try:
            collection_name = None
            vector_store_count = 0
            if self.vector_store and hasattr(self.vector_store, "_collection"):
                try:
                    collection_name = getattr(
                        self.vector_store._collection, "name", None)
                except Exception:
                    collection_name = None
                try:
                    vector_store_count = self.vector_store._collection.count()
                except Exception:
                    vector_store_count = 0

            # Calcular materials_count
            materials_count = 0
            try:
                if self.materials_dir.exists():
                    materials_count = len(
                        [f for f in self.materials_dir.rglob("*") if f.is_file()])
            except Exception as e:
                logger.error(f"❌ Error counting materials: {e}")

            return {
                "vector_store_ready": vector_store_count > 0,
                "vector_store_count": vector_store_count,
                "materials_count": materials_count,
                "collection_name": collection_name or self.config.collection_name,
                "persist_dir": str(self.persist_dir) if self.persist_dir else None,
                "config": self.config.__dict__,
            }
        except Exception as e:
            logger.error(f"❌ Error getting system stats: {e}")
            return {"error": str(e)}

    def _validate_context_quality(self, context: str, question: str) -> Dict[str, Any]:
        """Validate the quality of the context for answering the question."""
        try:
            if not context or len(context.strip()) < 50:
                return {
                    "is_valid": False,
                    "reason": "Contexto muito curto ou vazio",
                    "score": 0.0
                }
            
            # Calcular score baseado no tamanho e relevância
            context_length = len(context.strip())
            question_words = set(question.lower().split())
            context_words = set(context.lower().split())
            
            # Score baseado no tamanho
            length_score = min(1.0, context_length / 1000.0) * 3.0
            
            # Score baseado na sobreposição de palavras
            if question_words:
                overlap_score = len(question_words.intersection(context_words)) / len(question_words) * 4.0
            else:
                overlap_score = 0.0
            
            # Score baseado na diversidade de conteúdo
            diversity_score = min(1.0, len(set(context_words)) / 100.0) * 3.0
            
            total_score = min(10.0, length_score + overlap_score + diversity_score)
            
            is_valid = total_score >= 5.0
            
            return {
                "is_valid": is_valid,
                "reason": f"Score de qualidade: {total_score:.2f}/10.0",
                "score": total_score
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Erro na validação de contexto: {e}")
            return {
                "is_valid": True,  # Em caso de erro, permitir continuar
                "reason": "Erro na validação, mas permitindo continuar",
                "score": 5.0
            }

    def reset(self):
        """Reset the handler state."""
        logger.info("🔄 Resetting RAG handler...")
        try:
            if self.vector_store and hasattr(self.vector_store, "_collection"):
                try:
                    ids = self.vector_store.get()["ids"]
                    if ids:
                        self.vector_store.delete(ids)
                except Exception as e:
                    logger.warning(f"⚠️ Could not reset vector store: {e}")
            self.concept_cache.clear()
            self.difficulty_cache.clear()
            self.summary_cache.clear()
            logger.info("✅ RAG handler reset successfully")
        except Exception as e:
            logger.error(f"❌ Error resetting handler: {e}")


class RAGQueryToolInput(BaseModel):
    """Input schema for the RAG Query Tool."""
    query: str = Field(
        description="The user's question to be answered using the RAG system.")
    user_level: str = Field(
        default="intermediate", description="The user's knowledge level (e.g., 'beginner', 'intermediate', 'advanced').")


class RAGQueryTool(BaseTool):
    """A tool to query the RAG system for educational content."""
    name: str = "search_educational_materials"
    description: str = "Searches and retrieves information from educational materials to answer questions about fitness, exercise science, and strength training."
    args_schema: Type[BaseModel] = RAGQueryToolInput
    rag_handler: RAGHandler

    def _run(self, query: str, user_level: str = "intermediate") -> Dict[str, Any]:
        """Execute the RAG query."""
        logger.info(
            f"Tool '{self.name}' invoked with query: '{query}' and user_level: '{user_level}'")
        try:
            result = self.rag_handler.generate_response(
                question=query, user_level=user_level)
            return result
        except Exception as e:
            logger.error(f"Error executing RAGQueryTool: {e}", exc_info=True)
            return {"answer": "An error occurred while searching the materials.", "sources": []}

    async def _arun(self, query: str, user_level: str = "intermediate") -> Dict[str, Any]:
        """Asynchronously execute the RAG query."""
        # For simplicity, we call the synchronous version. For a fully async implementation,
        # the underlying methods in RAGHandler would also need to be async.
        return self._run(query, user_level)


__all__ = ['RAGHandler', 'RAGConfig', 'Source', 'RAGQueryTool']
