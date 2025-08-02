# 🧠 DNA da Força AI - Backend

Sistema de IA educacional especializado em Educação Física, com processamento RAG (Retrieval-Augmented Generation) e integração com Google Drive.

## 🏗️ Arquitetura

```
backend/
├── auth/                     # Autenticação e Gerenciamento de Usuários
│   ├── __init__.py
│   ├── auth.py              # Sistema principal de autenticação
│   ├── auth_token_manager.py # Gerenciamento de tokens
│   ├── user_management.py   # Gerenciamento de usuários
│   ├── external_id_manager.py # Gerenciamento de IDs externos
│   └── email_service.py     # Serviços de email
│
├── drive_sync/              # Sincronização com Google Drive
│   ├── __init__.py
│   ├── drive_handler.py     # Handler básico do Google Drive
│   └── drive_handler_recursive.py # Handler recursivo avançado
│
├── rag_system/              # Sistema RAG (Retrieval Augmented Generation)
│   ├── __init__.py
│   ├── rag_handler.py       # Handler principal do RAG
│   └── enhanced_rag_handler.py # Handler RAG aprimorado
│
├── chat_agents/             # Agentes de Chat e IA
│   ├── __init__.py
│   ├── chat_agent.py        # Agente de chat básico
│   └── educational_agent.py # Agente educacional avançado
│
├── video_processing/        # Processamento de Vídeo
│   ├── __init__.py
│   └── video_handler.py     # Handler de processamento de vídeo
│
├── tests/                   # Testes
│   ├── __init__.py
│   ├── test_recursive_drive.py # Testes do drive recursivo
│   └── drive_test_script.py # Scripts de teste do drive
│
├── maintenance/             # Manutenção do Sistema
│   ├── __init__.py
│   └── maintenance_endpoints.py # Endpoints de manutenção
│
├── utils/                   # Utilitários
│   ├── __init__.py
│   └── *.log               # Arquivos de log
│
├── config/                  # Configurações
│   ├── __init__.py
│   ├── requirements.txt    # Dependências Python
│   ├── start_backend.py    # Script de inicialização
│   └── start.sh           # Script de inicialização (Linux/Mac)
│
├── data/                    # Dados do Sistema
│   ├── users_db.json       # Banco de dados de usuários
│   ├── approved_users.json # Usuários aprovados
│   ├── auth_tokens.json    # Tokens de autenticação
│   ├── external_id_counter.json # Contador de IDs externos
│   ├── video_analysis_cache.json # Cache de análise de vídeo
│   └── users.json          # Dados de usuários (legado)
│
├── main.py                  # Aplicação principal FastAPI
├── backup/                  # Backups do sistema
├── .chromadb/              # Banco de dados ChromaDB
└── .venv/                  # Ambiente virtual Python
```

## 🚀 Deploy Rápido

### Pré-requisitos

1. **Docker e Docker Compose**
   ```bash
   # Verificar instalação
   docker --version
   docker-compose --version
   ```

2. **Variáveis de Ambiente**
   - Copie `env.example` para `.env`
   - Configure suas chaves de API

### Deploy Local

#### Usando Scripts Automatizados

**Linux/Mac:**
```bash
# Deploy completo
./scripts/deploy.sh deploy

# Verificar status
./scripts/deploy.sh status

# Ver logs
./scripts/deploy.sh logs rag-server
./scripts/deploy.sh logs api-server
```

**Windows:**
```cmd
# Deploy completo
scripts\deploy.bat deploy

# Verificar status
scripts\deploy.bat status

# Ver logs
scripts\deploy.bat logs rag-server
scripts\deploy.bat logs api-server
```

#### Usando Docker Compose Diretamente

```bash
# Construir e iniciar todos os serviços
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f rag-server
docker-compose logs -f api-server

# Parar serviços
docker-compose down
```

### Deploy no Render

