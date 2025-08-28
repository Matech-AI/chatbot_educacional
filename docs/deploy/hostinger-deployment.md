# 🚀 GUIA COMPLETO DE DEPLOY - SISTEMA COMPLETO (FRONTEND + RAG + API) NO HOSTINGER VPS

## 🎯 **OBJETIVO**

Substituir **COMPLETAMENTE** o servidor Render com um sistema completo rodando no seu VPS Hostinger, baseado na configuração do `render.yaml`:

- ✅ **Frontend React** (porta 3000) - Interface do usuário
- ✅ **RAG Server** (porta 8000) - Sistema de IA e documentos
- ✅ **API Server** (porta 8001) - Autenticação e gerenciamento
- ✅ **Nginx** - Proxy reverso e balanceamento
- ✅ **Redis** - Cache e sessões
- ✅ **Sistema completo** de gerenciamento

## 📋 **INFORMAÇÕES DO SERVIDOR**

- **Provedor**: Hostinger
- **OS**: Debian 12
- **IP**: 31.97.16.142
- **Acesso**: SSH root
- **Recursos**: 200GB disco, 16TB banda

## 🔧 **ETAPA 1: CONEXÃO E PREPARAÇÃO**

### **1.1 Conectar via SSH**

```bash
ssh root@31.97.16.142
```

### **1.2 Configurar Autenticação GitHub (REPOSITÓRIO PRIVADO)**

Como o repositório é privado, você precisa configurar autenticação:

#### **A) Criar Token de Acesso Pessoal (PAT) no GitHub:**

1. **GitHub.com** → Clique no seu avatar → `Settings`
2. **Sidebar esquerda** → `Developer settings`
3. **Personal access tokens** → `Tokens (classic)`
4. **Generate new token** → `Generate new token (classic)`
5. **Note**: `Hostinger Deploy Token`
6. **Expiration**: `90 days` (ou `No expiration` para desenvolvimento)
7. **Scopes**: ✅ `repo` (Full control of private repositories)
8. **Generate token**
9. **⚠️ COPIE O TOKEN** (você não verá novamente!)

#### **B) Configurar Autenticação no Servidor:**

```bash
# 1. Configurar token e username
export GITHUB_TOKEN="SEU_TOKEN_AQUI"
export GITHUB_USERNAME="SEU_USERNAME"

# 2. Configurar Git
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@exemplo.com"

# 3. Testar conexão GitHub
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user
```

### **1.3 Executar o script de deploy COMPLETO**

```bash
# Download do script usando autenticação GitHub
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -O https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh

# Dar permissão de execução
chmod +x deploy_frontend_hostinger.sh

# Executar o deploy COMPLETO (Frontend + RAG + API)
./deploy_frontend_hostinger.sh
```

### **1.4 Sequência Completa de Comandos**

```bash
# Configurar autenticação
export GITHUB_TOKEN="SEU_TOKEN_AQUI"
export GITHUB_USERNAME="SEU_USERNAME"

# Configurar Git
git config --global user.name "Matheus"
git config --global user.email "matheusbnas@gmail.com"

# Testar conexão
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user

# Download e execução
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -O https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh

chmod +x deploy_frontend_hostinger.sh
./deploy_frontend_hostinger.sh
```

## ⚙️ **ETAPA 2: CONFIGURAÇÃO DAS API KEYS**

### **2.1 Editar arquivo .env**

```bash
cd /root/dna-forca-complete
nano .env
```

### **2.2 Configurar suas chaves (baseado no render.yaml)**

```bash
# ===== API KEYS =====
OPENAI_API_KEY=sk-...sua-chave-openai...
NVIDIA_API_KEY=nvapi-...sua-chave-nvidia...
GEMINI_API_KEY=...sua-chave-gemini...
GOOGLE_DRIVE_API_KEY=...sua-chave-google-drive...

# ===== CONFIGURAÇÕES JWT =====
JWT_SECRET_KEY=sua-chave-secreta-jwt-aqui
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===== CONFIGURAÇÕES DE EMAIL =====
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=matheusbnas@gmail.com
EMAIL_PASSWORD=yoip qkvw aozn augl
EMAIL_FROM=matheusbnas@gmail.com
```

## 📦 **ETAPA 3: VERIFICAÇÃO DAS DEPENDÊNCIAS INSTALADAS**

### **3.1 Verificar Ambiente Virtual Python (.venv)**

```bash
# O script de deploy já criou o ambiente virtual
ls -la .venv/

# Verificar se está ativo
source .venv/bin/activate
which python
pip --version
```

### **3.2 Verificar Dependências Python Instaladas**

```bash
# O script de deploy já instalou todas as dependências do requirements.txt
source .venv/bin/activate

# Verificar dependências principais
pip list | grep -E "(fastapi|uvicorn|langchain|chromadb|redis)"

# Verificar todas as dependências instaladas
pip list | head -20
```

### **3.3 Verificar Dependências Node.js Instaladas**

```bash
# O script de deploy já instalou as dependências Node.js
ls -la node_modules/

# Verificar se o package.json existe
cat package.json | head -10

# Verificar se o src/ existe (Frontend React)
ls -la src/
```

