#!/bin/bash

echo "🔍 TESTE DE CONECTIVIDADE - DNA DA FORÇA"
echo "=========================================="

# Detectar IPs disponíveis
echo "🌐 Detectando IPs do servidor..."

# IPv4 público
echo "IPv4 Público:"
curl -4 -s ifconfig.me 2>/dev/null || echo "❌ Não foi possível detectar IPv4 público"

# IPv6
echo "IPv6:"
curl -6 -s ifconfig.me 2>/dev/null || echo "❌ Não foi possível detectar IPv6"

# IP local
echo "IP Local:"
hostname -I | awk '{print $1}' || echo "❌ Não foi possível detectar IP local"

# Testar conectividade nas portas
echo ""
echo "🔌 Testando conectividade nas portas..."

# Porta 3000 (Frontend)
echo "Porta 3000 (Frontend):"
if curl -s --connect-timeout 5 http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend acessível em localhost:3000"
else
    echo "❌ Frontend não acessível em localhost:3000"
fi

# Porta 8000 (RAG Server)
echo "Porta 8000 (RAG Server):"
if curl -s --connect-timeout 5 http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ RAG Server acessível em localhost:8000"
else
    echo "❌ RAG Server não acessível em localhost:8000"
fi

# Porta 8001 (API Server)
echo "Porta 8001 (API Server):"
if curl -s --connect-timeout 5 http://localhost:8001 > /dev/null 2>&1; then
    echo "✅ API Server acessível em localhost:8001"
else
    echo "❌ API Server não acessível em localhost:8001"
fi

# Testar com IP específico do status
echo ""
echo "🌐 Testando com IP do status (2a02:4780:14:42c4::1):"

# Frontend
if curl -s --connect-timeout 5 http://[2a02:4780:14:42c4::1]:3000 > /dev/null 2>&1; then
    echo "✅ Frontend acessível em [2a02:4780:14:42c4::1]:3000"
else
    echo "❌ Frontend não acessível em [2a02:4780:14:42c4::1]:3000"
fi

# RAG Server
if curl -s --connect-timeout 5 http://[2a02:4780:14:42c4::1]:8000 > /dev/null 2>&1; then
    echo "✅ RAG Server acessível em [2a02:4780:14:42c4::1]:8000"
else
    echo "❌ RAG Server não acessível em [2a02:4780:14:42c4::1]:8000"
fi

# API Server
if curl -s --connect-timeout 5 http://[2a02:4780:14:42c4::1]:8001 > /dev/null 2>&1; then
    echo "✅ API Server acessível em [2a02:4780:14:42c4::1]:8001"
else
    echo "❌ API Server não acessível em [2a02:4780:14:42c4::1]:8001"
fi

echo ""
echo "📋 Resumo das configurações atuais:"
echo "===================================="
echo "HOSTINGER: $HOSTINGER"
echo "SERVER_IP: $SERVER_IP"
echo "RAG_PORT: $RAG_PORT"
echo "API_PORT: $API_PORT"
echo "FRONTEND_PORT: $FRONTEND_PORT"
