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
    DirectoryLoader,
)
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.load import dumps, loads
import chromadb
from chromadb.config import Settings
try:
    import tiktoken  # for token estimation
except Exception:
    tiktoken = None

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
    embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.2
    max_tokens: int = 800

    # Retrieval configuration
    retrieval_search_type: str = "mmr"
    retrieval_k: int = 6
    retrieval_fetch_k: int = 20
    retrieval_lambda_mult: float = 0.7

    # Context assembly
    max_context_chunks: int = 4

    # Indexing
    add_batch_size: int = 8
    embedding_request_token_limit: int = 300000
    embedding_request_target: int = 280000

    # Vector store
    collection_name: str = "langchain"

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
            self.persist_dir = str(backend_dir / "data" / ".chromadb")

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
            logger.info(
                f"✅ Embeddings initialized: {self.config.embedding_model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings: {e}")
            raise

    def _initialize_llm(self):
        try:
            self.llm = ChatOpenAI(
                model=self.config.model_name,
                temperature=self.config.temperature,
                api_key=SecretStr(self.api_key),
                max_tokens=self.config.max_tokens,
            )
            logger.info(f"✅ LLM initialized: {self.config.model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            raise

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
            self.retriever = self.vector_store.as_retriever(
                search_type=self.config.retrieval_search_type,
                search_kwargs={
                    "k": self.config.retrieval_k,
                    "fetch_k": self.config.retrieval_fetch_k,
                    "lambda_mult": self.config.retrieval_lambda_mult,
                },
            )
            logger.info("✅ Retriever configured")

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
        level = self._run_llm_feature(
            text, self.difficulty_cache, prompt, "assess_difficulty", lambda r: r.strip().lower())
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
            retrieved: List[Tuple[Document, Optional[float]]] = []
            try:
                if self.vector_store:
                    try:
                        # Prefer retriever with relevance scores when available
                        vs_results = self.vector_store.similarity_search_with_relevance_scores(
                            question, k=self.config.retrieval_k
                        )
                        retrieved = [(doc, score) for doc, score in vs_results]
                        # If no results (e.g., thresholding in some backends), fallback to plain similarity search
                        if not retrieved:
                            logger.debug(
                                "No results from relevance_scores; falling back to similarity_search")
                            docs = self.vector_store.similarity_search(
                                question, k=max(self.config.retrieval_k, 8)
                            )
                            retrieved = [(doc, None) for doc in docs]
                    except Exception as e:
                        logger.debug(
                            f"similarity_search_with_relevance_scores unavailable, falling back: {e}")
                        try:
                            docs = self.vector_store.similarity_search(
                                question, k=max(self.config.retrieval_k, 8)
                            )
                            retrieved = [(doc, None) for doc in docs]
                        except Exception as e2:
                            logger.debug(
                                f"similarity_search failed: {e2}; using retriever.invoke")
                            docs = self.retriever.invoke(question)
                            retrieved = [(doc, None) for doc in docs]
                else:
                    docs = self.retriever.invoke(question)
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
            2. **Fontes e Evidências**: Referências dos materiais consultados no contexto, citando arquivo e página quando aplicável

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

            final_sources = [s.model_dump() for s in selected_sources]
            # Append a deterministic sources section to ensure references are visible
            try:
                sources_lines = []
                for s in selected_sources:
                    file_name = Path(s.source).name if s.source else s.title
                    page_info = f", página {s.page}" if s.page is not None else ""
                    sources_lines.append(f"- {file_name}{page_info}")
                if sources_lines:
                    answer = f"{answer}\n\nFontes:\n" + \
                        "\n".join(sources_lines)
            except Exception:
                pass
            logger.info(
                f"✅ Successfully generated response with {len(final_sources)} sources (selected).")
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

            return {
                "vector_store_ready": vector_store_count > 0,
                "vector_store_count": vector_store_count,
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
