# DNA da Força AI - Backend

Sistema educacional com IA para treinamento físico - Backend organizado e modular.

## 📁 Estrutura do Projeto

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

## 🚀 Como Executar

### Pré-requisitos

- Python 3.8+
- Dependências listadas em `config/requirements.txt`

### Instalação

```bash
# Navegar para o diretório backend
cd backend

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependências
pip install -r config/requirements.txt
```

### Execução

```bash
# Usando o script de inicialização
python config/start_backend.py

# Ou diretamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Módulos Principais

### 🔐 Autenticação (`auth/`)

- Sistema completo de autenticação JWT
- Gerenciamento de usuários e permissões
- Tokens de autenticação temporários
- Integração com sistemas externos
- Serviços de email para recuperação de senha

### ☁️ Sincronização Drive (`drive_sync/`)

- Integração completa com Google Drive
- Download recursivo de pastas
- Análise de estrutura de arquivos
- Cache inteligente de arquivos
- Suporte a diferentes tipos de autenticação

### 🧠 Sistema RAG (`rag_system/`)

- Processamento de documentos (PDF, Excel, Texto)
- Embeddings com OpenAI
- Busca semântica avançada
- Geração de respostas contextualizadas
- Configuração flexível de assistentes

### 💬 Agentes de Chat (`chat_agents/`)

- Agente educacional especializado
- Contexto de aprendizado personalizado
- Integração com sistema RAG
- Sugestões de aprendizado adaptativas
- Análise de progresso do usuário

### 🎥 Processamento de Vídeo (`video_processing/`)

- Análise de conteúdo de vídeo
- Geração de timestamps automáticos
- Metadados estruturados
- Integração com Google Drive
- Cache de análise para performance

### 🛠️ Manutenção (`maintenance/`)

- Limpeza de arquivos duplicados
- Otimização de armazenamento
- Relatórios de sistema
- Reset de componentes
- Monitoramento de saúde

## 📊 Dados do Sistema

Todos os dados persistentes estão organizados na pasta `data/`:

- **Usuários**: Informações de usuários e autenticação
- **Tokens**: Tokens de autenticação temporários
- **Cache**: Cache de análise de vídeo e outros dados
- **Configurações**: Configurações persistentes do sistema

## 🔍 Testes

Os testes estão organizados na pasta `tests/`:

- Testes de integração com Google Drive
- Validação de funcionalidades principais
- Scripts de teste automatizados

## 📝 Logs

Os arquivos de log estão organizados na pasta `utils/`:

- Logs de autenticação
- Logs de sincronização do drive
- Logs de testes

## 🔄 Migração da Estrutura Anterior

Esta estrutura foi reorganizada a partir de uma estrutura plana anterior. As principais mudanças:

1. **Modularização**: Código organizado em módulos lógicos
2. **Separação de Responsabilidades**: Cada pasta tem uma responsabilidade específica
3. **Facilidade de Manutenção**: Estrutura mais clara e organizada
4. **Escalabilidade**: Fácil adição de novos módulos
5. **Documentação**: Cada módulo tem documentação clara

## 🤝 Contribuição

Para contribuir com o projeto:

1. Mantenha a estrutura de pastas organizada
2. Adicione documentação para novos módulos
3. Atualize este README quando necessário
4. Siga as convenções de nomenclatura estabelecidas

## 📞 Suporte

Para dúvidas ou problemas:

- Verifique a documentação de cada módulo
- Consulte os logs em `utils/`
- Execute os testes em `tests/`
