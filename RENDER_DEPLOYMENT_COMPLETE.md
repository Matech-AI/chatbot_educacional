# 🚀 Deploy Completo no Render - DNA da Força AI

## 📋 Visão Geral

Este guia mostra como fazer deploy completo no Render com **3 serviços** usando **Docker** para um sistema profissional:

- 🎨 **Frontend React** (Docker + Nginx)
- 🔧 **API Server** (Docker + Python)
- 🧠 **RAG Server** (Docker + Python)

## 🏗️ Arquitetura

```
Frontend (Docker + Nginx) ←→ API Server (Docker + Python) ←→ RAG Server (Docker + Python)
         ↓                              ↓                              ↓
   Interface React                Autenticação                 Processamento RAG
   Upload de arquivos            Drive sync                  ChromaDB
   Chat interface                Endpoints gerais            Embeddings
```

## 📁 Estrutura de Arquivos

```
projeto/
├── render.yaml                    # Configuração de TODOS os serviços
├── Dockerfile.frontend           # Dockerfile do Frontend
├── nginx.conf                    # Configuração do Nginx
├── .dockerignore                 # Otimização do build frontend
├── backend/
│   ├── Dockerfile.rag           # Dockerfile do RAG Server
│   ├── Dockerfile.api           # Dockerfile do API Server
│   ├── .dockerignore            # Otimização do build backend
│   ├── rag_server.py            # Servidor RAG
│   ├── api_server.py            # Servidor API
│   └── config/
│       └── requirements.txt     # Dependências Python
├── src/                         # Código React
├── package.json                 # Dependências Node.js
└── vite.config.ts              # Configuração Vite
```

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
CORS_ORIGINS=https://dna-forca-frontend.onrender.com
LOG_LEVEL=INFO
```

### **Para o API Server:**

```bash
OPENAI_API_KEY=sua_chave_openai_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
GOOGLE_DRIVE_API_KEY=sua_chave_google_drive_aqui
RAG_SERVER_URL=https://dna-forca-rag-server.onrender.com
CORS_ORIGINS=https://dna-forca-frontend.onrender.com
LOG_LEVEL=INFO
```

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

5. **Erro de Docker:**
   - Verifique se os Dockerfiles estão corretos
   - Confirme se os contextos estão configurados

### **Logs Úteis:**

```bash
# Verificar status de todos os serviços
curl https://dna-forca-frontend.onrender.com
curl https://dna-forca-api-server.onrender.com/health
curl https://dna-forca-rag-server.onrender.com/health
```

## 📊 Monitoramento

- Use os endpoints `/health` para monitoramento
- Configure alertas no Render para downtime
- Monitore os logs regularmente
- Verifique o uso de recursos

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