### **3.4 Verificar Instalação Completa**

```bash
# Verificar se tudo foi instalado corretamente
echo "🔍 VERIFICAÇÃO COMPLETA DAS DEPENDÊNCIAS"
echo "=========================================="

# Python
echo "🐍 Python:"
source .venv/bin/activate
python --version
pip --version
echo "📦 Dependências Python: $(pip list | wc -l) pacotes"

# Node.js
echo "🟢 Node.js:"
node --version
npm --version
echo "📦 Dependências Node.js: $(cd frontend && npm list --depth=0 | wc -l) pacotes"

# Frontend
echo "🌐 Frontend:"
if [ -d "src" ]; then
    echo "✅ Diretório src/ encontrado: $(ls -la src/ | wc -l) arquivos"
    if [ -d "dist" ]; then
        echo "✅ Build criado: $(du -sh dist | cut -f1)"
    else
        echo "⚠️ Build não encontrado (execute: npm run build)"
    fi
else
    echo "⚠️ Diretório src/ não encontrado"
fi
```

## 🏗️ **ETAPA 4: VERIFICAÇÃO DO FRONTEND**

### **4.1 Verificar Estrutura do Frontend**

```bash
# O script de deploy já instalou as dependências
ls -la src/

# Verificar se há componentes React
ls -la src/components/

# Verificar se há páginas
ls -la src/pages/
```

### **4.2 Build do Frontend (se necessário)**

```bash
# Fazer build para produção
npm run build

# Verificar se o build foi criado
ls -la dist/

# Ver tamanho do build
du -sh dist/

# Iniciar em modo desenvolvimento
npm run dev
```

## 🚀 **ETAPA 5: INICIALIZAÇÃO DO SISTEMA COMPLETO**

### **5.1 Primeira execução**

```bash
./start_all.sh
```

### **5.2 Verificar se está funcionando**

```bash
# Em outro terminal SSH
curl http://localhost:3000          # Frontend
curl http://localhost:8000/status   # RAG Server
curl http://localhost:8001/status   # API Server
curl http://localhost/health        # Nginx Health Check
```

## 🌐 **ETAPA 6: CONFIGURAÇÃO DO NGINX E FIREWALL**

### **6.1 Verificar configuração do Nginx**

```bash
nginx -t
```

### **6.2 Reiniciar Nginx**

```bash
systemctl restart nginx
systemctl enable nginx
```

### **6.3 Configurar firewall**

```bash
ufw allow 80      # Nginx
ufw allow 3000    # Frontend
ufw allow 8000    # RAG Server
ufw allow 8001    # API Server
ufw enable
```

## 📊 **ETAPA 7: MONITORAMENTO E MANUTENÇÃO**

### **7.1 Verificar status completo**

```bash
./status.sh
```

### **7.2 Monitoramento em tempo real**

```bash
./monitor.sh
```

### **7.3 Ver logs específicos**

```bash
# Frontend
tail -f logs/frontend.log

# RAG Server
tail -f logs/rag-server.log

# API Server
tail -f logs/api-server.log

# Todos os logs
tail -f logs/*.log
```

## 🔄 **ETAPA 8: GITHUB ACTIONS - DEPLOY AUTOMÁTICO**

### **8.1 O QUE É GITHUB ACTIONS?**

**🚀 GitHub Actions** é um sistema de **deploy automático** que funciona como o Render:

- ✅ **Commit local** → Deploy automático no servidor
- ✅ **Zero intervenção manual** após configuração
- ✅ **Logs completos** de cada deploy
- ✅ **Rollback automático** se algo der errado

### **8.2 CONFIGURAÇÃO COMPLETA PASSO A PASSO**

#### **A) GERAR CHAVES SSH NO SERVIDOR HOSTINGER:**

```bash
# 1. Conectar no servidor Hostinger
ssh root@31.97.16.142

# 2. Gerar chave SSH para GitHub Actions
ssh-keygen -t rsa -b 4096 -C "github-actions@hostinger"
# Pressione ENTER para aceitar local padrão
# Pressione ENTER para não usar senha

# 3. Ver chave pública (copiar para GitHub)
cat ~/.ssh/id_rsa.pub

# 4. Ver chave privada (copiar para secrets)
cat ~/.ssh/id_rsa
```

#### **B) CONFIGURAR DEPLOY KEY NO GITHUB:**

1. **GitHub.com** → Seu Repo → **Settings**
2. **Sidebar esquerda** → **Deploy keys**
3. **Clique em "Add deploy key"**
4. **Title**: `Hostinger Deploy Key`
5. **Key**: Cole a chave pública (ssh-rsa...)
6. **✅ Allow write access**
7. **Clique em "Add key"**

#### **C) CONFIGURAR SECRETS NO GITHUB:**

1. **GitHub.com** → Seu Repo → **Settings**
2. **Sidebar esquerda** → **Secrets and variables** → **Actions**
3. **Clique em "New repository secret"**

**Secret 1:**

