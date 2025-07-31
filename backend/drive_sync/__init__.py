"""
Módulo de Sincronização com Google Drive

Este módulo contém todas as funcionalidades relacionadas à integração
e sincronização com o Google Drive, incluindo download de arquivos,
análise de pastas e gerenciamento de credenciais.
"""

from .drive_handler import DriveHandler
from .drive_handler_recursive import RecursiveDriveHandler

__all__ = [
    'DriveHandler',
    'RecursiveDriveHandler'
]
