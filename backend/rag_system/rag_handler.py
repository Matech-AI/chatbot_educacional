import os
import logging
import openai
import time
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Type
from dataclasses import dataclass, field
from pydantic import BaseModel, SecretStr, Field
from langchain_core.tools import BaseTool
import pandas as pd

from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
    DirectoryLoader,
)
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.load import dumps, loads

# Configure logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class RAGConfig:
    """Unified configuration for the RAG handler."""
    # Text processing
    chunk_size: int = 1500
    chunk_overlap: int = 300
    
    # Model configuration
    model_name: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-ada-002"
    temperature: float = 0.2
    max_tokens: int = 800
    
    # Retrieval configuration
    retrieval_search_type: str = "mmr"
    retrieval_k: int = 6
    retrieval_fetch_k: int = 20
    retrieval_lambda_mult: float = 0.7
    
    # Educational features (can be toggled)
    enable_educational_features: bool = True
    generate_learning_objectives: bool = True
    extract_key_concepts: bool = True
    identify_prerequisites: bool = True
    assess_difficulty_level: bool = True
    create_summaries: bool = True

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
    Unified RAG handler with configurable educational enhancements.
    """
    def __init__(
        self,
        api_key: str,
        config: Optional[RAGConfig] = None,
        persist_dir: Optional[str] = None,
        materials_dir: str = "data/materials",
    ):
        logger.info("🚀 Initializing Unified RAG Handler...")
        
        self.api_key = api_key
        openai.api_key = self.api_key
        self.config = config or RAGConfig()
        
        # Setup directories
        if persist_dir:
            self.persist_dir = persist_dir
        else:
            backend_dir = Path(__file__).parent.parent
            self.persist_dir = str(backend_dir / "data" / "chromadb")
        
        self.materials_dir = Path(materials_dir)
        
        # Initialize components
        self.embeddings: Optional[OpenAIEmbeddings] = None
        self.llm: Optional[ChatOpenAI] = None
        self.vector_store: Optional[Chroma] = None
        self.retriever = None
        
        # Caches for educational features
        self.concept_cache: Dict[str, List[str]] = {}
        self.difficulty_cache: Dict[str, str] = {}
        self.summary_cache: Dict[str, str] = {}
        
        self.course_structure: Optional[pd.DataFrame] = None
        
        self._initialize_components()
        logger.info("✅ Unified RAG Handler initialized successfully")

    def _initialize_components(self):
        """Initialize all necessary components."""
        self._initialize_embeddings()
        self._initialize_llm()
        self._initialize_vector_store()
        self._setup_retriever()
        self.load_course_structure()

    def _initialize_embeddings(self):
        try:
            self.embeddings = OpenAIEmbeddings(
                model=self.config.embedding_model,
                api_key=SecretStr(self.api_key)
            )
            logger.info(f"✅ Embeddings initialized: {self.config.embedding_model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings: {e}")
            raise

    def _initialize_llm(self):
        try:
            self.llm = ChatOpenAI(
                model=self.config.model_name,
                temperature=self.config.temperature,
                api_key=SecretStr(self.api_key)
            )
            logger.info(f"✅ LLM initialized: {self.config.model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            raise

    def _initialize_vector_store(self):
        try:
            os.makedirs(self.persist_dir, exist_ok=True)
            self.vector_store = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings
            )
            logger.info(f"✅ Vector store loaded/created at {self.persist_dir}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {e}")
            raise

    def _setup_retriever(self):
        if self.vector_store:
            self.retriever = self.vector_store.as_retriever(
                search_type=self.config.retrieval_search_type,
                search_kwargs={
                    "k": self.config.retrieval_k,
                    "fetch_k": self.config.retrieval_fetch_k,
                    "lambda_mult": self.config.retrieval_lambda_mult,
                },
            )
            logger.info("✅ Retriever configured")

    def get_retriever(self):
        """Get the retriever instance."""
        return self.retriever

    def load_course_structure(self, spreadsheet_path: str = "data/catalog.xlsx"):
        """Load and process the course structure from a spreadsheet."""
        try:
            spreadsheet_file = Path(spreadsheet_path)
            if not spreadsheet_file.exists():
                logger.warning(f"Spreadsheet not found at {spreadsheet_path}. Skipping course structure loading.")
                return

            self.course_structure = pd.read_excel(spreadsheet_file)
            self.course_structure.columns = [col.strip().lower() for col in self.course_structure.columns]
            required_columns = ['código', 'módulo', 'aula', 'nome da aula', 'resumo da aula']
            if not all(col in self.course_structure.columns for col in required_columns):
                logger.error(f"Spreadsheet is missing required columns. Found: {self.course_structure.columns}")
                self.course_structure = None
                return
            
            self.course_structure['código_normalized'] = self.course_structure['código'].str.strip().str.lower()
            logger.info(f"✅ Course structure loaded from {spreadsheet_path}.")
        except Exception as e:
            logger.error(f"Failed to load course structure: {e}")
            self.course_structure = None

    def process_documents(self, force_reprocess: bool = False) -> bool:
        """Process all documents with optional educational enhancements."""
        logger.info("📚 Starting document processing...")
        
        if not self.materials_dir.exists():
            logger.error(f"❌ Materials directory not found: {self.materials_dir}")
            return False
        
        if not self.vector_store:
            self._initialize_vector_store()

        if self.vector_store:
            if not force_reprocess and self.vector_store._collection.count() > 0:
                logger.info("📋 Documents already processed. Use force_reprocess=True to reprocess.")
                return True
            
            if force_reprocess and self.vector_store._collection.count() > 0:
                logger.info("🗑️ Clearing existing documents for reprocessing...")
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
            enhanced_documents = [self._enhance_document(doc) for doc in documents]
        else:
            enhanced_documents = documents

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        splits = text_splitter.split_documents(enhanced_documents)
        logger.info(f"🔪 Split into {len(splits)} chunks")

        # Add to vector store
        try:
            if self.vector_store:
                self.vector_store.add_documents(splits)
            logger.info(f"✅ Added {len(splits)} document chunks to vector store")
            self._setup_retriever()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add documents to vector store: {e}")
            return False

    def _load_all_documents(self) -> List[Document]:
        """Load all supported document types from the materials directory."""
        documents = []
        file_patterns = {
            "**/*.pdf": PyPDFLoader,
            "**/*.txt": TextLoader,
            "**/*.xlsx": UnstructuredExcelLoader,
        }
        for pattern, loader_class in file_patterns.items():
            try:
                loader = DirectoryLoader(
                    str(self.materials_dir),
                    glob=pattern,
                    loader_cls=loader_class,
                    show_progress=True,
                    use_multithreading=True,
                )
                loaded_docs = loader.load()
                # Filter documents to include only those ending with '_resumo'
                documents.extend([doc for doc in loaded_docs if Path(doc.metadata.get('source', '')).stem.endswith('_resumo')])
            except Exception as e:
                logger.warning(f"⚠️ Error loading {pattern}: {e}")
        logger.info(f"📄 Loaded {len(documents)} total documents.")
        return documents

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
            video_code = filename_stem.split(' ')[0].strip().lower()

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
        level = self._run_llm_feature(text, self.difficulty_cache, prompt, "assess_difficulty", lambda r: r.strip().lower())
        return level if level in ['beginner', 'intermediate', 'advanced'] else 'intermediate'

    def _create_content_summary(self, text: str) -> str:
        prompt = "Crie um resumo conciso (máximo 3 frases) do texto a seguir.\n\nTexto: {text}\n\nResumo:"
        return self._run_llm_feature(text, self.summary_cache, prompt, "create_summary", lambda r: r.strip()) or ""

    def generate_response(self, question: str, user_level: str = "intermediate") -> Dict[str, Any]:
        """Generate a response using the RAG system."""
        if not self.retriever:
            logger.error("Retriever not initialized.")
            return {"answer": "System not ready.", "sources": []}

        try:
            logger.info(f"🔍 Retrieving documents for question: '{question}'")
            docs = self.retriever.get_relevant_documents(question)
            logger.info(f"📄 Found {len(docs)} relevant documents.")

            if not docs:
                logger.warning("No documents found for the question.")
                return {"answer": "No relevant information found.", "sources": []}

            sources = []
            for i, doc in enumerate(docs):
                logger.info(f"  - Document {i+1}:")
                logger.info(f"    - Source: {doc.metadata.get('source', 'N/A')}")
                logger.info(f"    - Page: {doc.metadata.get('page', 'N/A')}")
                logger.info(f"    - Chunk Content: {doc.page_content}") # Log the full chunk content
                
                source = Source(
                    title=doc.metadata.get('title', Path(doc.metadata.get('source', '')).name),
                    source=doc.metadata.get('source', ''),
                    page=doc.metadata.get('page'),
                    chunk=doc.page_content,
                    content_type=doc.metadata.get('content_type', 'text'),
                    difficulty_level=doc.metadata.get('difficulty_level', 'intermediate'),
                    key_concepts=doc.metadata.get('key_concepts', []),
                    summary=doc.metadata.get('summary', ''),
                )
                source.educational_value = self._calculate_educational_value(source, user_level)
                sources.append(source)

            sources.sort(key=lambda x: x.educational_value, reverse=True)
            
            context = "\n\n".join([s.chunk for s in sources])
            logger.info(f"📝 Generated context with {len(sources)} sources.")
            logger.info(f"Full context for LLM:\n{context}")
            
            prompt_template = """
            Você é um Professor de Educação Física e Treinamento Esportivo especializado em força e condicionamento físico.

            SEUS OBJETIVOS EDUCACIONAIS:
            1. Ensinar conceitos de forma clara e progressiva
            2. Adaptar explicações ao nível do aluno ({user_level})
            3. Fornecer exemplos práticos e aplicáveis
            4. Citar as fontes consultadas no contexto

            METODOLOGIA DE ENSINO:
            - Use analogias e exemplos do dia a dia
            - Divida conceitos complexos em partes menores
            - Relacione teoria com prática
            - **Cite as fontes de onde a informação foi extraída (ex: "Conforme a Aula 3, página 7...")**

            ESTRUTURA DAS RESPOSTAS:
            1. **Resposta Principal**: Explicação clara e didática da pergunta: {question}
            2. **Fontes e Evidências**: Referências dos materiais consultados no {context}

            IMPORTANTE:
            - Sempre baseie suas respostas no conteúdo dos materiais de estudo fornecidos no {context}
            - Se não houver informação suficiente nos materiais, indique claramente
            """
            prompt = ChatPromptTemplate.from_template(prompt_template)

            if not self.llm:
                raise ValueError("LLM not initialized")

            chain = prompt | self.llm | StrOutputParser()
            answer = chain.invoke({
                "context": context,
                "question": question,
                "user_level": user_level
            })

            logger.info(f"🤖 LLM Answer: {answer}")

            final_sources = [s.dict() for s in sources]
            logger.info(f"✅ Successfully generated response with {len(final_sources)} sources.")
            return {"answer": answer, "sources": final_sources}
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}", exc_info=True)
            return {"answer": "An error occurred while generating the response.", "sources": []}

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
            return {
                "vector_store_count": self.vector_store._collection.count() if self.vector_store else 0,
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
    query: str = Field(description="The user's question to be answered using the RAG system.")
    user_level: str = Field(default="intermediate", description="The user's knowledge level (e.g., 'beginner', 'intermediate', 'advanced').")

class RAGQueryTool(BaseTool):
    """A tool to query the RAG system for educational content."""
    name: str = "search_educational_materials"
    description: str = "Searches and retrieves information from educational materials to answer questions about fitness, exercise science, and strength training."
    args_schema = RAGQueryToolInput
    rag_handler: RAGHandler

    def _run(self, query: str, user_level: str = "intermediate") -> Dict[str, Any]:
        """Execute the RAG query."""
        logger.info(f"Tool '{self.name}' invoked with query: '{query}' and user_level: '{user_level}'")
        try:
            result = self.rag_handler.generate_response(question=query, user_level=user_level)
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
