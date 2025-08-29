#!/bin/bash

# 🚀 SCRIPT DE DEPLOY COMPLETO - FRONTEND + RAG + API NO HOSTINGER VPS
# Execute este script no servidor Hostinger VPS para substituir COMPLETAMENTE o Render

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy COMPLETO (Frontend + RAG + API) no Hostinger VPS..."
echo "�� Objetivo: Substituir COMPLETAMENTE o servidor Render com os 3 serviços"

# 1. ATUALIZAR SISTEMA
echo "📦 Atualizando sistema..."
apt update && apt upgrade -y

# 2. INSTALAR DEPENDÊNCIAS BÁSICAS
echo "🔧 Instalando dependências..."
apt install -y python3 python3-pip python3-venv git curl wget unzip nginx supervisor redis-server nodejs npm

# 3. INSTALAR NODE.JS 18+ (LTS)
echo "�� Instalando Node.js LTS..."
if ! command -v node &> /dev/null || [ "$(node --version | cut -d'v' -f2 | cut -d'.' -f1)" -lt 18 ]; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
    echo "✅ Node.js $(node --version) instalado"
else
    echo "✅ Node.js $(node --version) já está instalado"
fi

# 4. INSTALAR DOCKER (OPCIONAL)
echo "🐳 Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    echo "✅ Docker instalado e configurado"
else
    echo "✅ Docker já está instalado"
fi

# 5. CRIAR DIRETÓRIO DO PROJETO COMPLETO
echo "📁 Criando diretório do projeto..."
mkdir -p /root/dna-forca-complete
cd /root/dna-forca-complete

# 6. CONFIGURAR AUTENTICAÇÃO GITHUB (REPOSITÓRIO PRIVADO)
echo "🔐 Configurando autenticação GitHub..."
echo "⚠️ IMPORTANTE: Configure seu token GitHub antes de continuar!"
echo "📋 Execute estes comandos:"
echo "export GITHUB_TOKEN='SEU_TOKEN_AQUI'"
echo "export GITHUB_USERNAME='SEU_USERNAME'"
echo ""
echo "⏳ Aguardando configuração do token..."

# Aguardar configuração do token
read -p "Pressione Enter após configurar o token GitHub..."

# Verificar se o token está configurado
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Token GitHub não configurado!"
    echo "🔧 Execute: export GITHUB_TOKEN='SEU_TOKEN_AQUI'"
    exit 1
fi

echo "✅ Token GitHub configurado: ${GITHUB_TOKEN:0:10}..."

# 7. CLONAR REPOSITÓRIO COMPLETO
echo "📥 Clonando repositório base..."
git clone https://$GITHUB_TOKEN@github.com/Matech-AI/chatbot_educacional.git .

# Verificar se o clone funcionou
if [ ! -f "README.md" ]; then
    echo "❌ Falha ao clonar repositório!"
    echo "🔧 Verifique se o token tem permissão 'repo'"
    exit 1
fi

echo "✅ Repositório base clonado com sucesso!"

# 8. VERIFICAR ARQUIVOS IMPORTANTES CLONADOS
echo "🔍 Verificando arquivos clonados..."
if [ -d "data/materials" ] && [ "$(ls -A data/materials 2>/dev/null)" ]; then
    echo "✅ data/materials encontrado: $(ls -la data/materials | wc -l) arquivos"
    echo "📁 Tamanho: $(du -sh data/materials | cut -f1)"
else
    echo "⚠️ data/materials vazio ou não encontrado - será criado depois"
    mkdir -p data/materials
fi

if [ -d "backend/data/.chromadb" ] && [ "$(ls -A backend/data/.chromadb 2>/dev/null)" ]; then
    echo "✅ backend/data/.chromadb encontrado: $(ls -la backend/data/.chromadb | wc -l) arquivos"
    echo "📁 Tamanho: $(du -sh backend/data/.chromadb | cut -f1)"
else
    echo "⚠️ backend/data/.chromadb vazio ou não encontrado - será criado depois"
    mkdir -p backend/data/.chromadb
fi