```
Name: HOSTINGER_HOST
Value: 31.97.16.142
```

**Secret 2:**

```
Name: HOSTINGER_USER
Value: root
```

**Secret 3:**

```
Name: HOSTINGER_SSH_KEY
Value: [Cole TODA a chave privada SSH]
```

#### **D) CRIAR WORKFLOW NO SEU COMPUTADOR LOCAL:**

```bash
# 1. No SEU COMPUTADOR LOCAL (NÃO no servidor)
cd /caminho/para/seu/projeto

# 2. Criar estrutura de diretórios
mkdir -p .github/workflows

# 3. Criar arquivo de workflow
# (O arquivo deploy.yml já foi criado automaticamente)

# 4. Verificar se todos os arquivos existem
ls -la
# Deve ter: .github/, src/, backend/, *.sh

# 5. Se faltar arquivos, criar
mkdir -p src backend
touch start_all.sh stop_all.sh status.sh
chmod +x *.sh
```

#### **E) FAZER COMMIT E PUSH:**

```bash
# NO SEU COMPUTADOR LOCAL (NÃO NO SERVIDOR!)
git add .
git commit -m "🚀 Adicionar GitHub Actions + estrutura completa"
git push origin main
```

### **8.3 O QUE ACONTECE APÓS O PUSH:**

1. **Você faz push** → GitHub detecta mudança
2. **GitHub Actions inicia** → Conecta no servidor Hostinger
3. **Servidor para sistema** → `./stop_all.sh`
4. **Servidor atualiza código** → `git pull origin main`
5. **Servidor reinicia sistema** → `./start_all.sh`
6. **Servidor testa endpoints** → Verifica se tudo funcionou
7. **🎉 Deploy automático concluído!**

### **8.4 MONITORAMENTO:**

#### **No GitHub:**

- **GitHub.com** → Seu Repo → **Actions** → Ver logs do deploy

#### **No servidor Hostinger:**

- `./status.sh` para ver status
- `tail -f logs/*.log` para acompanhar logs

### **8.5 ESTRUTURA CORRETA DO REPOSITÓRIO:**

```
chatbot_educacional/
├── .github/
│   └── workflows/
│       └── deploy.yml          ← Workflow GitHub Actions
├── src/                        ← Frontend React
├── backend/                    ← Backend Python
├── start_all.sh                ← Script de inicialização
├── stop_all.sh                 ← Script de parada
├── status.sh                   ← Script de status
└── ... outros arquivos
```

### **8.6 FLUXO CORRETO COMPLETO:**

```
1. Servidor Hostinger → Gera chaves SSH ✅
2. GitHub → Configura secrets ✅
3. Seu Computador → Cria workflow ✅
4. Seu Computador → Adiciona arquivos faltando ✅
5. Seu Computador → Commit + Push ✅
6. GitHub → Executa workflow ✅
7. Workflow → Conecta no servidor ✅
8. Servidor → Recebe deploy ✅
```

**🎯 STATUS ATUAL:**

- ✅ **Etapas 1-3**: Já configuradas
- ❌ **Etapas 4-8**: Precisam ser executadas

### **8.7 VERIFICAÇÃO RÁPIDA:**

```bash
# No seu computador local
ls -la
# Deve mostrar: .github/, src/, backend/, *.sh

# Se faltar algo, criar
mkdir -p src backend
touch start_all.sh stop_all.sh status.sh
chmod +x *.sh

# Commit e push
git add .
git commit -m "🚀 Estrutura completa + GitHub Actions"
git push origin main
```

**🚨 IMPORTANTE:** Execute estes comandos no **SEU COMPUTADOR LOCAL**, NÃO no servidor Hostinger!

### **8.8 VANTAGENS DO GITHUB ACTIONS:**

- ✅ **Deploy automático** como o Render
- ✅ **Commit local → Deploy automático** no servidor
- ✅ **Zero intervenção manual** após configuração
- ✅ **Logs completos** de cada deploy
- ✅ **Rollback automático** se algo der errado
- ✅ **Gratuito** para repositórios públicos
- ✅ **Seguro** usando secrets do GitHub

### **8.9 TROUBLESHOOTING COMUM:**

#### **Erro: "Missing files or directories"**

```bash
# NO SEU COMPUTADOR LOCAL (NÃO no servidor):
# Verificar se todos os arquivos existem
ls -la
# Criar arquivos faltando
mkdir -p src backend
touch start_all.sh stop_all.sh status.sh
chmod +x *.sh

# Fazer commit e push
git add .
git commit -m "🚀 Adicionar arquivos faltando"
git push origin main
```

#### **Erro: "SSH authentication failed"**

**🔑 Verificar no GitHub:**

- ✅ Secret `HOSTINGER_SSH_KEY` contém a chave **PRIVADA** completa
- ✅ Deploy key configurada com a chave **PÚBLICA**
- ✅ Secrets `HOSTINGER_HOST` e `HOSTINGER_USER` configurados

**🔍 Verificar no servidor Hostinger:**

