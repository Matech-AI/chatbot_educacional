"""
Módulo do Sistema RAG (Retrieval Augmented Generation)

Este módulo contém todas as funcionalidades relacionadas ao sistema RAG,
incluindo processamento de documentos, embeddings, busca semântica
e geração de respostas baseadas em contexto.
"""

from .rag_handler import RAGHandler, ProcessingConfig, AssistantConfigModel, Source
from .enhanced_rag_handler import EnhancedRAGHandler

__all__ = [
    'RAGHandler',
    'ProcessingConfig',
    'AssistantConfigModel',
    'Source',
    'EnhancedRAGHandler'
]
