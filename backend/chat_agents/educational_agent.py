import os
import json
import logging
import time
from typing import Annotated, TypedDict, List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from pydantic import SecretStr, BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
from langchain_core.runnables import RunnableConfig

from langchain_core.tools import BaseTool
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage, AIMessage
from langchain_core.tools.retriever import create_retriever_tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langgraph.graph.message import add_messages
from auth.auth import User, get_current_user
from video_processing.video_handler import get_video_handler

# Set environment variables
load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Configure logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["educational_chat"])


class Question(BaseModel):
    content: str


class Response(BaseModel):
    answer: str
    sources: List[dict]
    response_time: float


class LearningPathStep(BaseModel):
    """Represents a single step in a learning path."""
    step: int
    title: str
    description: str
    estimated_time: str
    difficulty: str
    completed: bool = False


class LearningPath(BaseModel):
    """A structured learning path with a list of steps."""
    learning_path: List[LearningPathStep] = Field(
        description="The list of steps in the learning path.")


class LearningContext(BaseModel):
    """Track learning context and progress for each user"""
    user_id: str
    session_id: str
    learning_objectives: List[str] = []
    topics_covered: List[str] = []
    knowledge_gaps: List[str] = []
    follow_up_questions: List[str] = []
    learning_path: List[LearningPathStep] = []


class AddTopicRequest(BaseModel):
    session_id: str
    topic_title: str
    topic_description: str


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


class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    sources: List[Dict[str, Any]]


class EducationalChatRequest(BaseModel):
    content: str
    session_id: Optional[str] = None
    learning_objectives: List[str] = []


class EducationalChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []
    follow_up_questions: List[str] = []
    learning_suggestions: List[str] = []
    related_topics: List[str] = []
    educational_metadata: Dict[str, Any] = {}
    learning_context: Dict[str, Any] = {}
    response_time: float = 0.0


