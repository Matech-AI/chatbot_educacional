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
    sources: List[Dict[str, Any]]
    educational_metadata: Dict[str, Any]


class EducationalChatRequest(BaseModel):
    content: str
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
        """Initialize RAG handler with enhanced retrieval and NVIDIA support"""
        # Tentar NVIDIA primeiro, depois OpenAI, depois Gemini
        nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not any([nvidia_api_key, openai_api_key, gemini_api_key]):
            logger.warning(
                "Nenhuma API key encontrada. RAG capabilities disabled.")
            return

        try:
            # Usar RAG handler unificado que suporta NVIDIA
            self.rag_handler = RAGHandler(
                api_key=openai_api_key,  # Parâmetro correto
                nvidia_api_key=nvidia_api_key,
                gemini_api_key=gemini_api_key
            )
            self.rag_tool = RAGQueryTool(rag_handler=self.rag_handler)
            logger.info(
                "✅ RAG Query Tool initialized successfully with NVIDIA support")
        except Exception as e:
            logger.error(f"Error initializing RAG: {e}")

    def _load_course_catalog(self, path: str = "data/catalog.xlsx"):
        """Loads the course catalog from an Excel file."""
        try:
            if os.path.exists(path):
                self.course_catalog = pd.read_excel(path)
                # Normalize column names for easier access
                self.course_catalog.columns = [
                    col.strip().lower() for col in self.course_catalog.columns]
                logger.info("✅ Course catalog loaded successfully.")
            else:
                logger.warning(
                    f"Course catalog not found at {path}. Video suggestions will be disabled.")
        except Exception as e:
            logger.error(f"Error loading course catalog: {e}")

    def _initialize_model(self):
        """Initialize AI model with fallback support"""
        # ✅ MODIFICADO: Usar RAG handler com fallback automático
        try:
            from rag_system.rag_handler import RAGHandler, RAGConfig

            # Configurar RAG handler com fallback
            config = RAGConfig(
                prefer_nvidia=True,  # Tentar NVIDIA primeiro
                prefer_openai=True,  # OpenAI como fallback
                prefer_gemini=True,  # Gemini como terceira opção
                nvidia_retry_attempts=2,  # Apenas 2 tentativas
                nvidia_retry_delay=0.5,   # Delay reduzido
            )

            # Inicializar RAG handler
            self.rag_handler = RAGHandler(config)

            # Usar o modelo do RAG handler (com fallback automático)
            self.model = self.rag_handler.llm
            self.model_provider = self.rag_handler.current_llm_provider
            self.model_name = getattr(self.model, 'model', 'Unknown')

            logger.info(
                f"✅ AI Model initialized with RAG fallback: {self.model_provider} ({self.model_name})")
            return

        except Exception as e:
            logger.error(f"RAG handler initialization failed: {e}")
            # Fallback para inicialização individual dos modelos
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            openai_api_key = os.getenv("OPENAI_API_KEY")
            nvidia_api_key = os.getenv("NVIDIA_API_KEY")

            # Tentar NVIDIA primeiro
            if nvidia_api_key:
                try:
                    from rag_system.rag_handler import NVIDIAChatOpenAI
                    model_name = "openai/gpt-oss-120b"
                    self.model = NVIDIAChatOpenAI(
                        nvidia_api_key=nvidia_api_key,
                        model=model_name,
                        base_url="https://integrate.api.nvidia.com/v1",
                        temperature=0.3,
                        retry_attempts=2,  # ✅ REDUZIDO: de 3 para 2
                        retry_delay=0.5
                    )
                    self.model_provider = "NVIDIA"
                    self.model_name = model_name
                    logger.info(
                        f"✅ AI Model initialized: {self.model_provider} ({self.model_name})")
                    return
                except Exception as e:
                    logger.warning(f"NVIDIA initialization failed: {e}")
                    self.model = None

            # Tentar Gemini
            if gemini_api_key:
                try:
                    model_name = "gemini-2.5-flash"
                    self.model = ChatGoogleGenerativeAI(
                        model=model_name,
                        temperature=0.3,  # Lower temperature for more consistent educational responses
                        api_key=SecretStr(gemini_api_key),
                    )
                    self.model_provider = "Gemini"
                    self.model_name = model_name
                    logger.info(
                        f"✅ AI Model initialized: {self.model_provider} ({self.model_name})")
                    return
                except Exception as e:
                    logger.warning(f"Gemini initialization failed: {e}")
                    self.model = None

            # Tentar OpenAI como último recurso
            if openai_api_key:
                try:
                    model_name = "gpt-4o-mini"
                    self.model = ChatOpenAI(
                        model=model_name,
                        temperature=0.3,
                        api_key=SecretStr(openai_api_key),
                    )
                    self.model_provider = "OpenAI"
                    self.model_name = model_name
                    logger.info(
                        f"✅ AI Model initialized: {self.model_provider} ({self.model_name})")
                    return
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
        - Padrão DNA-only: responda com base exclusiva nos materiais do DNA da Força quando disponíveis.
        - Se não houver cobertura suficiente no acervo, diga explicitamente: "Não encontrei essa informação nos materiais do DNA da Força" e, se útil, inclua um bloco separado "Informação complementar (fora do acervo)".
        - Nunca exiba caminhos de arquivos ou códigos internos (ex.: M13A52). Para o aluno, utilize: "Módulo X, Aula Y — 'Título' (PDF)" e inclua a página apenas quando houver metadado real.
        - Gere perguntas de acompanhamento que ajudem o aluno a explorar mais profundamente.
        - Mantenha o foco educacional, precisão biomecânica e coerência com o curso.
        """

        return base_prompt

    def _build_graph(self):
        """Build the educational conversation graph"""

        tools = []
        if self.rag_tool:
            tools.append(self.rag_tool)

        tool_node = ToolNode(tools)

        if not self.model:
            raise ValueError("Model not initialized")

        model_with_tools = self.model.bind_tools(tools)

        def agent_node(state: EducationalState):
            """The primary agent node that decides what to do."""
            learning_context = state.get("learning_context")
            if not learning_context:
                learning_context = LearningContext(
                    user_id="default", session_id="default")

            system_prompt = SystemMessage(
                content=self._get_educational_system_prompt(learning_context))

            messages = [system_prompt] + state["messages"]

            # Gentle insistence on using RAG tool when question needs grounding
            # Add a lightweight instruction message to bias tool usage
            insistence = SystemMessage(content=(
                "Quando a pergunta envolver conteúdo do curso ou fatos verificáveis, "
                "utilize a tool 'search_educational_materials' para buscar contexto antes de responder. "
                "Sempre prefira citar fontes dos materiais quando disponíveis."
            ))

            response = model_with_tools.invoke([insistence] + messages)

            # Log which model is responding
            logger.info(
                f"🤖 Generating response with: {self.model_provider} ({self.model_name})")

            return {"messages": [response]}

        # Build graph
        builder = StateGraph(EducationalState)
        builder.add_node("agent", agent_node)
        builder.add_node("tools", tool_node)

        builder.add_edge(START, "agent")
        builder.add_conditional_edges(
            "agent",
            tools_condition,
        )
        builder.add_edge("tools", "agent")

        self.graph = builder.compile(checkpointer=self.memory)
        logger.info("✅ Educational graph compiled successfully with RAG tool")

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
            self.update_learning_context(
                user_id, session_id, **learning_preferences)

        config = RunnableConfig(
            configurable={"thread_id": f"{user_id}_{session_id}"})

        initial_state = {
            "messages": [HumanMessage(content=message)],
            "learning_context": learning_context,
        }

        try:
            if not self.graph:
                raise ValueError("Graph not initialized")

            final_state = self.graph.invoke(initial_state, config)

            assistant_message = final_state["messages"][-1]
            response_content = assistant_message.content

            sources = []
            if self.rag_tool and assistant_message.tool_calls:
                tool_call = assistant_message.tool_calls[0]
                if tool_call['name'] == self.rag_tool.name:
                    for msg in reversed(final_state["messages"]):
                        if msg.type == "tool":
                            tool_output = msg.content
                            try:
                                # The tool output is a dictionary, not a JSON string
                                sources = tool_output.get("sources", [])
                            except Exception as e:
                                logger.warning(
                                    f"Could not extract sources from tool output: {e}")
                            break

            follow_up_questions = self.generate_follow_up_questions(
                learning_context.current_topic or "treinamento",
                learning_context.difficulty_level
            )

            # Generate video suggestions based on sources
            video_suggestions = []
            if sources and self.course_catalog is not None:
                video_codes = set()
                for source in sources:
                    # Extract video code like M01A01 from the source filename
                    filename = Path(source.get("source", "")).stem
                    if filename:
                        # Handle cases where filename might not have '_'
                        parts = filename.split('_')
                        if parts:
                            video_codes.add(parts[0].upper())

                for code in video_codes:
                    # Ensure column name is correct
                    if 'código' in self.course_catalog.columns:
                        match = self.course_catalog[self.course_catalog['código'] == code]
                        if not match.empty:
                            video_info = match.iloc[0]
                            video_suggestions.append({
                                "topic": video_info.get('nome da aula', 'N/A'),
                                "video_code": code,
                                "summary": video_info.get('resumo da aula', ''),
                                "module": video_info.get('módulo', 0),
                                "class": video_info.get('aula', 0)
                            })

            return {
                "response": response_content,
                "sources": sources,
                "follow_up_questions": follow_up_questions[:3],
                "learning_suggestions": [],
                "related_topics": [],
                "educational_metadata": {},
                "learning_context": learning_context.model_dump(),
                "video_suggestions": video_suggestions
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

        # Log current model being used
        logger.info(
            f"📊 Using AI Model: {agent.model_provider} ({agent.model_name})")

        # Prepare learning preferences
        learning_preferences = {
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

        response_time = time.time() - start_time

        video_suggestions = result.get("video_suggestions", [])
        logger.info(
            f"✅ Response generated by {agent.model_provider} ({agent.model_name}) in {response_time:.2f}s with {len(video_suggestions)} video suggestions")

        # Construct the final response
        response_data = {
            "response": result["response"],
            "sources": result["sources"],
            "follow_up_questions": result["follow_up_questions"],
            "learning_suggestions": result["learning_suggestions"],
            "related_topics": result["related_topics"],
            "educational_metadata": result["educational_metadata"],
            "learning_context": result["learning_context"],
            "video_suggestions": video_suggestions,
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
                "current_focus": context.current_topic,
                "difficulty_level": context.difficulty_level,
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

        # This would use enhanced RAG if available
        learning_path = [
            {"step": 1, "title": f"Fundamentos de {topic}",
                "description": "Conceitos básicos e terminologia"},
            {"step": 2, "title": f"Aplicação prática de {topic}",
                "description": "Como aplicar na prática"},
            {"step": 3, "title": f"Progressão em {topic}",
                "description": "Níveis avançados e variações"},
            {"step": 4, "title": f"Troubleshooting {topic}",
                "description": "Solucionando problemas comuns"}
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
