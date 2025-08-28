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

# Ativar ambiente virtual
source .venv/bin/activate

# Iniciar RAG Server em background
echo "🚀 Iniciando RAG Server..."
cd backend/rag_system
nohup uvicorn rag_handler:app --host 0.0.0.0 --port 8000 --reload > ../../logs/rag-server.log 2>&1 &
RAG_PID=$!
echo "✅ RAG Server iniciado com PID: $RAG_PID"

# Aguardar um pouco para o RAG Server inicializar
sleep 5

# Iniciar API Server em background
echo "🚀 Iniciando API Server..."
cd ../..
nohup uvicorn backend.api_server:app --host 0.0.0.0 --port 8001 --reload > logs/api-server.log 2>&1 &
API_PID=$!
echo "✅ API Server iniciado com PID: $API_PID"

# Aguardar um pouco para o API Server inicializar
sleep 5

# Iniciar Frontend em background
echo "🌐 Iniciando Frontend..."
nohup npm run dev > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend iniciado com PID: $FRONTEND_PID"

# Salvar PIDs para gerenciamento
echo $RAG_PID > logs/rag-server.pid
echo $API_PID > logs/api-server.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "🎉 Sistema COMPLETO iniciado!"
echo "📍 Frontend: http://localhost:3000"
echo "📍 RAG Server: http://localhost:8000"
echo "📍 API Server: http://localhost:8001"
echo ""
echo "📋 Para parar: ./stop_all.sh"
echo "📋 Para status: ./status.sh"
echo "📋 Para logs: tail -f logs/*.log"
