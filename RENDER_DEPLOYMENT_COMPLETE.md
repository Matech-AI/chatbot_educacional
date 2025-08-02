# 🚀 Deploy Completo no Render - DNA da Força AI

## 📋 Visão Geral

Este guia mostra como fazer deploy completo no Render com **3 serviços**:

- 🎨 **Frontend React** (gratuito)
- 🔧 **API Server** (gratuito)
- 🧠 **RAG Server** (gratuito)

## 🏗️ Arquitetura

```
Frontend (Render) ←→ API Server (Render) ←→ RAG Server (Render)
     ↓                      ↓                      ↓
Interface React        Autenticação         Processamento RAG
Upload de arquivos    Drive sync          ChromaDB
Chat interface        Endpoints gerais    Embeddings
```

## 📁 Estrutura de Arquivos

```
projeto/
├── render.yaml                    # Configuração frontend
├── backend/
│   ├── render.yaml               # Configuração backend
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
2. **Verifique se os arquivos estão corretos:**
   - `render.yaml` (raiz) - Frontend
   - `backend/render.yaml` - Backend

### **2. Deploy no Render**

#### **Opção A: Deploy Automático (Recomendado)**

1. Acesse [render.com](https://render.com)
2. Faça login com GitHub
3. Clique em **"New +"**
4. Selecione **"Blueprint"**
5. Conecte seu repositório
6. O Render detectará automaticamente os arquivos `render.yaml`

#### **Opção B: Deploy Manual**

1. Crie **3 Web Services** separados
2. Configure cada um conforme especificado abaixo

### **3. URLs dos Serviços**

Após o deploy, você terá:

- **Frontend**: `https://dna-forca-frontend.onrender.com`
- **API Server**: `https://dna-forca-api-server.onrender.com`
- **RAG Server**: `https://dna-forca-rag-server.onrender.com`

## 🔧 Configuração dos Serviços

### **Frontend (render.yaml na raiz)**

```yaml
services:
  - type: web
    name: dna-forca-frontend
    env: static
    buildCommand: npm install && npm run build
    staticPublishPath: ./dist
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
```

### **Backend (backend/render.yaml)**

```yaml
services:
  # RAG Server
  - type: web
    name: dna-forca-rag-server
    env: python
    buildCommand: pip install -r config/requirements.txt
    startCommand: python rag_server.py --host 0.0.0.0 --port $PORT
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: CORS_ORIGINS
        value: https://dna-forca-frontend.onrender.com
    autoDeploy: true

  # API Server
  - type: web
    name: dna-forca-api-server
    env: python
    buildCommand: pip install -r config/requirements.txt
    startCommand: python api_server.py --host 0.0.0.0 --port $PORT
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: RAG_SERVER_URL
        value: https://dna-forca-rag-server.onrender.com
      - key: CORS_ORIGINS
        value: https://dna-forca-frontend.onrender.com
    autoDeploy: true
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
CHROMA_PERSIST_DIR=/opt/render/project/src/data/.chromadb
MATERIALS_DIR=/opt/render/project/src/data/materials
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

- ✅ **Frontend** rodando no Render (gratuito)
- ✅ **API Server** rodando no Render (gratuito)
- ✅ **RAG Server** rodando no Render (gratuito)
- ✅ **Deploy automático** a cada push
- ✅ **Zero custos** mensais

## 📞 Suporte

- Logs detalhados no painel do Render
- Documentação da API em `/docs`
- Endpoints de health check para monitoramento
- Deploy automático para atualizações

---

**🎯 Resumo:** Com essa configuração, você terá todo o sistema rodando no Render de forma gratuita e com deploy automático!
