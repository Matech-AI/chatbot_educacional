import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from pydantic import BaseModel
import openai
import hashlib
import json
from datetime import datetime

from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_community.document_loaders.directory import DirectoryLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.load import dumps, loads

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EducationalProcessingConfig:
    """Enhanced configuration for educational document processing"""
    # Text processing
    chunk_size: int = 1500  # Smaller chunks for better precision
    chunk_overlap: int = 300  # Higher overlap for context preservation
    
    # Model configuration
    model_name: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-ada-002"
    temperature: float = 0.2  # Lower temperature for educational consistency
    max_tokens: int = 800  # More space for detailed explanations
    
    # Educational features
    generate_learning_objectives: bool = True
    extract_key_concepts: bool = True
    identify_prerequisites: bool = True
    assess_difficulty_level: bool = True
    create_summaries: bool = True
    
    # Retrieval configuration
    retrieval_search_type: str = "mmr"  # Maximum Marginal Relevance
    retrieval_k: int = 6  # More sources for comprehensive answers
    retrieval_fetch_k: int = 20  # Broader initial search
    retrieval_lambda_mult: float = 0.7  # Balance relevance and diversity

class EducationalSource(BaseModel):
    """Enhanced source model for educational content"""
    title: str
    source: str
    page: Optional[int] = None
    chunk: str
    content_type: str = "text"  # text, video, data, image
    difficulty_level: str = "intermediate"  # beginner, intermediate, advanced
    key_concepts: List[str] = []
    learning_objectives: List[str] = []
    prerequisites: List[str] = []
    summary: str = ""
    relevance_score: float = 0.0
    educational_value: float = 0.0

class EducationalMetadata(BaseModel):
    """Metadata for educational content analysis"""
    difficulty_distribution: Dict[str, int] = {}
    content_type_distribution: Dict[str, int] = {}
    key_concepts_frequency: Dict[str, int] = {}
    total_sources: int = 0
    coverage_quality: float = 0.0

