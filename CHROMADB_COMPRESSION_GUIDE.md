# 🗄️ Guia de Compactação Local do ChromaDB

## 📋 Visão Geral

Este guia documenta a funcionalidade implementada para **compactar pastas `.chromadb` locais** e fazer **upload automático para servidores Render**. A funcionalidade permite que usuários sincronizem seus dados locais com servidores de produção de forma simples e eficiente.

## 🎯 Funcionalidades Implementadas

### 1. **Compactação Local** (`/chromadb/compress-local`)

- Compacta pasta `.chromadb` local em arquivo `.tar.gz`
- Busca automática da pasta em diferentes localizações
- Validação de integridade dos dados
- Download automático do arquivo compactado

### 2. **Compactação com Caminho Específico** (`/chromadb/compress-local-path`)

- Permite especificar o caminho exato da pasta `.chromadb`
- Validação completa do caminho fornecido
- Logs detalhados para debug
- Compactação da pasta inteira (não apenas entrada)

### 3. **Upload Automático para Servidor** (Integrado)

- Compactação local + upload automático em uma operação
- Atualização automática do servidor Render
- Reinicialização automática do RAG handler
- Feedback em tempo real do processo

## 🔧 Implementação Técnica

### Backend - Endpoints

#### `POST /chromadb/compress-local`

```python
@app.post("/chromadb/compress-local")
async def compress_local_chromadb_folder(request: CompressLocalRequest):
    """Compactar pasta .chromadb local em arquivo .tar.gz"""
```

**Características:**

- Busca automática em múltiplos caminhos possíveis
- Validação de integridade via ChromaDB client
- Geração de arquivo `.tar.gz` temporário
- Streaming response para download

#### `POST /chromadb/compress-local-path`

```python
@app.post("/chromadb/compress-local-path")
async def compress_local_chromadb_folder_by_path(request: CompressLocalRequest):
    """Compactar pasta .chromadb local especificando caminho completo"""
```

**Características:**

- Caminho específico fornecido pelo usuário
- Validação rigorosa do caminho
- Verificação de nome da pasta (`.chromadb`)
- Tratamento de erros detalhado

### Frontend - Componentes

#### Botões Disponíveis

1. **"Compactar Local"** (Roxo)

   - Apenas compactação e download
   - Não faz upload automático

2. **"Compactar + Upload"** (Roxo Escuro)
   - Compactação + upload automático para servidor
   - Funcionalidade principal implementada

#### Funções Principais

```typescript
// Compactação local com caminho personalizado
const handleCompressLocalChromaDB = async () => {
  const chromaPath = prompt("Digite o caminho completo da pasta .chromadb:");
  // ... lógica de compactação
};

// Compactação + upload automático
const handleCompressAndUploadLocalChromaDB = async () => {
  // 1. Compactar pasta local
  // 2. Upload automático para servidor
  // 3. Atualizar status
};
```

## 🚀 Como Usar

### Passo a Passo

1. **Acesse a página de Materiais**

   - Navegue para a seção de sincronização ChromaDB

2. **Clique em "Compactar + Upload"**

   - Botão roxo escuro com ícone de upload

3. **Digite o caminho da pasta `.chromadb`**

   - **Windows**: `C:\projetos\.chromadb`
   - **Linux/Mac**: `/home/usuario/.chromadb`
   - **Exemplo específico**: `C:\repos_github\projetos_matheus\Dashs_BD_IA\chatbot_educacao_fisica\backend\.chromadb`

4. **Aguarde o processo automático**
   - Sistema compacta pasta local
   - Faz upload para servidor Render
   - Atualiza status automaticamente

### Exemplos de Caminhos

#### Windows

```
C:\projetos\.chromadb
C:\Users\usuario\.chromadb
C:\repos_github\projeto\.chromadb
```

#### Linux/Mac

```
/home/usuario/.chromadb
/opt/projetos/.chromadb
/var/lib/chromadb/.chromadb
```

## ⚙️ Configuração

### Variáveis de Ambiente

