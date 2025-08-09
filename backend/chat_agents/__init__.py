"""
Módulo de Agentes de Chat e IA

Este módulo contém todos os agentes de chat e funcionalidades de IA,
incluindo o agente educacional, chat básico e gerenciamento de conversas.
"""

from .educational_agent import (
    EducationalAgent, EducationalChatResponse,
    LearningContext, AgentState, router as educational_agent_router
)

__all__ = [
    'EducationalAgent',
    'EducationalChatResponse',
    'LearningContext',
    'AgentState',
    'educational_agent_router'
]