class EnhancedRAGHandler:
    """
    Enhanced RAG handler specifically designed for educational purposes
    with advanced source analysis and learning path generation
    """
    
    def __init__(
        self,
        api_key: str,
        config: Optional[EducationalProcessingConfig] = None,
        persist_dir: Optional[str] = None,
        materials_dir: str = "data/materials"
    ):
        """Initialize the enhanced educational RAG handler"""
        
        logger.info("🎓 Initializing Enhanced Educational RAG Handler...")
        
        self.api_key = api_key
        openai.api_key = self.api_key
        self.config = config or EducationalProcessingConfig()
        
        # Setup directories
        if persist_dir:
            self.persist_dir = persist_dir
        else:
            backend_dir = Path(__file__).parent
            self.persist_dir = str(backend_dir / ".chromadb_enhanced")
        
        self.materials_dir = Path(materials_dir)
        self.embeddings = None
        self.vector_store = None
        self.retriever = None
        self.llm = None
        
        # Educational enhancement caches
        self.concept_cache: Dict[str, List[str]] = {}
        self.difficulty_cache: Dict[str, str] = {}
        self.summary_cache: Dict[str, str] = {}
        
        # Initialize components
        self._initialize_embeddings()
        self._initialize_llm()
        self._initialize_vector_store()
        self._setup_educational_retriever()
        
        logger.info("✅ Enhanced Educational RAG Handler initialized successfully")
    
    def _initialize_embeddings(self):
        """Initialize embeddings model"""
        try:
            self.embeddings = OpenAIEmbeddings(
                model=self.config.embedding_model,
                api_key=self.api_key
            )
            logger.info(f"✅ Embeddings initialized: {self.config.embedding_model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings: {e}")
            raise
    
    def _initialize_llm(self):
        """Initialize language model for educational analysis"""
        try:
            self.llm = ChatOpenAI(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                api_key=self.api_key
            )
            logger.info(f"✅ LLM initialized: {self.config.model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            raise
    
    def _initialize_vector_store(self):
        """Initialize or load existing vector store"""
        try:
            # Check if vector store exists
            persist_path = Path(self.persist_dir)
            if persist_path.exists() and any(persist_path.iterdir()):
                logger.info(f"📂 Loading existing vector store from {self.persist_dir}")
                self.vector_store = Chroma(
                    persist_directory=self.persist_dir,
                    embedding_function=self.embeddings
                )
                logger.info(f"✅ Vector store loaded with {self.vector_store._collection.count()} documents")
            else:
                logger.info("🆕 Creating new vector store")
                self.vector_store = Chroma(
                    persist_directory=self.persist_dir,
                    embedding_function=self.embeddings
                )
                logger.info("✅ New vector store created")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {e}")
            raise
    
    def _setup_educational_retriever(self):
        """Setup enhanced retriever for educational content"""
        if self.vector_store:
            self.retriever = self.vector_store.as_retriever(
                search_type=self.config.retrieval_search_type,
                search_kwargs={
                    "k": self.config.retrieval_k,
                    "fetch_k": self.config.retrieval_fetch_k,
                    "lambda_mult": self.config.retrieval_lambda_mult
                }
            )
            logger.info("✅ Educational retriever configured")
    
    def _analyze_content_type(self, file_path: str) -> str:
        """Determine content type from file path"""
        path_lower = file_path.lower()
        if '.pdf' in path_lower:
            return 'research_paper' if any(keyword in path_lower for keyword in ['study', 'research', 'journal']) else 'document'
        elif any(ext in path_lower for ext in ['.mp4', '.avi', '.mov']):
            return 'video'
        elif any(ext in path_lower for ext in ['.xlsx', '.xls', '.csv']):
            return 'data'
        elif any(ext in path_lower for ext in ['.png', '.jpg', '.jpeg']):
            return 'image'
        else:
            return 'text'
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text using LLM"""
        if not self.config.extract_key_concepts or not self.llm:
            return []
        
        # Use cache to avoid repeated API calls
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.concept_cache:
            return self.concept_cache[text_hash]
        
        try:
            prompt = ChatPromptTemplate.from_template("""
            Analise o seguinte texto sobre treinamento físico e extraia os principais conceitos e termos técnicos.
            
            Texto: {text}
            
            Liste apenas os conceitos mais importantes, separados por vírgula. Máximo 8 conceitos.
            Foque em termos técnicos, métodos, princípios e conceitos científicos.
            
            Conceitos:
            """)
            
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"text": text[:2000]})  # Limit text length
            
            concepts = [concept.strip() for concept in result.split(',') if concept.strip()]
            concepts = concepts[:8]  # Limit to 8 concepts
            
            self.concept_cache[text_hash] = concepts
            return concepts
            
        except Exception as e:
            logger.warning(f"Failed to extract concepts: {e}")
            return []
    
    def _assess_difficulty_level(self, text: str) -> str:
        """Assess difficulty level of content"""
        if not self.config.assess_difficulty_level or not self.llm:
            return "intermediate"
        
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.difficulty_cache:
            return self.difficulty_cache[text_hash]
        
        try:
            prompt = ChatPromptTemplate.from_template("""
            Analise o nível de dificuldade do seguinte texto sobre treinamento físico.
            
            Texto: {text}
            
            Classifique o nível como:
            - beginner: Conceitos básicos, linguagem simples
            - intermediate: Termos técnicos moderados, conceitos aplicados
            - advanced: Conceitos complexos, linguagem técnica avançada
            
            Responda apenas com: beginner, intermediate ou advanced
            
            Nível:
            """)
            
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"text": text[:1500]})
            
            level = result.strip().lower()
            if level not in ['beginner', 'intermediate', 'advanced']:
                level = 'intermediate'
            
            self.difficulty_cache[text_hash] = level
            return level
            
        except Exception as e:
            logger.warning(f"Failed to assess difficulty: {e}")
            return "intermediate"
    
    def _create_content_summary(self, text: str) -> str:
        """Create educational summary of content"""
        if not self.config.create_summaries or not self.llm:
            return ""
        
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.summary_cache:
            return self.summary_cache[text_hash]
        
        try:
            prompt = ChatPromptTemplate.from_template("""
            Crie um resumo educacional conciso do seguinte texto sobre treinamento físico.
            
            Texto: {text}
            
            O resumo deve:
            - Ter no máximo 3 frases
            - Destacar os pontos principais
            - Usar linguagem clara
            - Focar nos aspectos práticos
            
            Resumo:
            """)
            
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"text": text[:2000]})
            
            summary = result.strip()
            self.summary_cache[text_hash] = summary
            return summary
            
        except Exception as e:
            logger.warning(f"Failed to create summary: {e}")
            return ""
    
    def process_documents(self, force_reprocess: bool = False) -> bool:
        """Process all documents with educational enhancements"""
        logger.info("📚 Starting enhanced document processing...")
        
        if not self.materials_dir.exists():
            logger.error(f"❌ Materials directory not found: {self.materials_dir}")
            return False
        
        # Check if reprocessing is needed
        if not force_reprocess and self.vector_store._collection.count() > 0:
            logger.info("📋 Documents already processed. Use force_reprocess=True to reprocess.")
            return True
        
        # Clear existing documents if reprocessing
        if force_reprocess and self.vector_store._collection.count() > 0:
            logger.info("🗑️ Clearing existing documents for reprocessing...")
            self.vector_store.delete_collection()
            self.vector_store = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings
            )
        
        # Load and process documents
        documents = []
        processed_files = 0
        
        # Process different file types
        file_patterns = {
            "**/*.pdf": PyPDFLoader,
            "**/*.txt": TextLoader,
            "**/*.xlsx": UnstructuredExcelLoader,
            "**/*.xls": UnstructuredExcelLoader
        }
        
        for pattern, loader_class in file_patterns.items():
            try:
                loader = DirectoryLoader(
                    str(self.materials_dir),
                    glob=pattern,
                    loader_cls=loader_class,
                    show_progress=True,
                    use_multithreading=True
                )
                
                pattern_docs = loader.load()
                logger.info(f"📄 Loaded {len(pattern_docs)} documents with pattern {pattern}")
                
                # Enhance documents with educational metadata
                for doc in pattern_docs:
                    enhanced_doc = self._enhance_document_with_educational_metadata(doc)
                    documents.append(enhanced_doc)
                
                processed_files += len(pattern_docs)
                
            except Exception as e:
                logger.warning(f"⚠️ Error loading {pattern}: {e}")
                continue
        
        if not documents:
            logger.warning("⚠️ No documents found to process")
            return False
        
        logger.info(f"📊 Enhancing {len(documents)} documents with educational metadata...")
        
        # Split documents with educational considerations
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],  # Preserve educational structure
            keep_separator=True
        )
        
        splits = text_splitter.split_documents(documents)
        logger.info(f"🔪 Split into {len(splits)} chunks")
        
        # Add to vector store
        try:
            self.vector_store.add_documents(splits)
            logger.info(f"✅ Added {len(splits)} document chunks to vector store")
            
            # Update retriever
            self._setup_educational_retriever()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents to vector store: {e}")
            return False
    
    def _enhance_document_with_educational_metadata(self, doc: Document) -> Document:
        """Enhance document with educational metadata"""
        try:
            # Extract basic information
            source_path = doc.metadata.get('source', '')
            content_type = self._analyze_content_type(source_path)
            
            # Enhance metadata
            enhanced_metadata = {
                **doc.metadata,
                'content_type': content_type,
                'processed_at': datetime.now().isoformat(),
                'enhancement_version': '1.0'
            }
            
            # Add educational analysis if enabled
            if len(doc.page_content) > 100:  # Only analyze substantial content
                if self.config.extract_key_concepts:
                    enhanced_metadata['key_concepts'] = self._extract_key_concepts(doc.page_content)
                
                if self.config.assess_difficulty_level:
                    enhanced_metadata['difficulty_level'] = self._assess_difficulty_level(doc.page_content)
                
                if self.config.create_summaries:
                    enhanced_metadata['summary'] = self._create_content_summary(doc.page_content)
            
            return Document(
                page_content=doc.page_content,
                metadata=enhanced_metadata
            )
            
        except Exception as e:
            logger.warning(f"Failed to enhance document: {e}")
            return doc
    
    def retrieve_educational_sources(self, query: str, user_level: str = "intermediate") -> List[EducationalSource]:
        """Retrieve sources optimized for educational purposes"""
        if not self.retriever:
            logger.warning("Retriever not available")
            return []
        
        try:
            # Get relevant documents
            docs = self.retriever.get_relevant_documents(query)
            
            educational_sources = []
            for doc in docs:
                source = EducationalSource(
                    title=doc.metadata.get('title', os.path.basename(doc.metadata.get('source', 'Unknown'))),
                    source=doc.metadata.get('source', ''),
                    page=doc.metadata.get('page'),
                    chunk=doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    content_type=doc.metadata.get('content_type', 'text'),
                    difficulty_level=doc.metadata.get('difficulty_level', 'intermediate'),
                    key_concepts=doc.metadata.get('key_concepts', []),
                    summary=doc.metadata.get('summary', ''),
                    relevance_score=getattr(doc, 'relevance_score', 0.8)
                )
                
                # Calculate educational value based on user level and content
                source.educational_value = self._calculate_educational_value(source, user_level)
                
                educational_sources.append(source)
            
            # Sort by educational value and relevance
            educational_sources.sort(
                key=lambda x: (x.educational_value, x.relevance_score),
                reverse=True
            )
            
            return educational_sources[:self.config.retrieval_k]
            
        except Exception as e:
            logger.error(f"Error retrieving educational sources: {e}")
            return []
    
    def _calculate_educational_value(self, source: EducationalSource, user_level: str) -> float:
        """Calculate educational value score for a source based on user level"""
        score = 0.5  # Base score
        
        # Level matching
        if source.difficulty_level == user_level:
            score += 0.3
        elif (user_level == "beginner" and source.difficulty_level == "intermediate") or \
             (user_level == "intermediate" and source.difficulty_level == "advanced"):
            score += 0.1  # Slightly challenging is good
        elif (user_level == "advanced" and source.difficulty_level == "beginner"):
            score -= 0.2  # Too basic for advanced users
        
        # Content type bonuses
        if source.content_type == 'research_paper':
            score += 0.2
        elif source.content_type == 'video':
            score += 0.1
        
        # Key concepts bonus
        if len(source.key_concepts) > 3:
            score += 0.1
        
        # Summary bonus
        if source.summary:
            score += 0.1
        
        return min(1.0, score)
    
    def get_educational_metadata(self) -> EducationalMetadata:
        """Get metadata about the educational content in the database"""
        if not self.vector_store:
            return EducationalMetadata()
        
        try:
            # This is a simplified version - in production, you'd query the actual metadata
            total_docs = self.vector_store._collection.count()
            
            return EducationalMetadata(
                total_sources=total_docs,
                difficulty_distribution={"beginner": 20, "intermediate": 60, "advanced": 20},
                content_type_distribution={"document": 70, "video": 20, "data": 10},
                coverage_quality=0.85
            )
            
        except Exception as e:
            logger.error(f"Error getting educational metadata: {e}")
            return EducationalMetadata()
    
    def suggest_learning_path(self, topic: str, user_level: str) -> List[str]:
        """Suggest a learning path for a specific topic"""
        suggestions = []
        
        # Get relevant sources
        sources = self.retrieve_educational_sources(f"learning path {topic}", user_level)
        
        if sources:
            # Basic learning path structure
            if user_level == "beginner":
                suggestions = [
                    f"Conceitos básicos de {topic}",
                    f"Aplicações práticas de {topic}",
                    f"Exercícios introdutórios de {topic}",
                    f"Progressão em {topic}"
                ]
            elif user_level == "intermediate":
                suggestions = [
                    f"Princípios avançados de {topic}",
                    f"Variações e adaptações de {topic}",
                    f"Integração de {topic} com outros métodos",
                    f"Troubleshooting em {topic}"
                ]
            else:  # advanced
                suggestions = [
                    f"Pesquisa atual em {topic}",
                    f"Aplicações especializadas de {topic}",
                    f"Otimização avançada de {topic}",
                    f"Inovações em {topic}"
                ]
        
        return suggestions[:4]  # Limit to 4 suggestions

# Export for use in other modules
__all__ = ['EnhancedRAGHandler', 'EducationalSource', 'EducationalMetadata', 'EducationalProcessingConfig']