```bash
# Ver chave pública (para deploy key)
cat ~/.ssh/id_rsa.pub

# Ver chave privada (para secret HOSTINGER_SSH_KEY)
cat ~/.ssh/id_rsa
```

#### **Workflow não executa:**

**🔍 Verificar no seu computador local:**

- ✅ Arquivo `.github/workflows/deploy.yml` existe
- ✅ Push foi feito para branch `main`
- ✅ Todos os arquivos (src/, backend/, \*.sh) existem

**🔍 Verificar no GitHub:**

- ✅ Secrets configurados corretamente
- ✅ Deploy key configurada
- ✅ Workflow aparece na aba Actions

**📋 Comandos para verificar:**

```bash
# No seu computador local
ls -la .github/workflows/
git status
git log --oneline -5
```

### **8.10 RESUMO FINAL - ONDE FAZER CADA COISA:**

**🎯 CLAREZA TOTAL:**

#### **✅ NO SERVIDOR HOSTINGER (JÁ FEITO):**

- ✅ **Gerar chaves SSH** ✅
- ✅ **Ajustar scripts** ✅
- ✅ **Configurar sistema** ✅

#### **✅ NO GITHUB (JÁ FEITO):**

- ✅ **Deploy keys** ✅
- ✅ **Secrets** ✅

#### **❌ NO SEU COMPUTADOR LOCAL (PRECISA FAZER):**

- ❌ **Adicionar arquivos faltando** (src/, backend/, \*.sh)
- ❌ **Fazer commit** de tudo
- ❌ **Fazer push** para GitHub

**🔄 FLUXO CORRETO COMPLETO:**

```
1. Servidor Hostinger → Gera chaves SSH ✅
2. GitHub → Configura secrets ✅
3. Seu Computador → Adiciona arquivos faltando ❌
4. Seu Computador → Commit + Push ❌
5. GitHub → Executa workflow ❌
6. Workflow → Conecta no servidor ❌
7. Servidor → Recebe deploy ❌
```

**🚨 O PROBLEMA ATUAL:**
**O servidor Hostinger tem os scripts ajustados, mas o repositório GitHub não tem:**

- ❌ `src/` (frontend)
- ❌ `backend/` (backend)
- ❌ `start_all.sh`, `stop_all.sh`, `status.sh`

**🎯 SOLUÇÃO:**
**No seu computador local, criar os arquivos faltando:**

```bash
# Criar diretórios
mkdir -p src backend

# Criar scripts (copiar do servidor se necessário)
touch start_all.sh stop_all.sh status.sh
chmod +x *.sh

# Commit e push
git add .
git commit -m "🚀 Estrutura completa + scripts"
git push origin main
```

### **8.2 ONDE fazer as mudanças?**

**🎯 IMPORTANTE:** As correções são feitas em **LOCAIS DIFERENTES**:

#### **✅ NO SERVIDOR HOSTINGER:**

- ✅ **Gerar chaves SSH** para GitHub Actions
- ✅ **Ajustar scripts** de inicialização
- ✅ **Configurar sistema** e dependências

#### **✅ NO SEU COMPUTADOR LOCAL:**

- ✅ **Criar workflow** GitHub Actions
- ✅ **Adicionar arquivos faltando** (src/, backend/, \*.sh)
- ✅ **Fazer commit e push** para GitHub

#### **✅ NO GITHUB:**

- ✅ **Configurar secrets** (HOSTINGER_HOST, HOSTINGER_USER, HOSTINGER_SSH_KEY)
- ✅ **Configurar deploy key** (chave pública SSH)

**📋 Fluxo correto:**

1. **Servidor Hostinger** - Gera chaves SSH e ajusta scripts
2. **Seu Computador Local** - Cria workflow e adiciona arquivos faltando
3. **Seu Computador Local** - Commit + Push para GitHub
4. **GitHub** - Executa workflow automaticamente
5. **Workflow** - Conecta no servidor e faz deploy
6. **Servidor** - Recebe código atualizado automaticamente

## 📤 **ETAPA 9: UPLOAD DE MATERIAIS E DADOS**

### **9.1 Estratégia de Deploy**

O sistema usa uma estratégia de **deploy em duas etapas**:

1. **Deploy base** - Clona repositório e configura sistema
2. **Upload de materiais** - Sobe arquivos grandes depois

### **9.2 Copiar arquivos do projeto local**

```bash
# No seu computador local
# Copiar materiais para o servidor
scp -r data/materials/* root@31.97.16.142:/root/dna-forca-complete/data/materials/

# Copiar ChromaDB para o servidor
scp -r backend/data/.chromadb/* root@31.97.16.142:/root/dna-forca-complete/backend/data/.chromadb/
```

### **9.3 Upload automático para GitHub**

```bash
# No servidor da Hostinger
cd /root/dna-forca-complete

# Executar script de upload
./upload_materials.sh

# Fazer upload manual
git add data/
git commit -m "Adicionar materiais e dados do projeto local"
git push origin main
```

### **9.4 Verificar upload**

