## Guia do Sistema RAG (LangChain + LangGraph)

Este documento descreve, de forma prática e objetiva, como o sistema de RAG (Retrieval-Augmented Generation) está implementado neste projeto, incluindo ingestão e indexação de materiais, recuperação, geração de respostas, a ferramenta RAG integrada ao agente e a orquestração conversacional com LangGraph.

- **Stack principal**: LangChain, LangGraph, ChromaDB (vetor store), OpenAI (Chat e Embeddings), FastAPI
- **Pastas/arquivos-chave**:
  - `backend/rag_system/rag_handler.py`: pipeline RAG (ingestão, embeddings, vector store, retriever, geração)
  - `backend/rag_server.py`: API dedicada ao RAG (inicialização, processamento, consulta, templates)
  - `backend/chat_agents/educational_agent.py`: agente educacional com LangGraph (grafo stateful com ferramentas, incluindo a ferramenta RAG)
  - Persistência do vetor store: `data/.chromadb`
  - Materiais a processar: `data/materials`

## 🎯 **ARQUITETURA DA CONVERSA - ONDE FICA DE FATO:**

### **📍 LOCALIZAÇÃO PRINCIPAL DA CONVERSA:**

- **✅ CONVERSA PRINCIPAL**: `backend/chat_agents/educational_agent.py`
- **🔧 FERRAMENTA RAG**: `backend/rag_system/rag_handler.py`

### **📊 FLUXO COMPLETO DA CONVERSA:**

```
Frontend → API Server → Educational Agent → RAG Handler → Resposta
```

### **🔍 RESPONSABILIDADES CLARAS:**

#### **1. Educational Agent (`educational_agent.py`) - CÉREBRO DA CONVERSA:**

- ✅ **Gerencia todo o estado da conversa**
- ✅ **Controla o fluxo de mensagens**
- ✅ **Aplica contexto de aprendizado**
- ✅ **Gera perguntas de acompanhamento**
- ✅ **Sugere vídeos relacionados**
- ✅ **Coordena todas as ferramentas (incluindo RAG)**
- ✅ **Mantém memória da sessão**
- ✅ **Retorna resposta final para o frontend**

#### **2. RAG Handler (`rag_handler.py`) - FERRAMENTA DE BUSCA:**

- ✅ **Busca documentos relevantes**
- ✅ **Gera respostas baseadas no contexto**
- ✅ **Fornece fontes e citações**
- ❌ **NÃO gerencia conversas**
- ❌ **NÃO mantém estado**
- ❌ **NÃO coordena fluxo**

### **🚨 IMPORTANTE - PROBLEMA DAS RESPOSTAS VAZIAS:**

O problema das **respostas com texto vazio** está no **Educational Agent**, não no RAG Handler, porque:

1. **Educational Agent** é quem recebe e processa as mensagens
2. **Educational Agent** é quem decide se usa o RAG Handler
3. **Educational Agent** é quem retorna a resposta final para o frontend

---

### 1) Configuração e Componentes do RAG (LangChain)

- **Configuração central** (`RAGConfig`) controla chunking, modelo, embeddings e parâmetros de recuperação (MMR):

```33:50:backend/rag_system/rag_handler.py
class RAGConfig:
    """Unified configuration for the RAG handler."""
    # Text processing
    chunk_size: int = 1500
    chunk_overlap: int = 300

    # Model configuration
    model_name: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.2
    max_tokens: int = 800

    # Retrieval configuration
    retrieval_search_type: str = "mmr"
    retrieval_k: int = 6
    retrieval_fetch_k: int = 20
    retrieval_lambda_mult: float = 0.7
```

- **Inicialização** de Embeddings, LLM, Vector Store e Retriever (MMR):

```122:131:backend/rag_system/rag_handler.py
def _initialize_embeddings(self):
    try:
        self.embeddings = OpenAIEmbeddings(
            model=self.config.embedding_model,
            api_key=SecretStr(self.api_key)
        )
        logger.info(f"✅ Embeddings initialized: {self.config.embedding_model}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize embeddings: {e}")
        raise
```

```133:141:backend/rag_system/rag_handler.py
def _initialize_llm(self):
    try:
        self.llm = ChatOpenAI(
            model=self.config.model_name,
            temperature=self.config.temperature,
            api_key=SecretStr(self.api_key)
        )
        logger.info(f"✅ LLM initialized: {self.config.model_name}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM: {e}")
        raise
```

