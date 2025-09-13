# 🚀 DNA da Força - Sistema Educacional com IA

Sistema educacional avançado para treinamento físico, utilizando Inteligência Artificial (RAG) para responder dúvidas sobre materiais de treinamento, com integração completa ao Google Drive.

---

## 📑 Tabela de Conteúdo

- [Principais Recursos](#principais-recursos)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Instalação](#instalação)
  - [Configuração Manual](#configuração-manual)
- [Configuração das APIs](#configuração-das-apis)
- [Sistema de Autenticação](#sistema-de-autenticação)
- [Como Executar](#como-executar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Fluxo de Uso](#fluxo-de-uso)
- [Debug e Solução de Problemas](#debug-e-solução-de-problemas)
- [Contribuição](#contribuição)
- [Suporte](#suporte)

---

## ✨ Principais Recursos

- 🤖 **Assistente IA Especializado** (RAG) para respostas precisas
- ☁️ **Integração Google Drive** (sincronização automática de materiais)
- 🔐 **Sistema de Autenticação** multi-nível (Admin, Instrutor, Aluno) com Supabase
- 📁 **Gestão de Materiais** (upload manual e sincronização)
- 💬 **Chat Inteligente** com múltiplas sessões
- 🔧 **Painel de Debug** e diagnóstico completo
- 📊 **Dashboard Responsivo**

---

## 🛠️ Tecnologias Utilizadas

### Backend

- FastAPI
- OpenAI GPT-4 (RAG via LangChain)
- ChromaDB (banco vetorial)
- Google Drive API
- Supabase (autenticação e banco de dados)
- JWT (autenticação local - legado)

### Frontend

- React 18 + TypeScript
- Tailwind CSS
- Zustand (estado global)
- Framer Motion (animações)
- Vite (bundler)

---

## �� Instalação

### 1. Clone o repositório

```bash
git clone <https://github.com/matheusbnas/chatbot_educacional>
```

### 2. Configuração Manual

**Pré-requisitos:** Python 3.8+, Node.js 16+, npm ou yarn

#### Backend

```bash
cd backend
python -m venv .venv
# Ative o ambiente virtual:
# Linux/Mac: source venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edite o .env com suas chaves
```

#### Frontend

```bash
npm install
cp .env.example .env  # Edite o .env se necessário
```

---

## 🔑 Configuração das APIs

### 1. OpenAI API Key (Obrigatório)

- Gere uma chave em [OpenAI API](https://platform.openai.com/)
- Adicione ao `backend/.env`:
  ```env
  OPENAI_API_KEY=sk-your-openai-api-key-here
  ```

### 2. Google Drive API (Para sincronização)

- **API Key (Pastas Públicas):**
  - Ative a Google Drive API no Google Cloud
  - Crie uma API Key e adicione ao `backend/.env`:
    ```env
    GOOGLE_DRIVE_API_KEY=your-google-drive-api-key
    ```
- **OAuth2 (Pastas Privadas):**
  - Crie um OAuth2 Client ID
  - Baixe o JSON e renomeie para `credentials.json` em `backend/`

---

## 🔐 Sistema de Autenticação

O sistema oferece duas opções de autenticação:

### 1. Supabase (Recomendado)

Sistema moderno com banco de dados PostgreSQL e autenticação segura.

**Configuração:**

1. ✅ Projeto Supabase já configurado: `bqvhtyodlsjcjitunmvs.supabase.co`
2. Execute o script SQL em `supabase/migrations/bd_forca_ai.sql`
3. Configure as variáveis de ambiente (já pré-configuradas):

```env
VITE_SUPABASE_URL=https://bqvhtyodlsjcjitunmvs.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=sua-service-role-key
```

**Setup Rápido:**

```bash
# Execute o script de configuração automática
python setup_supabase.py
```

**Endpoints disponíveis:**

- `POST /auth/supabase/signup` - Registrar usuário
- `POST /auth/supabase/signin` - Fazer login
- `GET /auth/supabase/me` - Dados do usuário atual
- `PUT /auth/supabase/profile` - Atualizar perfil
- `POST /auth/supabase/reset-password` - Reset de senha

### 2. Sistema Local (Legado)

Sistema baseado em arquivos JSON locais.

**Endpoints disponíveis:**

- `POST /auth/token` - Fazer login
- `GET /auth/me` - Dados do usuário atual
- `POST /auth/users` - Criar usuário (admin)

### Migração de Dados

Para migrar usuários do sistema local para o Supabase:

```bash
cd backend
python scripts/migrate_users_to_supabase.py
```

### Teste da Integração

```bash
cd backend
python scripts/test_supabase_integration.py
```

**Documentação completa:**

- [Guia de Autenticação Supabase](docs/authentication/supabase-auth-guide.md)
- [Quick Start - Setup Rápido](docs/setup/QUICK_START_SUPABASE.md)

---

## ▶️ Como Executar

### Backend

```bash
cd backend
uvicorn main_simple:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
npm run dev
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Documentação API: http://localhost:8000/docs

---

## 📁 Estrutura do Projeto

```
chatbot_educacional/
├── backend/           # FastAPI backend
│   ├── main_simple.py # API principal
│   ├── drive_handler.py
│   ├── rag_handler.py
│   ├── auth.py
│   ├── credentials.json
│   ├── data/
│   │   └── materials/ # Materiais baixados
│   └── .chromadb/     # Banco vetorial
├── src/               # Frontend React
│   ├── components/
│   ├── pages/
│   ├── store/
│   └── types/
├── test_drive_connection.py
└── README.md
```

---

## 🧭 Fluxo de Uso

### 1. Setup Inicial (Admin/Instrutor)

- Configure as API Keys
- Sincronize materiais do Drive
- Inicialize o assistente IA

### 2. Gestão de Materiais

- Upload manual via `/materials`
- Sincronização automática do Drive
- Organização por tags/categorias

### 3. Uso do Chat (Todos)

- Acesse `/chat`
- Faça perguntas sobre os materiais
- Múltiplas sessões de conversa
- Respostas com citação de fontes

### 4. Painel de Debug

- `/materials` → Aba "Debug"
- Informações detalhadas do sistema
- Teste de conectividade em tempo real
- Logs de depuração

---

## 🛠️ Debug e Solução de Problemas

### Problemas Comuns

- **Erro de Autenticação OpenAI:**
  - Verifique a `OPENAI_API_KEY` no `.env`
- **Erro de Conexão Google Drive:**
  - Verifique se a pasta é pública
  - Configure API Key válida ou use `credentials.json`
- **Erro de Dependências:**
  - Execute `pip install -r requirements.txt`
- **Erro de Porta em Uso:**
  - Libere a porta 8000 ou altere a configuração

### Comandos Úteis

```bash
# Status geral
curl http://localhost:8000/health
# Teste Drive
python test_drive_connection.py
# Verificar materiais
ls -la backend/data/materials/
# Status do banco vetorial
ls -la backend/.chromadb/
```

### Erro de autenticação Google Drive (token expirado ou revogado)

1. Apague o arquivo `token.json` na pasta do backend.
2. Feche programas que possam estar usando a porta 8080 ou 8000.
3. Rode novamente o script e faça o login Google na janela que abrir.
4. Se necessário, baixe um novo `credentials.json` no Google Cloud Console.

Se continuar com problemas, reinicie o computador e repita os passos.

---

## 🤝 Contribuição

- Adicione novos endpoints em `backend/main_simple.py`
- Modifique integração Drive em `backend/drive_handler.py`
- Ajuste IA/RAG em `backend/rag_handler.py`
- Componentes React em `src/components/`

Teste localmente, verifique endpoints e integração.

---

## 📞 Suporte

- Painel Debug: Interface web para diagnóstico
- Script de Teste: `test_drive_connection.py`
- Documentação API: http://localhost:8000/docs

Para reportar problemas, inclua:

- Logs do backend
- Resultado do teste de conexão Drive
- Configurações de ambiente (sem chaves sensíveis)
- Passos para reproduzir o problema

---

Desenvolvido para o **DNA da Força - Sistema Educacional de Treinamento Físico**
