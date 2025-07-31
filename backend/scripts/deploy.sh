#!/bin/bash

# Script de Deploy - DNA da Força AI
# Este script facilita o deploy dos serviços Docker

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  DNA da Força AI - Deploy${NC}"
    echo -e "${BLUE}================================${NC}"
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
    
    print_message "Docker e Docker Compose encontrados"
}

# Verificar arquivo .env
check_env() {
    if [ ! -f ".env" ]; then
        print_warning "Arquivo .env não encontrado. Criando a partir do exemplo..."
        if [ -f "env.example" ]; then
            cp env.example .env
            print_message "Arquivo .env criado. Configure as variáveis de ambiente antes de continuar."
            print_warning "Edite o arquivo .env e configure suas chaves de API antes de executar novamente."
            exit 1
        else
            print_error "Arquivo env.example não encontrado."
            exit 1
        fi
    fi
    
    print_message "Arquivo .env encontrado"
}

# Construir imagens
build_images() {
    print_message "Construindo imagens Docker..."
    
    # Construir imagem do servidor RAG
    print_message "Construindo imagem do servidor RAG..."
    docker build -f Dockerfile.rag -t dna-forca-rag-server .
    
    # Construir imagem do servidor API
    print_message "Construindo imagem do servidor API..."
    docker build -f Dockerfile.api -t dna-forca-api-server .
    
    print_message "Imagens construídas com sucesso"
}

# Iniciar serviços
start_services() {
    print_message "Iniciando serviços..."
    
    docker-compose up -d
    
    print_message "Serviços iniciados"
    print_message "Servidor RAG: http://localhost:8001"
    print_message "Servidor API: http://localhost:8000"
    print_message "Redis: localhost:6379"
}

# Parar serviços
stop_services() {
    print_message "Parando serviços..."
    
    docker-compose down
    
    print_message "Serviços parados"
}

# Verificar status
check_status() {
    print_message "Verificando status dos serviços..."
    
    echo ""
    echo "Status dos containers:"
    docker-compose ps
    
    echo ""
    echo "Logs do servidor RAG:"
    docker-compose logs --tail=10 rag-server
    
    echo ""
    echo "Logs do servidor API:"
    docker-compose logs --tail=10 api-server
}

# Limpar tudo
cleanup() {
    print_warning "Removendo todos os containers, volumes e imagens..."
    
    docker-compose down -v --rmi all
    
    print_message "Limpeza concluída"
}

# Mostrar logs
show_logs() {
    local service=${1:-"all"}
    
    if [ "$service" = "rag" ]; then
        docker-compose logs -f rag-server
    elif [ "$service" = "api" ]; then
        docker-compose logs -f api-server
    else
        docker-compose logs -f
    fi
}

# Função principal
main() {
    print_header
    
    case "${1:-help}" in
        "build")
            check_docker
            check_env
            build_images
            ;;
        "start")
            check_docker
            check_env
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            start_services
            ;;
        "status")
            check_status
            ;;
        "logs")
            show_logs $2
            ;;
        "cleanup")
            cleanup
            ;;
        "deploy")
            check_docker
            check_env
            build_images
            start_services
            ;;
        "help"|*)
            echo "Uso: $0 [comando]"
            echo ""
            echo "Comandos disponíveis:"
            echo "  build     - Construir imagens Docker"
            echo "  start     - Iniciar serviços"
            echo "  stop      - Parar serviços"
            echo "  restart   - Reiniciar serviços"
            echo "  status    - Verificar status dos serviços"
            echo "  logs      - Mostrar logs (opções: rag, api, all)"
            echo "  cleanup   - Limpar tudo (containers, volumes, imagens)"
            echo "  deploy    - Deploy completo (build + start)"
            echo "  help      - Mostrar esta ajuda"
            echo ""
            echo "Exemplos:"
            echo "  $0 deploy"
            echo "  $0 logs rag"
            echo "  $0 status"
            ;;
    esac
}

# Executar função principal
main "$@" 