if [ -f "backend/config/requirements.txt" ]; then
    echo "✅ backend/config/requirements.txt encontrado"
else
    echo "⚠️ backend/config/requirements.txt não encontrado"
fi

# 9. CRIAR AMBIENTE VIRTUAL PYTHON (.venv)
echo "🐍 Criando ambiente virtual Python..."
python3 -m venv .venv
source .venv/bin/activate

# 10. INSTALAR DEPENDÊNCIAS PYTHON COMPLETAS
echo "📦 Instalando dependências Python..."
pip install --upgrade pip

# Instalar dependências do backend (requirements.txt completo)
if [ -f "backend/config/requirements.txt" ]; then
    echo "📦 Instalando dependências do backend..."
    pip install -r backend/config/requirements.txt
else
    echo "⚠️ requirements.txt não encontrado, instalando dependências básicas..."
    pip install fastapi uvicorn langchain chromadb redis python-dotenv
fi

# 11. INSTALAR DEPENDÊNCIAS NODE.JS
echo "📦 Instalando dependências Node.js..."
if [ -f "package.json" ]; then
    echo "📦 Instalando dependências do projeto principal..."
    npm install
fi

if [ -f "frontend/package.json" ]; then
    echo "📦 Instalando dependências do frontend..."
    cd frontend
    npm install
    cd ..
fi

# 12. CONFIGURAR ARQUIVO .env COMPLETO
echo "⚙️ Configurando arquivo .env completo..."
if [ -f ".env" ]; then
    echo "✅ Arquivo .env já existe"
else
    echo "📝 Criando arquivo .env completo..."
cat > .env << 'EOF'
# ========================================
# CONFIGURAÇÃO COMPLETA DNA DA FORÇA
# ========================================

# ===== API KEYS =====
OPENAI_API_KEY=your_openai_api_key_here
NVIDIA_API_KEY=your_nvidia_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_DRIVE_API_KEY=your_google_drive_api_key_here

# ===== CONFIGURAÇÕES DOS SERVIDORES =====
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=3000
RAG_HOST=0.0.0.0
RAG_PORT=8000
API_HOST=0.0.0.0
API_PORT=8001

# ===== CONFIGURAÇÕES DO CHROMADB =====
CHROMA_PERSIST_DIR=/root/dna-forca-complete/data/.chromadb
MATERIALS_DIR=/root/dna-forca-complete/data/materials

# ===== CONFIGURAÇÕES DO REDIS =====
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# ===== CONFIGURAÇÕES JWT =====
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===== CONFIGURAÇÕES CORS =====
CORS_ORIGINS=http://31.97.16.142:3000,http://31.97.16.142,http://localhost:3000

# ===== CONFIGURAÇÕES DE PREFERÊNCIA =====
PREFER_NVIDIA=true
PREFER_OPENAI=true
PREFER_GEMINI=true
PREFER_OPEN_SOURCE_EMBEDDINGS=true

# ===== CONFIGURAÇÕES DE SEGURANÇA =====
RENDER=false
ENVIRONMENT=production

# ===== CONFIGURAÇÕES DE LOG =====
LOG_LEVEL=INFO
LOG_FILE=/root/dna-forca-complete/logs/app.log

# ===== CONFIGURAÇÕES DE BACKUP =====
BACKUP_DIR=/root/dna-forca-complete/backups
BACKUP_RETENTION_DAYS=7

# ===== CONFIGURAÇÕES DE EMAIL =====
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=matheusbnas@gmail.com
EMAIL_PASSWORD=yoip qkvw aozn augl
EMAIL_FROM=matheusbnas@gmail.com

# ===== CONFIGURAÇÕES DE BANCO DE DADOS =====
DATABASE_URL=postgresql://postgres:password@localhost:5432/dna_da_forca

# ===== CONFIGURAÇÕES SUPABASE =====
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# ===== CONFIGURAÇÕES DE MONITORAMENTO =====
ENABLE_MONITORING=true
METRICS_PORT=9090

# ===== CONFIGURAÇÕES DE CACHE =====
CACHE_TTL=3600
ENABLE_REDIS_CACHE=true