```bash
# Verificar se os arquivos foram adicionados
git status

# Ver tamanho dos diretórios
du -sh data/materials/
du -sh data/.chromadb/

# Ver arquivos no GitHub
git ls-files | grep -E "data/|chromadb"
```

## 👨‍💼 **ETAPA 10: DEPLOY AUTOMÁTICO (OPCIONAL)**

### **10.1 Configurar Supervisor**

```bash
# O script já criou a configuração
systemctl restart supervisor
systemctl enable supervisor
```

### **10.2 Verificar processos**

```bash
supervisorctl status
supervisorctl restart frontend
supervisorctl restart rag-server
supervisorctl restart api-server
```

## 📁 **ESTRUTURA FINAL DO PROJETO**

```
/root/dna-forca-complete/
├── .env                          # Configurações e API keys
├── start_all.sh                  # Script de inicialização completa
├── stop_all.sh                   # Script de parada completa
├── status.sh                     # Script de status
├── upload_materials.sh           # Script de upload de materiais
├── .venv/                        # Ambiente virtual Python
├── src/                          # Sistema Frontend React
│   ├── components/               # Componentes React
│   ├── pages/                    # Páginas da aplicação
│   ├── store/                    # Estado global (Zustand)
│   ├── types/                    # Tipos TypeScript
│   ├── lib/                      # Bibliotecas e utilitários
│   └── main.tsx                  # Ponto de entrada
├── backend/                      # Sistema Backend completo
│   ├── rag_system/               # Sistema RAG (IA e documentos)
│   │   ├── rag_handler.py        # Servidor RAG principal
│   │   ├── guardrails.py         # Controles de segurança
│   │   └── requirements.txt      # Dependências Python
│   ├── api_server.py             # Servidor API principal
│   ├── auth/                     # Sistema de autenticação
│   ├── chat_agents/              # Agentes de chat
│   ├── config/                   # Configurações
│   ├── data/                     # Dados e materiais
│   ├── utils/                    # Utilitários
│   └── requirements.txt          # Dependências Python
├── data/                         # Dados do sistema
│   ├── materials/                # Materiais para processar
│   └── .chromadb/               # Banco de dados vetorial
├── logs/                         # Logs do sistema
│   ├── frontend.log
│   ├── rag-server.log
│   ├── api-server.log
│   ├── frontend.pid
│   ├── rag-server.pid
│   └── api-server.pid
├── node_modules/                 # Dependências Node.js
├── package.json                  # Configuração Node.js
├── vite.config.ts                # Configuração Vite
├── tailwind.config.js            # Configuração Tailwind CSS
├── tsconfig.json                 # Configuração TypeScript
└── backups/                      # Backups automáticos
```

## 📤 **SCRIPT DE UPLOAD AUTOMÁTICO**

### **Funcionalidades do upload_materials.sh:**

- ✅ **Verificação automática** de arquivos
- ✅ **Contagem de arquivos** e tamanho
- ✅ **Instruções passo a passo** para upload
- ✅ **Suporte a Git LFS** para arquivos grandes
- ✅ **Validação** de repositório git

### **Uso do script:**

```bash
# Verificar arquivos disponíveis
./upload_materials.sh

# Upload automático (se implementado)
./upload_materials.sh --auto

# Ver ajuda
./upload_materials.sh --help
```

## 🚀 **ESTRATÉGIA COMPLETA DE DEPLOY**

### **Fase 1: Deploy Base**

1. ✅ Clonar repositório GitHub
2. ✅ Instalar dependências
3. ✅ Configurar ambiente
4. ✅ Build do frontend
5. ✅ Sistema funcionando

### **Fase 2: Upload de Materiais**

1. 📁 Copiar arquivos do projeto local
2. 📤 Fazer upload para GitHub
3. 📤 Sincronizar repositório
4. 📤 Sistema completo com dados

### **Vantagens desta abordagem:**

- 🚀 **Deploy rápido** - Sistema funcionando em minutos
- 📁 **Flexibilidade** - Escolhe o que subir
- 💾 **Controle de tamanho** - Gerencia arquivos grandes
- 🔄 **Sincronização** - Mantém GitHub atualizado

## 🌐 **URLS DE ACESSO**

### **Acesso Direto:**

- **Frontend**: http://31.97.16.142:3000
- **RAG Server**: http://31.97.16.142:8000
- **API Server**: http://31.97.16.142:8001

### **Acesso via Nginx (Recomendado):**

- **Frontend**: http://31.97.16.142 (página principal)
- **RAG Server**: http://31.97.16.142/rag/
- **API Server**: http://31.97.16.142/api/
- **Documentação RAG**: http://31.97.16.142/rag/docs
- **Documentação API**: http://31.97.16.142/api/docs
- **Health Check**: http://31.97.16.142/health

## 🔧 **COMANDOS ÚTEIS**

### **🔐 Autenticação GitHub (Repositório Privado)**

```bash
# Configurar token (SUBSTITUA SEU_TOKEN_AQUI)
export GITHUB_TOKEN="SEU_TOKEN_AQUI"
export GITHUB_USERNAME="SEU_USERNAME"

# Testar conexão GitHub
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user

# Download do script com autenticação
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -O https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh

# Verificar download
ls -la deploy_frontend_hostinger.sh
head -5 deploy_frontend_hostinger.sh
```