```145:155:backend/rag_system/rag_handler.py
def _initialize_vector_store(self):
    try:
        os.makedirs(self.persist_dir, exist_ok=True)
        self.vector_store = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings
        )
        logger.info(f"✅ Vector store loaded/created at {self.persist_dir}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize vector store: {e}")
        raise
```

```157:167:backend/rag_system/rag_handler.py
def _setup_retriever(self):
    if self.vector_store:
        self.retriever = self.vector_store.as_retriever(
            search_type=self.config.retrieval_search_type,
            search_kwargs={
                "k": self.config.retrieval_k,
                "fetch_k": self.config.retrieval_fetch_k,
                "lambda_mult": self.config.retrieval_lambda_mult,
            },
        )
        logger.info("✅ Retriever configured")
```

### 2) Ingestão e Indexação de Materiais

- **Carregamento** de documentos suportados (`pdf`, `txt`, `xlsx`) com `DirectoryLoader` e processamento em paralelo:

```245:266:backend/rag_system/rag_handler.py
def _load_all_documents(self) -> List[Document]:
    """Load all supported document types from the materials directory."""
    documents = []
    file_patterns = {
        "**/*.pdf": PyPDFLoader,
        "**/*.txt": TextLoader,
        "**/*.xlsx": UnstructuredExcelLoader,
    }
    for pattern, loader_class in file_patterns.items():
        try:
            loader = DirectoryLoader(
                str(self.materials_dir),
                glob=pattern,
                loader_cls=loader_class,
                show_progress=True,
                use_multithreading=True,
            )
            documents.extend(loader.load())
        except Exception as e:
            logger.warning(f"⚠️ Error loading {pattern}: {e}")
    logger.info(f"📄 Loaded {len(documents)} total documents.")
    return documents
```

- **Split** dos documentos em chunks e **indexação** no ChromaDB:

```226:243:backend/rag_system/rag_handler.py
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=self.config.chunk_size,
    chunk_overlap=self.config.chunk_overlap,
)
splits = text_splitter.split_documents(enhanced_documents)
logger.info(f"🔪 Split into {len(splits)} chunks")

# Add to vector store
if self.vector_store:
    self.vector_store.add_documents(splits)
logger.info(f"✅ Added {len(splits)} document chunks to vector store")
self._setup_retriever()
```

- **Metadados educacionais** (opcional; infraestrutura pronta e comentada por padrão):

```284:292:backend/rag_system/rag_handler.py
# if len(doc.page_content) > 100:
#     if self.config.extract_key_concepts:
#         enhanced_metadata['key_concepts'] = self._extract_key_concepts(doc.page_content)
#     if self.config.assess_difficulty_level:
#         enhanced_metadata['difficulty_level'] = self._assess_difficulty_level(doc.page_content)
#     if self.config.create_summaries:
#         enhanced_metadata['summary'] = self._create_content_summary(doc.page_content)
```

### 3) Consulta e Geração (RAG)

- **Recuperação** (MMR) e preparação de contexto:

```366:373:backend/rag_system/rag_handler.py
logger.info(f"🔍 Retrieving documents for question: '{question}'")
docs = self.retriever.get_relevant_documents(question)
logger.info(f"📄 Found {len(docs)} relevant documents.")

if not docs:
    logger.warning("No documents found for the question.")
    return {"answer": "No relevant information found.", "sources": []}
```

- **Geração** via chain `prompt | llm | StrOutputParser`:

```424:435:backend/rag_system/rag_handler.py
prompt = ChatPromptTemplate.from_template(prompt_template)

if not self.llm:
    raise ValueError("LLM not initialized")

chain = prompt | self.llm | StrOutputParser()
answer = chain.invoke({
    "context": context,
    "question": question,
    "user_level": user_level
})
```

- **Retorno** com fontes priorizadas por valor educacional:

```438:441:backend/rag_system/rag_handler.py
final_sources = [s.dict() for s in sources]
logger.info(f"✅ Successfully generated response with {len(final_sources)} sources.")
return {"answer": answer, "sources": final_sources}
```

### 4) Ferramenta RAG para o Agente (LangChain Tool)

- A ferramenta `RAGQueryTool` encapsula a consulta RAG para ser invocada pelo agente:

