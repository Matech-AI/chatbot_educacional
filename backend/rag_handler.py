import os
import logging
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders.directory import DirectoryLoader

from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
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
class IngestionConfig:
    """Configuration for document ingestion"""
    chunk_size: int = 2000
    chunk_overlap: int = 200


@dataclass
class EmbeddingConfig:
    """Configuration for embedding model"""
    embedding_model: str = "text-embedding-ada-002"


@dataclass
class GenerationConfig:
    """Configuration for response generation"""
    model_name: str = "gpt-4o-mini"
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
        ingestion_config: Optional[IngestionConfig] = None,
        embedding_config: Optional[EmbeddingConfig] = None,
        generation_config: Optional[GenerationConfig] = None,
        persist_dir: str = ".chromadb"
    ):
        """
        Initialize the RAG handler.
        Args:
            api_key: OpenAI API key
            ingestion_config: Configuration for document ingestion
            embedding_config: Configuration for embedding model
            generation_config: Configuration for response generation
            persist_dir: Directory to persist ChromaDB
        """
        logger.info("🚀 Initializing RAG handler...")
        self.api_key = api_key
        self.ingestion_config = ingestion_config or IngestionConfig()
        self.embedding_config = embedding_config or EmbeddingConfig()
        self.generation_config = generation_config or GenerationConfig()
        self.persist_dir = persist_dir

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
        logger.info(f"⚙️ Ingestion Config: {self.ingestion_config}")
        logger.info(f"⚙️ Embedding Config: {self.embedding_config}")
        logger.info(f"⚙️ Generation Config: {self.generation_config}")

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
                f"🔧 Setting up OpenAI embeddings with model: {self.embedding_config.embedding_model}")
            embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=self.api_key,
                model_name=self.embedding_config.embedding_model
            )
            logger.info("✅ OpenAI embedding function created")

            # Create or get collection
            collection_name = "dna_da_forca"
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

    def process_and_initialize(self, docs_dir: str, knowledge_base_id: str) -> Tuple[bool, List[str]]:
        """
        Complete processing and initialization pipeline.

        Args:
            docs_dir: Directory containing documents
            knowledge_base_id: Identifier for the knowledge base these documents belong to

        Returns:
            Tuple of (success, status messages)
        """
        logger.info(
            f"🚀 Starting complete RAG processing for directory: {docs_dir}")
        status_messages = []

        try:
            # Step 1: Process documents
            logger.info(f"🧠 Processing documents for knowledge base: {knowledge_base_id}")
            success, messages = self.process_documents(docs_dir, knowledge_base_id)
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

    def process_documents(self, docs_dir: str, knowledge_base_id: str) -> Tuple[bool, List[str]]:
        """
        Process documents from the specified directory with enhanced logging.

        Args:
            docs_dir: Directory containing documents
            knowledge_base_id: Identifier for the knowledge base

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
            status_messages.append(f"📥 Importing documents for KB: {knowledge_base_id}...")
            self._import_documents(docs_dir, knowledge_base_id)
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
            status_messages.append(f"🧠 Generating embeddings for KB: {knowledge_base_id}...")
            self._store_embeddings(knowledge_base_id) # Pass knowledge_base_id here
            status_messages.append("✓ Embeddings generated and stored")
            logger.info("✅ Embeddings stored in ChromaDB")

            return True, status_messages

        except Exception as e:
            error_msg = f"Error processing documents: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            status_messages.append(f"✗ {error_msg}")
            return False, status_messages

    def process_single_file(self, file_path: str, knowledge_base_id: str) -> Tuple[bool, List[str]]:
        """Process a single document file."""
        logger.info(f"📄 Processing single file: {file_path} for KB: {knowledge_base_id}")
        status_messages = []
        
        try:
            file = Path(file_path)
            if not file.exists():
                msg = f"File not found: {file_path}"
                logger.error(f"❌ {msg}")
                return False, [msg]

            # Use the appropriate loader based on file extension
            ext = file.suffix.lower()
            loader_cls = None
            if ext == '.pdf':
                loader_cls = PyPDFLoader
            elif ext == '.txt':
                loader_cls = TextLoader
            elif ext == '.docx':
                try:
                    from langchain_community.document_loaders.docx import Docx2txtLoader
                    loader_cls = Docx2txtLoader
                except ImportError:
                    msg = "DOCX support not available. Please install python-docx."
                    logger.error(f"❌ {msg}")
                    return False, [msg]
            
            if not loader_cls:
                msg = f"Unsupported file type: {ext}"
                logger.error(f"❌ {msg}")
                return False, [msg]

            # Load, split, and store the single document
            loader = loader_cls(file_path)
            self.documents = loader.load()
            for doc in self.documents:
                doc.metadata["knowledge_base_id"] = knowledge_base_id

            self._split_documents()
            self._store_embeddings(knowledge_base_id)
            
            msg = f"✓ Successfully processed and embedded {file.name} into KB: {knowledge_base_id}"
            logger.info(f"✅ {msg}")
            status_messages.append(msg)
            
            return True, status_messages

        except Exception as e:
            error_msg = f"Error processing single file: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, [error_msg]

    def _import_documents(self, docs_dir: str, knowledge_base_id: str) -> None:
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
            from langchain_community.document_loaders.docx import Docx2txtLoader
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
                "imported_at": time.time(),
                "knowledge_base_id": knowledge_base_id
            })

        logger.info(f"✅ Total documents imported: {len(self.documents)}")

    def _split_documents(self) -> None:
        """Split documents into chunks with logging"""
        logger.info("✂️ Splitting documents into chunks...")
        logger.info(
            f"⚙️ Chunk size: {self.ingestion_config.chunk_size}, Overlap: {self.ingestion_config.chunk_overlap}")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.ingestion_config.chunk_size,
            chunk_overlap=self.ingestion_config.chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

        self.chunks = splitter.split_documents(self.documents)

        # Add chunk IDs and enhanced metadata
        for idx, chunk in enumerate(self.chunks):
            chunk.metadata["chunk_id"] = idx
            chunk.metadata["chunk_size"] = len(chunk.page_content)
            chunk.metadata["created_at"] = time.time()
            # Propagate knowledge_base_id from parent document
            if 'knowledge_base_id' in chunk.metadata:
                pass # Already set if document had it, otherwise it might be missing
            elif self.documents and hasattr(self.documents[0], 'metadata') and 'knowledge_base_id' in self.documents[0].metadata:
                 # Fallback: if all docs in this batch are for the same KB, grab from the first one
                 # This assumes _split_documents is called after _import_documents for a specific KB
                chunk.metadata['knowledge_base_id'] = self.documents[0].metadata['knowledge_base_id']

        logger.info(f"✅ Documents split into {len(self.chunks)} chunks")

        # Log chunk statistics
        if self.chunks:
            sizes = [len(chunk.page_content) for chunk in self.chunks]
            avg_size = sum(sizes) / len(sizes)
            logger.info(
                f"📊 Chunk stats - Min: {min(sizes)}, Max: {max(sizes)}, Avg: {avg_size:.0f}")

    def _store_embeddings(self, knowledge_base_id: str) -> None:
        """Store document chunks in ChromaDB with progress tracking"""
        logger.info("🗄️ Storing embeddings in ChromaDB...")

        # Ensure all chunks have the knowledge_base_id in their metadata
        for chunk in self.chunks:
            if 'knowledge_base_id' not in chunk.metadata:
                # This is a fallback, ideally it's set during _import_documents and propagated by _split_documents
                chunk.metadata['knowledge_base_id'] = knowledge_base_id 
                logger.warning(f"Fallback: Added knowledge_base_id '{knowledge_base_id}' to chunk {chunk.metadata.get('chunk_id')} in _store_embeddings")
            elif chunk.metadata['knowledge_base_id'] != knowledge_base_id:
                logger.warning(f"Mismatch: Chunk {chunk.metadata.get('chunk_id')} has KB ID {chunk.metadata['knowledge_base_id']}, storing with {knowledge_base_id}")
                chunk.metadata['knowledge_base_id'] = knowledge_base_id # Ensure it's the current one

        # Prepare data for bulk insertion
        ids = []
        texts = []
        metadatas = []

        for chunk in self.chunks:
            chunk_id = f"chunk_{chunk.metadata['chunk_id']}"
            ids.append(chunk_id)
            texts.append(chunk.page_content)
            chunk.metadata["last_updated"] = time.time()
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
            # This is a placeholder. The actual chain is now created on-the-fly in generate_response
            self.chain = "initialized"
            logger.info("✅ Chain setup placeholder is set. Chain will be constructed per-request.")

        except Exception as e:
            logger.error(f"❌ Error in post-embedding setup: {str(e)}")
            raise

    def generate_response(self, question: str, allowed_knowledge_base_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a response to a question using a dynamically constructed RAG chain.
        Args:
            question: The user's question
            allowed_knowledge_base_ids: Optional list of knowledge base IDs to filter the search
        Returns:
            A dictionary containing the answer and sources.
        """
        if not self.collection:
            logger.error("❌ Collection not initialized")
            return {"answer": "O sistema de chat não foi inicializado corretamente.", "sources": []}

        logger.info(f"💬 Generating response for: '{question[:50]}...' with KBs: {allowed_knowledge_base_ids}")
        start_time = time.time()

        try:
            # 1. Retriever
            retriever = self.collection.as_retriever(
                search_kwargs={
                    "k": 5,
                    "where": {"knowledge_base_id": {"$in": allowed_knowledge_base_ids}} if allowed_knowledge_base_ids else {}
                }
            )

            # 2. LLM
            llm = ChatOpenAI(
                api_key=self.api_key,
                model_name=self.generation_config.model_name,
                temperature=self.generation_config.temperature,
                max_tokens=self.generation_config.max_tokens
            )

            # 3. Memory
            memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

            # 4. Prompt
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
            prompt = PromptTemplate(input_variables=["chat_history", "context", "question"], template=template)

            # 5. Chain
            chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                memory=memory,
                combine_docs_chain_kwargs={"prompt": prompt},
                return_source_documents=True
            )

            result = chain({"question": question})
            answer = result.get("answer", "Não foi possível gerar uma resposta.")

            sources = []
            if 'source_documents' in result:
                for doc in result['source_documents']:
                    metadata = doc.metadata
                    sources.append(Source(
                        title=metadata.get('filename', 'N/A'),
                        source=metadata.get('source', 'N/A'),
                        page=metadata.get('page'),
                        chunk=doc.page_content
                    ))

            response_time = time.time() - start_time
            logger.info(f"✅ Response generated in {response_time:.2f}s")

            return {
                "answer": answer,
                "sources": [s.__dict__ for s in sources],
                "response_time": response_time
            }

        except Exception as e:
            logger.error(f"❌ Error generating response: {str(e)}")
            raise

    def get_available_knowledge_bases(self) -> List[str]:
        """Get a list of unique knowledge_base_id values from the collection efficiently."""
        try:
            if not self.collection:
                logger.warning("⚠️ Collection not initialized, cannot get knowledge bases")
                return []

            # Efficiently get unique metadata values if the backend supports it.
            # ChromaDB's get() with include=['metadatas'] is the way for smaller sets.
            # For very large dbs, this might still be slow.
            metadatas = self.collection.get(include=["metadatas"])['metadatas']
            if not metadatas:
                return []

            kb_ids = set(md['knowledge_base_id'] for md in metadatas if md and 'knowledge_base_id' in md)
            
            logger.info(f"📚 Found knowledge bases: {list(kb_ids)}")
            return sorted(list(kb_ids))

        except Exception as e:
            logger.error(f"❌ Error getting knowledge bases: {str(e)}")
            return []

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics for debugging"""
        try:
            stats = {
                "chain_initialized": self.chain is not None,
                "collection_name": self.collection.name if self.collection else "N/A",
                "collection_count": self.collection.count() if self.collection else 0,
                "ingestion_config": self.ingestion_config.__dict__,
                "embedding_config": self.embedding_config.__dict__,
                "generation_config": self.generation_config.__dict__,
            }
            logger.info(f"📊 System stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"❌ Error getting system stats: {str(e)}")
            return {"error": str(e)}

    def reset(self) -> None:
        """Reset the handler state with logging"""
        logger.info("🔄 Resetting RAG handler...")
        try:
            if self.collection:
                # This is a more complex operation depending on Chroma's capabilities.
                # For a full reset, you might need to delete and recreate the collection.
                # self.db.delete_collection(name=self.collection.name)
                # self._setup_chromadb() # Re-initialize
                logger.warning("⚠️ Full collection reset is not implemented. Clearing in-memory state.")

            self.documents = []
            self.chunks = []
            self.chain = None
            logger.info("✅ RAG handler state reset")
        except Exception as e:
            logger.error(f"❌ Error resetting handler: {str(e)}")
            raise

    def list_documents(self, knowledge_base_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all documents in the vector store, optionally filtered by knowledge base."""
        logger.info(f"Listing documents for KB: {knowledge_base_id or 'all'}")
        try:
            if not self.collection:
                logger.warning("⚠️ Collection not initialized, cannot list documents")
                return []

            where_filter = {}
            if knowledge_base_id:
                where_filter = {"knowledge_base_id": knowledge_base_id}

            results = self.collection.get(where=where_filter, include=["metadatas"])
            
            # Deduplicate by filename
            unique_docs = {}
            for metadata in results.get('metadatas', []):
                filename = metadata.get('filename')
                if filename and filename not in unique_docs:
                    unique_docs[filename] = {
                        "filename": filename,
                        "knowledge_base_id": metadata.get('knowledge_base_id'),
                        "last_updated": metadata.get('last_updated'),
                        "source": metadata.get('source'),
                    }
            
            return list(unique_docs.values())

        except Exception as e:
            logger.error(f"❌ Error listing documents: {str(e)}")
            return []

    def delete_documents(self, knowledge_base_id: Optional[str] = None, filename: Optional[str] = None) -> Dict[str, Any]:
        """Delete documents from the collection by knowledge_base_id or filename."""
        if not knowledge_base_id and not filename:
            raise ValueError("Either knowledge_base_id or filename must be provided")

        logger.info(f"Deleting documents with KB: {knowledge_base_id} and filename: {filename}")
        try:
            if not self.collection:
                logger.warning("⚠️ Collection not initialized, cannot delete documents")
                return {"deleted_count": 0, "error": "Collection not initialized"}

            where_filter = {}
            if knowledge_base_id:
                where_filter["knowledge_base_id"] = knowledge_base_id
            if filename:
                where_filter["filename"] = filename
            
            # First, get the IDs of the documents to be deleted
            ids_to_delete = self.collection.get(where=where_filter, include=[])['ids']

            if not ids_to_delete:
                logger.info("No documents found to delete.")
                return {"deleted_count": 0}

            self.collection.delete(ids=ids_to_delete)
            logger.info(f"✅ Deleted {len(ids_to_delete)} document chunks.")
            return {"deleted_count": len(ids_to_delete)}

        except Exception as e:
            logger.error(f"❌ Error deleting documents: {str(e)}")
            return {"deleted_count": 0, "error": str(e)}
