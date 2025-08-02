## 🚀 Passos para Deploy

### **1. Preparação do Repositório**

1. **Certifique-se de que o código está no GitHub**
2. **Verifique se todos os arquivos Docker estão presentes:**
   - `render.yaml` (raiz) - Configuração dos serviços
   - `Dockerfile.frontend` - Frontend React
   - `nginx.conf` - Configuração Nginx
   - `backend/Dockerfile.rag` - RAG Server
   - `backend/Dockerfile.api` - API Server

### **2. Deploy no Render**

#### **Opção A: Deploy Automático (Recomendado)**

1. Acesse [render.com](https://render.com)
2. Faça login com GitHub
3. Clique em **"New +"**
4. Selecione **"Blueprint"**
5. Conecte seu repositório
6. O Render detectará automaticamente o arquivo `render.yaml` na raiz

#### **Opção B: Deploy Manual**

1. Crie **3 Web Services** separados
2. Configure cada um para usar Docker conforme especificado abaixo
   - **Servidor RAG**:
     - **Tipo:** Web Service
     - **Porta:** 8001
     - **Build Command:** `pip install -r config/requirements.txt`
     - **Start Command:** `python rag_server.py --host 0.0.0.0 --port $PORT`
   - **Servidor API**:
     - **Tipo:** Web Service
     - **Porta:** 8000
     - **Build Command:** `pip install -r config/requirements.txt`
     - **Start Command:** `python api_server.py --host 0.0.0.0 --port $PORT`
   - **Redis** (Opcional):
     - **Tipo:** Redis
     - **Plano:** Free

### **3. URLs dos Serviços**

Após o deploy, você terá:

- **Frontend**: `https://dna-forca-frontend.onrender.com`
- **API Server**: `https://dna-forca-api-server.onrender.com`
- **RAG Server**: `https://dna-forca-rag-server.onrender.com`

## 🔧 Configuração dos Serviços

### **Arquivo Único (render.yaml na raiz)**

```yaml
services:
  # Frontend React
  - type: web
    name: dna-forca-frontend
    env: docker
    dockerfilePath: ./Dockerfile.frontend
    dockerContext: .
    envVars:
      - key: VITE_API_BASE_URL
        value: https://dna-forca-api-server.onrender.com
      - key: VITE_RAG_BASE_URL
        value: https://dna-forca-rag-server.onrender.com
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
    autoDeploy: true

  # Servidor RAG
  - type: web
    name: dna-forca-rag-server
    env: docker
    dockerfilePath: ./backend/Dockerfile.rag
    dockerContext: ./backend
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: CORS_ORIGINS
        value: https://dna-forca-frontend.onrender.com
    autoDeploy: true

  # Servidor API
  - type: web
    name: dna-forca-api-server
    env: docker
    dockerfilePath: ./backend/Dockerfile.api
    dockerContext: ./backend
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: RAG_SERVER_URL
        value: https://dna-forca-rag-server.onrender.com
      - key: CORS_ORIGINS
        value: https://dna-forca-frontend.onrender.com
    autoDeploy: true
```

## 🐳 Dockerfiles

### **Frontend (Dockerfile.frontend)**

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### **RAG Server (backend/Dockerfile.rag)**

```dockerfile
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y \
    curl build-essential libmagic1 poppler-utils \
    tesseract-ocr tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rag_system/ ./rag_system/
COPY chat_agents/ ./chat_agents/
COPY auth/ ./auth/
COPY utils/ ./utils/
COPY data/ ./data/
COPY config/ ./config/
COPY rag_server.py .

RUN mkdir -p /app/data/.chromadb /app/data/materials /app/logs
EXPOSE 8000
CMD ["python", "rag_server.py"]
```

### **API Server (backend/Dockerfile.api)**

```dockerfile
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y \
    curl build-essential libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY auth/ ./auth/
COPY chat_agents/ ./chat_agents/
COPY drive_sync/ ./drive_sync/
COPY video_processing/ ./video_processing/
COPY maintenance/ ./maintenance/
COPY utils/ ./utils/
COPY data/ ./data/
COPY config/ ./config/
COPY rag_system/ ./rag_system/
COPY api_server.py .

RUN mkdir -p /app/data/materials /app/logs /app/data/.chromadb
EXPOSE 8000
CMD ["python", "api_server.py"]
```

## 🔑 Variáveis de Ambiente

### **Para o Frontend:**

```bash
VITE_API_BASE_URL=https://dna-forca-api-server.onrender.com
VITE_RAG_BASE_URL=https://dna-forca-rag-server.onrender.com
```

### **Para o RAG Server:**

```bash
OPENAI_API_KEY=sua_chave_openai_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
CHROMA_PERSIST_DIR=/app/data/.chromadb
MATERIALS_DIR=/app/data/materials
LOG_LEVEL=INFO
PORT=8001
CORS_ORIGINS=https://dna-forca-frontend.onrender.com,https://chatbot-educacional.vercel.app,http://localhost:3000,http://127.0.0.1:3000
JWT_SECRET_KEY=auto_gerado
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### **Para o API Server:**

```bash
OPENAI_API_KEY=sua_chave_openai_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
GOOGLE_DRIVE_API_KEY=sua_chave_google_drive_aqui
GOOGLE_CREDENTIALS_PATH=/etc/secrets/credentials.json
RAG_SERVER_URL=https://dna-forca-rag-server.onrender.com
DATABASE_URL=postgresql://user:password@localhost/dbname
PORT=8000
JWT_SECRET_KEY=auto_gerado
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=https://dna-forca-frontend.onrender.com,https://chatbot-educacional.vercel.app,http://localhost:3000,http://127.0.0.1:3000
LOG_LEVEL=INFO
CHROMA_PERSIST_DIR=/app/data/.chromadb
MATERIALS_DIR=/app/data/materials
EMAIL_HOST=smtp.seu_provedor.com
EMAIL_PORT=587
EMAIL_USERNAME=seu_email@exemplo.com
EMAIL_PASSWORD=sua_senha_ou_token_app
EMAIL_FROM=seu_email@exemplo.com
```

## 🔒 Configuração de Arquivos Secretos

### **Configurando o arquivo credentials.json para Google Drive API**

1. **No painel do Render:**
   - Acesse seu serviço `dna-forca-api-server`
   - Vá para a aba "Environment"
   - Role até a seção "Secret Files"
   - Clique em "Add Secret File"
   - Configure:
     - **Filename:** `credentials.json`
     - **Contents:** Cole o conteúdo do seu arquivo `credentials.json` do Google Cloud
     - **Mount Path:** `/etc/secrets/credentials.json`

2. **Verifique a variável de ambiente:**
   - Certifique-se de que `GOOGLE_CREDENTIALS_PATH` está configurado como `/etc/secrets/credentials.json`

3. **Após o deploy:**
   - O arquivo `credentials.json` estará disponível no caminho `/etc/secrets/credentials.json`
   - O sistema usará este arquivo para autenticação com a API do Google Drive

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

## 🧪 Teste do Deploy

### **1. Verificar Frontend:**

```bash
curl https://dna-forca-frontend.onrender.com
```

### **2. Verificar API Server:**

```bash
curl https://dna-forca-api-server.onrender.com/health
```

### **3. Verificar RAG Server:**

```bash
curl https://dna-forca-rag-server.onrender.com/health
```

### **4. Verificar Estatísticas do RAG:**

```bash
curl https://dna-forca-rag-server.onrender.com/stats
```

## 🔄 Deploy Automático

Após a configuração inicial:

- **Cada push** para o branch principal fará deploy automático
- **Todos os 3 serviços** serão atualizados automaticamente
- **Zero esforço** para manutenção

## 💰 Custos

- **Frontend**: Gratuito (static site)
- **API Server**: Gratuito (web service)
- **RAG Server**: Gratuito (web service)
- **Total**: 100% gratuito no Render!

## 🐳 Vantagens do Docker

### **Isolamento:**

- Cada serviço roda em seu próprio container
- Dependências isoladas
- Ambiente consistente

### **Performance:**

- Builds otimizados
- Cache de camadas
- Imagens menores

### **Segurança:**

- Containers isolados
- Permissões limitadas
- Menor superfície de ataque

### **Escalabilidade:**

- Fácil replicação
- Load balancing
- Deploy independente

## 🔒 Segurança

1. **Nunca commite chaves de API** no repositório
2. Use variáveis de ambiente para todas as chaves
3. Configure CORS adequadamente
4. Use HTTPS em produção

## 🔧 Troubleshooting

### **Problemas Comuns:**

1. **Erro de CORS:**

   - Verifique se `CORS_ORIGINS` inclui o domínio do frontend
   - Certifique-se de que as URLs estão corretas

2. **Frontend não carrega:**

   - Verifique se o build está funcionando
   - Confirme se as variáveis de ambiente estão configuradas

3. **API não responde:**

   - Verifique os logs no painel do Render
   - Confirme se as chaves de API estão configuradas

4. **RAG não inicializa:**

   - Verifique se `OPENAI_API_KEY` está configurada
   - Aguarde o RAG server inicializar completamente

5. **Erro de comunicação entre serviços:**

   - Verifique se `RAG_SERVER_URL` está correto
   - Aguarde o RAG server inicializar completamente

6. **Erro de dependências:**

   - Verifique se `requirements.txt` está atualizado
   - Verifique os logs de build

7. **Erro de Docker:**
   - Verifique se os Dockerfiles estão corretos
   - Confirme se os contextos estão configurados

### **Logs Úteis:**

```bash
# Verificar status de todos os serviços
curl https://dna-forca-frontend.onrender.com
curl https://dna-forca-api-server.onrender.com/health
curl https://dna-forca-rag-server.onrender.com/health
curl https://dna-forca-rag-server.onrender.com/stats
```

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

## 🎉 Resultado Final

Após o deploy, você terá:

- ✅ **Frontend** rodando no Render com Docker + Nginx (gratuito)
- ✅ **API Server** rodando no Render com Docker + Python (gratuito)
- ✅ **RAG Server** rodando no Render com Docker + Python (gratuito)
- ✅ **Deploy automático** a cada push
- ✅ **Zero custos** mensais
- ✅ **Sistema profissional** com isolamento e segurança

## 📞 Suporte

- Logs detalhados no painel do Render
- Documentação da API em `/docs`
- Endpoints de health check para monitoramento
- Deploy automático para atualizações

---

**🎯 Resumo:** Com essa configuração Docker, você terá um sistema completo e profissional rodando no Render de forma gratuita e com deploy automático!
