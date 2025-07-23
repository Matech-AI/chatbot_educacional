import os
import json
import logging
import time
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from pydantic import SecretStr, BaseModel
from fastapi import APIRouter, Depends, HTTPException
from pathlib import Path
from langchain_core.runnables import RunnableConfig

from langchain_core.tools import BaseTool
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage, AIMessage
from langchain_core.tools.retriever import create_retriever_tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from rag_handler import RAGHandler
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from auth import User, get_current_user
from video_handler import get_video_handler

# Set environment variables
load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["educational_chat"])

class LearningContext(BaseModel):
    """Track learning context and progress for each user"""
    user_id: str
    session_id: str
    current_topic: Optional[str] = None
    learning_objectives: List[str] = []
    topics_covered: List[str] = []
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    preferred_learning_style: str = "mixed"  # visual, auditory, kinesthetic, mixed
    knowledge_gaps: List[str] = []
    follow_up_questions: List[str] = []

class EducationalResponse(BaseModel):
    """Structure for educational responses"""
    main_answer: str
    sources: List[Dict[str, str]] = []
    follow_up_questions: List[str] = []
    learning_suggestions: List[str] = []
    related_topics: List[str] = []
    difficulty_assessment: str = "intermediate"
    confidence_score: float = 0.8

# Enhanced State for educational conversations
class EducationalState(TypedDict):
    messages: Annotated[list, add_messages]
    learning_context: LearningContext
    sources_retrieved: List[Document]
    educational_metadata: Dict[str, Any]

class EducationalChatRequest(BaseModel):
    content: str
    user_level: str = "intermediate"  # beginner, intermediate, advanced
    learning_style: str = "mixed"  # visual, auditory, kinesthetic, mixed
    session_id: Optional[str] = None
    current_topic: Optional[str] = None
    learning_objectives: List[str] = []

class EducationalChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []
    follow_up_questions: List[str] = []
    learning_suggestions: List[str] = []
    related_topics: List[str] = []
    educational_metadata: Dict[str, Any] = {}
    learning_context: Dict[str, Any] = {}
    video_suggestions: List[Dict[str, Any]] = []
    response_time: float = 0.0

