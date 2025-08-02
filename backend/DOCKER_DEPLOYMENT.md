# 🐳 Dockerização e Paralelização - DNA da Força AI

## 📋 Visão Geral

Este documento descreve a solução de Dockerização e paralelização do sistema DNA da Força AI, dividindo o backend em dois servidores independentes para melhor performance e escalabilidade.

## 🏗️ Arquitetura

### Servidor A: RAG Server (Porta 8001)

- **Função**: Processamento de materiais e treinamento de modelos
- **Status**: Sempre rodando
- **Responsabilidades**:
  - Processamento de documentos (PDF, Excel, etc.)
  - Geração de embeddings
  - Armazenamento no ChromaDB
  - Consultas RAG
  - Treinamento de modelos

### Servidor B: API Geral (Porta 8000)

- **Função**: Funcionalidades gerais do sistema
- **Status**: Ativo quando necessário
- **Responsabilidades**:
  - Autenticação de usuários
  - Chatbot (comunica com RAG Server)
  - Sincronização do Google Drive
  - Upload/download de materiais
  - Gerenciamento de usuários
  - Endpoints de manutenção

### Redis (Porta 6379)

- **Função**: Cache e sessões (opcional)
- **Status**: Sempre rodando
- **Responsabilidades**:
  - Cache de sessões
  - Cache de consultas
  - Filas de processamento

## 📁 Estrutura de Arquivos

```
backend/
├── docker-compose.yml          # Orquestração dos serviços
├── Dockerfile.rag             # Imagem do servidor RAG
├── Dockerfile.api             # Imagem do servidor API
├── rag_server.py              # Servidor RAG independente
├── api_server.py              # Servidor API geral
├── env.example                # Exemplo de variáveis de ambiente
├── scripts/
│   ├── deploy.sh              # Script de deploy (Linux/Mac)
│   └── deploy.bat             # Script de deploy (Windows)
├── rag_system/                # Componentes RAG
├── auth/                      # Autenticação
├── chat_agents/               # Agentes de chat
├── drive_sync/                # Sincronização do Drive
├── video_processing/          # Processamento de vídeo
├── maintenance/               # Manutenção
├── utils/                     # Utilitários
└── data/                      # Dados persistentes
```

## 🚀 Deploy

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
./scripts/deploy.sh logs rag
./scripts/deploy.sh logs api
```

**Windows:**

```cmd
# Deploy completo
scripts\deploy.bat deploy

# Verificar status
scripts\deploy.bat status

# Ver logs
scripts\deploy.bat logs rag
scripts\deploy.bat logs api
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
   - Start Command: `python rag_server.py`
   - Porta: 8000
   - Variáveis de ambiente: Configure todas as chaves de API

   **Servidor API:**

   - Tipo: Web Service
   - Build Command: `docker build -f Dockerfile.api -t api-server .`
   - Start Command: `python api_server.py`
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
GOOGLE_CREDENTIALS_PATH=/app/data/credentials.json

# Configurações do servidor RAG
RAG_SERVER_URL=http://rag-server:8000
CHROMA_PERSIST_DIR=/app/data/.chromadb
MATERIALS_DIR=/app/data/materials

# Configurações de autenticação
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configurações de CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Configurações de logging
LOG_LEVEL=INFO

# Configurações de Email
EMAIL_HOST=smtp.seu_provedor.com
EMAIL_PORT=587
EMAIL_USERNAME=seu_email@exemplo.com
EMAIL_PASSWORD=sua_senha_ou_token_app
EMAIL_FROM=seu_email@exemplo.com
```

### Configuração do Google Drive API

Para o funcionamento correto da integração com o Google Drive, você precisa:

1. **Arquivo de credenciais:**
   - Coloque seu arquivo `credentials.json` do Google Cloud na pasta `data/` do projeto
   - Certifique-se de que o caminho corresponde ao definido em `GOOGLE_CREDENTIALS_PATH`
   - Para desenvolvimento local: `/app/data/credentials.json`
   - Para Render: `/etc/secrets/credentials.json`

2. **Montagem de volume:**
   - O Docker Compose já configura o volume `api_data` que mapeia para `/app/data`
   - Coloque o arquivo `credentials.json` neste volume para persistência

3. **Primeira execução:**
   - Na primeira execução, o sistema pode solicitar autenticação OAuth2
   - Siga as instruções no console para autenticar
   - O token será salvo como `token.json` no mesmo diretório

### Volumes Docker

Os seguintes volumes são criados automaticamente:

- `rag_data`: Dados do servidor RAG (ChromaDB, materiais)
- `api_data`: Dados do servidor API (uploads, cache)
- `redis_data`: Dados do Redis

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

### Configuração de Rede

No `docker-compose.yml`, os serviços se comunicam através da rede `dna-forca-network`:

```yaml
networks:
  dna-forca-network:
    driver: bridge
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

### Métricas

- **Uptime**: Monitorado via `/status`
- **Performance**: Tempo de resposta das consultas RAG
- **Erros**: Logs estruturados com níveis de severidade

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
