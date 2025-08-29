#!/bin/bash

# Script de inicialização completa (Frontend + RAG + API)
cd /root/dna-forca-complete

# Detectar IP do servidor automaticamente (mesma lógica do status.sh)
# Para servidor da Hostinger, usar ifconfig.me que retorna o IP público real
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")

# Tentar também obter IPv4 específico
IPV4=$(curl -s ipv4.icanhazip.com 2>/dev/null || echo "")

echo "🚀 Iniciando sistema COMPLETO DNA da Força..."
echo "🌐 Serviços: Frontend + RAG Server + API Server"
echo "🌐 Servidor: $SERVER_IP"
if [ ! -z "$IPV4" ] && [ "$IPV4" != "$SERVER_IP" ]; then
    echo "🌐 Servidor IPv4: $IPV4"
fi
echo ""
echo "💡 INSTRUÇÕES DE ACESSO:"
echo "💡 1. Do seu PC local: http://$SERVER_IP:3000 (Frontend)"
echo "💡 2. Do seu PC local: http://$SERVER_IP:8000 (RAG Server)"
echo "💡 3. Do seu PC local: http://$SERVER_IP:8001 (API Server)"
echo "💡 4. Se não funcionar, verifique se as portas estão abertas no firewall da Hostinger"

# Verificar se o Redis está rodando
if ! systemctl is-active --quiet redis-server; then
    echo "🔄 Iniciando Redis..."
    systemctl start redis-server
    systemctl enable redis-server
fi

# Ativar ambiente virtual
source .venv/bin/activate

# Configurar PYTHONPATH para encontrar os módulos
export PYTHONPATH="/root/dna-forca-complete/backend:$PYTHONPATH"

# Iniciar RAG Server em background
echo "🚀 Iniciando RAG Server..."
cd backend
nohup uvicorn rag_server:app --host 0.0.0.0 --port 8001 --reload > ../logs/rag-server.log 2>&1 &
RAG_PID=$!
echo "✅ RAG Server iniciado com PID: $RAG_PID"

# Aguardar um pouco para o RAG Server inicializar
sleep 5

# Iniciar API Server em background
echo "🚀 Iniciando API Server..."
cd ..
nohup uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload > logs/api-server.log 2>&1 &
API_PID=$!
echo "✅ API Server iniciado com PID: $API_PID"

# Aguardar um pouco para o API Server inicializar
sleep 5

# Iniciar Frontend em background
echo "🌐 Iniciando Frontend..."
# Parar qualquer processo que possa estar usando a porta 3000
pkill -f "vite.*dev" 2>/dev/null || true
pkill -f "node.*vite" 2>/dev/null || true
sleep 3
# Forçar uso da porta 3000
nohup npm run dev -- --port 3000 > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend iniciado com PID: $FRONTEND_PID"

# Salvar PIDs para gerenciamento
echo $RAG_PID > logs/rag-server.pid
echo $API_PID > logs/api-server.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "🎉 Sistema COMPLETO iniciado!"
echo "🌐 Frontend: http://$SERVER_IP:3000"
echo "📍 RAG Server: http://$SERVER_IP:8000"
echo "📍 API Server: http://$SERVER_IP:8001"
echo ""
echo "🛑 Para parar: ./stop_all.sh"
echo "📋 Para status: ./status.sh"
echo "📝 Para logs: tail -f logs/*.log"