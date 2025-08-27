#!/bin/bash

# 🚀 SCRIPT DE DEPLOY COMPLETO - FRONTEND + RAG + API NO HOSTINGER VPS
# Execute este script no servidor Hostinger VPS para substituir COMPLETAMENTE o Render

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy COMPLETO (Frontend + RAG + API) no Hostinger VPS..."
echo "🎯 Objetivo: Substituir COMPLETAMENTE o servidor Render com os 3 serviços"

# 1. ATUALIZAR SISTEMA
echo "📦 Atualizando sistema..."
apt update && apt upgrade -y

# 2. INSTALAR DEPENDÊNCIAS BÁSICAS
echo "🔧 Instalando dependências..."
apt install -y python3 python3-pip python3-venv git curl wget unzip nginx supervisor redis-server nodejs npm

# 3. INSTALAR NODE.JS 18+ (LTS)
echo "🟢 Instalando Node.js LTS..."
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
echo "📁 Criando estrutura de diretórios..."
mkdir -p /root/dna-forca-complete
cd /root/dna-forca-complete

# 6. CRIAR ESTRUTURA COMPLETA
echo "🏗️ Criando estrutura completa do projeto..."
mkdir -p {frontend,rag_server,api_server,shared,data/materials,data/.chromadb,logs,scripts,backups}

# 7. CRIAR ARQUIVO .env PRINCIPAL
echo "⚙️ Criando arquivo de configuração principal..."
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
# Frontend
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=3000
FRONTEND_BUILD_DIR=dist

# RAG Server
RAG_HOST=0.0.0.0
RAG_PORT=8000
RAG_WORKERS=2

# API Server
API_HOST=0.0.0.0
API_PORT=8001
API_WORKERS=2

# ===== CONFIGURAÇÕES DO CHROMADB =====
CHROMA_PERSIST_DIR=/root/dna-forca-complete/data/.chromadb
MATERIALS_DIR=/root/dna-forca-complete/data/materials

# ===== CONFIGURAÇÕES DE PREFERÊNCIA =====
PREFER_NVIDIA=true
PREFER_OPENAI=true
PREFER_GEMINI=true
PREFER_OPEN_SOURCE_EMBEDDINGS=true

# ===== CONFIGURAÇÕES DE SEGURANÇA =====
RENDER=false
ENVIRONMENT=production

# ===== CONFIGURAÇÕES DO REDIS =====
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

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

# ===== CONFIGURAÇÕES JWT =====
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===== CONFIGURAÇÕES CORS =====
CORS_ORIGINS=http://31.97.16.142:3000,http://31.97.16.142,http://localhost:3000,http://127.0.0.1:3000
EOF

echo "⚠️ IMPORTANTE: Edite o arquivo .env e configure suas API keys!"

# 8. CRIAR REQUIREMENTS.TXT PARA RAG SERVER
echo "📋 Criando requirements.txt para RAG Server..."
cat > rag_server/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
langchain==0.1.0
langchain-openai==0.0.2
langchain-community==0.0.10
langchain-google-genai==0.0.5
langgraph==0.0.20
chromadb==0.4.18
openai==1.3.7
pandas==2.1.3
pydantic==2.5.0
python-multipart==0.0.6
aiofiles==23.2.1
sentence-transformers==2.2.2
tiktoken==0.5.1
PyPDF2==3.0.1
openpyxl==3.1.2
redis==5.0.1
celery==5.3.4
EOF

# 9. CRIAR REQUIREMENTS.TXT PARA API SERVER
echo "📋 Criando requirements.txt para API Server..."
cat > api_server/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
python-multipart==0.0.6
aiofiles==23.2.1
redis==5.0.1
celery==5.3.4
httpx==0.25.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
jinja2==3.1.2
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
EOF

# 10. CRIAR REQUIREMENTS.TXT COMPARTILHADO
echo "📋 Criando requirements.txt compartilhado..."
cat > shared/requirements.txt << 'EOF'
python-dotenv==1.0.0
pydantic==2.5.0
redis==5.0.1
celery==5.3.4
httpx==0.25.2
EOF

# 11. CRIAR PACKAGE.JSON PARA FRONTEND
echo "📦 Criando package.json para Frontend..."
cat > frontend/package.json << 'EOF'
{
  "name": "dna-forca-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview",
    "start": "vite preview --host 0.0.0.0 --port 3000"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.1",
    "zustand": "^4.3.8",
    "axios": "^1.4.0",
    "lucide-react": "^0.263.1",
    "clsx": "^1.2.1",
    "tailwind-merge": "^1.13.2"
  },
  "devDependencies": {
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.0.3",
    "autoprefixer": "^10.4.14",
    "eslint": "^8.45.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.3",
    "postcss": "^8.4.27",
    "tailwindcss": "^3.3.3",
    "typescript": "^5.0.2",
    "vite": "^4.4.5"
  }
}
EOF