class EducationalAgent:
    """Enhanced educational agent for fitness training with deep learning capabilities"""

    def __init__(self):
        self.model = None
        self.graph = None
        self.retriever = None
        self.vector_store = None
        self.memory = MemorySaver()
        self.learning_contexts: Dict[str, LearningContext] = {}
        self.last_retrieved_sources: List[Dict[str, Any]] = []
        self.course_catalog: Optional[pd.DataFrame] = None

        self._load_course_catalog()
        self._initialize_rag()
        self._initialize_model()
        self._build_graph()

    def _initialize_rag(self):
        """Initialize ChromaDB and retriever directly."""
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not found. RAG capabilities disabled.")
            return

        try:
            embeddings = OpenAIEmbeddings(
                model="text-embedding-ada-002",
                api_key=SecretStr(openai_api_key)
            )
            
            persist_directory = str(Path(__file__).parent.parent / "data" / "chromadb")
            
            self.vector_store = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings
            )
            
            self.retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 6, "fetch_k": 20, "lambda_mult": 0.7},
            )
            logger.info("✅ Retriever initialized successfully directly from ChromaDB")
        except Exception as e:
            logger.error(f"Error initializing retriever: {e}")

    def _load_course_catalog(self, path: str = "data/catalog.xlsx"):
        """Loads the course catalog from an Excel file."""
        try:
            if os.path.exists(path):
                self.course_catalog = pd.read_excel(path)
                # Normalize column names for easier access
                self.course_catalog.columns = [col.strip().lower() for col in self.course_catalog.columns]
                logger.info("✅ Course catalog loaded successfully.")
            else:
                logger.warning(f"Course catalog not found at {path}. Video suggestions will be disabled.")
        except Exception as e:
            logger.error(f"Error loading course catalog: {e}")

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

        if learning_context.learning_objectives:
            base_prompt += f"\n\nOBJETIVOS DE APRENDIZAGEM: {', '.join(learning_context.learning_objectives)}"

        if learning_context.knowledge_gaps:
            base_prompt += f"\n\nLACUNAS IDENTIFICADAS: {', '.join(learning_context.knowledge_gaps)}"

        base_prompt += """

        IMPORTANTE: 
        - Sempre baseie suas respostas no conteúdo dos materiais de estudo quando disponível utilizando a tool
          name: str = "search_educational_materials"
        - Se não houver informação suficiente nos materiais, indique claramente
        - Gere perguntas de acompanhamento que ajudem o aluno a explorar mais profundamente
        - Mantenha o foco educacional e pedagógico em todas as interações
        """

        return base_prompt

    def _build_graph(self):
        """Build the educational conversation graph."""
        if not self.model or not self.retriever:
            logger.error("Model or retriever not initialized. Cannot build graph.")
            return

        retriever_tool = self._create_custom_retriever_tool()
        tools = [retriever_tool]
        
        tool_node = ToolNode(tools)
        
        model_with_tools = self.model.bind_tools(tools)

        def agent_node(state: AgentState):
            response = model_with_tools.invoke(state["messages"])
            return {"messages": [response]}

        def should_continue(state: AgentState):
            last_message = state["messages"][-1]
            if not last_message.tool_calls:
                return END
            else:
                return "tools"

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tool_node)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", should_continue)
        workflow.add_edge("tools", "agent")

        self.graph = workflow.compile(checkpointer=self.memory)
        logger.info("✅ Educational graph compiled successfully")


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

        learning_context = self.get_learning_context(user_id, session_id)
        if learning_preferences:
            self.update_learning_context(user_id, session_id, **learning_preferences)

        config = RunnableConfig(configurable={"thread_id": f"{user_id}_{session_id}"})
        
        try:
            if not self.graph:
                raise ValueError("Graph not initialized")

            initial_state = {"messages": [HumanMessage(content=message)]}
            
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            response_content = final_state["messages"][-1].content
            sources = self.last_retrieved_sources

            follow_up_questions = self.generate_follow_up_questions(
                "treinamento", "intermediate"
            )

            return {
                "response": response_content,
                "sources": sources,
                "follow_up_questions": follow_up_questions[:3],
                "learning_suggestions": [],
                "related_topics": [],
                "educational_metadata": {},
                "learning_context": learning_context.model_dump(),
            }

        except Exception as e:
            logger.error(f"Error in educational chat: {e}", exc_info=True)
            return {
                "response": "Desculpe, ocorreu um erro durante nossa conversa educacional.",
                "sources": [],
                "follow_up_questions": [],
                "learning_suggestions": [],
                "related_topics": [],
                "educational_metadata": {},
                "learning_context": learning_context.model_dump()
            }




    def _create_custom_retriever_tool(self) -> BaseTool:
        """Creates a custom retriever tool that captures the sources."""
        
        class CustomRetrieverTool(BaseTool):
            """A custom retriever tool that captures the sources."""
            name: str = "search_educational_materials"
            description: str = "Searches and retrieves information from educational materials to answer questions about fitness, exercise science, and strength training."
            agent: "EducationalAgent"

            def _run(self, query: str) -> str:
                """Execute the retrieval and capture the sources."""
                if not self.agent.retriever:
                    return "Retriever not initialized."
                
                documents = self.agent.retriever.invoke(query)
                self.agent.last_retrieved_sources = [doc.metadata for doc in documents]
                
                return "\n\n".join([doc.page_content for doc in documents])

            async def _arun(self, query: str) -> str:
                """Asynchronously execute the retrieval and capture the sources."""
                if not self.agent.retriever:
                    return "Retriever not initialized."

                documents = await self.agent.retriever.ainvoke(query)
                self.agent.last_retrieved_sources = [doc.metadata for doc in documents]

                return "\n\n".join([doc.page_content for doc in documents])

        return CustomRetrieverTool(agent=self)


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
    current_user = User(id="default", username="default", role="student",
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    start_time = time.time()

    logger.info(
        f"🎓 Educational chat from {current_user.username}: {request.content[:50]}...")

    try:
        # Get educational agent
        agent = get_educational_agent()

        # Prepare learning preferences
        learning_preferences = {
            "learning_objectives": request.learning_objectives
        }

        # Process with educational agent
        result = await agent.chat(
            message=request.content,
            user_id=current_user.username,
            session_id=request.session_id or f"session_{int(time.time())}",
            learning_preferences=learning_preferences
        )


        response_time = time.time() - start_time
        
        logger.info(
            f"✅ Educational response generated in {response_time:.2f}s")

        # Construct the final response
        response_data = {
            "response": result["response"],
            "sources": [
                {
                    **source,
                    "chunk": source["chunk"][:200] + "..." if len(source["chunk"]) > 200 else source["chunk"],
                    "title": None  # Remove the title
                }
                for source in result["sources"]
            ],
            "follow_up_questions": result["follow_up_questions"],
            "learning_suggestions": result["learning_suggestions"],
            "related_topics": result["related_topics"],
            "educational_metadata": result["educational_metadata"],
            "learning_context": result["learning_context"],
            "response_time": response_time
        }
        
        return EducationalChatResponse(**response_data)

    except Exception as e:
        logger.error(f"❌ Educational chat error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Educational chat error: {str(e)}")




@router.get("/session/{session_id}/context")
async def get_session_context(
    session_id: str
):
    """Get learning context for a chat session"""
    current_user = User(id="default", username="default", role="student",
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    try:
        agent = get_educational_agent()
        context = agent.get_learning_context(current_user.username, session_id)

        return {
            "session_id": session_id,
            "learning_context": context.model_dump(),
            "summary": {
                "topics_covered": len(context.topics_covered),
                "current_focus": None,
                "difficulty_level": "intermediate",
                "objectives_count": len(context.learning_objectives)
            }
        }

    except Exception as e:
        logger.error(f"❌ Session context error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Session context error: {str(e)}")


@router.get("/learning-path/{topic}")
async def get_learning_path(
    topic: str,
    user_level: str = "intermediate",
    session_id: Optional[str] = None
):
    """Get suggested learning path for a topic, based on course materials."""
    logger.info(f"🛤️ Learning path request: {topic} for session {session_id}")

    agent = get_educational_agent()
    if not agent.retriever:
        raise HTTPException(
            status_code=503, detail="Retriever not initialized")

    # 1. Retrieve relevant documents from RAG
    try:
        retriever = agent.retriever
        documents = retriever.invoke(topic)
        context = "\n\n".join([doc.page_content for doc in documents])
    except Exception as e:
        logger.error(f"Error retrieving documents for learning path: {e}")
        raise HTTPException(
            status_code=500, detail="Could not retrieve context for learning path.")

    if not documents:
        # Fallback to a generic path if no context is found
        learning_path = [
            LearningPathStep(step=1, title=f"Introdução a {topic}",
                             description="Visão geral e conceitos chave.", estimated_time="1 hora", difficulty="easy"),
            LearningPathStep(step=2, title=f"Aplicações de {topic}",
                             description="Exemplos práticos e estudos de caso.", estimated_time="3 horas", difficulty="medium")
        ]
        return {"topic": topic, "learning_path": [step.model_dump() for step in learning_path]}

    # 2. Generate learning path with LLM using structured output
    prompt = f"""
    Você é um designer instrucional. Com base no CONTEÚDO fornecido, crie um caminho de aprendizado detalhado e estruturado para o tópico '{topic}' para um aluno de nível '{user_level}'.

    CONTEÚDO DISPONÍVEL:
    ---
    {context}
    ---

    Crie um caminho de aprendizado com 3 a 5 etapas lógicas e progressivas. Cada etapa deve ser diretamente relacionada ao conteúdo fornecido.
    """

    try:
        if not agent.model:
            raise ValueError("Model not initialized")

        # Use structured output to guarantee a valid Pydantic object
        structured_llm = agent.model.with_structured_output(LearningPath)
        response = structured_llm.invoke(prompt)

        # Ensure the response is of the correct type
        if isinstance(response, LearningPath):
            learning_path = response.learning_path
        else:
            # Handle cases where the structured output fails
            raise TypeError(
                f"Expected a LearningPath object, but got {type(response)}")

    except Exception as e:
        logger.error(f"Error generating structured learning path: {e}")
        # Fallback for any LLM or structuring errors
        learning_path = [
            LearningPathStep(step=1, title=f"Introdução a {topic}",
                             description="Visão geral e conceitos chave.", estimated_time="1 hora", difficulty="easy"),
            LearningPathStep(step=2, title=f"Aplicações de {topic}",
                             description="Exemplos práticos e estudos de caso.", estimated_time="3 horas", difficulty="medium")
        ]

    # 3. Save the learning path to the user's context if a session_id is provided
    if session_id:
        user_id = "default"  # Assuming a default user for now
        learning_context = agent.get_learning_context(user_id, session_id)
        learning_context.learning_path = learning_path
        agent.update_learning_context(
            user_id, session_id, learning_path=learning_path)
        logger.info(f"Saved learning path for session {session_id}")

    return {
        "topic": topic,
        "user_level": user_level,
        "learning_path": [step.model_dump() for step in learning_path],
    }


@router.post("/learning-path/add-topic")
async def add_topic_to_learning_path(
    request: AddTopicRequest,
):
    """Add a new topic to the user's learning path for a given session."""
    agent = get_educational_agent()
    user_id = "default"  # Assuming default user

    try:
        learning_context = agent.get_learning_context(
            user_id, request.session_id)

        new_step_number = len(learning_context.learning_path) + 1

        new_step = LearningPathStep(
            step=new_step_number,
            title=request.topic_title,
            description=request.topic_description,
            estimated_time="30 minutos",  # Default time
            difficulty="intermediate",  # Default difficulty
            completed=False
        )

        learning_context.learning_path.append(new_step)

        agent.update_learning_context(
            user_id, request.session_id, learning_path=learning_context.learning_path)

        logger.info(
            f"Added topic '{request.topic_title}' to learning path for session {request.session_id}")

        return {
            "status": "success",
            "message": "Topic added to learning path.",
            "learning_path": [step.model_dump() for step in learning_context.learning_path]
        }

    except Exception as e:
        logger.error(f"Error adding topic to learning path: {e}")
        raise HTTPException(
            status_code=500, detail="Could not add topic to learning path.")

@router.post("/simple", response_model=Response)
async def simple_chat(question: Question):
    """Simplified chat endpoint"""
    agent = get_educational_agent()
    logger.info(f"💬 Simple chat request: {question.content[:50]}...")

    if not agent.retriever:
        simulated_answer = f"Sistema não inicializado. Esta é uma resposta simulada para: '{question.content}'. Configure uma chave OpenAI válida para funcionalidades completas."
        return Response(
            answer=simulated_answer,
            sources=[{"title": "Sistema de Teste",
                      "source": "educational_agent.py", "page": 1, "relevance": 0.9}],
            response_time=0.1
        )

    try:
        start_time = time.time()
        result = await agent.chat(message=question.content)
        response_time = time.time() - start_time
        
        return Response(
            answer=result.get("response", ""),
            sources=result.get("sources", []),
            response_time=response_time
        )
    except Exception as e:
        logger.error(f"❌ Simple chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explore-topic", response_model=Response)
async def explore_topic(request: dict):
    """Explore a topic with the educational agent"""
    agent = get_educational_agent()
    try:
        topic = request.get("topic")
        user_level = request.get("user_level", "intermediate")
        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required")

        if not agent.retriever:
            raise HTTPException(
                status_code=503, detail="RAG handler not initialized in Educational Agent.")

        start_time = time.time()
        result = await agent.chat(
            message=f"Explique o tópico '{topic}' para um aluno de nível {user_level}."
        )
        response_time = time.time() - start_time

        return Response(
            answer=result.get("response", ""),
            sources=result.get("sources", []),
            response_time=response_time
        )

    except Exception as e:
        logger.error(f"❌ Error exploring topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Example usage
if __name__ == "__main__":
    agent = EducationalAgent()

    async def test_chat():
        result = await agent.chat(
            "O que é hipertrofia muscular e como alcançá-la?",
            user_id="test_user",
            session_id="test_session",
            learning_preferences={
                "learning_objectives": ["entender hipertrofia", "aplicar técnicas"]
            }
        )

        print("Response:", result["response"])
        print("Follow-up Questions:", result["follow_up_questions"])
        print("Sources:", len(result["sources"]))
        print("Learning Suggestions:", result["learning_suggestions"])

    import asyncio
    asyncio.run(test_chat())