### **🚀 Deploy Rápido (Com Token Configurado)**

```bash
# Deploy completo em um comando
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -O https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh && \
chmod +x deploy_frontend_hostinger.sh && \
./deploy_frontend_hostinger.sh
```

### **Gerenciamento do Sistema**

```bash
# Iniciar sistema completo
./start_all.sh

# Parar sistema completo
./stop_all.sh

# Verificar status
./status.sh

# Reinicializar sistema
./restart.sh

# Monitoramento
./monitor.sh
```

### **Upload de Materiais:**

```bash
# Verificar arquivos disponíveis
./upload_materials.sh

# Fazer upload para GitHub
git add data/
git commit -m "Adicionar materiais e dados"
git push origin main

# Verificar status do git
git status
git ls-files | grep -E "data/|materials"
```

### **Gerenciamento do Frontend**

```bash
# Build do frontend
npm run build

# Iniciar apenas frontend (desenvolvimento)
npm run dev

# Ver logs do frontend
tail -f logs/frontend.log
```

### **Gerenciamento Individual**

```bash
# Iniciar apenas RAG Server
cd backend/rag_system
uvicorn rag_handler:app --host 0.0.0.0 --port 8000 --reload

# Iniciar apenas API Server
uvicorn backend.api_server:app --host 0.0.0.0 --port 8001 --reload

# Ver logs específicos
tail -f logs/rag-server.log
tail -f logs/api-server.log
```

### **Gerenciamento de Dados**

```bash
# Fazer backup
./backup.sh

# Limpeza automática
./cleanup.sh

# Verificar uso de disco
df -h /root/dna-forca-complete/data/
```

## 🚨 **TROUBLESHOOTING**

### **Problema: Frontend não inicia**

```bash
# Verificar logs
tail -f logs/frontend.log

# Verificar se o build existe
ls -la dist/

# Fazer build novamente
npm run build

# Verificar dependências Node.js
npm list

# Verificar se o src/ existe
ls -la src/
```

### **Problema: Sistema não inicia**

```bash
# Verificar logs
tail -f logs/*.log

# Verificar variáveis de ambiente
cat .env

# Verificar dependências
source .venv/bin/activate
pip list
```

### **Problema: Porta já em uso**

```bash
# Verificar o que está usando as portas
netstat -tlnp | grep -E ":3000|:8000|:8001"

# Matar processos
pkill -f "vite.*preview"
pkill -f "uvicorn.*rag_server"
pkill -f "uvicorn.*api_server"
```

### **Problema: Nginx não funciona**

```bash
# Verificar configuração
nginx -t

# Verificar status
systemctl status nginx

# Ver logs do Nginx
tail -f /var/log/nginx/error.log
```

### **Problema: Build do frontend falha**

```bash
# Verificar versão do Node.js
node --version
npm --version

# Limpar cache
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### **Problema: Erro 404 ao baixar script (Repositório Privado)**

```bash
# ❌ ERRO: 404: Not Found
# ✅ SOLUÇÃO: Configurar autenticação GitHub

# 1. Verificar se o token está configurado
echo $GITHUB_TOKEN

# 2. Testar conexão com GitHub
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user

# 3. Verificar acesso ao repositório
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/Matech-AI/chatbot_educacional

# 4. Download correto com autenticação
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -O https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh

# 5. Verificar se o download funcionou
ls -la deploy_frontend_hostinger.sh
head -5 deploy_frontend_hostinger.sh
```

### **Problema: Token GitHub expirado ou inválido**

```bash
# ❌ ERRO: Bad credentials
# ✅ SOLUÇÃO: Renovar token

# 1. Criar novo token no GitHub
# GitHub.com → Settings → Developer settings → Personal access tokens

# 2. Configurar novo token
export GITHUB_TOKEN="NOVO_TOKEN_AQUI"

# 3. Testar novo token
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user

# 4. Fazer download novamente
curl -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -O https://raw.githubusercontent.com/Matech-AI/chatbot_educacional/main/deploy_frontend_hostinger.sh
```

### **Problema: Permissões insuficientes no token**

```bash
# ❌ ERRO: Not found (mesmo com token)
# ✅ SOLUÇÃO: Verificar permissões

# 1. Verificar scopes do token
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user

# 2. Token deve ter permissão 'repo' (Full control of private repositories)
# 3. Se não tiver, criar novo token com permissões corretas
```

## 🚨 **TROUBLESHOOTING DE UPLOAD**

### **Problema: Arquivos muito grandes**

```bash
# Configurar Git LFS
git lfs install
git lfs track "data/**"
git lfs track "*.pdf"
git lfs track "*.docx"

# Adicionar .gitattributes
git add .gitattributes
git commit -m "Configurar Git LFS"
git push origin main
```

### **Problema: Falha no push**

```bash
# Verificar tamanho do repositório
git count-objects -vH

# Limpar histórico se necessário
git gc --aggressive
git prune