#### Frontend (`.env`)

##### **Desenvolvimento Local**

```bash
# Frontend Environment Variables (LOCAL)
VITE_API_URL=http://localhost:8000
VITE_RAG_API_BASE_URL=http://localhost:8001
```

##### **Produção (Render)**

```bash
# Frontend Environment Variables (PRODUÇÃO)
VITE_API_URL=https://dna-forca-api-server.onrender.com
VITE_RAG_API_BASE_URL=https://dna-forca-rag-server.onrender.com
```

#### Backend (`.env`)

##### **Desenvolvimento Local**

```bash
# Configurações do servidor RAG (LOCAL)
RAG_SERVER_URL=http://localhost:8001

# Rotas das pastas locais
CHROMA_PERSIST_DIR=C:/repos_github/projetos_matheus/Dashs_BD_IA/chatbot_educacao_fisica/backend/data/.chromadb
MATERIALS_DIR=C:/repos_github/projetos_matheus/Dashs_BD_IA/backend/data/materials
```

##### **Produção (Render)**

```bash
# Configurações do servidor RAG (PRODUÇÃO)
RAG_SERVER_URL=https://dna-forca-rag-server.onrender.com
CHROMA_PERSIST_DIR=/app/data/.chromadb
MATERIALS_DIR=/app/data/materials
```

### Estrutura de URLs por Ambiente

| Ambiente   | Frontend                                  | API Server                                  | RAG Server                                  | ChromaDB Path            |
| ---------- | ----------------------------------------- | ------------------------------------------- | ------------------------------------------- | ------------------------ |
| **Local**  | `http://localhost:3000`                   | `http://localhost:8000`                     | `http://localhost:8001`                     | `backend/data/.chromadb` |
| **Render** | `https://dna-forca-frontend.onrender.com` | `https://dna-forca-api-server.onrender.com` | `https://dna-forca-rag-server.onrender.com` | `/app/data/.chromadb`    |

### Configuração do Render (render.yaml)

```yaml
services:
  - type: web
    name: dna-forca-frontend
    envVars:
      - key: VITE_API_URL
        value: "https://dna-forca-api-server.onrender.com"
      - key: VITE_RAG_API_BASE_URL
        value: "https://dna-forca-rag-server.onrender.com"

  - type: web
    name: dna-forca-api-server
    envVars:
      - key: API_SERVER_URL
        value: "https://dna-forca-api-server.onrender.com"
      - key: RAG_SERVER_URL
        value: "https://dna-forca-rag-server.onrender.com"

  - type: web
    name: dna-forca-rag-server
    envVars:
      - key: RAG_SERVER_URL
        value: "https://dna-forca-rag-server.onrender.com"
      - key: CHROMA_PERSIST_DIR
        value: "/app/data/.chromadb"
      - key: MATERIALS_DIR
        value: "/app/data/materials"
```

### Fluxo de Funcionamento por Ambiente

#### **Desenvolvimento Local**

```
Pasta .chromadb Local → Compactação → .tar.gz → Upload → backend/data/.chromadb → Reinicialização RAG
```

#### **Produção (Render)**

```
Pasta .chromadb Local → Compactação → .tar.gz → Upload → /app/data/.chromadb → Reinicialização RAG
```

## 📁 Estrutura de Arquivos

### Backend

```
backend/
├── rag_server.py                    # Servidor RAG com endpoints
├── .env                            # Configurações de ambiente
├── data/
│   ├── .chromadb/                  # ChromaDB local
│   └── materials/                  # Materiais de treinamento
└── rag_system/
    └── rag_handler.py              # Lógica RAG
```

### Frontend

```
src/
├── components/
│   └── materials/
│       └── chromadb-upload.tsx    # Componente principal
├── lib/
│   └── api.ts                      # Funções de API
└── .env                            # Variáveis de ambiente
```

## 🔄 Fluxo de Funcionamento

### 1. Compactação Local

```
Usuário especifica caminho → Validação → Conexão ChromaDB → Compactação → .tar.gz
```

