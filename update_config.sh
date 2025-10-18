#!/bin/bash

echo "🚀 ATUALIZADOR DE CONFIGURAÇÕES - DNA DA FORÇA"
echo "================================================"

# Navegar para o diretório do projeto
cd /root/dna-forca-complete

# Detectar IP do servidor automaticamente
echo "🌐 Detectando IP do servidor..."
SERVER_IP=$(curl -4 -s ifconfig.me 2>/dev/null || curl -s ifconfig.me 2>/dev/null || echo "localhost")

echo "📍 IP detectado: $SERVER_IP"

# Ativar ambiente virtual
source .venv/bin/activate

# Executar script Python de atualização
echo "🔧 Executando atualização de configurações..."
cd backend
python3 update_config.py

# Voltar ao diretório raiz
cd ..

# Atualizar variáveis de ambiente
export HOSTINGER=true
export SERVER_IP=$SERVER_IP
export RAG_PORT=8000
export API_PORT=8001
export FRONTEND_PORT=3000

# Criar arquivo .env se não existir
if [ ! -f ".env" ]; then
    echo "📝 Criando arquivo .env..."
    cat > .env << EOF
# Configurações específicas para o ambiente Hostinger
HOSTINGER=true
SERVER_IP=$SERVER_IP

# Portas dos serviços
RAG_PORT=8000
API_PORT=8001
FRONTEND_PORT=3000

# CORS Origins
CORS_ORIGINS=http://$SERVER_IP:3000,http://$SERVER_IP,http://localhost:3000,https://iadnadaforca.com.br,https://www.iadnadaforca.com.br

# Ambiente
ENVIRONMENT=production

# Caminhos dos dados
CHROMADB_PATH=/root/dna-forca-complete/backend/data/.chromadb
MATERIALS_PATH=/root/dna-forca-complete/backend/data/materials
EOF
    echo "✅ Arquivo .env criado"
else
    echo "✅ Arquivo .env já existe"
fi

# Atualizar vite.config.ts
echo "🔧 Atualizando vite.config.ts..."
if [ -f "vite.config.ts" ]; then
    # Substituir IPs estáticos por variáveis
    sed -i "s/31\.97\.16\.142/$SERVER_IP/g" vite.config.ts
    echo "✅ vite.config.ts atualizado"
else
    echo "❌ vite.config.ts não encontrado"
fi

# Testar conectividade
echo ""
echo "🔍 Testando conectividade..."
echo "Frontend: http://$SERVER_IP:3000"
echo "RAG Server: http://$SERVER_IP:8000"
echo "API Server: http://$SERVER_IP:8001"

# Verificar se os serviços estão rodando
echo ""
echo "📊 Status dos serviços:"
if pgrep -f "uvicorn.*8000" > /dev/null; then
    echo "✅ RAG Server: ATIVO"
else
    echo "❌ RAG Server: INATIVO"
fi

if pgrep -f "uvicorn.*8001" > /dev/null; then
    echo "✅ API Server: ATIVO"
else
    echo "❌ API Server: INATIVO"
fi

if pgrep -f "npm.*dev" > /dev/null; then
    echo "✅ Frontend: ATIVO"
else
    echo "❌ Frontend: INATIVO"
fi

echo ""
echo "🎉 Configurações atualizadas com sucesso!"
echo "📍 IP do servidor: $SERVER_IP"
echo "📍 Frontend: http://$SERVER_IP:3000"
echo "📍 RAG Server: http://$SERVER_IP:8000"
echo "📍 API Server: http://$SERVER_IP:8001"
echo ""
echo "💡 Para aplicar as mudanças, reinicie os serviços:"
echo "   ./stop_all.sh && ./start_all.sh"
echo ""
echo "📋 Para verificar o status: ./status.sh"
