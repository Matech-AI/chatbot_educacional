🚀 DNA da Força - Sistema Educacional com IA
Sistema educacional avançado para treinamento físico, utilizando Inteligência Artificial (RAG) para responder dúvidas sobre materiais de treinamento, com integração completa ao Google Drive.

📋 Versão 1.3.0 - Enhanced Drive Integration
✨ Principais Recursos
🤖 Assistente IA Especializado - RAG (Retrieval Augmented Generation) para respostas precisas
☁️ Integração Google Drive - Sincronização automática de materiais
🔐 Sistema de Autenticação - Multi-nível (Admin, Instrutor, Aluno)
📁 Gestão de Materiais - Upload manual e sincronização com Drive
💬 Chat Inteligente - Múltiplas sessões de conversa
🔧 Painel de Debug - Diagnóstico completo de conexões
📊 Dashboard Responsivo - Interface moderna e intuitiva
🛠️ Tecnologias Utilizadas
Backend
FastAPI - Framework web moderno e rápido
OpenAI GPT-4 - Modelo de linguagem para o assistente
LangChain - Framework para aplicações com LLM
ChromaDB - Banco vetorial para embeddings
Google Drive API - Integração com Google Drive
JWT - Autenticação segura
Frontend
React 18 - Biblioteca de interface
TypeScript - Tipagem estática
Tailwind CSS - Framework de estilização
Zustand - Gerenciamento de estado
Framer Motion - Animações fluidas
Vite - Bundler rápido
🚀 Instalação Rápida

1. Setup Automático (Recomendado)

# Clone o repositório

git clone <url-do-repositorio>
cd dna-da-forca

# Execute o setup automático

python setup.py
O script automático irá:

✅ Verificar dependências (Python 3.8+, Node.js, npm)
✅ Instalar dependências Python e Node.js
✅ Criar arquivos de configuração
✅ Configurar credenciais do Google Drive
✅ Testar conexão com a pasta do Drive
✅ Criar scripts de inicialização 2. Configuração Manual
Pré-requisitos
Python 3.8 ou superior
Node.js 16 ou superior
npm ou yarn
Backend Setup
cd backend

# Criar ambiente virtual

python -m venv venv
source venv/bin/activate # Linux/Mac

# ou

venv\Scripts\activate # Windows

# Instalar dependências

pip install -r requirements.txt

# Configurar variáveis de ambiente

cp .env.example .env

# Editar .env com suas chaves de API

Frontend Setup

# Instalar dependências

npm install

# Configurar variáveis de ambiente

cp .env.example .env
🔑 Configuração das APIs

1. OpenAI API Key (Obrigatório)
   Acesse OpenAI API
   Crie uma API Key
   Adicione no arquivo backend/.env:
   OPENAI_API_KEY=sk-your-openai-api-key-here
2. Google Drive API (Para sincronização)
   Opção A: API Key (Pastas Públicas)
   Acesse Google Cloud Console
   Crie um projeto ou selecione existente
   Ative a Google Drive API
   Crie uma API Key
   Adicione no backend/.env:
   GOOGLE_DRIVE_API_KEY=your-google-drive-api-key
   Opção B: OAuth2 (Pastas Privadas)
   No Google Cloud Console, crie um OAuth2 Client ID
   Baixe o arquivo JSON das credenciais
   Renomeie para credentials.json na pasta backend/
   Nota: As credenciais já estão configuradas no projeto para a pasta específica.

🚀 Executando o Sistema
Método 1: Scripts Automáticos

# Backend

python start_backend.py

# Frontend (nova aba do terminal)

./start_frontend.sh
Método 2: Manual

# Backend

cd backend
uvicorn main_simple:app --host 0.0.0.0 --port 8000 --reload

# Frontend

npm run dev
🌐 Acessos
Frontend: http://localhost:3000
Backend API: http://localhost:8000
Documentação API: http://localhost:8000/docs
👥 Usuários Padrão
Usuário Senha Papel Permissões
admin adminpass Administrador Todas
instrutor instrutorpass Instrutor Gerenciar materiais, configurar
aluno alunopass Aluno Apenas chat
📁 Estrutura do Projeto
dna-da-forca/
├── backend/ # Backend FastAPI
│ ├── main_simple.py # API principal
│ ├── drive_handler.py # Handler do Google Drive
│ ├── rag_handler.py # Handler do RAG/IA
│ ├── auth.py # Autenticação
│ ├── credentials.json # Credenciais Google Drive
│ ├── data/
│ │ └── materials/ # Materiais baixados
│ └── .chromadb/ # Banco vetorial
├── src/ # Frontend React
│ ├── components/ # Componentes React
│ ├── pages/ # Páginas principais
│ ├── store/ # Estado global (Zustand)
│ └── types/ # Tipos TypeScript
├── setup.py # Script de instalação
├── test_drive_connection.py # Teste de conexão Drive
└── README.md # Esta documentação
🔧 Configuração do Google Drive
Pasta Alvo
O sistema está configurado para acessar esta pasta específica:

URL: https://drive.google.com/drive/folders/1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ
ID: 1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ
Teste de Conexão

# Teste específico da pasta alvo

python test_drive_connection.py

