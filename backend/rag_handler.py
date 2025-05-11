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
from langchain.document_loaders.pdf import PyPDFLoader
from langchain.document_loaders.text import TextLoader
from langchain.document_loaders.docx import Docx2txtLoader
from langchain.document_loaders.directory import DirectoryLoader

from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

# Configure logging
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
    model_name: str = "gpt-4"
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
    Manages document processing, embedding generation, and response generation.
    """

    def __init__(
        self,
        api_key: str,
        config: Optional[ProcessingConfig] = None,
        persist_dir: str = ".chromadb"
    ):
        """
        Initialize the RAG handler.

        Args:
            api_key: OpenAI API key
            config: Processing configuration
            persist_dir: Directory to persist ChromaDB
        """
        self.api_key = api_key
        self.config = config or ProcessingConfig()
        self.persist_dir = persist_dir

        # Initialize components
        self.documents = []
        self.chunks = []
        self.db = None
        self.collection = None
        self.chain = None

        # Set up ChromaDB
        self._setup_chromadb()

        logger.info(
            f"Initialized RAG handler with model {self.config.model_name} "
            f"and embedding model {self.config.embedding_model}"
        )

    def _setup_chromadb(self) -> None:
        """Set up ChromaDB with persistence"""
        try:
            self.db = chromadb.Client(
                Settings(
                    persist_directory=self.persist_dir,
                    chroma_db_impl="duckdb+parquet"
                )
            )

            # Use OpenAI embeddings
            embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=self.api_key,
                model_name=self.config.embedding_model
            )

            # Create or get collection
            self.collection = self.db.get_or_create_collection(
                name="dna_da_forca",
                embedding_function=embedding_function
            )

            logger.info("ChromaDB setup completed successfully")

        except Exception as e:
            logger.error(f"Error setting up ChromaDB: {str(e)}")
            raise

    def process_documents(self, docs_dir: str) -> Tuple[bool, List[str]]:
        """
        Process documents from the specified directory.

        Args:
            docs_dir: Directory containing documents

        Returns:
            Tuple of (success, status messages)
        """
        status_messages = []

        try:
            # Import documents
            status_messages.append("Importing documents...")
            self._import_documents(docs_dir)
            status_messages.append(
                f"✓ Imported {len(self.documents)} documents")

            # Split into chunks
            status_messages.append("Splitting documents...")
            self._split_documents()
            status_messages.append(f"✓ Created {len(self.chunks)} chunks")

            # Generate embeddings and store in ChromaDB
            status_messages.append("Generating embeddings...")
            self._store_embeddings()
            status_messages.append("✓ Embeddings generated and stored")

            # Create conversation chain
            status_messages.append("Setting up conversation chain...")
            self._setup_chain()
            status_messages.append("✓ Conversation chain ready")

            return True, status_messages

        except Exception as e:
            error_msg = f"Error processing documents: {str(e)}"
            logger.error(error_msg)
            status_messages.append(f"✗ {error_msg}")
            return False, status_messages

    def _import_documents(self, docs_dir: str) -> None:
        """Import documents from directory"""
        if not os.path.exists(docs_dir):
            raise ValueError(f"Directory not found: {docs_dir}")

        loaders = {
            "**/*.pdf": PyPDFLoader,
            "**/*.txt": TextLoader,
            "**/*.docx": Docx2txtLoader
        }

        for glob_pattern, loader_class in loaders.items():
            loader = DirectoryLoader(
                docs_dir,
                glob=glob_pattern,
                loader_cls=loader_class,
                recursive=True
            )
            self.documents.extend(loader.load())

        # Add metadata
        for idx, doc in enumerate(self.documents):
            doc.metadata.update({
                "doc_id": idx,
                "filename": Path(doc.metadata["source"]).name,
                "filetype": Path(doc.metadata["source"]).suffix[1:].lower()
            })

    def _split_documents(self) -> None:
        """Split documents into chunks"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

        self.chunks = splitter.split_documents(self.documents)

        # Add chunk IDs
        for idx, chunk in enumerate(self.chunks):
            chunk.metadata["chunk_id"] = idx

    def _store_embeddings(self) -> None:
        """Store document chunks in ChromaDB"""
        # Clear existing data
        self.collection.delete(where={})

        # Prepare data for bulk insertion
        ids = []
        texts = []
        metadatas = []

        for chunk in self.chunks:
            chunk_id = f"chunk_{chunk.metadata['chunk_id']}"
            ids.append(chunk_id)
            texts.append(chunk.page_content)
            metadatas.append(chunk.metadata)

        # Add to collection
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

    def _setup_chain(self) -> None:
        """Set up the conversation chain"""
        # Initialize LLM
        llm = ChatOpenAI(
            api_key=self.api_key,
            model_name=self.config.model_name,
            temperature=self.config.temperature
        )

        # Create memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Create prompt template
        template = """Você é um assistente especializado em treinamento físico do DNA da Força.
        Use o contexto fornecido para responder à pergunta de forma precisa e profissional.
        Se a informação não estiver no contexto, diga que não pode responder.
        
        Histórico do chat: {chat_history}
        Contexto: {context}
        Pergunta: {question}
        
        Resposta:"""

        prompt = PromptTemplate(
            input_variables=["chat_history", "context", "question"],
            template=template
        )

        # Create retriever
        retriever = self.collection.as_retriever(
            search_kwargs={"k": 5}
        )

        # Create chain
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": prompt},
            return_source_documents=True
        )

    def generate_response(self, question: str) -> Dict[str, Any]:
        """
        Generate a response to a question.

        Args:
            question: User question

        Returns:
            Dictionary containing answer, sources, and response time
        """
        if not self.chain:
            return {
                "answer": "Sistema não inicializado. Configure o assistente primeiro.",
                "sources": [],
                "response_time": 0
            }

        try:
            # Time the response
            start_time = time.time()

            # Generate response
            response = self.chain({"question": question})

            # Format sources
            sources = []
            for doc in response.get("source_documents", []):
                source = Source(
                    title=doc.metadata.get("filename", "Unknown"),
                    source=doc.metadata.get("source", "Unknown"),
                    page=doc.metadata.get("page"),
                    chunk=doc.page_content[:200] + "..."
                )
                sources.append(source)

            return {
                "answer": response.get("answer", ""),
                "sources": sources,
                "response_time": time.time() - start_time
            }

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "answer": "Erro ao gerar resposta. Por favor, tente novamente.",
                "sources": [],
                "response_time": 0
            }

    def reset(self) -> None:
        """Reset the handler state"""
        self.documents = []
        self.chunks = []
        self.collection.delete(where={})
        self.chain = None