### 2. Upload para Servidor

```
Arquivo .tar.gz → Upload Render → Extração → /app/data/.chromadb → Reinicialização RAG
```

### 3. Resultado Final

```
Servidor atualizado → ChromaDB funcional → RAG handler ativo → Sistema operacional
```

## 📊 Endpoints Disponíveis

| Endpoint                        | Método | Descrição                                  | Servidor   |
| ------------------------------- | ------ | ------------------------------------------ | ---------- |
| `/chromadb/upload`              | POST   | Upload de arquivo .tar.gz                  | RAG (8001) |
| `/chromadb/upload-folder`       | POST   | Upload de pasta .zip                       | RAG (8001) |
| `/chromadb/download`            | GET    | Download do ChromaDB                       | RAG (8001) |
| `/chromadb/compress`            | POST   | Compactar ChromaDB ativo                   | RAG (8001) |
| `/chromadb/compress-local`      | POST   | Compactar pasta local (busca automática)   | RAG (8001) |
| `/chromadb/compress-local-path` | POST   | Compactar pasta local (caminho específico) | RAG (8001) |
| `/chromadb/status`              | GET    | Status do ChromaDB                         | RAG (8001) |

## 🛠️ Troubleshooting

### Problemas Comuns

#### 1. Erro 404 - Endpoint não encontrado

**Causa**: Variável de ambiente incorreta
**Solução**: Verificar arquivo `.env` e reiniciar frontend

**Verificação por ambiente:**

```bash
# Local
VITE_RAG_API_BASE_URL=http://localhost:8001

# Produção (Render)
VITE_RAG_API_BASE_URL=https://dna-forca-rag-server.onrender.com
```

#### 2. Pasta .chromadb não encontrada

**Causa**: Caminho incorreto ou pasta inexistente
**Solução**: Verificar caminho e usar caminho absoluto

#### 3. Erro de conexão

**Causa Local**: Servidor RAG não está rodando
**Solução Local**: Verificar se servidor está ativo na porta 8001

**Causa Produção**: Servidor Render não está respondendo
**Solução Produção**:

- Verificar status dos serviços no dashboard do Render
- Confirmar se as variáveis de ambiente estão configuradas
- Verificar logs do servidor no Render

#### 4. Erro de CORS (Produção)

**Causa**: Configuração de CORS incorreta no servidor
**Solução**: Verificar se `CORS_ORIGINS` inclui o domínio do frontend

```bash
# Backend .env (Produção)
CORS_ORIGINS=https://dna-forca-frontend.onrender.com,http://localhost:3000
```

#### 5. Timeout de Conexão (Produção)

**Causa**: Servidor Render demorando para responder
**Solução**:

- Verificar se o servidor não está "dormindo" (Render free tier)
- Aguardar primeira requisição para "acordar" o servidor
- Considerar upgrade para plano pago se necessário

### Logs de Debug

#### Backend

##### **Local**

```bash
📦 Compactando pasta local: C:\projetos\.chromadb
✅ Pasta .chromadb encontrada em: C:\projetos\.chromadb
📊 Pasta local contém 3 coleções com 150 documentos
✅ Arquivo .tar.gz criado: 45.67 MB
```

##### **Produção (Render)**

```bash
📦 Compactando pasta local: /app/data/.chromadb
✅ Pasta .chromadb encontrada em: /app/data/.chromadb
📊 Pasta local contém 5 coleções com 300 documentos
✅ Arquivo .tar.gz criado: 67.89 MB
```

#### Frontend

##### **Verificar Variáveis de Ambiente**

```typescript
// Verificar variáveis de ambiente
console.log("VITE_RAG_API_BASE_URL:", import.meta.env.VITE_RAG_API_BASE_URL);
console.log("VITE_API_URL:", import.meta.env.VITE_API_URL);

// Verificar se está apontando para produção
if (import.meta.env.VITE_RAG_API_BASE_URL.includes("onrender.com")) {
  console.log("✅ Configurado para PRODUÇÃO (Render)");
} else {
  console.log("🔄 Configurado para DESENVOLVIMENTO LOCAL");
}
```