# Forçar push
git push origin main --force
```

### **Problema: Arquivos não aparecem**

```bash
# Verificar se foram adicionados
git status
git ls-files | grep -E "data/|materials"

# Verificar se estão no .gitignore
cat .gitignore | grep -i "data\|materials"

# Adicionar manualmente
git add -f data/materials/
git add -f data/.chromadb/
```

## 📈 **OTIMIZAÇÕES RECOMENDADAS**

### **1. Configuração do Frontend**

```bash
# Otimizar build do Vite
cd frontend
nano vite.config.ts

# Adicionar otimizações
build: {
  outDir: 'dist',
  sourcemap: false,
  minify: 'terser',
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom'],
        router: ['react-router-dom']
      }
    }
  }
}
```

### **2. Configuração do Uvicorn**

```bash
# Editar start.sh para usar mais workers
uvicorn rag_server:app --host 0.0.0.0 --port 8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### **3. Configuração do Nginx**

```bash
# Otimizar Nginx para produção
nano /etc/nginx/nginx.conf

# Aumentar workers
worker_processes auto;
worker_connections 1024;

# Adicionar gzip
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

## 🔒 **SEGURANÇA**

### **1. Segurança de Tokens GitHub**

#### **A) Boas Práticas para Tokens:**

```bash
# ✅ RECOMENDADO:
# - Usar expiração de 90 dias para produção
# - Usar permissões mínimas necessárias (apenas 'repo')
# - Nunca compartilhar tokens em logs ou código
# - Revogar tokens não utilizados

# ❌ NUNCA FAZER:
# - Usar tokens sem expiração em produção
# - Dar permissões excessivas (admin, delete_repo, etc.)
# - Compartilhar tokens em mensagens ou commits
# - Usar tokens pessoais em CI/CD público
```

#### **B) Gerenciamento de Tokens:**

```bash
# 1. Listar tokens ativos
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/authorizations

# 2. Revogar token específico (se necessário)
curl -X DELETE \
     -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/authorizations/TOKEN_ID

# 3. Verificar permissões do token atual
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user
```

#### **C) Configuração Segura no Servidor:**

```bash
# 1. Usar variáveis de ambiente (não hardcoded)
export GITHUB_TOKEN="SEU_TOKEN_AQUI"

# 2. Configurar no .bashrc para persistência
echo 'export GITHUB_TOKEN="SEU_TOKEN_AQUI"' >> ~/.bashrc
source ~/.bashrc

# 3. Verificar se está configurado
echo $GITHUB_TOKEN

# 4. Limpar histórico de comandos (opcional)
history -c
```

### **2. Firewall Completo**

```bash
# Configurar firewall restritivo
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 3000
ufw allow 8000
ufw allow 8001
ufw enable
```

### **2. Usuário não-root (Recomendado)**

```bash
# Criar usuário específico
adduser dnaforca
usermod -aG sudo dnaforca

# Transferir projeto
cp -r /root/dna-forca-complete /home/dnaforca/
chown -R dnaforca:dnaforca /home/dnaforca/dna-forca-complete
```

### **3. SSL/HTTPS (Recomendado para produção)**

```bash
# Instalar Certbot
apt install certbot python3-certbot-nginx

# Gerar certificado
certbot --nginx -d seu-dominio.com
```

## 📞 **SUPORTE**

### **Logs importantes**

- **Frontend**: `/root/dna-forca-complete/logs/frontend.log`
- **RAG Server**: `/root/dna-forca-complete/logs/rag-server.log`
- **API Server**: `/root/dna-forca-complete/logs/api-server.log`
- **Nginx**: `/var/log/nginx/`
- **Redis**: `/var/log/redis/`
- **Sistema**: `/var/log/syslog`

### **Comandos de diagnóstico**

```bash
# Status completo do sistema
./status.sh

# Monitoramento em tempo real
./monitor.sh

# Verificar conectividade
ping google.com
curl -I http://localhost:3000
curl -I http://localhost:8000
curl -I http://localhost:8001

