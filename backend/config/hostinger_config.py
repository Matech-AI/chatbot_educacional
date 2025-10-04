#!/usr/bin/env python3
"""
Configurações específicas para o ambiente Hostinger
"""

import os
import socket
from pathlib import Path


def is_hostinger_environment() -> bool:
    """
    Verifica se estamos rodando no ambiente Hostinger
    """
    return os.getenv("HOSTINGER", "").lower() == "true" or os.path.exists("/etc/hostinger")


def get_chromadb_path() -> str:
    """
    Retorna o caminho para o ChromaDB baseado no ambiente
    """
    if is_hostinger_environment():
        # No Hostinger, usar o diretório de dados persistente
        return "/root/dna-forca-complete/backend/data/.chromadb"
    else:
        # Em desenvolvimento local
        return ".chromadb"


def get_materials_path() -> str:
    """
    Retorna o caminho para os materiais baseado no ambiente
    """
    if is_hostinger_environment():
        # No Hostinger, usar o diretório de dados persistente
        return "/root/dna-forca-complete/backend/data/materials"
    else:
        # Em desenvolvimento local
        return "data/materials"


def get_port() -> int:
    """
    Retorna a porta baseada no ambiente
    """
    if is_hostinger_environment():
        # No Hostinger, usar as portas configuradas
        return int(os.getenv("PORT", "5001"))
    else:
        # Em desenvolvimento local
        return 5001


def get_host() -> str:
    """
    Retorna o host baseado no ambiente
    """
    if is_hostinger_environment():
        # No Hostinger, usar 0.0.0.0 para aceitar conexões externas
        return "0.0.0.0"
    else:
        # Em desenvolvimento local
        return "127.0.0.1"


def get_server_ip() -> str:
    """
    Retorna o IP do servidor automaticamente detectado
    """
    try:
        # Tenta obter o hostname do servidor
        hostname = socket.gethostname()
        
        # Obtém o IP associado ao hostname
        ip_address = socket.gethostbyname(hostname)
        
        # Se for localhost, tenta obter o IP externo
        if ip_address in ['127.0.0.1', 'localhost']:
            # Tenta conectar a um servidor externo para descobrir o IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]
        
        return ip_address
    except Exception as e:
        # Em caso de erro, retorna o IP padrão ou uma mensagem de erro
        print(f"Erro ao detectar IP do servidor: {e}")
        return "0.0.0.0"  # Fallback para aceitar todas as conexões