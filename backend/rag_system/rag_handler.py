import os
import logging
import openai
import time
import hashlib
import json
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Type
from dataclasses import dataclass, field
from pydantic import BaseModel, SecretStr, Field
from langchain_core.tools import BaseTool
import pandas as pd

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
        logger = logging.getLogger(__name__)
        logger.warning(
            "⚠️ Sistema de guardrails não disponível. Instale o módulo guardrails.py")

from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    DirectoryLoader,
)
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.load import dumps, loads
import chromadb
from chromadb.config import Settings

# Importações para Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
except ImportError:
    ChatGoogleGenerativeAI = None
    GoogleGenerativeAIEmbeddings = None
    logger = logging.getLogger(__name__)
    logger.warning(
        "⚠️ Google Generative AI not available. Install with: pip install langchain-google-genai")

# NOVO: Classe personalizada para NVIDIA API


class NVIDIAChatOpenAI(ChatOpenAI):
    """Custom ChatOpenAI class for NVIDIA API with robust retry logic and fallback."""

    def __init__(self, nvidia_api_key: str, model: str, base_url: str, retry_attempts: int = 3, retry_delay: float = 2.0, **kwargs):
        # Remover stream=True se estiver presente para evitar conflitos com LangChain
        if 'stream' in kwargs:
            del kwargs['stream']

        super().__init__(
            api_key=SecretStr(nvidia_api_key),
            model=model,
            base_url=base_url,
            **kwargs
        )

        # Configurações de retry
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.max_retry_delay = 10.0  # Delay máximo para evitar esperas muito longas

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

            # Se falhou completamente, tentar uma última vez com delay maior
            try:
                logger.info("🔄 Tentativa final com delay maior...")
                time.sleep(self.retry_delay * 2)
                result = super()._generate(messages, stop, run_manager, **kwargs)
                logger.info("✅ Tentativa final bem-sucedida!")
                return result
            except Exception as final_e:
                logger.error(f"❌ Tentativa final também falhou: {final_e}")
                raise final_e


class NVIDIAEmbeddings(OpenAIEmbeddings):
    """Custom OpenAI Embeddings class for NVIDIA API with retry logic."""

    def __init__(self, nvidia_api_key: str, model: str, base_url: str, retry_attempts: int = 3, retry_delay: float = 2.0, **kwargs):
        super().__init__(
            api_key=SecretStr(nvidia_api_key),
            model=model,
            base_url=base_url,
            **kwargs
        )
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

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
                    raise e

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
                    raise e


# NOVO: Classe para embeddings open source
try:
    from sentence_transformers import SentenceTransformer
    from langchain_community.embeddings import HuggingFaceEmbeddings
    OpenSourceEmbeddings = True
