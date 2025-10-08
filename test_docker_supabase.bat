@echo off
REM Script para testar configurações Docker com Supabase no Windows
REM Execute este script antes de fazer deploy no Coolify

echo 🔍 Testando configurações Docker com Supabase...

REM Verificar se o arquivo .env existe
if not exist ".env" (
    echo ❌ Arquivo .env não encontrado!
    echo 📝 Copie o env.example para .env e configure as variáveis:
    echo    copy env.example .env
    exit /b 1
)

echo 🔧 Verificando variáveis do Supabase...

REM Verificar se as variáveis críticas estão configuradas
findstr /C:"VITE_SUPABASE_URL=" .env >nul
if errorlevel 1 (
    echo ❌ VITE_SUPABASE_URL não encontrada
    set MISSING_VARS=1
) else (
    echo ✅ VITE_SUPABASE_URL configurada
)

findstr /C:"VITE_SUPABASE_ANON_KEY=" .env >nul
if errorlevel 1 (
    echo ❌ VITE_SUPABASE_ANON_KEY não encontrada
    set MISSING_VARS=1
) else (
    echo ✅ VITE_SUPABASE_ANON_KEY configurada
)

findstr /C:"SUPABASE_SERVICE_ROLE_KEY=" .env >nul
if errorlevel 1 (
    echo ❌ SUPABASE_SERVICE_ROLE_KEY não encontrada
    set MISSING_VARS=1
) else (
    echo ✅ SUPABASE_SERVICE_ROLE_KEY configurada
)

findstr /C:"OPENAI_API_KEY=" .env >nul
if errorlevel 1 (
    echo ❌ OPENAI_API_KEY não encontrada
    set MISSING_VARS=1
) else (
    echo ✅ OPENAI_API_KEY configurada
)

findstr /C:"JWT_SECRET_KEY=" .env >nul
if errorlevel 1 (
    echo ❌ JWT_SECRET_KEY não encontrada
    set MISSING_VARS=1
) else (
    echo ✅ JWT_SECRET_KEY configurada
)

if defined MISSING_VARS (
    echo.
    echo ❌ Variáveis críticas não configuradas!
    echo 📝 Configure as variáveis no arquivo .env antes de continuar
    exit /b 1
)

echo.
echo ✅ Todas as variáveis críticas estão configuradas!

REM Testar se Docker está disponível
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker não está instalado ou não está no PATH
    exit /b 1
)

echo.
echo 🏗️ Testando build do frontend...
docker build -f Dockerfile.frontend -t test-frontend . >nul 2>&1
if errorlevel 1 (
    echo ❌ Falha no build do frontend!
    exit /b 1
) else (
    echo ✅ Build do frontend bem-sucedido!
    docker rmi test-frontend >nul 2>&1
)

echo.
echo 🏗️ Testando build do backend...
docker build -f backend/Dockerfile.api -t test-backend . >nul 2>&1
if errorlevel 1 (
    echo ❌ Falha no build do backend!
    exit /b 1
) else (
    echo ✅ Build do backend bem-sucedido!
    docker rmi test-backend >nul 2>&1
)

echo.
echo 🏗️ Testando build do RAG server...
docker build -f backend/Dockerfile.rag -t test-rag backend/ >nul 2>&1
if errorlevel 1 (
    echo ❌ Falha no build do RAG server!
    exit /b 1
) else (
    echo ✅ Build do RAG server bem-sucedido!
    docker rmi test-rag >nul 2>&1
)

echo.
echo 🎉 Todos os testes passaram!
echo ✅ Seu projeto está pronto para deploy no Coolify
echo.
echo 📋 Próximos passos:
echo 1. Faça commit das alterações
echo 2. Configure as mesmas variáveis de ambiente no Coolify
echo 3. Execute o deploy no Coolify
echo 4. Consulte docs/deploy/coolify-deployment.md para mais detalhes