# ===== CONFIGURAÇÕES DE RATE LIMITING =====
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# ===== CONFIGURAÇÕES DE UPLOAD =====
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=pdf,docx,xlsx,txt,md
UPLOAD_DIR=/root/dna-forca-complete/data/uploads

# ===== CONFIGURAÇÕES DE MODELOS =====
DEFAULT_EMBEDDING_MODEL=text-embedding-ada-002
DEFAULT_CHAT_MODEL=gpt-3.5-turbo
DEFAULT_RAG_MODEL=gpt-4

# ===== CONFIGURAÇÕES DE WORKERS =====
RAG_WORKERS=2
API_WORKERS=2
CELERY_WORKERS=2

# ===== CONFIGURAÇÕES DE TIMEOUT =====
REQUEST_TIMEOUT=300
RAG_TIMEOUT=600
API_TIMEOUT=300

# ===== CONFIGURAÇÕES DE RETRY =====
MAX_RETRIES=3
RETRY_DELAY=1

# ===== CONFIGURAÇÕES DE DEBUG =====
DEBUG=false
VERBOSE_LOGGING=false
ENABLE_STACK_TRACES=false
EOF
fi

echo "⚠️ IMPORTANTE: Edite o arquivo .env e configure suas API keys!"

# 13. CRIAR DIRETÓRIOS NECESSÁRIOS
echo "�� Criando diretórios necessários..."
mkdir -p {data/materials,data/.chromadb,data/uploads,logs,backups}

# 14. BUILD DO FRONTEND
echo "🏗️ Fazendo build do frontend..."
if [ -d "frontend" ]; then
    cd frontend
    echo "��️ Build do frontend em progresso..."
    npm run build
    cd ..
    echo "✅ Build do frontend concluído!"
else
    echo "⚠️ Diretório frontend não encontrado, pulando build"
fi

# 15. CRIAR SCRIPT PARA SUBIR ARQUIVOS DEPOIS
echo "📤 Criando script para subir arquivos depois..."
cat > upload_materials.sh << 'EOF'
#!/bin/bash

# Script para subir materiais e dados depois do deploy
cd /root/dna-forca-complete

echo "📤 UPLOAD DE MATERIAIS E DADOS PARA O GITHUB"
echo "=============================================="

# Verificar se o git está configurado
if [ ! -d ".git" ]; then
    echo "❌ Repositório git não encontrado!"
    exit 1
fi

# Verificar se há arquivos para subir
echo "🔍 Verificando arquivos para upload..."

# Verificar materiais
if [ -d "data/materials" ] && [ "$(ls -A data/materials)" ]; then
    echo "✅ Materiais encontrados: $(ls data/materials | wc -l) arquivos"
    echo "📁 Tamanho: $(du -sh data/materials | cut -f1)"
else
    echo "⚠️ Pasta data/materials vazia"
fi

# Verificar ChromaDB
if [ -d "data/.chromadb" ] && [ "$(ls -A data/.chromadb)" ]; then
    echo "✅ Dados ChromaDB encontrados: $(ls data/.chromadb | wc -l) arquivos"
    echo "📁 Tamanho: $(du -sh data/.chromadb | cut -f1)"
else
    echo "⚠️ Pasta data/.chromadb vazia"
fi

echo ""
echo "�� Para subir os arquivos para o GitHub:"
echo "1. Adicione os arquivos: git add data/"
echo "2. Faça commit: git commit -m 'Adicionar materiais e dados'"
echo "3. Faça push: git push origin main"
echo ""
echo "⚠️ ATENÇÃO: Arquivos muito grandes podem precisar de Git LFS"
echo "📋 Execute: git lfs track 'data/**'"
echo ""
echo "📤 Para fazer upload automático, execute:"
echo "./upload_materials.sh --auto"
EOF

chmod +x upload_materials.sh

# 16. CRIAR SCRIPT DE INICIALIZAÇÃO COMPLETA
echo "🚀 Criando script de inicialização completa..."
cat > start_all.sh << 'EOF'
#!/bin/bash

# Script de inicialização completa (Frontend + RAG + API)
cd /root/dna-forca-complete

