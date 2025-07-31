"""
Módulo de Manutenção

Este módulo contém todas as funcionalidades relacionadas à manutenção
do sistema, incluindo limpeza, otimização e monitoramento.
"""

from .maintenance_endpoints import router as maintenance_router

__all__ = [
    'maintenance_router'
] 