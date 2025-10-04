#!/bin/bash

# Script de Deploy - DNA da Força AI
# Este script automatiza o processo de deploy dos servidores RAG e API

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de log
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker não está instalado. Instale o Docker primeiro."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose não está instalado. Instale o Docker Compose primeiro."
        exit 1
    fi

    print_success "Docker e Docker Compose encontrados"
}

# Verificar arquivo .env
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning "Arquivo .env não encontrado. Criando a partir do exemplo..."
        cp env.example .env
        print_message "Arquivo .env criado. Configure as variáveis de ambiente antes de continuar."
        print_warning "Edite o arquivo .env e configure suas chaves de API antes de executar novamente."
        exit 1
    fi
    print_message "Arquivo .env encontrado"
}

# Verificar dependências Python
check_python_deps() {
    if [ ! -f "config/requirements.txt" ]; then
        print_error "Arquivo requirements.txt não encontrado em config/"
        exit 1
    fi
    print_message "Dependências Python verificadas"
}

# Construir imagens Docker
build_images() {
    print_message "Construindo imagens Docker..."
    
    # Construir imagem RAG
    print_message "Construindo imagem RAG..."
    docker build -f Dockerfile.rag -t dna-forca-rag-server .
    
    # Construir imagem API
    print_message "Construindo imagem API..."
    docker build -f Dockerfile.api -t dna-forca-api-server .
    
    print_success "Imagens construídas com sucesso"
}

# Iniciar serviços
start_services() {
    print_message "Iniciando serviços..."
    
    # Parar serviços existentes
    docker-compose down 2>/dev/null || true
    
    # Iniciar serviços
    docker-compose up -d
    
    print_success "Serviços iniciados"
}

# Verificar status dos serviços
check_status() {
    print_message "Verificando status dos serviços..."
    
    # Aguardar um pouco para os serviços inicializarem
    sleep 10
    
    # Verificar RAG Server
    if curl -f http://localhost:5001/health >/dev/null 2>&1; then
        print_success "RAG Server está respondendo"
    else
        print_error "RAG Server não está respondendo"
        return 1
    fi
    
    # Verificar API Server
    if curl -f http://localhost:5000/health >/dev/null 2>&1; then
        print_success "API Server está respondendo"
    else
        print_error "API Server não está respondendo"
        return 1
    fi
    
    print_success "Todos os serviços estão funcionando"
}

# Mostrar logs
show_logs() {
    local service=$1
    
    if [ -z "$service" ]; then
        print_message "Mostrando logs de todos os serviços..."
        docker-compose logs -f
    else
        print_message "Mostrando logs do serviço: $service"
        docker-compose logs -f "$service"
    fi
}

# Parar serviços
stop_services() {
    print_message "Parando serviços..."
    docker-compose down
    print_success "Serviços parados"
}

# Limpar tudo
cleanup() {
    print_message "Limpando tudo..."
    docker-compose down -v
    docker system prune -f
    print_success "Limpeza concluída"
}

# Mostrar ajuda
show_help() {
    echo "Script de Deploy - DNA da Força AI"
    echo ""
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "Comandos:"
    echo "  deploy     - Deploy completo (construir e iniciar)"
    echo "  build      - Apenas construir imagens"
    echo "  start      - Apenas iniciar serviços"
    echo "  stop       - Parar serviços"
    echo "  restart    - Reiniciar serviços"
    echo "  status     - Verificar status dos serviços"
    echo "  logs       - Mostrar logs (todos os serviços)"
    echo "  logs [service] - Mostrar logs de um serviço específico"
    echo "  cleanup    - Limpar tudo (parar e remover volumes)"
    echo "  help       - Mostrar esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 deploy"
    echo "  $0 logs rag-server"
    echo "  $0 status"
}

# Função principal
main() {
    case "${1:-help}" in
        "deploy")
            check_docker
            check_env_file
            check_python_deps
            build_images
            start_services
            check_status
            print_success "Deploy concluído com sucesso!"
            print_message "Servidores disponíveis em:"
            print_message "  - API Server: http://localhost:5000"
            print_message "  - RAG Server: http://localhost:5001"
            ;;
        "build")
            check_docker
            check_python_deps
            build_images
            ;;
        "start")
            check_docker
            check_env_file
            start_services
            check_status
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            start_services
            check_status
            ;;
        "status")
            check_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Executar função principal
main "$@" 