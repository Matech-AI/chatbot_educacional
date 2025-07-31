"""
Módulo de Agentes de Chat e IA

Este módulo contém todos os agentes de chat e funcionalidades de IA,
incluindo o agente educacional, chat básico e gerenciamento de conversas.
"""

from .chat_agent import graph as chat_agent_graph
from .educational_agent import (
    EducationalAgent, EducationalChatRequest, EducationalChatResponse,
    LearningContext, EducationalState, router as educational_agent_router
)

__all__ = [
    'chat_agent_graph',
    'EducationalAgent',
    'EducationalChatRequest',
    'EducationalChatResponse',
    'LearningContext',
    'EducationalState',
    'educational_agent_router'
]