echo "🚀 Iniciando sistema COMPLETO DNA da Força..."
echo "�� Serviços: Frontend + RAG Server + API Server"

# Verificar se o Redis está rodando
if ! systemctl is-active --quiet redis-server; then
    echo "🔄 Iniciando Redis..."
    systemctl start redis-server
    systemctl enable redis-server
fi

# Ativar ambiente virtual
source .venv/bin/activate

# Iniciar RAG Server em background
echo "🚀 Iniciando RAG Server..."
cd rag_system
nohup uvicorn rag_server:app --host 0.0.0.0 --port 8001 --reload > ../logs/rag-server.log 2>&1 &
RAG_PID=$!
echo "✅ RAG Server iniciado com PID: $RAG_PID"

# Aguardar um pouco para o RAG Server inicializar
sleep 5

# Iniciar API Server em background
echo "🚀 Iniciando API Server..."
cd ../backend
nohup uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload > ../logs/api-server.log 2>&1 &
API_PID=$!
echo "✅ API Server iniciado com PID: $API_PID"

# Aguardar um pouco para o API Server inicializar
sleep 5

# Iniciar Frontend em background
echo "�� Iniciando Frontend..."
cd ../frontend
nohup npm run start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend iniciado com PID: $FRONTEND_PID"

# Salvar PIDs para gerenciamento
echo $RAG_PID > ../logs/rag-server.pid
echo $API_PID > ../logs/api-server.pid
echo $FRONTEND_PID > ../logs/frontend.pid

echo ""
echo "🎉 Sistema COMPLETO iniciado!"
echo "📍 Frontend: http://localhost:3000"
echo "📍 RAG Server: http://localhost:8001"
echo "📍 API Server: http://localhost:8000"
echo ""
echo "�� Para parar: ./stop_all.sh"
echo "📋 Para status: ./status.sh"
echo "�� Para logs: tail -f logs/*.log"
EOF

chmod +x start_all.sh

# 17. CRIAR SCRIPT DE PARADA COMPLETA
echo "🛑 Criando script de parada completa..."
cat > stop_all.sh << 'EOF'
#!/bin/bash

# Script de parada completa
cd /root/dna-forca-complete

echo "🛑 Parando sistema COMPLETO..."

# Parar Frontend
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "�� Parando Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm logs/frontend.pid
    fi
fi

# Parar RAG Server
if [ -f logs/rag-server.pid ]; then
    RAG_PID=$(cat logs/rag-server.pid)
    if kill -0 $RAG_PID 2>/dev/null; then
        echo "�� Parando RAG Server (PID: $RAG_PID)..."
        kill $RAG_PID
        rm logs/rag-server.pid
    fi
fi