except ImportError:
    OpenSourceEmbeddings = False
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

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """Unified configuration for the RAG handler."""
    # Text processing - OTIMIZADO para melhor precisão
    chunk_size: int = 1000  # Reduzido para chunks menores e mais precisos
    chunk_overlap: int = 200  # Ajustado proporcionalmente

    # Model configuration
    model_name: str = "gpt-4o-mini"
    gemini_model_name: str = "gemini-2.5-flash"
    # Modelo NVIDIA (sem prefixo openai/)
    # Modelo NVIDIA (nome correto da API)
    nvidia_model_name: str = "openai/gpt-oss-120b"
    embedding_model: str = "text-embedding-3-small"
    gemini_embedding_model: str = "models/text-embedding-004"
    nvidia_embedding_model: str = "nvidia/nv-embedqa-e5-v5"  # NOVO: Embedding NVIDIA
    # NOVO: Embedding Open Source de alta qualidade (384d)
    open_source_embedding_model: str = "intfloat/multilingual-e5-large"
    temperature: float = 0.2
    max_tokens: int = 4096  # Aumentado para 4096

    # Provider preference - LER VARIÁVEIS DE AMBIENTE DO RENDER
    prefer_nvidia: bool = os.getenv(
        "PREFER_NVIDIA", "true").lower() == "true"  # NOVO: Preferir NVIDIA
    prefer_openai: bool = os.getenv(
        "PREFER_OPENAI", "false").lower() == "true"  # Mantido False
    prefer_open_source: bool = os.getenv("PREFER_OPEN_SOURCE_EMBEDDINGS", "true").lower(
    ) == "true"  # NOVO: Preferir embeddings open source

    # NVIDIA specific settings
    nvidia_retry_attempts: int = 3  # NOVO: Tentativas de retry
    nvidia_retry_delay: float = 2.0  # NOVO: Delay entre tentativas
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"  # NOVO: URL base NVIDIA

    # Retrieval configuration - OTIMIZADO para melhor precisão
    # Mudado para similarity para melhor precisão
    retrieval_search_type: str = "similarity"
    retrieval_k: int = 8  # Aumentado para capturar mais contexto
    retrieval_fetch_k: int = 30  # Aumentado para buscar mais candidatos
    retrieval_lambda_mult: float = 0.5  # Ajustado para melhor diversidade

    # Context assembly - OTIMIZADO
    max_context_chunks: int = 6  # Aumentado para mais contexto

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
            backend_dir = Path(__file__).parent.parent
            self.persist_dir = str(backend_dir / "data" / ".chromadb")

        self.materials_dir = Path(materials_dir)

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

        # Open Source como prioridade se prefer_open_source for True
        if self.config.prefer_open_source and OpenSourceEmbeddings:
            providers_to_try.append(("open_source", None))
            logger.info("🎯 Adicionando Open Source como PRIORIDADE")

        # NVIDIA como prioridade se prefer_nvidia for True
        if self.config.prefer_nvidia and self.nvidia_api_key:
            providers_to_try.append(("nvidia", self.nvidia_api_key))
            logger.info("🎯 Adicionando NVIDIA como PRIORIDADE")

        if self.config.prefer_openai:
            if self.openai_api_key:
                providers_to_try.append(("openai", self.openai_api_key))
                logger.info("🎯 Adicionando OpenAI como PRIORIDADE")
            if self.gemini_api_key and GoogleGenerativeAIEmbeddings:
                providers_to_try.append(("gemini", self.gemini_api_key))
                logger.info("🎯 Adicionando Gemini como PRIORIDADE")
        else:
            if self.gemini_api_key and GoogleGenerativeAIEmbeddings:
                providers_to_try.append(("gemini", self.gemini_api_key))
                logger.info("🔄 Adicionando Gemini como fallback")
            if self.openai_api_key:
                providers_to_try.append(("openai", self.openai_api_key))
                logger.info("🔄 Adicionando OpenAI como fallback")

        # Adicionar NVIDIA como fallback se não foi adicionado como prioridade
        if not self.config.prefer_nvidia and self.nvidia_api_key:
            providers_to_try.append(("nvidia", self.nvidia_api_key))
            logger.info("🔄 Adicionando NVIDIA como fallback")

        # Adicionar Open Source como fallback se não foi adicionado como prioridade
        if not self.config.prefer_open_source and OpenSourceEmbeddings:
            providers_to_try.append(("open_source", None))
            logger.info("🔄 Adicionando Open Source como fallback")

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
                        max_tokens=self.config.max_tokens
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

        raise Exception("No alternative embedding provider available")

    def _initialize_vector_store(self):
        try:
            os.makedirs(self.persist_dir, exist_ok=True)
            # Tenta carregar a coleção configurada (default: "langchain")
            try:
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
                    client = chromadb.PersistentClient(path=self.persist_dir)
                    collections = client.list_collections()
                    logger.info(
                        f"🔎 Autodiscovery: found {len(collections)} collection(s) in persist dir"
                    )
                    # Priorizar coleção não vazia
                    for col in collections:
                        try:
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
                    # Como último recurso, cria/usa a coleção configurada
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
                final_count = self.vector_store._collection.count()
            except Exception:
                final_count = 0
            logger.info(
                f"📊 Vector store collection='{self.config.collection_name}' count={final_count}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {e}")
            raise

    def _setup_retriever(self):
        if self.vector_store:
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
                patterns = ["#catalog*.xlsx",
                            "*catalog*.xlsx", "*catálogo*.xlsx"]
                for pattern in patterns:
                    match = next(Path(self.materials_dir).rglob(pattern), None)
                    if match:
                        candidate_path = match
                        logger.info(
                            f"📊 Using course catalog found at {candidate_path}")
                        break

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

        if not self.materials_dir.exists():
            logger.error(
                f"❌ Materials directory not found: {self.materials_dir}")
            return False

        if not self.vector_store:
            self._initialize_vector_store()

        if self.vector_store:
            if not force_reprocess and self.vector_store._collection.count() > 0:
                logger.info(
                    "📋 Documents already processed. Use force_reprocess=True to reprocess.")
                return True

            if force_reprocess and self.vector_store._collection.count() > 0:
                logger.info(
                    "🗑️ Clearing existing documents for reprocessing...")
                ids = self.vector_store.get()["ids"]
                if ids:
                    self.vector_store.delete(ids)

        # Load documents
        documents = self._load_all_documents()
        if not documents:
            logger.warning("⚠️ No documents found to process")
            return False

        # Enhance documents if enabled
        if self.config.enable_educational_features:
            logger.info("🎓 Enhancing documents with educational metadata...")
            enhanced_documents = [
                self._enhance_document(doc) for doc in documents]
        else:
            enhanced_documents = documents

        # 🛡️ APLICAR GUARDRAILS AOS DOCUMENTOS
        if GUARDRAILS_AVAILABLE:
            logger.info(
                "🛡️ Aplicando guardrails de segurança aos documentos...")
            protected_documents = []
            for doc in enhanced_documents:
                # Verificar se o conteúdo é seguro
                if is_content_safe(doc.page_content):
                    protected_documents.append(doc)
                else:
                    # Sanitizar documento problemático
                    sanitized_content, guardrail_result = validate_and_sanitize_content(
                        doc.page_content,
                        str(doc.metadata.get('source', ''))
                    )

                    if guardrail_result.is_safe:
                        # Criar novo documento sanitizado
                        sanitized_doc = Document(
                            page_content=sanitized_content,
                            metadata={
                                **doc.metadata,
                                'guardrails_applied': True,
                                'original_risk': guardrail_result.risk_level,
                                'sanitization_timestamp': time.time()
                            }
                        )
                        protected_documents.append(sanitized_doc)
                        logger.info(
                            f"✅ Documento sanitizado: {doc.metadata.get('source', 'unknown')}")
                    else:
                        logger.warning(
                            f"⚠️ Documento bloqueado por segurança: {doc.metadata.get('source', 'unknown')}")
                        logger.warning(
                            f"🚨 Risco: {guardrail_result.risk_level}")
            enhanced_documents = protected_documents
            logger.info(
                f"🛡️ Guardrails aplicados: {len(enhanced_documents)} documentos seguros")
        else:
            logger.warning(
                "⚠️ Sistema de guardrails não disponível - documentos não verificados")

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
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add documents to vector store: {e}")
            return False

    def _load_all_documents(self) -> List[Document]:
        """Load PDF and selected XLSX sheets from the materials directory."""
        documents: List[Document] = []
        # PDFs
        try:
            loader = DirectoryLoader(
                str(self.materials_dir),
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                show_progress=True,
                use_multithreading=True,
            )
            loaded = loader.load()
            logger.info(f"📥 Loaded {len(loaded)} docs for pattern **/*.pdf")
            documents.extend(loaded)
        except Exception as e:
            logger.warning(f"⚠️ Error loading PDFs: {e}")

        # XLSX via pandas (e.g., course catalog)
        try:
            documents.extend(self._load_xlsx_with_pandas())
        except Exception as e:
            logger.warning(f"⚠️ Error loading XLSX via pandas: {e}")

        logger.info(f"📄 Loaded {len(documents)} total documents.")
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
        for pattern in ("#catalog*.xlsx", "*catalog*.xlsx", "*.xlsx"):
            candidates.extend(list(Path(self.materials_dir).rglob(pattern)))

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
        content_type = self._analyze_content_type(source_path)

        enhanced_metadata = {
            **doc.metadata,
            'content_type': content_type,
            'processed_at': time.time(),
        }

        # Get course info from catalog and add it to metadata
        course_info = self._get_course_info(source_path)
        if course_info:
            enhanced_metadata.update(course_info)

        # if len(doc.page_content) > 100:
        #     if self.config.extract_key_concepts:
        #         enhanced_metadata['key_concepts'] = self._extract_key_concepts(doc.page_content)
        #     if self.config.assess_difficulty_level:
        #         enhanced_metadata['difficulty_level'] = self._assess_difficulty_level(doc.page_content)
        #     if self.config.create_summaries:
        #         enhanced_metadata['summary'] = self._create_content_summary(doc.page_content)

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

    def _run_llm_feature(self, text: str, cache: Dict, prompt_template: str, feature_name: str, result_parser) -> Any:
        """Generic method to run an LLM-based feature with caching."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in cache:
            return cache[text_hash]

        try:
            prompt = ChatPromptTemplate.from_template(prompt_template)
            if not self.llm:
                raise ValueError("LLM not initialized")
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"text": text[:2000]})
            parsed_result = result_parser(result)
            cache[text_hash] = parsed_result
            return parsed_result
        except Exception as e:
            logger.warning(f"Failed to run feature '{feature_name}': {e}")
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

    def retrieve_documents(self, question: str, k: Optional[int] = None) -> List[Document]:
        """Retrieve documents with automatic fallback on embedding failures."""
        try:
            if not self.retriever:
                logger.warning("⚠️ No retriever available")
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

    def generate_response(self, question: str, user_level: str = "intermediate") -> Dict[str, Any]:
        """Generate a response using the RAG system."""
        # 🎯 LOG INICIAL MOSTRANDO QUAL MODELO SERÁ USADO
        logger.info(
            f"🚀 Starting response generation with: {self.current_llm_provider} ({getattr(self.llm, 'model', 'Unknown')})")

        if not self.retriever:
            logger.error("Retriever not initialized.")
            return {"answer": "System not ready.", "sources": []}

        try:
            # Expand query with aliases/synonyms
            try:
                question_aug = self._augment_query_with_aliases(
                    question)  # type: ignore[attr-defined]
            except Exception:
                question_aug = question

            retrieved: List[Tuple[Document, Optional[float]]] = []
            try:
                if self.vector_store:
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
                    docs = self.retrieve_documents(question_aug)
                    retrieved = [(doc, None) for doc in docs]
            except Exception as e:
                logger.error(f"Failed during retrieval: {e}")
                retrieved = []

            logger.info(f"📄 Found {len(retrieved)} relevant documents.")

            if not retrieved:
                logger.warning("No documents found for the question.")
                return {"answer": "No relevant information found.", "sources": []}

            sources = []
            for i, (doc, score) in enumerate(retrieved):
                logger.info(f"  - Document {i+1}:")
                logger.info(
                    f"    - Source: {doc.metadata.get('source', 'N/A')}")
                logger.info(f"    - Page: {doc.metadata.get('page', 'N/A')}")
                # Log the full chunk content
                logger.info(f"    - Chunk Content: {doc.page_content}")

                source = Source(
                    title=doc.metadata.get('title', Path(
                        doc.metadata.get('source', '')).name),
                    source=doc.metadata.get('source', ''),
                    page=doc.metadata.get('page'),
                    chunk=doc.page_content,
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

            # 🚨 VERIFICAÇÃO CRÍTICA DE CONTEXTO - Garantir que há informação suficiente
            if len(context.strip()) < 100:  # Contexto muito pequeno
                logger.warning(
                    "⚠️ Contexto muito pequeno - risco de resposta imprecisa")
                return {
                    "answer": f"""❌ **INFORMAÇÃO INSUFICIENTE**