# 12. CRIAR VITE.CONFIG.TS PARA FRONTEND
echo "⚡ Criando vite.config.ts para Frontend..."
cat > frontend/vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
      '/rag-api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
EOF

# 13. CRIAR TAILWIND.CONFIG.JS PARA FRONTEND
echo "🎨 Criando tailwind.config.js para Frontend..."
cat > frontend/tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      }
    },
  },
  plugins: [],
}
EOF

# 14. CRIAR POSTCSS.CONFIG.JS PARA FRONTEND
echo "🔄 Criando postcss.config.js para Frontend..."
cat > frontend/postcss.config.js << 'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF

# 15. CRIAR TSConfig.JSON PARA FRONTEND
echo "📝 Criando tsconfig.json para Frontend..."
cat > frontend/tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF

# 16. CRIAR TSConfig.NODE.JSON PARA FRONTEND
echo "📝 Criando tsconfig.node.json para Frontend..."
cat > frontend/tsconfig.node.json << 'EOF'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
EOF

# 17. CRIAR INDEX.HTML PARA FRONTEND
echo "🌐 Criando index.html para Frontend..."
cat > frontend/index.html << 'EOF'
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DNA da Força - IA Educacional</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF

# 18. CRIAR SCRIPT DE INICIALIZAÇÃO DO FRONTEND
echo "🚀 Criando script de inicialização do Frontend..."
cat > frontend/start.sh << 'EOF'
#!/bin/bash

# Script de inicialização do Frontend
cd /root/dna-forca-complete/frontend

# Verificar se o node_modules existe
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependências do Frontend..."
    npm install
fi

# Verificar se o build existe
if [ ! -d "dist" ]; then
    echo "🏗️ Fazendo build do Frontend..."
    npm run build
fi

echo "🚀 Iniciando Frontend..."
echo "📍 Host: 0.0.0.0"
echo "📍 Port: 3000"
echo "📍 Build: dist/"

# Iniciar servidor de produção
npm run start
EOF

chmod +x frontend/start.sh

# 19. CRIAR SCRIPT DE BUILD DO FRONTEND
echo "🏗️ Criando script de build do Frontend..."
cat > frontend/build.sh << 'EOF'
#!/bin/bash

# Script de build do Frontend
cd /root/dna-forca-complete/frontend

echo "🏗️ Fazendo build do Frontend..."

# Limpar build anterior
rm -rf dist

# Instalar dependências se necessário
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependências..."
    npm install
fi

# Fazer build
npm run build

echo "✅ Build concluído em dist/"
echo "📁 Tamanho do build: $(du -sh dist | cut -f1)"
EOF

chmod +x frontend/build.sh

# 20. CRIAR SCRIPT DE INICIALIZAÇÃO DO RAG SERVER
echo "🚀 Criando script de inicialização do RAG Server..."
cat > rag_server/start.sh << 'EOF'
#!/bin/bash

# Script de inicialização do RAG Server
cd /root/dna-forca-complete/rag_server

# Ativar ambiente virtual
source ../venv/bin/activate

