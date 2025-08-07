import os
import json
import logging
import time
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
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
from rag_system.rag_handler import RAGHandler, RAGQueryTool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from auth.auth import User, get_current_user
from video_processing.video_handler import get_video_handler

# Set environment variables
load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Configure logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["educational_chat"])


class LearningContext(BaseModel):
    """Track learning context and progress for each user"""
    user_id: str
    session_id: str
    learning_objectives: List[str] = []
    topics_covered: List[str] = []
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
    documents: List[Document]
    formatted_documents: str
    response: str


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
        self.rag_handler = None
        self.rag_tool: Optional[RAGQueryTool] = None
        self.model = None
        self.graph = None
        self.memory = MemorySaver()
        self.learning_contexts: Dict[str, LearningContext] = {}
        self.course_catalog: Optional[pd.DataFrame] = None

        self._load_course_catalog()
        self._initialize_rag()
        self._initialize_model()
        self._build_graph()

    def _initialize_rag(self):
        """Initialize RAG handler with enhanced retrieval"""
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning(
                "OPENAI_API_KEY not found. RAG capabilities disabled.")
            return

        try:
            self.rag_handler = RAGHandler(api_key=openai_api_key)
            self.rag_tool = RAGQueryTool(rag_handler=self.rag_handler)
            logger.info("✅ RAG Query Tool initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG: {e}")

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
        """Build the educational conversation graph"""

        def retriever_node(state: EducationalState):
            if not self.rag_handler:
                raise ValueError("RAG handler not initialized")
            retriever = self.rag_handler.retriever
            if not retriever:
                logger.warning("Retriever not available, returning empty documents.")
                return {"documents": []}
            documents = retriever.invoke(state["messages"][-1].content)
            return {"documents": documents}

        def format_documents_node(state: EducationalState):
            formatted_docs = "\n\n".join(doc.page_content for doc in state["documents"])
            return {"formatted_documents": formatted_docs}

        def chatbot_node(state: EducationalState):
            prompt_rag = f"""Você é um assistente útil que responde à perguntas do usuário com base no contexto fornecido.
Leia atentamente a dúvida do usuário e observe o contexto retornado de um banco vetorial de pesquisa utilizado como fonte de informação:

<contexto>
{state["formatted_documents"]}
</contexto>

Caso você não saiba, responda que não tem informações sobre isso. Não invente informações."""

            if not self.model:
                raise ValueError("Model not initialized")

            response = self.model.invoke([
                SystemMessage(content=prompt_rag),
                HumanMessage(content=state["messages"][-1].content)
            ])
            return {"response": response.content}

        graph = StateGraph(EducationalState)
        graph.add_node("retriever", retriever_node)
        graph.add_node("format_documents", format_documents_node)
        graph.add_node("chatbot", chatbot_node)

        graph.add_edge(START, "retriever")
        graph.add_edge("retriever", "format_documents")
        graph.add_edge("format_documents", "chatbot")
        graph.add_edge("chatbot", END)

        self.graph = graph.compile()
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
        
        initial_state = {
            "messages": [HumanMessage(content=message)],
        }

        try:
            if not self.graph:
                raise ValueError("Graph not initialized")

            final_state = self.graph.invoke(initial_state, config)
            
            response_content = final_state["response"]
            sources = [doc.metadata for doc in final_state.get("documents", [])]

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
                "learning_context": learning_context.dict(),
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
            "sources": result["sources"],
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
            "learning_context": context.dict(),
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
    user_level: str = "intermediate"
):
    """Get suggested learning path for a topic"""
    logger.info(f"🛤️ Learning path request: {topic}")

    try:
        agent = get_educational_agent()

        if not agent.rag_handler:
            raise HTTPException(
                status_code=503, detail="RAG handler not initialized")

        # Generate a prompt to ask the model for a learning path
        prompt = f"""
        Crie um caminho de aprendizado detalhado para o tópico '{topic}' para um aluno de nível {user_level}.
        O caminho de aprendizado deve conter de 3 a 5 etapas.
        Para cada etapa, forneça:
        - 'step': um número sequencial.
        - 'title': um título claro e conciso.
        - 'description': uma breve descrição do que será aprendido.
        - 'estimated_time': uma estimativa de tempo (ex: '2-3 horas', '1 semana').
        - 'difficulty': o nível de dificuldade (easy, medium, hard).

        Retorne a resposta em formato JSON.
        """

        # Use the RAG handler to generate the learning path
        response = await agent.chat(
            message=prompt,
            user_id="system_learning_path",
            session_id=f"lp_{topic.replace(' ', '_')}",
            learning_preferences={"difficulty_level": user_level}
        )

        # Extract the learning path from the response
        try:
            # The response content should be a JSON string
            learning_path_data = json.loads(response["response"])
            learning_path = learning_path_data.get("learning_path", [])
        except (json.JSONDecodeError, KeyError):
            # Fallback to a simple structure if parsing fails
            learning_path = [
                {"step": 1, "title": f"Introdução a {topic}",
                    "description": "Visão geral e conceitos chave.", "estimated_time": "1 hora", "difficulty": "easy"},
                {"step": 2, "title": f"Aplicações de {topic}",
                    "description": "Exemplos práticos e estudos de caso.", "estimated_time": "3 horas", "difficulty": "medium"}
            ]

        return {
            "topic": topic,
            "user_level": user_level,
            "learning_path": learning_path,
            "estimated_time": "1-2 semanas",
            "prerequisites": ["Conhecimento básico de treinamento"],
            "resources_available": True
        }

    except Exception as e:
        logger.error(f"❌ Learning path error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Learning path error: {str(e)}")

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