##### **Testar Conectividade**

```typescript
// Testar se o servidor está respondendo
const testConnection = async () => {
  try {
    const response = await fetch(
      `${import.meta.env.VITE_RAG_API_BASE_URL}/chromadb/status`
    );
    if (response.ok) {
      console.log("✅ Servidor RAG respondendo");
    } else {
      console.log("❌ Servidor RAG com erro:", response.status);
    }
  } catch (error) {
    console.log("❌ Erro de conexão:", error);
  }
};
```

## 🧪 Testando em Produção (Render)

### Preparação para Teste

#### **1. Verificar Configuração**

- Confirmar se todos os serviços estão rodando no Render
- Verificar se as variáveis de ambiente estão configuradas
- Confirmar se as chaves API estão válidas

#### **2. Testar Conectividade**

```typescript
// No console do navegador (frontend do Render)
const testRenderConnection = async () => {
  try {
    const response = await fetch(
      "https://dna-forca-rag-server.onrender.com/chromadb/status"
    );
    if (response.ok) {
      console.log("✅ Servidor RAG do Render respondendo");
      const data = await response.json();
      console.log("📊 Status:", data);
    } else {
      console.log("❌ Erro no servidor:", response.status);
    }
  } catch (error) {
    console.log("❌ Erro de conexão:", error);
  }
};

testRenderConnection();
```

### Teste da Funcionalidade de Compactação

#### **1. Teste Básico - Status do ChromaDB**

- Acessar: `https://dna-forca-frontend.onrender.com`
- Navegar para página de Materiais
- Clicar em "Verificar Status"
- Confirmar se está conectando ao servidor do Render

#### **2. Teste de Compactação Local**

- Clicar em "Compactar + Upload"
- Digite um caminho de teste (ex: `C:\teste\.chromadb`)
- Observar logs no console do navegador
- Verificar se está apontando para URLs do Render

#### **3. Verificar URLs nos Logs**

```typescript
// Deve mostrar URLs do Render, não localhost
console.log("URLs configuradas:");
console.log("VITE_RAG_API_BASE_URL:", import.meta.env.VITE_RAG_API_BASE_URL);
console.log("VITE_API_URL:", import.meta.env.VITE_API_URL);

// Deve mostrar:
// VITE_RAG_API_BASE_URL: https://dna-forca-rag-server.onrender.com
// VITE_API_URL: https://dna-forca-api-server.onrender.com
```

### Monitoramento Durante o Teste

#### **Dashboard do Render**

- **Frontend**: Verificar se está recebendo requisições
- **API Server**: Monitorar logs de autenticação
- **RAG Server**: Acompanhar logs de compactação

#### **Logs Esperados no RAG Server**

```bash
# Durante teste de compactação
📦 Compactando pasta local: C:\teste\.chromadb
✅ Pasta .chromadb encontrada em: C:\teste\.chromadb
📊 Pasta local contém X coleções com Y documentos
✅ Arquivo .tar.gz criado: X.XX MB
```

### Troubleshooting de Teste

#### **Problemas Comuns Durante Teste**

1. **Erro 404 - Endpoint não encontrado**

   - Verificar se `VITE_RAG_API_BASE_URL` está apontando para Render
   - Confirmar se o servidor RAG está rodando

2. **Timeout de Conexão**

   - Aguardar primeira requisição (servidor pode estar "dormindo")
   - Verificar se não há bloqueio de firewall

3. **Erro de CORS**

   - Verificar se `CORS_ORIGINS` inclui o domínio do frontend
   - Confirmar se está configurado no servidor RAG

4. **Erro de Autenticação**
   - Verificar se o token JWT está sendo enviado
   - Confirmar se o sistema de auth está funcionando

#### **Comandos de Debug no Render**

```bash
# No servidor RAG do Render
# Verificar variáveis de ambiente
env | grep VITE
env | grep RAG

# Verificar se diretórios existem
ls -la /app/data/
ls -la /app/data/.chromadb/

# Ver logs em tempo real
tail -f /var/log/app.log
```