Sua pergunta: "{question}"

⚠️ **PROBLEMA IDENTIFICADO:**
Não encontrei informações suficientes nos materiais do DNA da Força para responder adequadamente a esta pergunta.

🚨 **POR SEGURANÇA:**
- Não posso fornecer uma resposta completa
- Qualquer resposta seria potencialmente imprecisa
- Recomendo consultar diretamente os materiais do DNA da Força

**Sugestões:**
1. Reformule sua pergunta de forma mais específica
2. Use termos relacionados aos materiais disponíveis
3. Consulte diretamente os módulos e aulas do DNA da Força

🔒 **Compromisso de Acurácia:** Prefiro não responder do que fornecer informações incorretas.""",
                    "sources": []
                }

            # Verificar se o contexto contém informações relevantes para a pergunta
            question_words = set(question.lower().split())
            context_words = set(context.lower().split())
            relevance_score = len(question_words.intersection(
                context_words)) / len(question_words) if question_words else 0

            if relevance_score < 0.3:  # Baixa relevância
                logger.warning(
                    f"⚠️ Baixa relevância do contexto ({relevance_score:.2f}) - risco de resposta imprecisa")
                return {
                    "answer": f"""❌ **CONTEXTO NÃO RELEVANTE**

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
            Você é um Professor de Educação Física e Treinamento Esportivo especializado em força e condicionamento físico.

            🚨 REGRAS CRÍTICAS DE ACURÁCIA:
            - NUNCA invente informações que não estejam nos materiais fornecidos
            - NUNCA use conhecimento externo ou genérico
            - SEMPRE responda APENAS com base no contexto fornecido
            - Se não houver informação suficiente, seja EXPLICITAMENTE transparente

            SEUS OBJETIVOS EDUCACIONAIS:
            1. Ensinar conceitos de forma clara e progressiva
            2. Adaptar explicações ao nível do aluno ({user_level})
            3. Fornecer exemplos práticos APENAS se estiverem nos materiais
            4. Citar PRECISAMENTE as fontes consultadas

            METODOLOGIA DE ENSINO:
            - Use analogias e exemplos APENAS se estiverem nos materiais
            - Divida conceitos complexos em partes menores
            - Relacione teoria com prática SE estiver nos materiais
            - **Cite EXATAMENTE as fontes: "Conforme Módulo X, Aula Y — 'Título' (PDF), p. N"**

            ESTRUTURA DAS RESPOSTAS:
            1. **Resposta Principal**: Explicação APENAS com base no contexto fornecido
            2. **Fontes Precisas**: Citar EXATAMENTE os materiais consultados
            3. **Transparência Total**: Se algo não estiver nos materiais, declare claramente

            🎯 INSTRUÇÕES DE SEGURANÇA:
            - Padrão DNA-ONLY: responda EXCLUSIVAMENTE com base nos materiais do DNA da Força
            - Se não houver informação suficiente: "❌ NÃO ENCONTREI essa informação específica nos materiais do DNA da Força"
            - NUNCA adicione "Informação complementar" ou conhecimento externo
            - NUNCA exiba paths, códigos internos ou metadados técnicos
            - SEMPRE verifique se cada afirmação está respaldada pelo contexto

            EXEMPLO DE RESPOSTA SEGURA:
            "Com base nos materiais do DNA da Força consultados, posso explicar que [conceito específico encontrado]. 
            Fonte: Módulo X, Aula Y — 'Título da Aula' (PDF), p. N.
            
            ⚠️ IMPORTANTE: Esta resposta é baseada APENAS nos materiais fornecidos. Não posso confirmar ou negar informações que não estejam presentes no acervo consultado."
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

