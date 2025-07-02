import os
import logging
import openai
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from pydantic import BaseModel

from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.document_loaders.text import TextLoader
from langchain_community.document_loaders.directory import DirectoryLoader

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.load import dumps, loads
from operator import itemgetter


# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingConfig:
    """Configuration for document processing"""
    chunk_size: int = 2000
    chunk_overlap: int = 200
    model_name: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-ada-002"
    temperature: float = 0.1
    max_tokens: int = 500


class AssistantConfigModel(BaseModel):
    """Data model for assistant configuration."""
    name: str = "Assistente Padrão"
    description: str = "Um assistente de IA geral."
    prompt: str = "Você é um assistente de IA. Responda à pergunta com base no contexto fornecido."
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    # Os campos a seguir não são usados diretamente na geração de resposta, mas fazem parte do modelo
    chunkSize: int = 2000
    chunkOverlap: int = 200
    retrievalSearchType: str = "mmr"
    embeddingModel: str = "text-embedding-ada-002"

@dataclass
class Source:
    """Source document information"""
    title: str
    source: str
    page: Optional[int]
    chunk: str


class RAGHandler:
    """
    Handles Retrieval Augmented Generation (RAG) for the DNA da Força assistant.
    Enhanced version with detailed logging and error handling.
    """

    def __init__(
        self,
        api_key: str,
        config: Optional[ProcessingConfig] = None,
        persist_dir: Optional[str] = None,
    ):
        """
        Initialize the RAG handler.

        Args:
            api_key: OpenAI API key
            config: Processing configuration
            persist_dir: Directory to persist ChromaDB. Defaults to 'backend/.chromadb'
        """
        logger.info("🚀 Initializing RAG handler...")

        self.api_key = api_key
        openai.api_key = self.api_key
        self.config = config or ProcessingConfig()

        if persist_dir:
            self.persist_dir = persist_dir
        else:
            # Default to .chromadb inside the backend directory
            backend_dir = Path(__file__).parent
            self.persist_dir = str(backend_dir / ".chromadb")

        # Initialize components
        self.documents = []
        self.chunks = []
        self.vector_store = None
        self.embeddings = None
        self.chain = None

        # Validate API key
        if not api_key or len(api_key) < 10:
            logger.error("❌ Invalid OpenAI API key provided")
            raise ValueError("Valid OpenAI API key is required")

        logger.info(f"🔑 API key validated (length: {len(api_key)})")
        logger.info(f"⚙️ Configuration: {self.config}")

        # Set up ChromaDB
        self._setup_chromadb()

        self._setup_chain()

        logger.info("✅ RAG handler initialized successfully")

    def update_config(self, new_config: ProcessingConfig) -> None:
        """
        Update the RAG handler's configuration dynamically.

        Args:
            new_config: The new processing configuration.
        """
        logger.info(f"🔄 Updating RAG handler configuration to: {new_config}")
        self.config = new_config
        
        # Re-initialize components that depend on the configuration
        try:
            try:
                self.embeddings = OpenAIEmbeddings(
                    model=self.config.embedding_model
                )
                self.llm = ChatOpenAI(
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    max_completion_tokens=self.config.max_tokens
                )
            except openai.AuthenticationError:
                logger.error("❌ Invalid OpenAI API key provided.")
                raise ValueError("Invalid OpenAI API key provided.")
            logger.info("✅ Components re-initialized with new configuration")
        except Exception as e:
            logger.error(f"❌ Error re-initializing components with new config: {e}")
            # Optionally, revert to old config or handle the error appropriately
            raise

    def _setup_chromadb(self) -> None:
        """Set up ChromaDB using langchain-chroma with persistence."""
        try:
            logger.info("🗄️ Setting up ChromaDB with langchain-chroma...")
            logger.info(f"📁 Persist directory: {self.persist_dir}")

            # Create persist directory if it doesn't exist
            os.makedirs(self.persist_dir, exist_ok=True)
            logger.info("✅ Persist directory created/verified")

            # Initialize embeddings
            try:
                self.embeddings = OpenAIEmbeddings(
                    model=self.config.embedding_model
                )
            except openai.AuthenticationError:
                logger.error("❌ Invalid OpenAI API key provided.")
                raise ValueError("Invalid OpenAI API key provided.")
            logger.info(
                f"✅ OpenAI embeddings initialized with model: {self.config.embedding_model}")

            # Initialize Chroma vector store
            self.vector_store = Chroma(
                collection_name="materials",
                embedding_function=self.embeddings,
                persist_directory=self.persist_dir,
            )

            existing_count = self.vector_store._collection.count()
            logger.info(
                f"📊 Collection 'materials' loaded with {existing_count} documents.")

            logger.info("✅ ChromaDB setup completed successfully")

        except Exception as e:
            logger.error(f"❌ Error setting up ChromaDB: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            raise

    def process_and_initialize(self, docs_dir: str) -> Tuple[bool, List[str]]:
        """
        Complete processing and initialization pipeline.

        Args:
            docs_dir: Directory containing documents

        Returns:
            Tuple of (success, status messages)
        """
        logger.info(
            f"🚀 Starting complete RAG processing for directory: {docs_dir}")
        status_messages = []

        try:
            # Step 1: Process documents
            success, messages = self.add_documents(docs_dir)
            status_messages.extend(messages)

            if not success:
                logger.error("❌ Document processing failed")
                return False, status_messages

            # Step 2: Initialize if we have documents
            if len(self.chunks) > 0:
                logger.info("🧠 Initializing conversation chain...")
                self._setup_chain()
                status_messages.append("✓ Conversation chain initialized")
                logger.info("✅ RAG system fully initialized and ready")
                return True, status_messages
            else:
                logger.warning("⚠️ No documents found to process")
                status_messages.append("⚠️ No documents found to process")
                return False, status_messages

        except Exception as e:
            error_msg = f"Error in complete initialization: {str(e)}"
            logger.error(f"❌ {error_msg}")
            status_messages.append(f"✗ {error_msg}")
            return False, status_messages

    def add_documents(self, docs_dir: str) -> Tuple[bool, List[str]]:
        """
        Add documents from the specified directory with enhanced logging.

        Args:
            docs_dir: Directory containing documents

        Returns:
            Tuple of (success, status messages)
        """
        logger.info(f"📂 Processing documents from: {docs_dir}")
        status_messages = []

        try:
            # Verify directory exists
            docs_path = Path(docs_dir)
            if not docs_path.exists():
                logger.error(f"❌ Directory does not exist: {docs_dir}")
                status_messages.append(f"✗ Directory not found: {docs_dir}")
                return False, status_messages

            logger.info(f"✅ Directory exists: {docs_path.absolute()}")

            # Count files before processing
            all_files = list(docs_path.rglob("*"))
            doc_files = [f for f in all_files if f.is_file() and f.suffix.lower() in [
                '.pdf', '.txt', '.docx']]

            logger.info(
                f"📊 Found {len(all_files)} total files, {len(doc_files)} processable documents")

            if len(doc_files) == 0:
                logger.warning("⚠️ No processable documents found")
                status_messages.append("⚠️ No documents found to process")
                return False, status_messages

            # List found files
            for file in doc_files:
                logger.info(
                    f"📄 Found: {file.name} ({file.stat().st_size} bytes)")

            # Import documents
            status_messages.append("📥 Importing documents...")
            self._import_documents(docs_dir)
            status_messages.append(
                f"✓ Imported {len(self.documents)} documents")
            logger.info(f"✅ Imported {len(self.documents)} documents")

            if len(self.documents) == 0:
                logger.warning("⚠️ No documents were successfully imported")
                status_messages.append(
                    "⚠️ No documents were successfully imported")
                return False, status_messages

            # Split into chunks
            status_messages.append("✂️ Splitting documents into chunks...")
            self._split_documents()
            status_messages.append(f"✓ Created {len(self.chunks)} chunks")
            logger.info(f"✅ Created {len(self.chunks)} chunks")

            # Generate embeddings and store in ChromaDB
            status_messages.append("🧠 Generating embeddings...")
            self._store_embeddings()
            status_messages.append("✓ Embeddings generated and stored")
            logger.info("✅ Embeddings stored in ChromaDB")

            return True, status_messages

        except Exception as e:
            error_msg = f"Error processing documents: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            status_messages.append(f"✗ {error_msg}")
            return False, status_messages

    def _import_documents(self, docs_dir: str) -> None:
        """Import documents from directory with enhanced error handling"""
        logger.info(f"📥 Importing documents from: {docs_dir}")

        if not os.path.exists(docs_dir):
            raise ValueError(f"Directory not found: {docs_dir}")

        # Define loaders with error handling
        loaders = {
            "**/*.pdf": PyPDFLoader,
            "**/*.txt": TextLoader,
        }

        # Try to add DOCX support
        try:
            from langchain_community.document_loaders import Docx2txtLoader
            loaders["**/*.docx"] = Docx2txtLoader
            logger.info("✅ DOCX support enabled")
        except ImportError:
            logger.warning(
                "⚠️ DOCX support not available - install python-docx if needed")

        # Process each file type
        for glob_pattern, loader_class in loaders.items():
            try:
                logger.info(f"🔍 Processing {glob_pattern} files...")
                loader = DirectoryLoader(
                    docs_dir,
                    glob=glob_pattern,
                    loader_cls=loader_class,
                    recursive=True
                )

                docs = loader.load()
                if docs:
                    self.documents.extend(docs)
                    logger.info(
                        f"✅ Loaded {len(docs)} documents from {glob_pattern}")
                else:
                    logger.info(f"ℹ️ No documents found for {glob_pattern}")

            except Exception as e:
                logger.error(f"❌ Error loading {glob_pattern}: {str(e)}")
                continue

        # Add enhanced metadata
        for idx, doc in enumerate(self.documents):
            doc.metadata.update({
                "doc_id": idx,
                "filename": Path(doc.metadata["source"]).name,
                "filetype": Path(doc.metadata["source"]).suffix[1:].lower(),
                "imported_at": time.time()
            })

        logger.info(f"✅ Total documents imported: {len(self.documents)}")

    def _split_documents(self) -> None:
        """Split documents into chunks with logging"""
        logger.info("✂️ Splitting documents into chunks...")
        logger.info(
            f"⚙️ Chunk size: {self.config.chunk_size}, Overlap: {self.config.chunk_overlap}")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

        self.chunks = splitter.split_documents(self.documents)

        # Add chunk IDs and enhanced metadata
        for idx, chunk in enumerate(self.chunks):
            chunk.metadata["chunk_id"] = idx
            chunk.metadata["chunk_size"] = len(chunk.page_content)
            chunk.metadata["created_at"] = time.time()

        logger.info(f"✅ Documents split into {len(self.chunks)} chunks")

        # Log chunk statistics
        if self.chunks:
            sizes = [len(chunk.page_content) for chunk in self.chunks]
            avg_size = sum(sizes) / len(sizes)
            logger.info(
                f"📊 Chunk stats - Min: {min(sizes)}, Max: {max(sizes)}, Avg: {avg_size:.0f}")

    def _store_embeddings(self) -> None:
        """Store document chunks in ChromaDB using the langchain wrapper."""
        logger.info("🗄️ Storing embeddings in ChromaDB...")

        if not self.chunks:
            logger.warning("⚠️ No chunks to store. Skipping embedding process.")
            return

        logger.info(f"📤 Storing {len(self.chunks)} chunks...")

        if not self.vector_store:
            logger.error("❌ Vector store not initialized. Skipping embedding process.")
            raise ValueError("Vector store not initialized")

        try:
            # The add_documents method handles chunking, embedding, and storage
            self.vector_store.add_documents(self.chunks)
            logger.info(f"✅ Successfully stored {len(self.chunks)} chunks.")

            # Verify storage
            count = self.vector_store._collection.count()
            logger.info(f"📊 Collection now contains {count} documents")

        except Exception as e:
            logger.error(f"❌ Error storing embeddings: {str(e)}")
            raise

    def _setup_chain(self) -> None:
        """Set up the components for the RAG-Fusion conversation chain."""
        logger.info("🔗 Setting up RAG-Fusion components...")

        try:
            # Initialize LLM
            try:
                self.llm = ChatOpenAI(
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    max_completion_tokens=self.config.max_tokens
                )
            except openai.AuthenticationError:
                logger.error("❌ Invalid OpenAI API key provided.")
                raise ValueError("Invalid OpenAI API key provided.")
            logger.info("✅ LLM initialized")

            # RAG-Fusion: Query Generation Prompt
            query_gen_template = """You are a helpful assistant that generates multiple search queries based on a single input query.
Generate multiple search queries related to: {question}
Output (4 queries):"""
            self.query_gen_prompt = ChatPromptTemplate.from_template(
                query_gen_template)

            # Final RAG Chain Prompt
            answer_template = """{prompt}

Context:
{context}

Question: {question}
"""
            self.answer_prompt = ChatPromptTemplate.from_template(answer_template)

            self.chain = True  # Mark as initialized
            logger.info("✅ RAG-Fusion components created successfully")

        except Exception as e:
            logger.error(
                f"❌ Error setting up conversation chain components: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            self.chain = None
            raise

    def generate_response(
        self,
        question: str,
        material_ids: Optional[List[str]] = None,
        config: Optional[AssistantConfigModel] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using the RAG system. If a config is provided,
        it uses a temporary chain for the request.

        Args:
            question: User question.
            material_ids: Optional list of source material IDs to filter by.
            config: Optional assistant configuration for this specific request.

        Returns:
            Dictionary containing answer, sources, and response time.
        """
        if not self.chain or not self.vector_store:
            logger.error("❌ System not properly initialized")
            return {
                "answer": "Sistema não inicializado corretamente. Execute a inicialização primeiro.",
                "sources": [],
                "response_time": 0
            }

        try:
            logger.info(f"💭 Generating response for: '{question[:50]}...'")
            if material_ids:
                logger.info(f"🔍 Filtering by {len(material_ids)} material(s).")
            start_time = time.time()

            # Determine which LLM and prompt to use
            if config:
                logger.info(f"⚡ Using temporary config for this request: {config.name}")
                # Create a temporary LLM instance for this request
                temp_llm = ChatOpenAI(
                    model=config.model,
                    temperature=config.temperature,
                    max_completion_tokens=self.config.max_tokens  # Keep max_tokens from default
                )
                # Use the prompt from the provided config
                final_prompt = self.answer_prompt.partial(prompt=config.prompt)
            else:
                # Fallback to the handler's default LLM and a generic prompt
                temp_llm = self.llm
                final_prompt = self.answer_prompt.partial(
                    prompt="Você é um assistente de IA. Responda à pergunta com base no contexto fornecido."
                )


            # 1. Generate multiple queries (using the default LLM for this step)
            query_gen_chain = (
                self.query_gen_prompt
                | self.llm
                | StrOutputParser()
                | (lambda x: [q.strip() for q in x.split("\n") if q.strip()])
            )
            generated_queries = query_gen_chain.invoke({"question": question})
            logger.info(f"🔍 Generated {len(generated_queries)} queries.")

            # 2. Retrieve documents for each query
            search_kwargs: Dict[str, Any] = {'k': 5}
            if material_ids:
                search_kwargs['filter'] = {"source": {"$in": material_ids}}

            retriever = self.vector_store.as_retriever(search_kwargs=search_kwargs)

            retrieved_docs = []
            for q in generated_queries:
                docs = retriever.get_relevant_documents(q)
                retrieved_docs.append(docs)

            # 3. Rerank documents
            reranked_results = reciprocal_rank_fusion(retrieved_docs)
            logger.info(f"🔄 Reranked {len(reranked_results)} documents.")

            # 4. Format context and extract sources
            context = "\n\n".join([doc.page_content for doc, score in reranked_results[:5]])

            unique_sources = []
            seen_sources = set()
            for doc, score in reranked_results[:5]:
                source = doc.metadata.get('source')
                if source and source not in seen_sources:
                    unique_sources.append({
                        "source": source,
                        "filename": doc.metadata.get('filename', Path(source).name)
                    })
                    seen_sources.add(source)

            # 5. Generate final answer using the selected LLM and prompt
            answer_chain = final_prompt | temp_llm | StrOutputParser()
            answer = answer_chain.invoke({"context": context, "question": question})

            response_time = time.time() - start_time
            logger.info(f"✅ Response generated in {response_time:.2f}s")

            return {
                "answer": answer,
                "sources": unique_sources,
                "response_time": response_time
            }

        except Exception as e:
            logger.error(f"❌ Error generating response: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            return {
                "answer": "Ocorreu um erro ao gerar a resposta. Verifique os logs para mais detalhes.",
                "sources": [],
                "response_time": 0
            }

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics for debugging"""
        try:
            stats = {
                "documents_loaded": len(self.documents),
                "chunks_created": len(self.chunks),
                "collection_count": self.vector_store._collection.count() if self.vector_store else 0,
                "chain_initialized": self.chain is not None,
                "retriever_available": hasattr(self, 'retriever'),
                "config": {
                    "model_name": self.config.model_name,
                    "chunk_size": self.config.chunk_size,
                    "chunk_overlap": self.config.chunk_overlap,
                    "temperature": self.config.temperature
                }
            }

            if self.documents:
                file_types = {}
                for doc in self.documents:
                    file_type = doc.metadata.get("filetype", "unknown")
                    file_types[file_type] = file_types.get(file_type, 0) + 1
                stats["file_types"] = file_types

            return stats

        except Exception as e:
            logger.error(f"❌ Error getting system stats: {e}")
            return {"error": str(e)}

    def reset(self) -> None:
        """Reset the handler state with logging"""
        logger.info("🔄 Resetting RAG handler...")

        try:
            self.documents = []
            self.chunks = []

            if self.vector_store:
                # Access the underlying collection to delete all items
                self.vector_store._collection.delete(where={})
                logger.info("🧹 Cleared collection")

            self.chain = None
            if hasattr(self, 'retriever'):
                delattr(self, 'retriever')

            logger.info("✅ RAG handler reset successfully")

        except Exception as e:
            logger.error(f"❌ Error resetting handler: {e}")


def reciprocal_rank_fusion(results: list[list], k=60):
    """ Reciprocal_rank_fusion that takes multiple lists of ranked documents
        and an optional parameter k used in the RRF formula """

    # Initialize a dictionary to hold fused scores for each unique document
    fused_scores = {}

    # Iterate through each list of ranked documents
    for docs in results:
        # Iterate through each document in the list, with its rank (position in the list)
        for rank, doc in enumerate(docs):
            # Convert the document to a string format to use as a key (assumes documents can be serialized to JSON)
            doc_str = dumps(doc)
            # If the document is not yet in the fused_scores dictionary, add it with an initial score of 0
            if doc_str not in fused_scores:
                fused_scores[doc_str] = 0
            # Retrieve the current score of the document, if any
            previous_score = fused_scores[doc_str]
            # Update the score of the document using the RRF formula: 1 / (rank + k)
            fused_scores[doc_str] += 1 / (rank + k)

    # Sort the documents based on their fused scores in descending order to get the final reranked results
    reranked_results = [
        (loads(doc), score)
        for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    ]

    # Return the reranked results as a list of tuples, each containing the document and its fused score
    return reranked_results