### Validação do Teste

#### **✅ Teste Bem-Sucedido**

- Frontend conecta ao servidor RAG do Render
- Funcionalidade de compactação responde
- Logs mostram URLs corretas (onrender.com)
- Sistema processa requisições sem erros

#### **❌ Teste Falhou**

- Verificar configuração das variáveis de ambiente
- Confirmar se serviços estão rodando no Render
- Verificar logs de erro no dashboard
- Testar conectividade básica entre serviços

### Próximos Passos Após Teste

#### **Se Teste Passou**

- Funcionalidade está pronta para uso em produção
- Usuários podem compactar e fazer upload de ChromaDB local
- Sistema sincroniza dados automaticamente com servidor Render

#### **Se Teste Falhou**

- Revisar configuração das variáveis de ambiente
- Verificar status dos serviços no Render
- Consultar logs de erro para diagnóstico
- Ajustar configuração conforme necessário

## 🚀 Deploy para Render

### Configuração do Render

#### **render.yaml Completo**

```yaml
services:
  - type: web
    name: dna-forca-frontend
    envVars:
      - key: VITE_API_URL
        value: "https://dna-forca-api-server.onrender.com"
      - key: VITE_RAG_API_BASE_URL
        value: "https://dna-forca-rag-server.onrender.com"
      - key: VITE_SUPABASE_URL
        value: "https://bqvhtyodlsjcjitunmvs.supabase.co"
      - key: VITE_SUPABASE_ANON_KEY
        value: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

  - type: web
    name: dna-forca-api-server
    envVars:
      - key: API_SERVER_URL
        value: "https://dna-forca-api-server.onrender.com"
      - key: RAG_SERVER_URL
        value: "https://dna-forca-rag-server.onrender.com"
      - key: OPENAI_API_KEY
        value: "sk-proj-..."
      - key: NVIDIA_API_KEY
        value: "nvapi-..."
      - key: GEMINI_API_KEY
        value: "AIzaSyC..."
      - key: CORS_ORIGINS
        value: "https://dna-forca-frontend.onrender.com,http://localhost:3000"

  - type: web
    name: dna-forca-rag-server
    envVars:
      - key: RAG_SERVER_URL
        value: "https://dna-forca-rag-server.onrender.com"
      - key: CHROMA_PERSIST_DIR
        value: "/app/data/.chromadb"
      - key: MATERIALS_DIR
        value: "/app/data/materials"
      - key: OPENAI_API_KEY
        value: "sk-proj-..."
      - key: NVIDIA_API_KEY
        value: "nvapi-..."
      - key: GEMINI_API_KEY
        value: "AIzaSyC..."
      - key: CORS_ORIGINS
        value: "https://dna-forca-frontend.onrender.com,http://localhost:3000"
```

### Estrutura no Render

#### **Diretórios do Servidor RAG**

```
/app/data/
├── .chromadb/          ← ChromaDB principal (destino do upload)
├── materials/          ← Materiais de treinamento
├── assistant_configs.json
├── users_db.json
└── approved_users.json
```

#### **Diretórios do Servidor API**

```
/app/
├── data/
│   ├── .chromadb/      ← Backup do ChromaDB
│   └── materials/      ← Materiais processados
├── auth/               ← Sistema de autenticação
├── rag_system/         ← Sistema RAG
└── main.py             ← Servidor principal
```

### Processo de Deploy

#### **1. Configuração das Variáveis de Ambiente**

- Acessar dashboard do Render
- Configurar variáveis para cada serviço
- Verificar se todas as chaves API estão configuradas

#### **2. Deploy dos Serviços**

```bash
# 1. Frontend
git push origin main  # Render detecta automaticamente

# 2. API Server
cd backend
git push origin main

# 3. RAG Server
cd backend
git push origin main
```

#### **3. Verificação Pós-Deploy**

- Verificar se todos os serviços estão rodando
- Testar conectividade entre serviços
- Verificar logs de inicialização
- Testar funcionalidade de compactação local