# Verificar recursos
free -h
df -h
top
```

## ✅ **CHECKLIST DE DEPLOY COMPLETO**

### **🔐 Autenticação GitHub (Repositório Privado)**

- [ ] Token de acesso pessoal criado no GitHub
- [ ] Token com permissão 'repo' (Full control of private repositories)
- [ ] Token configurado no servidor via `export GITHUB_TOKEN`
- [ ] Conexão GitHub testada com `curl -H "Authorization: token $GITHUB_TOKEN"`
- [ ] Script `deploy_frontend_hostinger.sh` baixado com sucesso

### **🚀 Deploy do Sistema**

- [x] Script de deploy executado
- [x] API keys configuradas no .env
- [x] Dependências Python verificadas (já instaladas pelo script)
- [x] Dependências Node.js verificadas (já instaladas pelo script)
- [x] Estrutura do frontend verificada (src/ existe)
- [x] Frontend buildado (se necessário: npm run build)
- [x] Scripts ajustados para estrutura real do projeto
- [x] **GitHub Actions configurado (deploy automático)**
- [x] Sistema completo iniciado e funcionando
- [x] Nginx configurado e funcionando
- [x] Redis configurado e funcionando
- [x] Firewall configurado
- [x] Backup configurado
- [x] Monitoramento funcionando
- [x] Logs sendo gerados
- [x] Acesso externo funcionando
- [x] Proxy reverso funcionando
- [x] Health checks funcionando
- [x] Frontend acessível via Nginx

### **🔄 GitHub Actions (Deploy Automático)**

- [x] Chaves SSH geradas no servidor Hostinger
- [x] Deploy key configurada no GitHub
- [x] Secrets configurados no GitHub
- [x] Workflow criado no repositório local
- [ ] **Arquivos faltando adicionados no repositório local** ❌
- [ ] **Commit e push feitos do repositório local** ❌
- [ ] **Workflow executado automaticamente** ❌
- [ ] **Deploy automático funcionando** ❌

### **📤 Upload de Materiais:**

- [ ] Arquivos copiados do projeto local
- [ ] Script upload_materials.sh executado
- [ ] Arquivos adicionados ao git
- [ ] Commit realizado
- [ ] Push para GitHub
- [ ] Verificação no GitHub
- [ ] Sistema funcionando com dados

## 🎯 **PRÓXIMOS PASSOS**

### **🔄 ETAPA ATUAL - GITHUB ACTIONS:**

1. **✅ NO SEU COMPUTADOR LOCAL:**

   - [ ] Criar diretórios `src/` e `backend/` (se não existirem)
   - [ ] Criar scripts `start_all.sh`, `stop_all.sh`, `status.sh` (se não existirem)
   - [ ] Fazer commit de tudo: `git add . && git commit -m "🚀 Estrutura completa"`
   - [ ] Fazer push: `git push origin main`

2. **✅ VERIFICAR NO GITHUB:**
   - [ ] Workflow aparece na aba Actions
   - [ ] Workflow executa automaticamente após push
   - [ ] Deploy no servidor Hostinger é bem-sucedido

### **🚀 DEPLOY AUTOMÁTICO FUNCIONANDO:**

3. **Testar deploy automático** fazendo mudanças locais
4. **Verificar logs** do GitHub Actions
5. **Monitorar servidor** durante deploy automático

### **📁 UPLOAD DE MATERIAIS:**

6. **Copiar materiais** do projeto local para o servidor
7. **Executar upload_materials.sh** para subir arquivos
8. **Fazer upload de materiais** via endpoint `/rag/process-materials`

### **🔧 OTIMIZAÇÕES:**

9. **Configurar backup automático** via cron
10. **Implementar monitoramento** mais avançado
11. **Configurar domínio** personalizado (opcional)
12. **Configurar SSL/HTTPS** para produção
13. **Implementar rate limiting** no Nginx
14. **Configurar alertas** de monitoramento

## 🔄 **MIGRAÇÃO DO RENDER**

### **1. Atualizar configurações do frontend**

```javascript
// O frontend já está configurado para usar as URLs locais
// via proxy no vite.config.ts
const API_BASE = "/api"; // Proxy para localhost:8001
const RAG_API_BASE = "/rag-api"; // Proxy para localhost:8000
```

### **2. Testar funcionalidades**

- ✅ Interface do usuário (React)
- ✅ Chat educacional
- ✅ Upload de materiais
- ✅ Processamento RAG
- ✅ Autenticação
- ✅ Gerenciamento de usuários

### **3. Desativar Render**

- Parar serviços no Render
- Redirecionar tráfego para seu VPS
- Monitorar performance

---

## 🎉 **PARABÉNS! SISTEMA COMPLETO FUNCIONANDO!**

**🎯 Você agora tem um sistema COMPLETO (3 SERVIDORES) rodando no seu VPS Hostinger que substitui 100% o Render!**

### **✅ VANTAGENS DO SEU VPS:**

- **Controle total** sobre a infraestrutura
- **Custo reduzido** (sem taxas do Render)
- **Performance dedicada** (200GB disco, 16TB banda)
- **Segurança personalizada** (firewall, SSL)
- **Backup automático** e monitoramento
- **Escalabilidade** conforme necessário
- **Frontend otimizado** com build de produção

### **📋 PARA DÚVIDAS OU PROBLEMAS:**

1. Verifique os logs: `tail -f logs/*.log`
2. Use os scripts de diagnóstico: `./status.sh`
3. Consulte o troubleshooting acima
4. Verifique a documentação das APIs
5. Use o comando de build: `npm run build`

**🚀 Seu sistema DNA da Força está rodando independentemente do Render com FRONTEND + RAG + API!**

### **🎨 FRONTEND ESPECIALMENTE:**

- **Estrutura React** em `src/` com componentes organizados
- **Build otimizado** para produção (`npm run build`)
- **Proxy automático** para APIs via Vite
- **Tailwind CSS** configurado
- **TypeScript** configurado
- **Vite** para desenvolvimento rápido
- **Hot reload** em desenvolvimento (`npm run dev`)
- **Componentes modulares** e páginas organizadas
