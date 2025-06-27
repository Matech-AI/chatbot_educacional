import os
import logging
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.document_loaders.text import TextLoader
from langchain.document_loaders.directory import DirectoryLoader

from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

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
        self.db = None
        self.collection = None
        self.chain = None

        # Validate API key
        if not api_key or len(api_key) < 10:
            logger.error("❌ Invalid OpenAI API key provided")
            raise ValueError("Valid OpenAI API key is required")

        logger.info(f"🔑 API key validated (length: {len(api_key)})")
        logger.info(f"⚙️ Configuration: {self.config}")

        # Set up ChromaDB
        self._setup_chromadb()

        logger.info("✅ RAG handler initialized successfully")

    def _setup_chromadb(self) -> None:
        """Set up ChromaDB with persistence and enhanced logging"""
        try:
            logger.info("🗄️ Setting up ChromaDB...")
            logger.info(f"📁 Persist directory: {self.persist_dir}")

            # Create persist directory if it doesn't exist
            os.makedirs(self.persist_dir, exist_ok=True)
            logger.info("✅ Persist directory created/verified")

            self.db = chromadb.Client(
                Settings(
                    persist_directory=self.persist_dir,
                    chroma_db_impl="duckdb+parquet"
                )
            )
            logger.info("✅ ChromaDB client initialized")

            # Use OpenAI embeddings
            logger.info(
                f"🔧 Setting up OpenAI embeddings with model: {self.config.embedding_model}")
            embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=self.api_key,
                model_name=self.config.embedding_model
            )
            logger.info("✅ OpenAI embedding function created")

            # Create or get collection
            collection_name = "materials"
            logger.info(f"📦 Creating/getting collection: {collection_name}")

            self.collection = self.db.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_function
            )

            # Check existing documents in collection
            existing_count = self.collection.count()
            logger.info(
                f"📊 Existing documents in collection: {existing_count}")

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
            success, messages = self.process_documents(docs_dir)
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

    def process_documents(self, docs_dir: str) -> Tuple[bool, List[str]]:
        """
        Process documents from the specified directory with enhanced logging.

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
            from langchain.document_loaders.docx import Docx2txtLoader
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
        """Store document chunks in ChromaDB with progress tracking"""
        logger.info("🗄️ Storing embeddings in ChromaDB...")

        # Clear existing data
        try:
            self.collection.delete(where={})
            logger.info("🧹 Cleared existing embeddings")
        except Exception as e:
            logger.warning(f"⚠️ Could not clear existing data: {e}")

        # Prepare data for bulk insertion
        ids = []
        texts = []
        metadatas = []

        for chunk in self.chunks:
            chunk_id = f"chunk_{chunk.metadata['chunk_id']}"
            ids.append(chunk_id)
            texts.append(chunk.page_content)
            metadatas.append(chunk.metadata)

        logger.info(f"📤 Preparing to store {len(ids)} chunks...")

        # Add to collection with progress tracking
        try:
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            logger.info(f"✅ Successfully stored {len(ids)} embeddings")

            # Verify storage
            count = self.collection.count()
            logger.info(f"📊 Collection now contains {count} documents")

        except Exception as e:
            logger.error(f"❌ Error storing embeddings: {str(e)}")
            raise

    def _setup_chain(self) -> None:
        """Set up the conversation chain with enhanced configuration"""
        logger.info("🔗 Setting up conversation chain...")

        try:
            # Initialize LLM
            logger.info(f"🤖 Initializing LLM: {self.config.model_name}")
            llm = ChatOpenAI(
                api_key=self.api_key,
                model_name=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            logger.info("✅ LLM initialized")

            # Create memory
            logger.info("🧠 Creating conversation memory...")
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            logger.info("✅ Memory created")

            # Create enhanced prompt template
            template = """Você é um assistente especializado em treinamento físico e educação física do sistema DNA da Força.

DIRETRIZES IMPORTANTES:
1. Use APENAS o contexto fornecido para responder às perguntas
2. Se a informação não estiver no contexto, diga claramente que não pode responder
3. Cite as fontes quando possível (nome do documento, página)
4. Mantenha um tom profissional e educativo
5. Forneça explicações claras e práticas
6. Use exemplos quando apropriado

Histórico da conversa: {chat_history}

Contexto dos documentos: {context}

Pergunta do usuário: {question}

Resposta (baseada apenas no contexto fornecido):"""

            prompt = PromptTemplate(
                input_variables=["chat_history", "context", "question"],
                template=template
            )
            logger.info("✅ Prompt template created")

            # Create retriever
            logger.info("🔍 Creating document retriever...")

            # Use the collection as a retriever through a custom wrapper
            class ChromaRetriever:
                def __init__(self, collection):
                    self.collection = collection

                def get_relevant_documents(self, query: str, k: int = 5):
                    results = self.collection.query(
                        query_texts=[query],
                        n_results=k
                    )

                    # Convert to LangChain document format
                    documents = []
                    if results['documents']:
                        for i, doc_text in enumerate(results['documents'][0]):
                            metadata = results['metadatas'][0][i] if results['metadatas'] else {
                            }
                            from langchain.schema import Document
                            documents.append(Document(
                                page_content=doc_text,
                                metadata=metadata
                            ))

                    return documents

            retriever = ChromaRetriever(self.collection)
            logger.info("✅ Retriever created")

            # Create a simple QA chain
            from langchain.chains.question_answering import load_qa_chain

            self.chain = load_qa_chain(
                llm=llm,
                chain_type="stuff",
                prompt=prompt,
                memory=memory
            )

            # Store retriever for later use
            self.retriever = retriever

            logger.info("✅ Conversation chain created successfully")

        except Exception as e:
            logger.error(f"❌ Error setting up conversation chain: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            raise

    def generate_response(self, question: str) -> Dict[str, Any]:
        """
        Generate a response to a question with enhanced error handling.

        Args:
            question: User question

        Returns:
            Dictionary containing answer, sources, and response time
        """
        if not self.chain or not hasattr(self, 'retriever'):
            logger.error("❌ System not properly initialized")
            return {
                "answer": "Sistema não inicializado corretamente. Execute a inicialização primeiro.",
                "sources": [],
                "response_time": 0
            }

        try:
            logger.info(f"💭 Generating response for: {question[:50]}...")
            start_time = time.time()

            # Get relevant documents
            logger.info("🔍 Retrieving relevant documents...")
            relevant_docs = self.retriever.get_relevant_documents(
                question, k=5)
            logger.info(f"📄 Found {len(relevant_docs)} relevant documents")

            # Generate response
            logger.info("🤖 Generating AI response...")
            response = self.chain.run(
                input_documents=relevant_docs,
                question=question
            )

            # Format sources
            sources = []
            for doc in relevant_docs:
                source = {
                    "title": doc.metadata.get("filename", "Unknown"),
                    "source": doc.metadata.get("source", "Unknown"),
                    "page": doc.metadata.get("page"),
                    "chunk": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                }
                sources.append(source)

            response_time = time.time() - start_time
            logger.info(f"✅ Response generated in {response_time:.2f}s")

            return {
                "answer": response,
                "sources": sources,
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
                "collection_count": self.collection.count() if self.collection else 0,
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

            if self.collection:
                self.collection.delete(where={})
                logger.info("🧹 Cleared collection")

            self.chain = None
            if hasattr(self, 'retriever'):
                delattr(self, 'retriever')

            logger.info("✅ RAG handler reset successfully")

        except Exception as e:
            logger.error(f"❌ Error resetting handler: {e}")