### Monitoramento e Logs

#### **Dashboard do Render**

- **Status dos Serviços**: Verde = Rodando, Vermelho = Erro
- **Logs em Tempo Real**: Ver erros e informações de debug
- **Métricas de Performance**: CPU, memória, tempo de resposta

#### **Logs Importantes para Monitorar**

```bash
# Inicialização do RAG Server
✅ RAG handler inicializado com sucesso
📊 ChromaDB contém X coleções com Y documentos

# Operações de Compactação
📦 Compactando pasta local: /app/data/.chromadb
✅ Arquivo .tar.gz criado: X.XX MB

# Uploads e Processamento
📤 Upload iniciado para /app/data/.chromadb
🔄 RAG handler reinicializado com sucesso
```

### Troubleshooting de Produção

#### **Problemas Comuns no Render**

1. **Servidor "Dormindo" (Free Tier)**

   - Primeira requisição pode demorar 30-60 segundos
   - Solução: Aguardar ou fazer upgrade para plano pago

2. **Timeout de Conexão**

   - Verificar se serviços estão respondendo
   - Verificar logs de erro no dashboard

3. **Erro de CORS**

   - Confirmar se `CORS_ORIGINS` está configurado corretamente
   - Incluir domínio do frontend na lista

4. **Chave API Inválida**
   - Verificar se todas as chaves estão configuradas
   - Confirmar se as chaves não expiraram

#### **Comandos de Debug no Render**

```bash
# Verificar variáveis de ambiente
echo $VITE_RAG_API_BASE_URL
echo $CHROMA_PERSIST_DIR

# Verificar se diretórios existem
ls -la /app/data/
ls -la /app/data/.chromadb/

# Verificar logs do sistema
tail -f /var/log/syslog
```

## 📈 Benefícios da Implementação

### 1. **Automatização**

- Compactação e upload em uma operação
- Sem necessidade de upload manual
- Processo simplificado para o usuário

### 2. **Flexibilidade**

- Caminhos personalizados
- Suporte a diferentes sistemas operacionais
- Validação robusta de caminhos

### 3. **Confiabilidade**

- Verificação de integridade dos dados
- Backup automático antes de substituição
- Logs detalhados para debug

### 4. **Integração**

- Funciona com sistema RAG existente
- Atualização automática do handler
- Status em tempo real

## 🔮 Próximas Melhorias

### Funcionalidades Futuras

1. **Interface de Seleção de Pasta**

   - Browser de arquivos nativo
   - Histórico de caminhos utilizados
   - Favoritos para caminhos frequentes

2. **Validação Avançada**

   - Verificação de tamanho da pasta
   - Análise de conteúdo antes do upload
   - Estimativa de tempo de processamento

3. **Sincronização Bidirecional**

   - Download de dados do servidor
   - Merge automático de dados
   - Resolução de conflitos

4. **Monitoramento**
   - Progress bar em tempo real
   - Notificações de conclusão
   - Histórico de operações

## 📚 Referências

### Documentação Relacionada

- [RAG System Guide](./backend/RAG_SYSTEM_GUIDE.md)
- [Docker Deployment Guide](./backend/DOCKER_DEPLOYMENT.md)
- [Render Deployment Guide](./backend/RENDER_DEPLOYMENT.md)

### Tecnologias Utilizadas

- **Backend**: FastAPI, Python, ChromaDB
- **Frontend**: React, TypeScript, Tailwind CSS
- **Compactação**: tarfile, gzip
- **Deploy**: Render, Docker

---

## 📞 Suporte

Para dúvidas ou problemas com a funcionalidade de compactação local do ChromaDB:

1. **Verificar logs** do servidor RAG
2. **Confirmar configuração** das variáveis de ambiente
3. **Validar caminhos** das pastas locais
4. **Testar conectividade** com servidores

---

_Documentação criada em: 25/08/2025_  
_Versão: 1.0_  
_Última atualização: Implementação inicial da funcionalidade_