1. **Criar conta no Render**
   - Acesse [render.com](https://render.com)
   - Crie uma conta gratuita

2. **Configurar Serviços**

   **Servidor RAG:**
   - Tipo: Web Service
   - Build Command: `docker build -f Dockerfile.rag -t rag-server .`
   - Start Command: `python rag_server.py --host 0.0.0.0 --port $PORT`
   - Porta: 8000
   - Variáveis de ambiente: Configure todas as chaves de API

   **Servidor API:**
   - Tipo: Web Service
   - Build Command: `docker build -f Dockerfile.api -t api-server .`
   - Start Command: `python api_server.py --host 0.0.0.0 --port $PORT`
   - Porta: 8000
   - Variáveis de ambiente: Configure todas as chaves de API

3. **Configurar Rede**
   - Use variáveis de ambiente para comunicação entre serviços
   - Configure `RAG_SERVER_URL` no servidor API

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` baseado no `env.example`:

```env
# Configurações da API
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_DRIVE_API_KEY=your_google_drive_api_key_here

# Configurações do servidor RAG
RAG_SERVER_URL=http://rag-server:8000
CHROMA_PERSIST_DIR=/app/data/.chromadb
MATERIALS_DIR=/app/data/materials

# Configurações de autenticação
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configurações de CORS
CORS_ORIGINS=https://chatbot-educacional.vercel.app,http://localhost:3000,http://127.0.0.1:3000,https://dna-forca-frontend.vercel.app

# Configurações de logging
LOG_LEVEL=INFO
```

## 🔌 Endpoints

### Servidor RAG (Porta 8001)

| Endpoint             | Método | Descrição                         |
| -------------------- | ------ | --------------------------------- |
| `/health`            | GET    | Verificar saúde do servidor       |
| `/status`            | GET    | Status detalhado do sistema       |
| `/process-materials` | POST   | Processar materiais em background |
| `/query`             | POST   | Realizar consulta RAG             |
| `/initialize`        | POST   | Inicializar RAG handler           |
| `/reset`             | POST   | Resetar RAG handler               |
| `/stats`             | GET    | Estatísticas do sistema           |
| `/chat`              | POST   | Chat básico                       |
| `/chat-auth`         | POST   | Chat autenticado                  |

### Servidor API (Porta 8000)

| Endpoint             | Método | Descrição                   |
| -------------------- | ------ | --------------------------- |
| `/`                  | GET    | Informações do sistema      |
| `/health`            | GET    | Verificar saúde do servidor |
| `/status`            | GET    | Status detalhado            |
| `/chat`              | POST   | Chat básico                 |
| `/chat-auth`         | POST   | Chat autenticado            |
| `/auth/*`            | \*     | Endpoints de autenticação   |
| `/drive/*`           | \*     | Endpoints do Google Drive   |
| `/materials/*`       | \*     | Gerenciamento de materiais  |
| `/initialize-rag`    | POST   | Inicializar RAG via API     |
| `/process-materials` | POST   | Processar materiais via API |

## 🔄 Comunicação Entre Servidores

### API Server → RAG Server

O servidor API se comunica com o servidor RAG através de HTTP requests:

```python
# Exemplo de comunicação
async with aiohttp.ClientSession() as session:
    async with session.post(
        f"{RAG_SERVER_URL}/query",
        json={
            "question": "Pergunta do usuário",
            "material_ids": None,
            "config": None
        }
    ) as response:
        result = await response.json()
```

## 📊 Monitoramento

### Health Checks

Ambos os servidores implementam health checks:

```bash
# Verificar servidor RAG
curl http://localhost:8001/health

# Verificar servidor API
curl http://localhost:8000/health
```

### Logs

```bash
# Logs do servidor RAG
docker-compose logs -f rag-server

# Logs do servidor API
docker-compose logs -f api-server

# Todos os logs
docker-compose logs -f
```

## 🔒 Segurança

### Variáveis de Ambiente

- Todas as chaves de API são configuradas via variáveis de ambiente
- Arquivo `.env` não deve ser commitado no repositório

### CORS

- Configurado para permitir apenas origens específicas
- Em produção, configure `CORS_ORIGINS` adequadamente

### Autenticação

- JWT tokens para autenticação
- Tokens expiram automaticamente
- Senhas são hasheadas com bcrypt

## 🚨 Troubleshooting

### Problemas Comuns

1. **Servidor RAG não responde**

   ```bash
   # Verificar se o container está rodando
   docker-compose ps

   # Verificar logs
   docker-compose logs rag-server

   # Reiniciar serviço
   docker-compose restart rag-server
   ```

2. **Erro de comunicação entre servidores**

   ```bash
   # Verificar rede
   docker network ls
   docker network inspect dna-forca-network

   # Verificar variável RAG_SERVER_URL
   docker-compose exec api-server env | grep RAG_SERVER_URL
   ```

3. **Problemas de volume**

   ```bash
   # Verificar volumes
   docker volume ls

   # Limpar volumes (cuidado!)
   docker-compose down -v
   ```

### Logs de Debug

Para habilitar logs detalhados, configure `LOG_LEVEL=DEBUG` no arquivo `.env`.

## 📈 Escalabilidade

### Horizontal Scaling

Para escalar horizontalmente:

1. **Servidor RAG**: Pode ser replicado com load balancer
2. **Servidor API**: Pode ser replicado com load balancer
3. **Redis**: Use Redis Cluster para alta disponibilidade

### Vertical Scaling

Ajuste recursos no `docker-compose.yml`:

```yaml
services:
  rag-server:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: "2.0"
```

## 🔄 CI/CD

### GitHub Actions (Exemplo)

```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Render
        uses: johnbeynon/render-deploy-action@v1.0.0
        with:
          service-id: ${{ secrets.RENDER_SERVICE_ID }}
          api-key: ${{ secrets.RENDER_API_KEY }}
```

## 📞 Suporte

Para problemas ou dúvidas:

1. Verifique os logs dos containers
2. Consulte a documentação do FastAPI
3. Verifique as configurações de rede
4. Teste a conectividade entre serviços

## 🎯 Próximos Passos

1. **Implementar monitoramento avançado** (Prometheus/Grafana)
2. **Adicionar testes automatizados**
3. **Implementar backup automático dos dados**
4. **Configurar CDN para arquivos estáticos**
5. **Implementar rate limiting**
6. **Adicionar autenticação entre serviços**