```487:506:backend/rag_system/rag_handler.py
class RAGQueryTool(BaseTool):
    """A tool to query the RAG system for educational content."""
    name: str = "search_educational_materials"
    description: str = "Searches and retrieves information from educational materials to answer questions about fitness, exercise science, and strength training."
    args_schema = RAGQueryToolInput
    rag_handler: RAGHandler

    def _run(self, query: str, user_level: str = "intermediate") -> Dict[str, Any]:
        """Execute the RAG query."""
        logger.info(f"Tool '{self.name}' invoked with query: '{query}' and user_level: '{user_level}'")
        try:
            result = self.rag_handler.generate_response(question=query, user_level=user_level)
            return result
        except Exception as e:
            logger.error(f"Error executing RAGQueryTool: {e}", exc_info=True)
            return {"answer": "An error occurred while searching the materials.", "sources": []}
```

### 5) Orquestração Conversacional (LangGraph – stateful graph)

- **Estado** da conversação com agregação de mensagens e contexto de aprendizagem:

```65:70:backend/chat_agents/educational_agent.py
class EducationalState(TypedDict):
    messages: Annotated[list, add_messages]
    learning_context: LearningContext
    sources: List[Dict[str, Any]]
    educational_metadata: Dict[str, Any]
```

- **Memória** e identificação de sessão (stateful):

```99:101:backend/chat_agents/educational_agent.py
self.memory = MemorySaver()
```

```325:330:backend/chat_agents/educational_agent.py
config = RunnableConfig(configurable={"thread_id": f"{user_id}_{session_id}"})
initial_state = {
    "messages": [HumanMessage(content=message)],
    "learning_context": learning_context,
}
```

- **Construção do grafo** com nó do agente e nó de ferramentas; roteamento condicional para ferramentas; compilação com checkpointer (memória):

```254:267:backend/chat_agents/educational_agent.py
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
```

- **Nó do agente** (gera a resposta e/ou decide acionar ferramentas):

```240:252:backend/chat_agents/educational_agent.py
def agent_node(state: EducationalState):
    """The primary agent node that decides what to do."""
    learning_context = state.get("learning_context")
    if not learning_context:
        learning_context = LearningContext(user_id="default", session_id="default")

    system_prompt = SystemMessage(content=self._get_educational_system_prompt(learning_context))
    messages = [system_prompt] + state["messages"]

    response = model_with_tools.invoke(messages)
    return {"messages": [response]}
```

- **Execução** do grafo e extração de fontes quando a tool RAG é chamada:

```336:353:backend/chat_agents/educational_agent.py
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
                    sources = tool_output.get("sources", [])
                except Exception as e:
                    logger.warning(f"Could not extract sources from tool output: {e}")
                break
```

### 6) API do Servidor RAG (FastAPI)

- **Inicialização automática** e diretórios de dados:

```250:281:backend/rag_server.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    ...
    chroma_persist_dir = Path("data/.chromadb")
    materials_dir = Path("data/materials")
    ...
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key and openai_api_key != "your_openai_api_key_here":
        try:
            logger.info("🔧 Inicializando RAG handler automaticamente...")
            rag_handler = RAGHandler(
                api_key=openai_api_key,
                persist_dir=str(chroma_persist_dir)
            )
            logger.info("✅ RAG handler inicializado automaticamente")
        except Exception as e:
            logger.warning(
                f"⚠️  Não foi possível inicializar RAG handler automaticamente: {e}")
```

- **Processamento** de materiais (background) e reprocessamento com recursos educacionais:

```464:485:backend/rag_server.py
@app.post("/process-materials", response_model=ProcessResponse)
async def process_materials(request: ProcessMaterialsRequest, background_tasks: BackgroundTasks):
    ...
    rag_handler.config.enable_educational_features = request.enable_educational_features
    background_tasks.add_task(
        rag_handler.process_documents, force_reprocess=request.force_reprocess)
    return ProcessResponse(success=True, message="Material processing started in the background.")
```

```491:517:backend/rag_server.py
@app.post("/reprocess-enhanced-materials", response_model=ProcessResponse)
async def reprocess_enhanced_materials(background_tasks: BackgroundTasks):
    ...
    rag_handler.config.enable_educational_features = True
    background_tasks.add_task(
        rag_handler.process_documents, force_reprocess=True)
    return ProcessResponse(success=True, message="Enhanced material reprocessing started in the background.")
```

