@echo off
REM Script de Deploy - DNA da Força AI (Windows)
REM Este script facilita o deploy dos serviços Docker no Windows

setlocal enabledelayedexpansion

REM Cores para output (Windows)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Função para imprimir mensagens coloridas
:print_message
echo %GREEN%[INFO]%NC% %~1
goto :eof

:print_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %~1
goto :eof

:print_header
echo %BLUE%================================%NC%
echo %BLUE%  DNA da Força AI - Deploy%NC%
echo %BLUE%================================%NC%
goto :eof

REM Verificar se Docker está instalado
:check_docker
docker --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker não está instalado. Instale o Docker Desktop primeiro."
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker Compose não está instalado. Instale o Docker Compose primeiro."
    exit /b 1
)

call :print_message "Docker e Docker Compose encontrados"
goto :eof

REM Verificar arquivo .env
:check_env
if not exist ".env" (
    call :print_warning "Arquivo .env não encontrado. Criando a partir do exemplo..."
    if exist "env.example" (
        copy env.example .env >nul
        call :print_message "Arquivo .env criado. Configure as variáveis de ambiente antes de continuar."
        call :print_warning "Edite o arquivo .env e configure suas chaves de API antes de executar novamente."
        exit /b 1
    ) else (
        call :print_error "Arquivo env.example não encontrado."
        exit /b 1
    )
)

call :print_message "Arquivo .env encontrado"
goto :eof

REM Construir imagens
:build_images
call :print_message "Construindo imagens Docker..."

call :print_message "Construindo imagem do servidor RAG..."
docker build -f Dockerfile.rag -t dna-forca-rag-server .

call :print_message "Construindo imagem do servidor API..."
docker build -f Dockerfile.api -t dna-forca-api-server .

call :print_message "Imagens construídas com sucesso"
goto :eof

REM Iniciar serviços
:start_services
call :print_message "Iniciando serviços..."

docker-compose up -d

call :print_message "Serviços iniciados"
call :print_message "Servidor RAG: http://localhost:8001"
call :print_message "Servidor API: http://localhost:8000"
call :print_message "Redis: localhost:6379"
goto :eof

REM Parar serviços
:stop_services
call :print_message "Parando serviços..."

docker-compose down

call :print_message "Serviços parados"
goto :eof

REM Verificar status
:check_status
call :print_message "Verificando status dos serviços..."

echo.
echo Status dos containers:
docker-compose ps

echo.
echo Logs do servidor RAG:
docker-compose logs --tail=10 rag-server

echo.
echo Logs do servidor API:
docker-compose logs --tail=10 api-server
goto :eof

REM Limpar tudo
:cleanup
call :print_warning "Removendo todos os containers, volumes e imagens..."

docker-compose down -v --rmi all

call :print_message "Limpeza concluída"
goto :eof

REM Mostrar logs
:show_logs
set "service=%~1"
if "%service%"=="" set "service=all"

if "%service%"=="rag" (
    docker-compose logs -f rag-server
) else if "%service%"=="api" (
    docker-compose logs -f api-server
) else (
    docker-compose logs -f
)
goto :eof

REM Função principal
:main
call :print_header

set "command=%~1"
if "%command%"=="" set "command=help"

if "%command%"=="build" (
    call :check_docker
    call :check_env
    call :build_images
) else if "%command%"=="start" (
    call :check_docker
    call :check_env
    call :start_services
) else if "%command%"=="stop" (
    call :stop_services
) else if "%command%"=="restart" (
    call :stop_services
    call :start_services
) else if "%command%"=="status" (
    call :check_status
) else if "%command%"=="logs" (
    call :show_logs %2
) else if "%command%"=="cleanup" (
    call :cleanup
) else if "%command%"=="deploy" (
    call :check_docker
    call :check_env
    call :build_images
    call :start_services
) else (
    echo Uso: %0 [comando]
    echo.
    echo Comandos disponíveis:
    echo   build     - Construir imagens Docker
    echo   start     - Iniciar serviços
    echo   stop      - Parar serviços
    echo   restart   - Reiniciar serviços
    echo   status    - Verificar status dos serviços
    echo   logs      - Mostrar logs ^(opções: rag, api, all^)
    echo   cleanup   - Limpar tudo ^(containers, volumes, imagens^)
    echo   deploy    - Deploy completo ^(build + start^)
    echo   help      - Mostrar esta ajuda
    echo.
    echo Exemplos:
    echo   %0 deploy
    echo   %0 logs rag
    echo   %0 status
)

goto :eof

REM Executar função principal
call :main %* 