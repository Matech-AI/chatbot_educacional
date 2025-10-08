#!/bin/bash

# Script para testar configurações Docker com Supabase
# Execute este script antes de fazer deploy no Coolify

echo "🔍 Testando configurações Docker com Supabase..."

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "📝 Copie o env.example para .env e configure as variáveis:"
    echo "   cp env.example .env"
    exit 1
fi

# Verificar variáveis obrigatórias do Supabase
echo "🔧 Verificando variáveis do Supabase..."

check_var() {
    local var_name=$1
    local var_value=$(grep "^$var_name=" .env | cut -d'=' -f2- | tr -d '"')
    
    if [ -z "$var_value" ] || [ "$var_value" = "your_${var_name,,}_here" ] || [ "$var_value" = "sua_chave_${var_name,,}_aqui" ]; then
        echo "❌ $var_name não configurada ou usando valor padrão"
        return 1
    else
        echo "✅ $var_name configurada"
        return 0
    fi
}

# Verificar variáveis críticas
MISSING_VARS=0

if ! check_var "VITE_SUPABASE_URL"; then
    MISSING_VARS=$((MISSING_VARS + 1))
fi

if ! check_var "VITE_SUPABASE_ANON_KEY"; then
    MISSING_VARS=$((MISSING_VARS + 1))
fi

if ! check_var "SUPABASE_SERVICE_ROLE_KEY"; then
    MISSING_VARS=$((MISSING_VARS + 1))
fi

if ! check_var "OPENAI_API_KEY"; then
    MISSING_VARS=$((MISSING_VARS + 1))
fi

if ! check_var "JWT_SECRET_KEY"; then
    MISSING_VARS=$((MISSING_VARS + 1))
fi

if [ $MISSING_VARS -gt 0 ]; then
    echo ""
    echo "❌ $MISSING_VARS variáveis críticas não configuradas!"
    echo "📝 Configure as variáveis no arquivo .env antes de continuar"
    exit 1
fi

echo ""
echo "✅ Todas as variáveis críticas estão configuradas!"

# Testar build do frontend
echo ""
echo "🏗️ Testando build do frontend..."
if docker build -f Dockerfile.frontend --build-arg VITE_SUPABASE_URL="$(grep VITE_SUPABASE_URL .env | cut -d'=' -f2- | tr -d '"')" --build-arg VITE_SUPABASE_ANON_KEY="$(grep VITE_SUPABASE_ANON_KEY .env | cut -d'=' -f2- | tr -d '"')" --build-arg VITE_API_URL="$(grep VITE_API_URL .env | cut -d'=' -f2- | tr -d '"')" -t test-frontend .; then
    echo "✅ Build do frontend bem-sucedido!"
    docker rmi test-frontend
else
    echo "❌ Falha no build do frontend!"
    exit 1
fi

# Testar build do backend
echo ""
echo "🏗️ Testando build do backend..."
if docker build -f backend/Dockerfile.api -t test-backend .; then
    echo "✅ Build do backend bem-sucedido!"
    docker rmi test-backend
else
    echo "❌ Falha no build do backend!"
    exit 1
fi

# Testar build do RAG server
echo ""
echo "🏗️ Testando build do RAG server..."
if docker build -f backend/Dockerfile.rag -t test-rag backend/; then
    echo "✅ Build do RAG server bem-sucedido!"
    docker rmi test-rag
else
    echo "❌ Falha no build do RAG server!"
    exit 1
fi

echo ""
echo "🎉 Todos os testes passaram!"
echo "✅ Seu projeto está pronto para deploy no Coolify"
echo ""
echo "📋 Próximos passos:"
echo "1. Faça commit das alterações"
echo "2. Configure as mesmas variáveis de ambiente no Coolify"
echo "3. Execute o deploy no Coolify"
echo "4. Consulte docs/deploy/coolify-deployment.md para mais detalhes"