- **Consulta RAG**:

```523:548:backend/rag_server.py
@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    ...
    result = rag_handler.generate_response(
        question=request.question,
        user_level=request.user_level
    )
    return QueryResponse(
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        response_time=response_time
    )
```

- **Inicializar/Resetar/Estatísticas**:

```556:570:backend/rag_server.py
@app.post("/initialize")
async def initialize_rag(api_key: str):
    rag_handler = RAGHandler(
        api_key=api_key,
        persist_dir=str(chroma_persist_dir)
    )
    return {"success": True, "message": "RAG handler inicializado"}
```

```578:589:backend/rag_server.py
@app.post("/reset")
async def reset_rag():
    if rag_handler:
        rag_handler.reset()
    return {"success": True, message": "RAG handler resetado"}
```

```595:606:backend/rag_server.py
@app.get("/stats")
async def get_rag_stats():
    stats = rag_handler.get_system_stats()
    return stats
```

- **Aplicação dinâmica** de templates/configurações no `RAGHandler` (chunking, modelo, embeddings, busca):

```324:351:backend/rag_server.py
def _apply_config_to_rag_handler(cfg: Dict[str, Any]):
    if not rag_handler:
        return
    try:
        if 'chunkSize' in cfg and isinstance(cfg['chunkSize'], int):
            rag_handler.config.chunk_size = cfg['chunkSize']
        if 'chunkOverlap' in cfg and isinstance(cfg['chunkOverlap'], int):
            rag_handler.config.chunk_overlap = cfg['chunkOverlap']
        if 'model' in cfg and isinstance(cfg['model'], str):
            rag_handler.config.model_name = cfg['model']
        if 'embeddingModel' in cfg and isinstance(cfg['embeddingModel'], str):
            rag_handler.config.embedding_model = cfg['embeddingModel']
        if 'temperature' in cfg:
            try:
                rag_handler.config.temperature = float(cfg['temperature'])
            except Exception:
                pass
        if 'retrievalSearchType' in cfg and isinstance(cfg['retrievalSearchType'], str):
            rag_handler.config.retrieval_search_type = cfg['retrievalSearchType']
        # Reconfigurar retriever após mudanças
        rag_handler._setup_retriever()
    except Exception as e:
        logger.warning(
            f"Não foi possível aplicar configuração ao RAG handler: {e}")
```

### 7) Fluxo Operacional (passo a passo)

1. Garantir `OPENAI_API_KEY` no ambiente. Ao subir o servidor, o handler pode inicializar automaticamente; caso contrário, usar `/initialize`.
2. Processar materiais com `/process-materials` (ou `/reprocess-enhanced-materials` para forçar reindexação com recursos educacionais).
3. Realizar consultas RAG via `/query` (RAG direto) ou usar `/chat/educational` (conversa com grafo, memória por sessão e tool RAG).
4. Acompanhar `/stats` e `/status` para diagnóstico.

### 8) Notas de Design e Observações

- **Stateful Graph (LangGraph)**: sim, o grafo mantém estado por sessão (thread_id), usa `MemorySaver` como checkpointer e agrega `messages` no `EducationalState`. Fluxo: `agent -> tools -> agent` baseado em `tools_condition`.
- **Reranking**: não há reranker externo; a diversidade é via MMR no retriever (`retrieval_search_type="mmr"`).
- **Diretórios**: `data/materials` (entrada), `data/.chromadb` (persistência do ChromaDB).
- **Metadados educacionais**: infraestrutura pronta e caches; para ativar extrações no ingestion, descomente o bloco indicado em `_enhance_document` e mantenha `enable_educational_features=True`.
- **Templates**: o servidor RAG expõe endpoints para ler/aplicar/salvar templates; mudanças relevantes (chunking/modelo/busca) são refletidas no `RAGHandler` em tempo de execução.

### 9) Troubleshooting rápido

- "RAG handler não inicializado": chame `/initialize` com uma `api_key` válida ou defina `OPENAI_API_KEY` antes de subir o servidor.
- "No documents found": verifique se há arquivos em `data/materials` e rode `/process-materials`.
- Embeddings/LLM falham: confira chaves, conectividade de rede e versões em `backend/config/requirements-*.txt`.
- Mudanças de chunking/busca não surtiram efeito: garanta reprocessamento (`/reprocess-enhanced-materials`) e que `_apply_config_to_rag_handler` foi chamado via endpoints de config.

