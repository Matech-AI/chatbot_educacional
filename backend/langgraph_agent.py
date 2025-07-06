import os
import logging
import time
from typing import List, Dict, Tuple, Optional, Any
from pydantic import BaseModel

from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langchain.load import dumps, loads
from langchain_core.runnables import Runnable

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentState(BaseModel):
    """Defines the state of the LangGraph agent."""
    question: str
    material_ids: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    generated_queries: List[str] = []
    retrieved_docs: List[List[Any]] = []
    reranked_docs: List[Tuple[Any, float]] = []
    context: str = ""
    answer: str = ""
    sources: List[Dict[str, str]] = []
    response_time: float = 0.0

def reciprocal_rank_fusion(results: list[list], k=60):
    """ Reciprocal_rank_fusion that takes multiple lists of ranked documents
        and an optional parameter k used in the RRF formula """
    fused_scores = {}
    for docs in results:
        for rank, doc in enumerate(docs):
            doc_str = dumps(doc)
            if doc_str not in fused_scores:
                fused_scores[doc_str] = 0
            previous_score = fused_scores[doc_str]
            fused_scores[doc_str] += 1 / (rank + k)
    reranked_results = [
        (loads(doc), score)
        for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    ]
    return reranked_results

class LangGraphAgent:
    """A LangGraph-based agent for RAG."""

    def __init__(self, llm: ChatOpenAI, vector_store: Chroma):
        self.llm = llm
        self.vector_store = vector_store
        self.graph = self._build_graph()

    def _build_graph(self) -> Runnable:
        """Builds the LangGraph agent."""
        graph = StateGraph(AgentState)

        graph.add_node("generate_queries", self.generate_queries_node)
        graph.add_node("retrieve_documents", self.retrieve_documents_node)
        graph.add_node("rerank_documents", self.rerank_documents_node)
        graph.add_node("generate_answer", self.generate_answer_node)
        graph.add_node("handle_no_documents", self.handle_no_documents_node)

        graph.set_entry_point("generate_queries")
        graph.add_edge("generate_queries", "retrieve_documents")
        graph.add_edge("retrieve_documents", "rerank_documents")
        graph.add_conditional_edges(
            "rerank_documents",
            self.has_documents,
            {
                "yes": "generate_answer",
                "no": "handle_no_documents",
            },
        )
        graph.add_edge("generate_answer", END)
        graph.add_edge("handle_no_documents", END)

        return graph.compile()

    def generate_queries_node(self, state: AgentState) -> AgentState:
        """Generates search queries based on the user's question."""
        logger.info("Generating queries...")
        query_gen_template = """You are a helpful assistant that generates multiple search queries based on a single input query.
Generate multiple search queries related to: {question}
Output (4 queries):"""
        query_gen_prompt = ChatPromptTemplate.from_template(query_gen_template)
        
        query_gen_chain = query_gen_prompt | self.llm | StrOutputParser() | (lambda x: [q.strip() for q in x.split("\n") if q.strip()])
        
        state.generated_queries = query_gen_chain.invoke({"question": state.question})
        logger.info(f"Generated {len(state.generated_queries)} queries.")
        return state

    def retrieve_documents_node(self, state: AgentState) -> AgentState:
        """Retrieves documents for each generated query."""
        logger.info("Retrieving documents...")
        search_kwargs: Dict[str, Any] = {'k': 5}
        if state.material_ids:
            search_kwargs['filter'] = {"source": {"$in": state.material_ids}}

        retriever = self.vector_store.as_retriever(search_kwargs=search_kwargs)
        
        retrieved_docs = []
        for q in state.generated_queries:
            docs = retriever.invoke(q)
            retrieved_docs.append(docs)
        
        state.retrieved_docs = retrieved_docs
        logger.info(f"Retrieved {sum(len(docs) for docs in retrieved_docs)} documents.")
        return state

    def rerank_documents_node(self, state: AgentState) -> AgentState:
        """Reranks the retrieved documents using reciprocal rank fusion."""
        logger.info("Reranking documents...")
        state.reranked_docs = reciprocal_rank_fusion(state.retrieved_docs)
        logger.info(f"Reranked {len(state.reranked_docs)} documents.")
        return state

    def has_documents(self, state: AgentState) -> str:
        """Determines if any documents were found."""
        return "yes" if state.reranked_docs else "no"

    def generate_answer_node(self, state: AgentState) -> AgentState:
        """Generates the final answer based on the reranked documents."""
        logger.info("Generating answer...")
        context = "\n\n".join([doc.page_content for doc, score in state.reranked_docs[:5]])
        
        unique_sources = []
        seen_sources = set()
        for doc, score in state.reranked_docs[:5]:
            source = doc.metadata.get('source')
            if source and source not in seen_sources:
                unique_sources.append({
                    "source": source,
                    "filename": doc.metadata.get('filename', os.path.basename(source))
                })
                seen_sources.add(source)

        state.context = context
        state.sources = unique_sources

        prompt = "Você é um assistente de IA. Responda à pergunta com base no contexto fornecido."
        if state.config and 'prompt' in state.config:
            prompt = state.config['prompt']

        answer_template = """{prompt}

Context:
{context}

Question: {question}
"""
        answer_prompt = ChatPromptTemplate.from_template(answer_template)
        
        llm = self.llm
        if state.config:
            llm = ChatOpenAI(
                model=state.config.get('model', self.llm.model_name),
                temperature=state.config.get('temperature', self.llm.temperature),
            )

        answer_chain = answer_prompt | llm | StrOutputParser()
        state.answer = answer_chain.invoke({"context": state.context, "question": state.question, "prompt": prompt})
        
        logger.info("Answer generated.")
        return state

    def handle_no_documents_node(self, state: AgentState) -> AgentState:
        """Handles the case where no documents are found."""
        logger.info("No documents found.")
        state.answer = "Não foram encontrados documentos relevantes para responder à sua pergunta."
        return state

    def run(self, question: str, material_ids: Optional[List[str]] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Runs the LangGraph agent."""
        start_time = time.time()
        
        initial_state = AgentState(
            question=question,
            material_ids=material_ids,
            config=config
        )
        
        final_state = self.graph.invoke(initial_state)
        
        response_time = time.time() - start_time
        
        return {
            "answer": final_state.get('answer', ''),
            "sources": final_state.get('sources', []),
            "response_time": response_time,
        }