# Verificar variáveis de ambiente
if [ ! -f ../.env ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "⚠️ Configure suas API keys no arquivo .env"
    exit 1
fi

# Carregar variáveis de ambiente
export $(cat ../.env | xargs)

# Verificar se as API keys estão configuradas
if [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ] && [ "$NVIDIA_API_KEY" = "your_nvidia_api_key_here" ]; then
    echo "❌ API keys não configuradas!"
    echo "⚠️ Edite o arquivo .env e configure suas API keys"
    exit 1
fi

echo "🚀 Iniciando RAG Server..."
echo "📍 Host: $RAG_HOST"
echo "📍 Port: $RAG_PORT"
echo "📍 Workers: $RAG_WORKERS"
echo "📍 ChromaDB: $CHROMA_PERSIST_DIR"
echo "📍 Materiais: $MATERIALS_DIR"

# Iniciar servidor
uvicorn rag_server:app --host $RAG_HOST --port $RAG_PORT --workers $RAG_WORKERS --reload
EOF

chmod +x rag_server/start.sh

# 21. CRIAR SCRIPT DE INICIALIZAÇÃO DO API SERVER
echo "🚀 Criando script de inicialização do API Server..."
cat > api_server/start.sh << 'EOF'
#!/bin/bash

# Script de inicialização do API Server
cd /root/dna-forca-complete/api_server

# Ativar ambiente virtual
source ../venv/bin/activate

# Verificar variáveis de ambiente
if [ ! -f ../.env ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "⚠️ Configure suas API keys no arquivo .env"
    exit 1
fi

# Carregar variáveis de ambiente
export $(cat ../.env | xargs)

echo "🚀 Iniciando API Server..."
echo "📍 Host: $API_HOST"
echo "📍 Port: $API_PORT"
echo "📍 Workers: $API_WORKERS"
echo "📍 Redis: $REDIS_HOST:$REDIS_PORT"

# Iniciar servidor
uvicorn api_server:app --host $API_HOST --port $API_PORT --workers $API_WORKERS --reload
EOF

chmod +x api_server/start.sh

# 22. CRIAR SCRIPT DE INICIALIZAÇÃO COMPLETA
echo "🚀 Criando script de inicialização completa..."
cat > start_all.sh << 'EOF'
#!/bin/bash

# Script de inicialização completa (Frontend + RAG + API)
cd /root/dna-forca-complete

echo "🚀 Iniciando sistema COMPLETO DNA da Força..."
echo "🎯 Serviços: Frontend + RAG Server + API Server"

# Verificar se o Redis está rodando
if ! systemctl is-active --quiet redis-server; then
    echo "🔄 Iniciando Redis..."
    systemctl start redis-server
    systemctl enable redis-server
fi

# Verificar se o Nginx está rodando
if ! systemctl is-active --quiet nginx; then
    echo "🔄 Iniciando Nginx..."
    systemctl start nginx
    systemctl enable nginx
fi

# Iniciar RAG Server em background
echo "🚀 Iniciando RAG Server..."
cd rag_server
nohup ./start.sh > ../logs/rag-server.log 2>&1 &
RAG_PID=$!
echo "✅ RAG Server iniciado com PID: $RAG_PID"

# Aguardar um pouco para o RAG Server inicializar
sleep 5

# Iniciar API Server em background
echo "🚀 Iniciando API Server..."
cd ../api_server
nohup ./start.sh > ../logs/api-server.log 2>&1 &
API_PID=$!
echo "✅ API Server iniciado com PID: $API_PID"

# Aguardar um pouco para o API Server inicializar
sleep 5

# Iniciar Frontend em background
echo "🚀 Iniciando Frontend..."
cd ../frontend
nohup ./start.sh > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend iniciado com PID: $FRONTEND_PID"

# Salvar PIDs para gerenciamento
echo $RAG_PID > ../logs/rag-server.pid
echo $API_PID > ../logs/api-server.pid
echo $FRONTEND_PID > ../logs/frontend.pid

echo ""
echo "🎉 Sistema COMPLETO iniciado!"
echo "📍 Frontend: http://localhost:3000"
echo "📍 RAG Server: http://localhost:8000"
echo "📍 API Server: http://localhost:8001"
echo "📍 Nginx Proxy: http://localhost"
echo ""
echo "📋 Para parar: ./stop_all.sh"
echo "📋 Para status: ./status.sh"
echo "📋 Para logs: tail -f logs/*.log"
EOF

chmod +x start_all.sh

# 23. CRIAR SCRIPT DE PARADA COMPLETA
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
        echo "🛑 Parando Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm logs/frontend.pid
    fi
fi

# Parar RAG Server
if [ -f logs/rag-server.pid ]; then
    RAG_PID=$(cat logs/rag-server.pid)
    if kill -0 $RAG_PID 2>/dev/null; then
        echo "🛑 Parando RAG Server (PID: $RAG_PID)..."
        kill $RAG_PID
        rm logs/rag-server.pid
    fi
fi

# Parar API Server
if [ -f logs/api-server.pid ]; then
    API_PID=$(cat logs/api-server.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo "🛑 Parando API Server (PID: $API_PID)..."
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

# 24. CRIAR SCRIPT DE STATUS COMPLETO
echo "📊 Criando script de status completo..."
cat > status.sh << 'EOF'
#!/bin/bash

# Script de status do sistema COMPLETO
cd /root/dna-forca-complete

echo "📊 STATUS DO SISTEMA COMPLETO DNA DA FORÇA - $(date)"
echo "=================================================="

# Status do Frontend
echo ""
echo "🔍 FRONTEND:"
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "✅ Status: ATIVO"
        echo "📍 PID: $FRONTEND_PID"
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
    echo "📍 Porta: 6379"
else
    echo "❌ Status: INATIVO"
fi

# Status do Nginx
echo ""
echo "🔍 NGINX:"
if systemctl is-active --quiet nginx; then
    echo "✅ Status: ATIVO"
    echo "📍 Porta: 80"
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
netstat -tlnp | grep -E ":3000|:8000|:8001|:6379|:80" | sort
EOF

chmod +x status.sh

# 25. CRIAR SCRIPT DE INSTALAÇÃO COMPLETA
echo "📦 Criando script de instalação completa..."
cat > install.sh << 'EOF'
#!/bin/bash

# Script de instalação completa
cd /root/dna-forca-complete

echo "🐍 Criando ambiente virtual Python..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Instalando dependências compartilhadas..."
pip install --upgrade pip
pip install -r shared/requirements.txt

echo "📦 Instalando dependências do RAG Server..."
pip install -r rag_server/requirements.txt

echo "📦 Instalando dependências do API Server..."
pip install -r api_server/requirements.txt

echo "📦 Instalando dependências do Frontend..."
cd frontend
npm install
cd ..

echo "✅ Todas as dependências instaladas com sucesso!"
echo "🚀 Execute './start_all.sh' para iniciar o sistema COMPLETO"
EOF

chmod +x install.sh

# 26. CRIAR CONFIGURAÇÃO DO SUPERVISOR COMPLETA
echo "👨‍💼 Criando configuração do Supervisor completa..."
cat > /etc/supervisor/conf.d/dna-forca-complete.conf << 'EOF'
[program:frontend]
command=/root/dna-forca-complete/frontend/start.sh
directory=/root/dna-forca-complete/frontend
user=root
autostart=true
autorestart=true
stderr_logfile=/root/dna-forca-complete/logs/frontend.err.log
stdout_logfile=/root/dna-forca-complete/logs/frontend.out.log
environment=HOME="/root"

[program:rag-server]
command=/root/dna-forca-complete/rag_server/start.sh
directory=/root/dna-forca-complete/rag_server
user=root
autostart=true
autorestart=true
stderr_logfile=/root/dna-forca-complete/logs/rag-server.err.log
stdout_logfile=/root/dna-forca-complete/logs/rag-server.out.log
environment=HOME="/root"

[program:api-server]
command=/root/dna-forca-complete/api_server/start.sh
directory=/root/dna-forca-complete/api_server
user=root
autostart=true
autorestart=true
stderr_logfile=/root/dna-forca-complete/logs/api-server.err.log
stdout_logfile=/root/dna-forca-complete/logs/api-server.out.log
environment=HOME="/root"
EOF

# 27. CRIAR CONFIGURAÇÃO DO NGINX COMPLETA
echo "🌐 Criando configuração do Nginx completa..."
cat > /etc/nginx/sites-available/dna-forca-complete << 'EOF'
server {
    listen 80;
    server_name 31.97.16.142;

    # Frontend (React)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # RAG Server
    location /rag/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Server
    location /api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Documentação RAG
    location /rag/docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }

    # Documentação API
    location /api/docs {
        proxy_pass http://127.0.0.1:8001/docs;
    }

    # Health check
    location /health {
        return 200 "OK";
        add_header Content-Type text/plain;
    }

    # Static files (se necessário)
    location /static/ {
        alias /root/dna-forca-complete/frontend/dist/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Ativar site do Nginx
ln -sf /etc/nginx/sites-available/dna-forca-complete /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 28. CRIAR SCRIPT DE BACKUP COMPLETO
echo "💾 Criando script de backup completo..."
cat > backup.sh << 'EOF'
#!/bin/bash

# Script de backup completo
cd /root/dna-forca-complete

echo "💾 Criando backup completo..."

# Backup dos dados
tar -czf "backups/data-$(date +%Y%m%d-%H%M%S).tar.gz" data/

# Backup da configuração
tar -czf "backups/config-$(date +%Y%m%d-%H%M%S).tar.gz" .env *.txt

# Backup dos logs
tar -czf "backups/logs-$(date +%Y%m%d-%H%M%S).tar.gz" logs/

# Backup do frontend build
if [ -d "frontend/dist" ]; then
    tar -czf "backups/frontend-$(date +%Y%m%d-%H%M%S).tar.gz" frontend/dist/
fi

# Limpar backups antigos
find backups/ -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup completo criado em backups/"
echo "🗑️ Backups antigos (>7 dias) foram removidos automaticamente"
EOF

chmod +x backup.sh

# 29. CRIAR SCRIPT DE MONITORAMENTO COMPLETO
echo "📊 Criando script de monitoramento completo..."
cat > monitor.sh << 'EOF'
#!/bin/bash

# Script de monitoramento completo
cd /root/dna-forca-complete

echo "📊 MONITORAMENTO COMPLETO - $(date)"
echo "====================================="

# Executar status
./status.sh

# Verificar logs em tempo real
echo ""
echo "📋 ÚLTIMOS LOGS:"
echo "🔍 Frontend (últimas 5 linhas):"
tail -n 5 logs/frontend.log 2>/dev/null || echo "Log não disponível"

echo ""
echo "🔍 RAG Server (últimas 5 linhas):"
tail -n 5 logs/rag-server.log 2>/dev/null || echo "Log não disponível"

echo ""
echo "🔍 API Server (últimas 5 linhas):"
tail -n 5 logs/api-server.log 2>/dev/null || echo "Log não disponível"

# Verificar uso de disco dos dados
echo ""
echo "💾 USO DE DISCO:"
df -h /root/dna-forca-complete/data/

# Verificar tamanho dos logs
echo ""
echo "📋 TAMANHO DOS LOGS:"
du -sh logs/* 2>/dev/null || echo "Logs não disponíveis"

# Verificar tamanho do frontend
echo ""
echo "🌐 TAMANHO DO FRONTEND:"
if [ -d "frontend/dist" ]; then
    du -sh frontend/dist/
else
    echo "Build do frontend não encontrado"
fi
EOF

chmod +x monitor.sh

# 30. CRIAR SCRIPT DE BUILD AUTOMÁTICO
echo "🏗️ Criando script de build automático..."
cat > build_frontend.sh << 'EOF'
#!/bin/bash

# Script de build automático do frontend
cd /root/dna-forca-complete

echo "🏗️ BUILD AUTOMÁTICO DO FRONTEND..."

# Parar frontend se estiver rodando
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🛑 Parando frontend para rebuild..."
        kill $FRONTEND_PID
        rm logs/frontend.pid
        sleep 2
    fi
fi

# Fazer build
cd frontend
./build.sh

# Reiniciar frontend
cd ..
echo "🚀 Reiniciando frontend..."
cd frontend
nohup ./start.sh > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
echo "✅ Frontend reiniciado com PID: $FRONTEND_PID"

echo "🎉 Build e reinicialização concluídos!"
EOF

chmod +x build_frontend.sh

# 31. FINALIZAÇÃO
echo ""
echo "🎉 DEPLOY COMPLETO (FRONTEND + RAG + API) CONCLUÍDO COM SUCESSO!"
echo "=================================================================="
echo ""
echo "📁 Diretório do projeto: /root/dna-forca-complete"
echo "⚙️ Arquivo de configuração: .env"
echo "🚀 Script de inicialização completa: start_all.sh"
echo "📦 Script de instalação: install.sh"
echo "🏗️ Script de build do frontend: build_frontend.sh"
echo "🛑 Script de parada: stop_all.sh"
echo "📊 Script de status: status.sh"
echo "💾 Script de backup: backup.sh"
echo "📊 Script de monitoramento: monitor.sh"
echo ""
echo "🔧 PRÓXIMOS PASSOS:"
echo "1. Edite o arquivo .env e configure suas API keys"
echo "2. Execute: ./install.sh"
echo "3. Execute: ./build_frontend.sh (para build do frontend)"
echo "4. Execute: ./start_all.sh"
echo ""
echo "🌐 O sistema estará disponível em:"
echo "   - Frontend: http://31.97.16.142 (via Nginx)"
echo "   - Frontend Direto: http://31.97.16.142:3000"
echo "   - RAG Server: http://31.97.16.142:8000"
echo "   - API Server: http://31.97.16.142:8001"
echo "   - Nginx Proxy: http://31.97.16.142/rag/ e /api/"
echo "   - Documentação RAG: http://31.97.16.142/rag/docs"
echo "   - Documentação API: http://31.97.16.142/api/docs"
echo ""
echo "📋 COMANDOS ÚTEIS:"
echo "   - Status: ./status.sh"
echo "   - Monitoramento: ./monitor.sh"
echo "   - Backup: ./backup.sh"
echo "   - Build Frontend: ./build_frontend.sh"
echo "   - Reinicializar: ./restart.sh"
echo ""
echo "⚠️ IMPORTANTE: Configure o firewall para permitir acesso às portas 80, 3000, 8000 e 8001"
echo "   ufw allow 80"
echo "   ufw allow 3000"
echo "   ufw allow 8000"
echo "   ufw allow 8001"
echo ""
echo "🎯 SISTEMA COMPLETO (3 SERVIDORES) SUBSTITUINDO O RENDER!"
echo "✅ Deploy concluído! Configure suas API keys e inicie o sistema completo."
