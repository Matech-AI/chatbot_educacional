#!/usr/bin/env python3
"""
Configurações específicas para o ambiente Render
"""

import os
from pathlib import Path


def is_render_environment() -> bool:
    """
    Verifica se estamos rodando no ambiente Render
    """
    return os.getenv("RENDER", "").lower() == "true"


def get_chromadb_path() -> str:
    """
    Retorna o caminho para o ChromaDB baseado no ambiente
    """
    if is_render_environment():
        # No Render, usar o diretório de dados persistente
        return "/app/data/.chromadb"
    else:
        # Em desenvolvimento local
        return ".chromadb"


def get_materials_path() -> str:
    """
    Retorna o caminho para os materiais baseado no ambiente
    """
    if is_render_environment():
        # No Render, usar o diretório de dados persistente
        return "/app/data/materials"
    else:
        # Em desenvolvimento local
        return "data/materials"


def get_port() -> int:
    """
    Retorna a porta baseada no ambiente
    """
    if is_render_environment():
        # No Render, usar a porta da variável de ambiente
        return int(os.getenv("PORT", "5001"))
    else:
        # Em desenvolvimento local
        return 5001


def get_host() -> str:
    """
    Retorna o host baseado no ambiente
    """
    if is_render_environment():
        # No Render, usar 0.0.0.0 para aceitar conexões externas
        return "0.0.0.0"
    else:
        # Em desenvolvimento local
        return "127.0.0.1"
