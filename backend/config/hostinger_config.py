#!/usr/bin/env python3
"""
Configurações específicas para o ambiente Hostinger
"""

import os
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
        return int(os.getenv("PORT", "8001"))
    else:
        # Em desenvolvimento local
        return 8001


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
    Retorna o IP do servidor Hostinger
    """
    return "31.97.16.142"