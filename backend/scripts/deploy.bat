@echo off
REM Script de Deploy - DNA da Força AI (Windows)
REM Este script automatiza o processo de deploy dos servidores RAG e API

setlocal enabledelayedexpansion

REM Cores para output (Windows não suporta cores ANSI, mas mantemos a estrutura)
set "RED=[ERROR]"
set "GREEN=[SUCCESS]"
set "YELLOW=[WARNING]"
set "BLUE=[INFO]"

REM Funções de log
:print_message
echo %BLUE% %~1
goto :eof

:print_success
echo %GREEN% %~1
goto :eof

:print_warning
echo %YELLOW% %~1
goto :eof

:print_error
echo %RED% %~1
goto :eof

REM Verificar se Docker está instalado
:check_docker
docker --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker não está instalado. Instale o Docker primeiro."
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker Compose não está instalado. Instale o Docker Compose primeiro."
    exit /b 1
)

call :print_success "Docker e Docker Compose encontrados"
goto :eof

REM Verificar arquivo .env
:check_env_file
if not exist ".env" (
    call :print_warning "Arquivo .env não encontrado. Criando a partir do exemplo..."
    copy env.example .env >nul
    call :print_message "Arquivo .env criado. Configure as variáveis de ambiente antes de continuar."
    call :print_warning "Edite o arquivo .env e configure suas chaves de API antes de executar novamente."
    exit /b 1
)
call :print_message "Arquivo .env encontrado"
goto :eof

REM Verificar dependências Python
:check_python_deps
if not exist "config\requirements.txt" (
    call :print_error "Arquivo requirements.txt não encontrado em config/"
    exit /b 1
)
call :print_message "Dependências Python verificadas"
goto :eof

REM Construir imagens Docker
:build_images
call :print_message "Construindo imagens Docker..."

REM Construir imagem RAG
call :print_message "Construindo imagem RAG..."
docker build -f Dockerfile.rag -t dna-forca-rag-server .
if errorlevel 1 (
    call :print_error "Erro ao construir imagem RAG"
    exit /b 1
)

REM Construir imagem API
call :print_message "Construindo imagem API..."
docker build -f Dockerfile.api -t dna-forca-api-server .
if errorlevel 1 (
    call :print_error "Erro ao construir imagem API"
    exit /b 1
)

call :print_success "Imagens construídas com sucesso"
goto :eof

REM Iniciar serviços
:start_services
call :print_message "Iniciando serviços..."

REM Parar serviços existentes
docker-compose down >nul 2>&1

REM Iniciar serviços
docker-compose up -d
if errorlevel 1 (
    call :print_error "Erro ao iniciar serviços"
    exit /b 1
)

call :print_success "Serviços iniciados"
goto :eof

REM Verificar status dos serviços
:check_status
call :print_message "Verificando status dos serviços..."

REM Aguardar um pouco para os serviços inicializarem
timeout /t 10 /nobreak >nul

REM Verificar RAG Server
curl -f http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    call :print_error "RAG Server não está respondendo"
    exit /b 1
) else (
    call :print_success "RAG Server está respondendo"
)

REM Verificar API Server
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    call :print_error "API Server não está respondendo"
    exit /b 1
) else (
    call :print_success "API Server está respondendo"
)

call :print_success "Todos os serviços estão funcionando"
goto :eof

REM Mostrar logs
:show_logs
if "%~1"=="" (
    call :print_message "Mostrando logs de todos os serviços..."
    docker-compose logs -f
) else (
    call :print_message "Mostrando logs do serviço: %~1"
    docker-compose logs -f "%~1"
)
goto :eof

REM Parar serviços
:stop_services
call :print_message "Parando serviços..."
docker-compose down
call :print_success "Serviços parados"
goto :eof

REM Limpar tudo
:cleanup
call :print_message "Limpando tudo..."
docker-compose down -v
docker system prune -f
call :print_success "Limpeza concluída"
goto :eof

REM Mostrar ajuda
:show_help
echo Script de Deploy - DNA da Força AI
echo.
echo Uso: %0 [COMANDO]
echo.
echo Comandos:
echo   deploy     - Deploy completo (construir e iniciar)
echo   build      - Apenas construir imagens
echo   start      - Apenas iniciar serviços
echo   stop       - Parar serviços
echo   restart    - Reiniciar serviços
echo   status     - Verificar status dos serviços
echo   logs       - Mostrar logs (todos os serviços)
echo   logs [service] - Mostrar logs de um serviço específico
echo   cleanup    - Limpar tudo (parar e remover volumes)
echo   help       - Mostrar esta ajuda
echo.
echo Exemplos:
echo   %0 deploy
echo   %0 logs rag-server
echo   %0 status
goto :eof

REM Função principal
:main
if "%~1"=="" goto :help
if "%~1"=="help" goto :help
if "%~1"=="deploy" goto :deploy
if "%~1"=="build" goto :build
if "%~1"=="start" goto :start
if "%~1"=="stop" goto :stop
if "%~1"=="restart" goto :restart
if "%~1"=="status" goto :status
if "%~1"=="logs" goto :logs
if "%~1"=="cleanup" goto :cleanup
goto :help

:deploy
call :check_docker
call :check_env_file
call :check_python_deps
call :build_images
call :start_services
call :check_status
call :print_success "Deploy concluído com sucesso!"
call :print_message "Servidores disponíveis em:"
call :print_message "  - API Server: http://localhost:8000"
call :print_message "  - RAG Server: http://localhost:8001"
goto :eof

:build
call :check_docker
call :check_python_deps
call :build_images
goto :eof

:start
call :check_docker
call :check_env_file
call :start_services
call :check_status
goto :eof

:stop
call :stop_services
goto :eof

:restart
call :stop_services
call :start_services
call :check_status
goto :eof

:status
call :check_status
goto :eof

:logs
call :show_logs "%~2"
goto :eof

:cleanup
call :cleanup
goto :eof

:help
call :show_help
goto :eof

REM Executar função principal
call :main %* 