class EducationalAgent:
    """Enhanced educational agent for fitness training with deep learning capabilities"""
    
    def __init__(self):
        self.rag_handler = None
        self.retriever_tool = None
        self.model = None
        self.graph = None
        self.memory = MemorySaver()
        self.learning_contexts: Dict[str, LearningContext] = {}
        
        self._initialize_rag()
        self._initialize_model()
        self._build_graph()
    
    def _initialize_rag(self):
        """Initialize RAG handler with enhanced retrieval"""
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not found. RAG capabilities disabled.")
            return
        
        try:
            self.rag_handler = RAGHandler(api_key=openai_api_key)
            if self.rag_handler.vector_store:
                # Enhanced retriever with more results for educational context
                retriever = self.rag_handler.vector_store.as_retriever(
                    search_type="mmr",  # Maximum Marginal Relevance for diversity
                    search_kwargs={
                        "k": 8,  # More sources for comprehensive answers
                        "fetch_k": 20,  # Broader initial search
                        "lambda_mult": 0.7  # Balance between relevance and diversity
                    }
                )
                
                self.retriever_tool = create_retriever_tool(
                    retriever,
                    "search_training_materials",
                    "Search training materials for comprehensive information about fitness, exercise science, and strength training. Returns detailed content with multiple perspectives."
                )
                logger.info("✅ Enhanced RAG system initialized successfully")
            else:
                logger.warning("Vector store not available")
        except Exception as e:
            logger.error(f"Error initializing RAG: {e}")
    
    def _initialize_model(self):
        """Initialize the AI model with educational focus"""
        # Try Gemini first, fallback to OpenAI
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if gemini_api_key:
            try:
                self.model = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    temperature=0.3,  # Lower temperature for more consistent educational responses
                    api_key=SecretStr(gemini_api_key),
                )
                logger.info("✅ Gemini model initialized")
            except Exception as e:
                logger.warning(f"Gemini initialization failed: {e}")
                self.model = None
        
        if not self.model and openai_api_key:
            try:
                self.model = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.3,
                    api_key=SecretStr(openai_api_key),
                )
                logger.info("✅ OpenAI model initialized")
            except Exception as e:
                logger.error(f"OpenAI initialization failed: {e}")
        
        if not self.model:
            raise ValueError("No valid AI model could be initialized")
    
    def _get_educational_system_prompt(self, learning_context: LearningContext) -> str:
        """Generate contextual system prompt based on learning context"""
        
        base_prompt = """Você é um Professor de Educação Física e Treinamento Esportivo especializado em força e condicionamento físico. 

        SEUS OBJETIVOS EDUCACIONAIS:
        1. Ensinar conceitos de forma clara e progressiva
        2. Adaptar explicações ao nível do aluno
        3. Fornecer exemplos práticos e aplicáveis
        4. Incentivar o pensamento crítico
        5. Sugerir caminhos de aprofundamento

        METODOLOGIA DE ENSINO:
        - Use analogias e exemplos do dia a dia
        - Divida conceitos complexos em partes menores
        - Relacione teoria com prática
        - Cite fontes científicas quando relevante
        - Estimule perguntas e curiosidade

        ESTRUTURA DAS RESPOSTAS:
        1. **Resposta Principal**: Explicação clara e didática
        2. **Fontes e Evidências**: Referências dos materiais consultados
        3. **Aplicação Prática**: Como aplicar o conhecimento
        4. **Perguntas para Reflexão**: Questões para aprofundar o entendimento
        5. **Próximos Passos**: Sugestões de tópicos relacionados

        ADAPTAÇÃO AO ALUNO:
        """
        
        # Customize based on learning context
        if learning_context.difficulty_level == "beginner":
            base_prompt += "\n- Use linguagem simples e defina termos técnicos\n- Comece com conceitos fundamentais\n- Use muitos exemplos práticos"
        elif learning_context.difficulty_level == "intermediate":
            base_prompt += "\n- Pode usar termos técnicos com explicações breves\n- Faça conexões entre conceitos\n- Inclua nuances e considerações especiais"
        else:  # advanced
            base_prompt += "\n- Use linguagem técnica apropriada\n- Discuta controvérsias e debates atuais\n- Explore implicações avançadas"
        
        if learning_context.current_topic:
            base_prompt += f"\n\nTÓPICO ATUAL DE FOCO: {learning_context.current_topic}"
        
        if learning_context.learning_objectives:
            base_prompt += f"\n\nOBJETIVOS DE APRENDIZAGEM: {', '.join(learning_context.learning_objectives)}"
        
        if learning_context.knowledge_gaps:
            base_prompt += f"\n\nLACUNAS IDENTIFICADAS: {', '.join(learning_context.knowledge_gaps)}"
        
        base_prompt += """

        IMPORTANTE: 
        - Sempre baseie suas respostas no conteúdo dos materiais de estudo quando disponível
        - Se não houver informação suficiente nos materiais, indique claramente
        - Gere perguntas de acompanhamento que ajudem o aluno a explorar mais profundamente
        - Mantenha o foco educacional e pedagógico em todas as interações
        """
        
        return base_prompt
    
    def _build_graph(self):
        """Build the educational conversation graph"""
        
        # Define tools
        tools = []
        if self.retriever_tool:
            tools.append(self.retriever_tool)
        
        tool_node = ToolNode(tools)
        if not self.model:
            raise ValueError("Model not initialized")
        model_with_tools = self.model.bind_tools(tools)
        
        def educational_agent(state: EducationalState):
            """Enhanced agent with educational focus"""
            learning_context = state.get("learning_context")
            if not learning_context:
                # Create default context
                learning_context = LearningContext(
                    user_id="default",
                    session_id="default"
                )
            
            # Generate contextual system prompt
            system_prompt = SystemMessage(
                content=self._get_educational_system_prompt(learning_context)
            )
            
            messages = [system_prompt] + state["messages"]
            response = model_with_tools.invoke(messages)
            
            # Analyze response for educational metadata
            content = response.content if isinstance(response.content, str) else ""
            educational_metadata = self._analyze_educational_content(
                content,
                learning_context
            )
            
            return {
                "messages": [response],
                "educational_metadata": educational_metadata
            }
        
        def process_retrieval(state: EducationalState):
            """Process retrieved sources for educational enhancement"""
            sources = state.get("sources_retrieved", [])
            learning_context = state.get("learning_context")
            
            if sources and learning_context:
                # Analyze sources for learning opportunities
                learning_opportunities = self._identify_learning_opportunities(sources, learning_context)
                
                return {
                    "educational_metadata": {
                        **state.get("educational_metadata", {}),
                        "learning_opportunities": learning_opportunities
                    }
                }
            
            return {}
        
        # Build graph
        builder = StateGraph(EducationalState)
        builder.add_node("agent", educational_agent)
        builder.add_node("tools", tool_node)
        builder.add_node("process_retrieval", process_retrieval)
        
        builder.add_edge(START, "agent")
        builder.add_conditional_edges("agent", tools_condition)
        builder.add_edge("tools", "process_retrieval")
        builder.add_edge("process_retrieval", "agent")
        
        self.graph = builder.compile(checkpointer=self.memory)
        logger.info("✅ Educational graph compiled successfully")
    
    def _analyze_educational_content(self, content: str, learning_context: LearningContext) -> Dict[str, Any]:
        """Analyze response content for educational value"""
        
        # Simple analysis - in production, could use more sophisticated NLP
        metadata = {
            "estimated_reading_time": len(content.split()) / 200,  # minutes
            "complexity_score": self._assess_complexity(content),
            "topics_mentioned": self._extract_topics(content),
            "learning_opportunities": []
        }
        
        return metadata
    
    def _assess_complexity(self, text: str) -> float:
        """Simple complexity assessment based on text features"""
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        long_words = sum(1 for word in words if len(word) > 6)
        long_word_ratio = long_words / len(words) if words else 0
        
        # Simple complexity score (0-1)
        complexity = min(1.0, (avg_word_length / 10) * 0.5 + long_word_ratio * 0.5)
        return complexity
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text"""
        # Keywords related to fitness training
        fitness_keywords = [
            "treino", "exercício", "musculação", "força", "resistência", "cardio",
            "hipertrofia", "definição", "periodização", "volume", "intensidade",
            "técnica", "biomecânica", "anatomia", "fisiologia", "nutrição",
            "recuperação", "sono", "suplementação", "lesão", "prevenção"
        ]
        
        text_lower = text.lower()
        found_topics = [keyword for keyword in fitness_keywords if keyword in text_lower]
        return found_topics
    
    def _identify_learning_opportunities(self, sources: List[Document], learning_context: LearningContext) -> List[str]:
        """Identify learning opportunities from retrieved sources"""
        opportunities = []
        
        # Analyze source diversity
        source_types = set()
        for source in sources:
            if hasattr(source, 'metadata') and 'source' in source.metadata:
                source_path = source.metadata['source']
                if '.pdf' in source_path:
                    source_types.add('research_paper')
                elif '.mp4' in source_path:
                    source_types.add('video')
                elif '.xlsx' in source_path or '.xls' in source_path:
                    source_types.add('data')
        
        if len(source_types) > 1:
            opportunities.append("Multiple content types available for different learning styles")
        
        if 'video' in source_types:
            opportunities.append("Visual learners: Video content available")
        
        if 'research_paper' in source_types:
            opportunities.append("Deep dive: Scientific papers available for advanced study")
        
        return opportunities
    
    def get_learning_context(self, user_id: str, session_id: str) -> LearningContext:
        """Get or create learning context for user/session"""
        context_key = f"{user_id}_{session_id}"
        
        if context_key not in self.learning_contexts:
            self.learning_contexts[context_key] = LearningContext(
                user_id=user_id,
                session_id=session_id
            )
        
        return self.learning_contexts[context_key]
    
    def update_learning_context(self, user_id: str, session_id: str, **updates):
        """Update learning context with new information"""
        context = self.get_learning_context(user_id, session_id)
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
    
    def generate_follow_up_questions(self, topic: str, difficulty_level: str) -> List[str]:
        """Generate contextual follow-up questions"""
        base_questions = {
            "beginner": [
                f"Como posso aplicar {topic} no meu dia a dia?",
                f"Quais são os benefícios principais de {topic}?",
                f"Existe alguma contraindicação para {topic}?",
                f"Como começar com {topic} de forma segura?"
            ],
            "intermediate": [
                f"Quais são as variações mais eficazes de {topic}?",
                f"Como {topic} se relaciona com outros aspectos do treinamento?",
                f"Qual a evidência científica por trás de {topic}?",
                f"Como adaptar {topic} para diferentes objetivos?"
            ],
            "advanced": [
                f"Quais são as controvérsias atuais sobre {topic}?",
                f"Como otimizar {topic} para atletas de elite?",
                f"Quais pesquisas recentes mudaram nossa compreensão de {topic}?",
                f"Como {topic} difere entre populações especiais?"
            ]
        }
        
        return base_questions.get(difficulty_level, base_questions["intermediate"])
    
    async def chat(self, 
                   message: str, 
                   user_id: str = "default", 
                   session_id: str = "default",
                   learning_preferences: Optional[Dict] = None) -> Dict[str, Any]:
        """Main chat interface with educational enhancements"""
        
        # Get or update learning context
        learning_context = self.get_learning_context(user_id, session_id)
        
        if learning_preferences:
            self.update_learning_context(user_id, session_id, **learning_preferences)
        
        # Prepare initial state
        config = RunnableConfig(configurable={"thread_id": f"{user_id}_{session_id}"})
        
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "learning_context": learning_context,
            "sources_retrieved": [],
            "educational_metadata": {}
        }
        
        # Run conversation graph
        try:
            if not self.graph:
                raise ValueError("Graph not initialized")
            result = self.graph.invoke(initial_state, config)
            
            # Extract response and metadata
            assistant_message = result["messages"][-1]
            educational_metadata = result.get("educational_metadata", {})
            
            # Generate educational enhancements
            follow_up_questions = self.generate_follow_up_questions(
                learning_context.current_topic or "treinamento",
                learning_context.difficulty_level
            )
            
            # Extract sources from retrieved documents
            sources = []
            if "sources_retrieved" in result:
                for doc in result["sources_retrieved"]:
                    if hasattr(doc, 'metadata'):
                        sources.append({
                            "title": doc.metadata.get("title", "Material de Estudo"),
                            "source": doc.metadata.get("source", ""),
                            "chunk": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                            "page": doc.metadata.get("page")
                        })
            
            # Update learning context based on response
            topics_mentioned = educational_metadata.get("topics_mentioned", [])
            if topics_mentioned:
                learning_context.topics_covered.extend(topics_mentioned)
                learning_context.current_topic = topics_mentioned[0]  # Most relevant topic
            
            return {
                "response": assistant_message.content,
                "sources": sources,
                "follow_up_questions": follow_up_questions[:3],  # Limit to 3 questions
                "learning_suggestions": educational_metadata.get("learning_opportunities", []),
                "related_topics": topics_mentioned,
                "educational_metadata": educational_metadata,
                "learning_context": learning_context.dict()
            }
            
        except Exception as e:
            logger.error(f"Error in educational chat: {e}")
            return {
                "response": "Desculpe, ocorreu um erro durante nossa conversa educacional. Pode tentar novamente?",
                "sources": [],
                "follow_up_questions": [],
                "learning_suggestions": [],
                "related_topics": [],
                "educational_metadata": {},
                "learning_context": learning_context.dict()
            }

# Global instance
educational_agent = None

def get_educational_agent() -> EducationalAgent:
    """Get or create the global educational agent instance"""
    global educational_agent
    if educational_agent is None:
        educational_agent = EducationalAgent()
    return educational_agent

@router.post("/educational", response_model=EducationalChatResponse)
async def educational_chat(
    request: EducationalChatRequest
):
    """Enhanced educational chat with learning features"""
    current_user = User(id="default", username="default", role="student", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    start_time = time.time()
    
    logger.info(f"🎓 Educational chat from {current_user.username}: {request.content[:50]}...")
    
    try:
        # Get educational agent
        agent = get_educational_agent()
        video_handler = get_video_handler()
        
        # Prepare learning preferences
        learning_preferences = {
            "difficulty_level": request.user_level,
            "learning_style": request.learning_style,
            "current_topic": request.current_topic,
            "learning_objectives": request.learning_objectives
        }
        
        # Process with educational agent
        result = await agent.chat(
            message=request.content,
            user_id=current_user.username,
            session_id=request.session_id or f"session_{int(time.time())}",
            learning_preferences=learning_preferences
        )
        
        # Add RAG sources to the result
        if agent.rag_handler and agent.rag_handler.vector_store:
            retriever = agent.rag_handler.vector_store.as_retriever()
            docs = retriever.invoke(request.content)
            sources = []
            for doc in docs:
                sources.append({
                    "title": doc.metadata.get("title", "Material de Estudo"),
                    "source": doc.metadata.get("source", ""),
                    "chunk": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "page": doc.metadata.get("page")
                })
            result["sources"] = sources
        
        # Search for relevant videos based on the topic
        video_suggestions = []
        try:
            # Extract main topic from related topics or content
            search_topic = request.current_topic or (result["related_topics"][0] if result["related_topics"] else "")
            
            if search_topic:
                # Get all video files from materials directory
                materials_dir = Path("data/materials")
                video_files = []
                
                if materials_dir.exists():
                    for file_path in materials_dir.rglob("*"):
                        if file_path.is_file() and any(ext in file_path.suffix.lower() for ext in ['.mp4', '.avi', '.mov', '.webm']):
                            video_files.append(str(file_path))
                
                # Find videos related to each topic
                for topic in result["related_topics"][:3]:  # Check top 3 related topics
                    video_result = video_handler.find_video_for_topic(topic, video_files)
                    if video_result:
                        video_path, timestamp = video_result
                        
                        # Get video metadata
                        metadata = video_handler.get_video_metadata(video_path)
                        
                        video_suggestions.append({
                            "topic": topic,
                            "video_path": str(Path(video_path).relative_to(materials_dir)) if materials_dir.exists() else video_path,
                            "video_title": metadata.title,
                            "start_timestamp": timestamp,
                            "duration": metadata.duration,
                            "difficulty_level": metadata.difficulty_level,
                            "description": f"Vídeo relacionado ao tópico '{topic}'"
                        })
                        
        except Exception as e:
            logger.warning(f"⚠️ Error searching for video suggestions: {e}")
        
        response_time = time.time() - start_time
        
        logger.info(f"✅ Educational response generated in {response_time:.2f}s with {len(video_suggestions)} video suggestions")
        
        # Add video suggestions to the response
        response_data = {
            "response": result["response"],
            "sources": result["sources"],
            "follow_up_questions": result["follow_up_questions"],
            "learning_suggestions": result["learning_suggestions"],
            "related_topics": result["related_topics"],
            "educational_metadata": result["educational_metadata"],
            "learning_context": result["learning_context"],
            "response_time": response_time
        }
        
        # Add video suggestions if any found
        if video_suggestions:
            response_data["video_suggestions"] = video_suggestions
            if "video_content" not in response_data["learning_suggestions"]:
                response_data["learning_suggestions"].append(f"📹 {len(video_suggestions)} vídeo(s) relacionado(s) disponível(eis) para este tópico")
        
        return EducationalChatResponse(**response_data)
        
    except Exception as e:
        logger.error(f"❌ Educational chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Educational chat error: {str(e)}")

@router.get("/session/{session_id}/context")
async def get_session_context(
    session_id: str
):
    """Get learning context for a chat session"""
    current_user = User(id="default", username="default", role="student", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    try:
        agent = get_educational_agent()
        context = agent.get_learning_context(current_user.username, session_id)
        
        return {
            "session_id": session_id,
            "learning_context": context.dict(),
            "summary": {
                "topics_covered": len(context.topics_covered),
                "current_focus": context.current_topic,
                "difficulty_level": context.difficulty_level,
                "objectives_count": len(context.learning_objectives)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Session context error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session context error: {str(e)}")

@router.get("/learning-path/{topic}")
async def get_learning_path(
    topic: str,
    user_level: str = "intermediate"
):
    """Get suggested learning path for a topic"""
    logger.info(f"🛤️ Learning path request: {topic}")
    
    try:
        agent = get_educational_agent()
        
        # This would use enhanced RAG if available
        learning_path = [
            {"step": 1, "title": f"Fundamentos de {topic}", "description": "Conceitos básicos e terminologia"},
            {"step": 2, "title": f"Aplicação prática de {topic}", "description": "Como aplicar na prática"},
            {"step": 3, "title": f"Progressão em {topic}", "description": "Níveis avançados e variações"},
            {"step": 4, "title": f"Troubleshooting {topic}", "description": "Solucionando problemas comuns"}
        ]
        
        return {
            "topic": topic,
            "user_level": user_level,
            "learning_path": learning_path,
            "estimated_time": "2-4 semanas",
            "prerequisites": [],
            "resources_available": True
        }
        
    except Exception as e:
        logger.error(f"❌ Learning path error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Learning path error: {str(e)}")

# Example usage
if __name__ == "__main__":
    agent = EducationalAgent()
    
    async def test_chat():
        result = await agent.chat(
            "O que é hipertrofia muscular e como alcançá-la?",
            user_id="test_user",
            session_id="test_session",
            learning_preferences={
                "difficulty_level": "intermediate",
                "current_topic": "hipertrofia",
                "learning_objectives": ["entender hipertrofia", "aplicar técnicas"]
            }
        )
        
        print("Response:", result["response"])
        print("Follow-up Questions:", result["follow_up_questions"])
        print("Sources:", len(result["sources"]))
        print("Learning Suggestions:", result["learning_suggestions"])
    
    import asyncio
    asyncio.run(test_chat())