### 10) Referências Rápidas de Endpoints

- `POST /initialize`: inicializa o RAG handler
- `POST /process-materials`: processa materiais no background
- `POST /reprocess-enhanced-materials`: reprocessamento completo com recursos educacionais
- `POST /query`: consulta RAG
- `GET /stats` e `GET /status`: diagnóstico/estatísticas
- `GET/POST /assistant/config`, `GET /assistant/templates`, `POST /assistant/config/template/{name}`, `POST /assistant/config/save-template`: gerência de templates/config

### 11) Qualidade dos Resultados: Diagnóstico e Melhorias

- **Principais causas identificadas**:

  - Uso inconsistente da tool de RAG no grafo (respostas sem grounding quando o modelo não aciona a ferramenta).
  - Contexto diluído: muitos chunks concatenados sem priorização forte por relevância.
  - Embeddings legados reduzem precisão na recuperação.
  - Parâmetros MMR possivelmente privilegiando diversidade em detrimento de relevância.
  - Metadados educacionais não usados no ranking (infraestrutura pronta, mas desativada por padrão).

- **Ajustes implementados no código**:

  - Embeddings atualizados para `text-embedding-3-small`.
  - Ordenação por relevância e limite de contexto via `max_context_chunks` (default 4), priorizando os melhores chunks.
  - Passagem de `max_tokens` ao `ChatOpenAI` para controlar comprimento de saída.
  - Instrução de sistema extra no nó do agente reforçando uso da tool `search_educational_materials`.

- **Ações recomendadas**:

  - Reindexar materiais após a troca de embeddings: `POST /reprocess-enhanced-materials`.
  - Testar `retrieval_search_type="similarity"` e `k` menor (3–5) via `/assistant/config` para perguntas objetivas.
  - Considerar adicionar um reranker (ex.: Cohere Rerank, bge-reranker) entre `fetch_k` e `k`.
  - Opcional: ativar metadados educacionais na ingestão (descomentar bloco em `_enhance_document`) e reprocessar.

- **Checklist de saúde**:
  - `OPENAI_API_KEY` configurada; `/status` e `/stats` indicando `vector_store_count > 0`.
  - Materiais presentes em `data/materials` e processados após as mudanças.
  - Nas conversas que exigem grounding, a tool de RAG é acionada (ver logs).

### 12) 🔍 DIAGNÓSTICO DE PROBLEMAS DE RESPOSTAS VAZIAS

#### **🚨 PROBLEMA PRINCIPAL IDENTIFICADO:**

As **respostas com texto vazio** no frontend são causadas por problemas no **Educational Agent**, não no RAG Handler.

#### **📍 LOCALIZAÇÃO DO PROBLEMA:**

- **Arquivo**: `backend/chat_agents/educational_agent.py`
- **Função**: `async def chat()` (linhas 421-500)
- **Responsabilidade**: Processamento da mensagem e retorno da resposta

#### **🔧 CAUSAS PROVÁVEIS:**

1. **Inicialização do RAG Handler falhou**
2. **Graph não foi compilado corretamente**
3. **Modelo de IA não está funcionando**
4. **Erro na execução do grafo LangGraph**
5. **Problema na extração da resposta do estado final**

#### **✅ SOLUÇÕES IMPLEMENTADAS:**

1. **Verificações robustas** na função `chat()`
2. **Fallback de resposta** quando o conteúdo está vazio
3. **Logs detalhados** para diagnóstico
4. **Tratamento de erros** com respostas úteis

#### **📋 CHECKLIST DE DIAGNÓSTICO:**

- [ ] Verificar se `rag_handler` foi inicializado
- [ ] Verificar se `graph` foi compilado
- [ ] Verificar se `model` está funcionando
- [ ] Verificar logs de erro no Educational Agent
- [ ] Verificar se o RAG Handler está retornando respostas válidas

#### **🔄 FLUXO DE RESOLUÇÃO:**

1. **Identificar** onde a falha está ocorrendo (logs)
2. **Corrigir** a inicialização do componente problemático
3. **Testar** com uma pergunta simples
4. **Verificar** se a resposta está sendo retornada corretamente

---

Este guia cobre o fluxo RAG (LangChain) e a orquestração conversacional (LangGraph) conforme implementado hoje no projeto, com trechos citados do código para facilitar a navegação e auditoria.
