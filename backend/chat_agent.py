import os
from typing import Annotated, TypedDict, List
from dotenv import load_dotenv
from pydantic import SecretStr

from langchain_core.tools import BaseTool
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage
from langchain_core.tools.retriever import create_retriever_tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from rag_handler import RAGHandler
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# Set environment variables
load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 1. Define State
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 2. Setup Retriever
# Initialize RAG Handler to manage the vector store
# 2. Setup Retriever
# Initialize RAG Handler to manage the vector store
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("⚠️ OPENAI_API_KEY not found. Retriever tool will be disabled.")
    retriever_tool = None
else:
    try:
        rag_handler = RAGHandler(api_key=openai_api_key)
        if rag_handler.vector_store:
            retriever = rag_handler.vector_store.as_retriever(search_kwargs={"k": 3})
            
            retriever_tool = create_retriever_tool(
                retriever,
                "search_study_materials",
                "Search and return information from the study materials about the 'Força Suprema' training.",
            )
        else:
            print("⚠️ Vector store not available. Retriever tool will be disabled.")
            retriever_tool = None
        print("✅ RAG handler and retriever tool initialized successfully.")
    except Exception as e:
        print(f"❌ Error initializing RAG handler: {e}")
        retriever_tool = None

# 3. Setup Tools
tools: list = []
if retriever_tool:
    tools.append(retriever_tool)

tool_node = ToolNode(tools)

# 4. Setup Model
gemini_api_key_str = os.getenv("GEMINI_API_KEY")
if not gemini_api_key_str:
    raise ValueError("GEMINI_API_KEY environment variable not set.")
gemini_api_key = SecretStr(gemini_api_key_str)


# System prompt is now part of the initial state
system_prompt = SystemMessage(
    content="""Você é o Don Corleone. Se você falar a palavra 'carro', você morre."""
)

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    api_key=gemini_api_key,
)
model_with_tools = model.bind_tools(tools)

# 5. Define Graph Nodes
def agent(state: State):
    """Invokes the agent model with the current state."""
    messages = [system_prompt] + state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

# 6. Build Graph
builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

# 7. Compile Graph
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# Example of how to run the graph
if __name__ == "__main__":
    def stream_graph_updates(user_input: str, thread_id: str):
        """Streams graph updates for a given user input and thread ID."""
        for event in graph.stream(
            {"messages": [("user", user_input)]},
            {"configurable": {"thread_id": thread_id}},
        ):
            for value in event.values():
                if "messages" in value and value["messages"]:
                    print("Assistant:", value["messages"][-1].content)

    thread_id_counter = 1
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            
            current_thread_id = str(thread_id_counter)
            stream_graph_updates(user_input, current_thread_id)
            thread_id_counter += 1

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break