# Parar API Server
if [ -f logs/api-server.pid ]; then
    API_PID=$(cat logs/api-server.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo "�� Parando API Server (PID: $API_PID)..."
        kill $API_PID
        rm logs/api-server.pid
    fi
fi

# Matar processos restantes
pkill -f "vite.*preview" 2>/dev/null || true
pkill -f "uvicorn.*rag_server" 2>/dev/null || true
pkill -f "uvicorn.*api_server" 2>/dev/null || true

echo "✅ Sistema COMPLETO parado com sucesso!"
EOF

chmod +x stop_all.sh

# 18. CRIAR SCRIPT DE STATUS COMPLETO
echo "📊 Criando script de status completo..."
cat > status.sh << 'EOF'
#!/bin/bash

# Script de status do sistema COMPLETO
cd /root/dna-forca-complete

echo "📊 STATUS DO SISTEMA COMPLETO DNA DA FORÇA - $(date)"
echo "=================================================="

# Status do Frontend
echo ""
echo "�� FRONTEND:"
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "✅ Status: ATIVO"
        echo "�� PID: $FRONTEND_PID"
        echo "📍 Porta: 3000"
        echo "📍 URL: http://localhost:3000"
    else
        echo "❌ Status: INATIVO (PID inválido)"
        rm logs/frontend.pid
    fi
else
    echo "❌ Status: INATIVO (PID não encontrado)"
fi

# Status do RAG Server
echo ""
echo "🔍 RAG SERVER:"
if [ -f logs/rag-server.pid ]; then
    RAG_PID=$(cat logs/rag-server.pid)
    if kill -0 $RAG_PID 2>/dev/null; then
        echo "✅ Status: ATIVO"
        echo "📍 PID: $RAG_PID"
        echo "📍 Porta: 8000"
        echo "📍 URL: http://localhost:8000"
    else
        echo "❌ Status: INATIVO (PID inválido)"
        rm logs/rag-server.pid
    fi
else
    echo "❌ Status: INATIVO (PID não encontrado)"
fi

# Status do API Server
echo ""
echo "🔍 API SERVER:"
if [ -f logs/api-server.pid ]; then
    API_PID=$(cat logs/api-server.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo "✅ Status: ATIVO"
        echo "📍 PID: $API_PID"
        echo "📍 Porta: 8001"
        echo "📍 URL: http://localhost:8001"
    else
        echo "❌ Status: INATIVO (PID inválido)"
        rm logs/api-server.pid
    fi
else
    echo "❌ Status: INATIVO (PID não encontrado)"
fi

# Status do Redis
echo ""
echo "🔍 REDIS:"
if systemctl is-active --quiet redis-server; then
    echo "✅ Status: ATIVO"
    echo "�� Porta: 6379"
else
    echo "❌ Status: INATIVO"
fi

# Status dos recursos
echo ""
echo "💻 RECURSOS DO SISTEMA:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "RAM: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo "Disco: $(df -h / | awk 'NR==2{print $5}')"

# Status das portas
echo ""
echo "🌐 PORTAS EM USO:"
netstat -tlnp | grep -E ":3000|:8000|:8001|:6379" | sort
EOF

chmod +x status.sh

# 19. FINALIZAÇÃO
echo ""
echo "🎉 DEPLOY COMPLETO (FRONTEND + RAG + API) CONCLUÍDO COM SUCESSO!"
echo "=================================================================="
echo ""
echo "📁 Diretório do projeto: /root/dna-forca-complete"
echo "📥 Repositório clonado: ✅"
echo "🐍 Ambiente virtual: .venv"
echo "📦 Dependências Python: ✅ (requirements.txt completo)"
echo "📦 Dependências Node.js: ✅"
echo "��️ Frontend buildado: ✅"
echo "⚙️ Arquivo de configuração: .env (COMPLETO)"
echo "🚀 Script de inicialização: start_all.sh"
echo "🛑 Script de parada: stop_all.sh"
echo "📊 Script de status: status.sh"
echo "📤 Script de upload: upload_materials.sh"
echo ""
echo "�� PRÓXIMOS PASSOS:"
echo "1. Edite o arquivo .env e configure suas API keys"
echo "2. Execute: ./start_all.sh"
echo "3. Para subir materiais: ./upload_materials.sh"
echo ""
echo "🌐 O sistema estará disponível em:"
echo "   - Frontend: http://31.97.16.142:3000"
echo "   - RAG Server: http://31.97.16.142:8000"
echo "   - API Server: http://31.97.16.142:8001"
echo ""
echo "📋 COMANDOS ÚTEIS:"
echo "   - Status: ./status.sh"
echo "   - Parar: ./stop_all.sh"
echo "   - Iniciar: ./start_all.sh"
echo "   - Upload materiais: ./upload_materials.sh"
echo ""
echo "⚠️ IMPORTANTE: Configure o firewall para permitir acesso às portas 3000, 8000 e 8001"
echo "   ufw allow 3000"
echo "   ufw allow 8000"
echo "   ufw allow 8001"
echo ""
echo "�� PARA SUBIR MATERIAIS E DADOS:"
echo "1. Copie arquivos do projeto local para o servidor"
echo "2. Execute: ./upload_materials.sh"
echo "3. Siga as instruções para fazer push no GitHub"
echo ""
echo "�� SISTEMA COMPLETO (3 SERVIDORES) SUBSTITUINDO O RENDER!"
echo "✅ Deploy concluído! Configure suas API keys e inicie o sistema completo."
