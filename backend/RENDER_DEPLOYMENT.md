# 🚀 Deploy no Render - DNA da Força AI

## 📋 Pré-requisitos

1. **Conta no Render** (gratuita)
2. **Chaves de API configuradas:**
   - OpenAI API Key
   - Gemini API Key (opcional)
   - Google Drive API Key (opcional)

## 🔧 Configuração dos Serviços

### 1. **Servidor RAG** (`dna-forca-rag-server`)

- **Tipo:** Web Service
- **Porta:** 8001
- **Build Command:** `pip install -r config/requirements.txt`
- **Start Command:** `python rag_server.py --host 0.0.0.0 --port $PORT`

### 2. **Servidor API** (`dna-forca-api-server`)

- **Tipo:** Web Service
- **Porta:** 8000
- **Build Command:** `pip install -r config/requirements.txt`
- **Start Command:** `python api_server.py --host 0.0.0.0 --port $PORT`

### 3. **Redis** (Opcional)

- **Tipo:** Redis
- **Plano:** Free

## 🔑 Variáveis de Ambiente

### Para o RAG Server:

```bash
OPENAI_API_KEY=sua_chave_openai_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
CHROMA_PERSIST_DIR=/opt/render/project/src/data/.chromadb
MATERIALS_DIR=/opt/render/project/src/data/materials
LOG_LEVEL=INFO
PORT=8001
CORS_ORIGINS=https://chatbot-educacional.vercel.app,http://localhost:3000,http://127.0.0.1:3000,https://dna-forca-frontend.vercel.app
JWT_SECRET_KEY=auto_gerado
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Para o API Server:

```bash
OPENAI_API_KEY=sua_chave_openai_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
GOOGLE_DRIVE_API_KEY=sua_chave_google_drive_aqui
RAG_SERVER_URL=https://dna-forca-rag-server.onrender.com
DATABASE_URL=postgresql://user:password@localhost/dbname
PORT=8000
JWT_SECRET_KEY=auto_gerado
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=https://chatbot-educacional.vercel.app,http://localhost:3000,http://127.0.0.1:3000,https://dna-forca-frontend.vercel.app
LOG_LEVEL=INFO
CHROMA_PERSIST_DIR=/opt/render/project/src/data/.chromadb
MATERIALS_DIR=/opt/render/project/src/data/materials
```

## 📁 Estrutura de Arquivos

```
backend/
├── render.yaml              # Configuração automática do Render
├── rag_server.py            # Servidor RAG
├── api_server.py            # Servidor API
├── config/
│   └── requirements.txt     # Dependências Python
├── rag_system/              # Sistema RAG
├── chat_agents/             # Agentes de chat
├── auth/                    # Autenticação
├── utils/                   # Utilitários
├── data/                    # Dados e materiais
└── Dockerfile.*            # Dockerfiles (para referência)
```

## 🚀 Passos para Deploy

### Opção 1: Deploy Automático (Recomendado)

1. Conecte seu repositório GitHub ao Render
2. O arquivo `render.yaml` configurará automaticamente os serviços
3. Configure as variáveis de ambiente no painel do Render

### Opção 2: Deploy Manual

1. Crie um novo Web Service no Render
2. Conecte ao repositório GitHub
3. Configure as variáveis de ambiente
4. Use os comandos de build e start especificados acima

## 🔍 Endpoints Disponíveis

### RAG Server (Porta 8001):

- `GET /health` - Status do servidor
- `GET /status` - Status detalhado
- `GET /stats` - Estatísticas do RAG
- `POST /initialize` - Inicializar RAG
- `POST /query` - Consulta RAG
- `POST /chat` - Chat simples
- `POST /chat/agent` - Chat com agente
- `POST /process-materials` - Processar materiais

### API Server (Porta 8000):

- `GET /health` - Status do servidor
- `GET /docs` - Documentação Swagger
- `POST /auth/login` - Login
- `POST /auth/register` - Registro
- `POST /chat` - Chat via API
- `GET /drive/sync` - Sincronizar Google Drive
- `POST /materials/upload` - Upload de materiais

## 🔧 Troubleshooting

### Problemas Comuns:

1. **Erro de CORS:**

   - Verifique se `CORS_ORIGINS` está configurado corretamente
   - Inclua o domínio do frontend no Vercel

2. **RAG Server não inicializa:**

   - Verifique se `OPENAI_API_KEY` está configurada
   - Verifique os logs no painel do Render

3. **Erro de comunicação entre serviços:**

   - Verifique se `RAG_SERVER_URL` está correto
   - Aguarde o RAG server inicializar completamente

4. **Erro de dependências:**
   - Verifique se `requirements.txt` está atualizado
   - Verifique os logs de build

### Logs Úteis:

```bash
# Verificar status do RAG server
curl https://dna-forca-rag-server.onrender.com/health

# Verificar status da API
curl https://dna-forca-api-server.onrender.com/health

# Verificar estatísticas do RAG
curl https://dna-forca-rag-server.onrender.com/stats
```

## 🔒 Segurança

1. **Nunca commite chaves de API** no repositório
2. Use variáveis de ambiente para todas as chaves
3. Configure CORS adequadamente
4. Use HTTPS em produção

## 📊 Monitoramento

- Use os endpoints `/health` para monitoramento
- Configure alertas no Render para downtime
- Monitore os logs regularmente
- Verifique o uso de recursos

## 🔄 Atualizações

1. Push para o branch principal
2. O Render fará deploy automático
3. Verifique os logs após o deploy
4. Teste os endpoints principais

## 📞 Suporte

- Logs detalhados no painel do Render
- Documentação da API em `/docs`
- Endpoints de health check para monitoramento