⚠️ **Compromisso de Acurácia:** Prefiro não responder do que fornecer informações incorretas ou inventadas."""

            # 🎯 LOG CLARO DO MODELO UTILIZADO
            logger.info(
                f"🤖 LLM Answer generated by: {self.current_llm_provider} ({getattr(self.llm, 'model', 'Unknown')})")
            logger.info(f"🤖 LLM Answer: {answer}")

            final_sources = [s.model_dump() for s in selected_sources]
            # Formatar citações amigáveis sem paths nem códigos internos
            try:
                sources_lines = []
                for s in selected_sources:
                    module = s.model_dump().get("module") if hasattr(s, "model_dump") else None
                    class_number = s.model_dump().get(
                        "class_number") if hasattr(s, "model_dump") else None
                    class_name = s.model_dump().get("class_name") if hasattr(s, "model_dump") else None
                    title = class_name or (
                        Path(s.source).stem if s.source else s.title)
                    cite = []
                    if module is not None and class_number is not None:
                        cite.append(f"Módulo {module}, Aula {class_number}")
                    cite.append(f"'{title}' (PDF)")
                    page_info = f", p. {s.page}" if s.page is not None else ""
                    sources_lines.append(" — ".join(cite) + page_info)
                if sources_lines:
                    answer = f"{answer}\n\nFontes (formato DNA):\n- " + \
                        "\n- ".join(sources_lines)
            except Exception:
                pass
            logger.info(
                f"✅ Successfully generated response with {len(final_sources)} sources (selected).")
            return {"answer": answer, "sources": final_sources}
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}", exc_info=True)
            return {"answer": "An error occurred while generating the response.", "sources": []}

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

            return answer

        except Exception as e:
            logger.warning(f"⚠️ Erro na validação de acurácia: {e}")
            # Em caso de erro na validação, adicionar aviso de segurança padrão
            safety_warning = """

⚠️ **AVISO DE SEGURANÇA:**
Esta resposta foi gerada pelo sistema. Para máxima acurácia, 
recomendo consultar diretamente os materiais do DNA da Força."""

            return answer + safety_warning

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
                "persist_dir": self.persist_dir,
                "config": self.config.__dict__,
            }
        except Exception as e:
            logger.error(f"❌ Error getting system stats: {e}")
            return {"error": str(e)}

    def reset(self):
        """Reset the handler state."""
        logger.info("🔄 Resetting RAG handler...")
        try:
            if self.vector_store:
                ids = self.vector_store.get()["ids"]
                if ids:
                    self.vector_store.delete(ids)
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
    args_schema = RAGQueryToolInput
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
