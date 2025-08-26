# 🗄️ Guia de Compactação Local do ChromaDB

## 📋 Visão Geral

Este guia documenta a funcionalidade implementada para **compactar pastas `.chromadb` locais** e fazer **upload para servidores Render**. A funcionalidade foi adaptada para funcionar tanto em desenvolvimento local quanto em produção.

## 🎯 Funcionalidades Implementadas

### 1. **Compactação Local** (`/chromadb/compress-local`)

- Compacta pasta `.chromadb` local em arquivo `.tar.gz`
- Busca automática da pasta em diferentes localizações
- Validação de integridade dos dados
- Download automático do arquivo compactado
- **⚠️ Funciona apenas em desenvolvimento local**

### 2. **Compactação com Caminho Específico** (`/chromadb/compress-local-path`)

- Permite especificar o caminho exato da pasta `.chromadb`
- Validação completa do caminho fornecido
- Logs detalhados para debug
- Compactação da pasta inteira (não apenas entrada)
- **⚠️ Funciona apenas em desenvolvimento local**

### 3. **Instruções para Produção** (Frontend)

- Botões que mostram instruções detalhadas para compactação manual
- Funciona em qualquer ambiente (desenvolvimento e produção)
- Guia o usuário através do processo manual
- Não depende de acesso direto ao sistema de arquivos do usuário

## 🔧 Implementação Técnica

### Backend - Endpoints

#### `POST /chromadb/compress-local` (Desenvolvimento Local)

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
- **⚠️ Não funciona em produção (Render)**

#### `POST /chromadb/compress-local-path` (Desenvolvimento Local)

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
- **⚠️ Não funciona em produção (Render)**

### Frontend - Componentes

#### Botões Disponíveis

1. **"📋 Instruções Local"** (Roxo)

   - Mostra instruções para compactação manual
   - Funciona em qualquer ambiente
   - Não executa operações automáticas

2. **"📋 Instruções + Upload"** (Roxo Escuro)
   - Mostra instruções para sincronização completa
   - Funciona em qualquer ambiente
   - Guia o usuário através do processo

#### Funções Principais

```typescript
// Mostra instruções para compactação local
const handleCompressLocalChromaDB = async () => {
  setMessage({
    type: "info",
    text: `📋 Para compactar sua pasta .chromadb local:
    1. **Windows**: Use 7-Zip ou WinRAR para criar um arquivo .tar.gz
    2. **Linux/Mac**: Use o comando: tar -czf chromadb.tar.gz .chromadb/
    3. **Faça upload** do arquivo .tar.gz usando o botão "Upload ChromaDB" acima
    ⚠️ O servidor não pode acessar arquivos do seu PC diretamente.`,
  });
};

// Mostra instruções para sincronização completa
const handleCompressAndUploadLocalChromaDB = async () => {
  setMessage({
    type: "info",
    text: `📋 Para sincronizar sua pasta .chromadb local:
    1. **Compacte manualmente** sua pasta .chromadb
    2. **Faça upload** do arquivo .tar.gz usando o botão "Upload ChromaDB" acima
    3. **O sistema** fará o resto automaticamente!
    ⚠️ O servidor não pode acessar arquivos do seu PC diretamente.`,
  });
};
```

## 🚀 Como Usar

### Passo a Passo

1. **Acesse a página de Materiais**

   - Navegue para a seção de sincronização ChromaDB

2. **Clique em "📋 Instruções Local" ou "📋 Instruções + Upload"**

   - Botões roxos com ícone de instruções

3. **Siga as instruções exibidas**

   - **Windows**: Use 7-Zip ou WinRAR para criar um arquivo .tar.gz
   - **Linux/Mac**: Use o comando: `tar -czf chromadb.tar.gz .chromadb/`

4. **Faça upload do arquivo .tar.gz**

   - Use o botão "Upload ChromaDB" na área de upload
   - Sistema processa e atualiza automaticamente

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
# Frontend Environment Variables (PRODUCTION)
VITE_API_URL=https://dna-forca-api.onrender.com
VITE_RAG_API_BASE_URL=https://dna-forca-rag-server.onrender.com
```

#### Backend (`.env`)

```bash
# Backend Environment Variables
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

### 1. Instruções para Compactação Manual

```
Usuário clica no botão → Instruções são exibidas → Usuário segue passos manuais
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

| Endpoint                        | Método | Descrição                                  | Servidor   | Ambiente |
| ------------------------------- | ------ | ------------------------------------------ | ---------- | -------- |
| `/chromadb/upload`              | POST   | Upload de arquivo .tar.gz                  | RAG (8001) | Ambos    |
| `/chromadb/upload-folder`       | POST   | Upload de pasta .zip                       | RAG (8001) | Ambos    |
| `/chromadb/download`            | GET    | Download do ChromaDB                       | RAG (8001) | Ambos    |
| `/chromadb/compress`            | POST   | Compactar ChromaDB ativo                   | RAG (8001) | Ambos    |
| `/chromadb/compress-local`      | POST   | Compactar pasta local (busca automática)   | RAG (8001) | Local    |
| `/chromadb/compress-local-path` | POST   | Compactar pasta local (caminho específico) | RAG (8001) | Local    |
| `/chromadb/status`              | GET    | Status do ChromaDB                         | RAG (8001) | Ambos    |

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

#### 2. Funcionalidade de compactação local não funciona

**Causa**: Servidor em produção (Render) não pode acessar arquivos locais
**Solução**: Use os botões de instruções e siga o processo manual

**Verificação:**

- Se estiver usando Render, use compactação manual
- Se estiver em desenvolvimento local, os endpoints funcionam normalmente

#### 3. Erro de conexão

**Causa Local**: Servidor RAG não está rodando
**Solução Local**: Verificar se servidor está ativo na porta 8001

**Causa Produção**: Problemas de rede ou servidor indisponível
**Solução Produção**: Verificar status do servidor Render

## 🔒 Limitações de Segurança

### Produção (Render)

- **❌ Sem acesso direto** ao sistema de arquivos do usuário
- **❌ Não pode** compactar pastas locais automaticamente
- **✅ Funciona** com upload de arquivos já compactados
- **✅ Seguro** para ambientes de produção

### Desenvolvimento Local

- **✅ Acesso direto** ao sistema de arquivos local
- **✅ Pode** compactar pastas automaticamente
- **⚠️ Cuidado** com permissões e caminhos
- **✅ Ideal** para desenvolvimento e testes

## 📝 Resumo da Solução

### Problema Original

O endpoint `/chromadb/compress-local-path` tentava acessar caminhos locais do usuário a partir do servidor Render, o que é impossível por questões de segurança e arquitetura.

### Solução Implementada

1. **Mantidos** os endpoints de compactação local para desenvolvimento
2. **Substituídos** os botões de execução automática por instruções
3. **Adicionadas** mensagens claras sobre limitações de produção
4. **Preservada** a funcionalidade de upload de arquivos compactados

### Benefícios

- ✅ **Funciona em qualquer ambiente** (desenvolvimento e produção)
- ✅ **Seguro** para ambientes de produção
- ✅ **Claro** para o usuário sobre o que fazer
- ✅ **Mantém** funcionalidade de upload e processamento
- ✅ **Educativo** sobre limitações de arquitetura

## 🎯 Próximos Passos

### Melhorias Futuras

1. **Validação de arquivos** antes do upload
2. **Progress bar** durante upload de arquivos grandes
3. **Histórico** de uploads realizados
4. **Notificações** de conclusão de processamento
5. **Integração** com sistemas de backup automático