# Ou via API

curl -X POST "http://localhost:8000/debug/test-specific-folder" \
 -H "Authorization: Bearer <seu-token>"
Sincronização de Materiais
Via Interface Web:

Acesse /materials
Aba "Drive Sync"
Configure API Key (se necessário)
Clique em "Sincronizar"
Via API:

curl -X POST "http://localhost:8000/sync-drive" \
 -H "Content-Type: application/json" \
 -H "Authorization: Bearer <token>" \
 -d '{"folder_id": "1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ", "download_files": true}'
🤖 Configuração do Assistente IA

1. Inicialização do Sistema
   curl -X POST "http://localhost:8000/initialize" \
    -H "Authorization: Bearer <token>" \
    -F "api_key=<sua-openai-api-key>" \
    -F "drive_folder_id=1s00SfrQ04z0YIheq1ub0Dj1GpA_3TVNJ"
2. Via Interface Web
   Faça login como admin/instrutor
   Acesse /assistant
   Configure parâmetros do modelo
   Teste no /chat
3. Parâmetros Configuráveis
   Modelo: GPT-4o-mini, GPT-4o, GPT-3.5-turbo
   Temperatura: Criatividade das respostas (0.0-1.0)
   Chunk Size: Tamanho dos fragmentos de documento
   Prompt Template: Personalização do comportamento
   🔍 Debug e Diagnóstico
   Painel de Debug (Admin)
   Acesse /materials → Aba "Debug"
   Informações detalhadas do sistema
   Teste de conectividade em tempo real
   Logs de depuração
   Logs Detalhados

# Logs do backend em tempo real

tail -f logs/backend.log

# Teste específico de conexão

python test_drive_connection.py --test-drive
Endpoints de Debug

# Status do sistema

GET /health

# Debug do Google Drive

GET /debug/drive

# Teste da pasta específica

POST /debug/test-specific-folder

# Estatísticas dos materiais

GET /drive-stats
📚 Uso do Sistema

1. Fluxo Básico de Trabalho
   Setup Inicial (Admin/Instrutor):

Execute python setup.py
Configure API Keys
Sincronize materiais do Drive
Inicialize o assistente IA
Gestão de Materiais:

Upload manual via /materials
Sincronização automática do Drive
Organização por tags e categorias
Uso do Chat (Todos os usuários):

Acesse /chat
Faça perguntas sobre os materiais
Múltiplas sessões de conversa
Respostas com citação de fontes 2. Casos de Uso
Para Instrutores:
Upload de novos materiais de treino
Sincronização com biblioteca do Drive
Configuração do assistente especializado
Monitoramento de uso pelos alunos
Para Alunos:
Consulta inteligente sobre exercícios
Esclarecimento de dúvidas sobre treino
Acesso a materiais organizados
Histórico de conversas
🔧 Solução de Problemas
Problemas Comuns

1. Erro de Autenticação OpenAI
   ❌ Error: Invalid API key provided
   Solução: Verifique a OPENAI_API_KEY no arquivo .env

2. Erro de Conexão Google Drive
   ❌ Error: 403 Forbidden
   Soluções:

Verifique se a pasta é pública
Configure API Key válida
Use arquivo credentials.json para pastas privadas 3. Erro de Dependências
❌ ModuleNotFoundError: No module named 'langchain'
Solução: Execute pip install -r requirements.txt

4. Erro de Porta em Uso
   ❌ Error: Port 8000 is already in use
   Solução: Mate processos ou use porta diferente:

lsof -ti:8000 | xargs kill -9
Verificação de Saúde do Sistema

# Status geral

curl http://localhost:8000/health

# Teste completo do Drive

python test_drive_connection.py

# Verificar materiais baixados

ls -la backend/data/materials/

# Status do banco vetorial

ls -la backend/.chromadb/
🤝 Contribuição
Estrutura de Desenvolvimento
Backend: Adicione novos endpoints em main_simple.py
Google Drive: Modifique drive_handler.py
IA/RAG: Ajuste rag_handler.py
Frontend: Componentes em src/components/
Processo de Deploy
Teste localmente
Execute python setup.py em ambiente limpo
Verifique todos os endpoints
Teste integração Drive + IA
📞 Suporte
Recursos de Ajuda
Logs Detalhados: Ativados por padrão
Painel Debug: Interface web para diagnóstico
Script de Teste: test_drive_connection.py
Documentação API: http://localhost:8000/docs
Informações de Debug
Para reportar problemas, inclua:

Logs do backend
Resultado do teste de conexão Drive
Configurações de ambiente (sem chaves sensíveis)
Passos para reproduzir o problema
🎉 Sistema Pronto!
Após seguir este guia, você terá:

✅ Sistema funcional com IA especializada
✅ Integração completa com Google Drive
✅ Interface moderna e responsiva
✅ Logs detalhados para debug
✅ Autenticação multi-nível
✅ Chat inteligente com múltiplas sessões
Próximos passos:

Execute python setup.py
Configure suas API Keys
Sincronize materiais do Drive
Teste o chat com perguntas sobre treino
Explore todas as funcionalidades!
Desenvolvido para o DNA da Força - Sistema Educacional de Treinamento Físico
