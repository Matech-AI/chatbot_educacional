# 🤖 Chatbot Educacional

## 📁 Localização do Projeto
**Pasta:** `C:\Users\Felipe\Desktop\ChatbotEducacional`

## 🚀 Como Executar o Projeto

### 1. Abrir Terminais
Abra **dois terminais** no diretório do projeto:

**Terminal 1 - Backend (FastAPI):**
```bash
cd C:\Users\Felipe\Desktop\ChatbotEducacional\backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 - Frontend (React):**
```bash
cd C:\Users\Felipe\Desktop\ChatbotEducacional
npm run dev
```

### 2. Acessar a Aplicação
- **Frontend:** http://localhost:3000/
- **Backend API:** http://127.0.0.1:8000/
- **Documentação da API:** http://127.0.0.1:8000/docs

## 🔧 Configuração

### Dependências já instaladas:
- ✅ Python packages (backend)
- ✅ Node.js packages (frontend)
- ✅ Arquivo .env criado

### Para usar funcionalidades de IA:
1. Edite o arquivo `backend\.env`
2. Adicione sua chave da OpenAI:
   ```
   OPENAI_API_KEY=sk-sua_chave_aqui
   ```

## 📋 Estrutura do Projeto

```
ChatbotEducacional/
├── backend/           # API FastAPI (Python)
│   ├── main.py       # Arquivo principal da API
│   ├── .env          # Variáveis de ambiente
│   └── ...
├── src/              # Frontend React
├── package.json      # Dependências do frontend
└── README.md         # Documentação original
```

## 🛠️ Tecnologias
- **Frontend:** React + TypeScript + Vite
- **Backend:** FastAPI + Python
- **IA:** LangChain + OpenAI
- **Database:** ChromaDB (para embeddings)

## 📞 Suporte
Se tiver problemas:
1. Verifique se ambos os terminais estão rodando
2. Confirme se as dependências estão instaladas
3. Verifique se as portas 3000 e 8000 estão livres

---
**Criado em:** 12/06/2025 - 02:01
**Localização:** Desktop\ChatbotEducacional

