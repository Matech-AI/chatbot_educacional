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
pkill -f "vite.*dev" 2>/dev/null || true
pkill -f "uvicorn.*rag_handler" 2>/dev/null || true
pkill -f "uvicorn.*api_server" 2>/dev/null || true

echo "✅ Sistema COMPLETO parado com sucesso!"
