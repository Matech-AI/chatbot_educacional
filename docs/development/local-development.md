# 💻 Desenvolvimento Local - Sistema RAG DNA da Força

Este guia explica como configurar e executar o Sistema RAG DNA da Força em seu ambiente local para desenvolvimento e testes.

## 🎯 **Visão Geral**

O desenvolvimento local permite que você:

- **Teste funcionalidades** antes do deploy
- **Debug problemas** com acesso completo aos logs
- **Desenvolva novas features** em um ambiente controlado
- **Experimente configurações** sem custos de infraestrutura

## 📋 **Pré-requisitos**

### **Software Necessário:**

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)
- **Visual Studio Code** (recomendado) - [Download](https://code.visualstudio.com/)

### **Contas e APIs:**

- [OpenAI](https://platform.openai.com/) ou [Anthropic](https://console.anthropic.com/)
- [Supabase](https://supabase.com/)
- [Google Cloud](https://cloud.google.com/)

## 🚀 **Configuração Inicial**

### **1. Clone o Repositório**

```bash
git clone https://github.com/seu-usuario/chatbot_educacao_fisica.git
cd chatbot_educacao_fisica
```

### **2. Configure o Backend Python**

```bash
# Navegue para a pasta backend
cd backend

# Crie um ambiente virtual
python -m venv .venv

# Ative o ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp env.example .env
# Edite o arquivo .env com suas chaves
```

### **3. Configure o Frontend Node.js**

```bash
# Volte para a raiz do projeto
cd ..

# Instale as dependências do frontend
npm install

# Configure as variáveis de ambiente
cp env.example .env.local
# Edite o arquivo .env.local com suas configurações
```

## 🔧 **Configuração das Variáveis de Ambiente**

### **Backend (.env):**

```bash
# Configurações da IA
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Supabase
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Google Drive
GOOGLE_DRIVE_CREDENTIALS=token.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here

# Configurações do Sistema
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
PORT=8000
HOST=0.0.0.0

# ChromaDB
CHROMA_PERSIST_DIRECTORY=data/.chromadb
CHROMA_ANONYMIZED_TELEMETRY=false
```

### **Frontend (.env.local):**

```bash
# Supabase
VITE_SUPABASE_URL=your_supabase_url_here
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Backend API
VITE_API_URL=http://localhost:8000

# Configurações
VITE_APP_NAME=DNA da Força
VITE_APP_VERSION=2.0.0
VITE_DEBUG=true
```

## 🗄️ **Configuração do Banco de Dados**

### **1. Supabase Setup**

```bash
# 1. Crie um projeto no Supabase
# 2. Execute as migrações SQL
# 3. Configure as políticas de segurança
# 4. Copie as chaves de API
```

### **2. ChromaDB Local**

```bash
# O ChromaDB será criado automaticamente em:
# backend/data/.chromadb

# Para limpar e recriar:
rm -rf backend/data/.chromadb
# O sistema recriará na primeira execução
```

### **3. Google Drive Setup**

```bash
# 1. Acesse Google Cloud Console
# 2. Crie um projeto
# 3. Ative a Google Drive API
# 4. Crie credenciais de serviço
# 5. Baixe o arquivo JSON
# 6. Renomeie para token.json
# 7. Coloque em backend/token.json
```

## 🚀 **Executando o Sistema Localmente**

### **1. Inicie o Backend**

```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Execute o servidor
python main.py
# ou
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

### **2. Inicie o Frontend**

```bash
# Terminal 2 - Frontend
cd frontend  # ou na raiz se não tiver pasta separada
npm run dev
```

### **3. Acesse o Sistema**

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Docs da API:** http://localhost:8000/docs

## 🧪 **Testando o Sistema**

### **1. Testes Automatizados**

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
npm run test

# Testes de integração
python -m pytest tests/integration/
```

### **2. Testes Manuais**

```bash
# Teste da API
curl http://localhost:8000/health

# Teste do frontend
# Abra http://localhost:5173 no navegador

# Teste de autenticação
# Tente fazer login no sistema
```

### **3. Teste do Chatbot**

```bash
# 1. Faça login no sistema
# 2. Acesse a página de chat
# 3. Envie uma pergunta sobre educação física
# 4. Verifique se a resposta é gerada
```

## 🔍 **Debug e Logs**

### **1. Logs do Backend**

```bash
# Logs em tempo real
tail -f backend/logs/app.log

# Logs de debug
tail -f backend/logs/debug.log

# Logs de erro
tail -f backend/logs/error.log
```

### **2. Logs do Frontend**

```bash
# Console do navegador
# F12 > Console

# Logs do Vite
# Terminal onde npm run dev está rodando
```

### **3. Debug do Python**

```python
# Adicione breakpoints
import pdb; pdb.set_trace()

# Ou use o debugger do VS Code
# Configure launch.json para debugging
```

## 🛠️ **Ferramentas de Desenvolvimento**

### **1. VS Code Extensions Recomendadas:**

- **Python** - Microsoft
- **Python Docstring Generator** - njpwerner
- **Python Indent** - Kevin Rose
- **Python Type Hint** - nhoizey
- **ES7+ React/Redux/React-Native snippets** - dsznajder
- **Tailwind CSS IntelliSense** - bradlc
- **GitLens** - GitKraken

### **2. Configuração do VS Code:**

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.autoSave": "onFocusChange"
}
```

### **3. Pre-commit Hooks:**

```bash
# Instale pre-commit
pip install pre-commit

# Configure os hooks
pre-commit install

# Execute manualmente
pre-commit run --all-files
```

## 📊 **Monitoramento Local**

### **1. Métricas do Sistema:**

```bash
# Uso de memória
htop
# ou
top

# Uso de disco
df -h

# Processos Python
ps aux | grep python

# Portas em uso
netstat -tulpn | grep :8000
```

### **2. Performance do ChromaDB:**

```bash
# Tamanho do banco
du -sh backend/data/.chromadb

# Número de documentos
python -c "
import chromadb
client = chromadb.PersistentClient('backend/data/.chromadb')
print(f'Coleções: {len(client.list_collections())}')
for col in client.list_collections():
    print(f'{col.name}: {col.count()} documentos')
"
```

## 🚨 **Problemas Comuns e Soluções**

### **1. Erro de Porta em Uso**

```bash
# Encontre o processo usando a porta
lsof -i :8000
# ou
netstat -tulpn | grep :8000

# Mate o processo
kill -9 <PID>
```

### **2. Erro de Dependências Python**

```bash
# Reinstale o ambiente virtual
rm -rf backend/.venv
python -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

### **3. Erro de Node Modules**

```bash
# Limpe e reinstale
rm -rf node_modules package-lock.json
npm install
```

### **4. Erro de ChromaDB**

```bash
# Limpe o banco
rm -rf backend/data/.chromadb
# Reinicie o backend
```

## 🔄 **Fluxo de Desenvolvimento**

### **1. Desenvolvimento de Features:**

```bash
# Crie uma branch
git checkout -b feature/nova-funcionalidade

# Desenvolva
# Teste localmente
# Commit suas mudanças
git add .
git commit -m "feat: adiciona nova funcionalidade"

# Push e crie PR
git push origin feature/nova-funcionalidade
```

### **2. Debug de Bugs:**

```bash
# Reproduza o bug localmente
# Adicione logs de debug
# Use breakpoints
# Teste a correção
# Commit a correção
git commit -m "fix: corrige bug específico"
```

### **3. Refatoração:**

```bash
# Teste as mudanças localmente
# Execute todos os testes
# Verifique a cobertura
pytest --cov=backend tests/
# Commit a refatoração
git commit -m "refactor: melhora estrutura do código"
```

## 📚 **Recursos de Aprendizado**

### **1. Documentação das Tecnologias:**

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [ChromaDB](https://docs.trychroma.com/)
- [LangChain](https://python.langchain.com/)
- [Supabase](https://supabase.com/docs)

### **2. Tutoriais e Exemplos:**

- [Exemplos de Prompts](../examples/prompts.md)
- [Configurações de IA](../examples/ai-configs.md)
- [Casos de Uso](../examples/use-cases.md)

### **3. Comunidade:**

- [Discord DNA da Força](https://discord.gg/dnadaforca)
- [GitHub Issues](https://github.com/seu-repo/issues)
- [Stack Overflow](https://stackoverflow.com/)

## 🎯 **Próximos Passos**

1. **Configure seu ambiente** seguindo este guia
2. **Execute o sistema** localmente
3. **Teste as funcionalidades** principais
4. **Explore o código** para entender a arquitetura
5. **Contribua** com melhorias e correções
6. **Documente** suas descobertas

---

## 📞 **Precisa de Ajuda?**

- **GitHub Issues:** [Reporte problemas](https://github.com/seu-repo/issues)
- **Discord:** [Comunidade ativa](https://discord.gg/dnadaforca)
- **Email:** suporte@dnadaforca.com

---

**📅 Última atualização:** Agosto 2025  
**🔄 Versão:** 2.0.0  
**👨‍💻 Mantido por:** Equipe DNA da Força
