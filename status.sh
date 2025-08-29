#!/bin/bash

# Script de status do sistema COMPLETO
cd /root/dna-forca-complete

# Detectar IP do servidor automaticamente
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")

echo "📊 STATUS DO SISTEMA COMPLETO DNA DA FORÇA - $(date)"
echo "=================================================="
echo "�� Servidor: $SERVER_IP"
echo ""

# Status do Frontend
echo "�� FRONTEND:"
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "✅ Status: ATIVO"
        echo "�� PID: $FRONTEND_PID"
        echo "📍 Porta: 3000"
        echo "📍 URL: http://$SERVER_IP:3000"
        echo "📍 Diretório: src/ (React)"
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
        echo "📍 URL: http://$SERVER_IP:8000"
        echo "�� Diretório: backend/rag_system/"
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
if [ -f logs/rag-server.pid ]; then
    API_PID=$(cat logs/api-server.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo "✅ Status: ATIVO"
        echo "📍 PID: $API_PID"
        echo "📍 Porta: 8001"
        echo "📍 URL: http://$SERVER_IP:8001"
        echo "📍 Arquivo: backend/api_server.py"
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

# Verificar estrutura do projeto
echo ""
echo "📁 ESTRUTURA DO PROJETO:"
echo "Frontend (src/): $(ls -la src/ | wc -l) arquivos"
echo "Backend (backend/): $(ls -la backend/ | wc -l) arquivos"
echo "Ambiente Python (.venv): $(ls -la .venv/ | wc -l) arquivos"
echo "Dependências Node.js: $(ls -la node_modules/ | wc -l) arquivos"