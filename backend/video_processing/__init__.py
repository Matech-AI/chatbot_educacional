"""
Módulo de Processamento de Vídeo

Este módulo contém todas as funcionalidades relacionadas ao processamento
de vídeos, incluindo análise de conteúdo, geração de timestamps,
metadados e integração com Google Drive para vídeos.
"""

from .video_handler import (
    VideoContentAnalyzer, DriveVideoHandler, VideoMetadata, VideoTimestamp
)

__all__ = [
    'VideoContentAnalyzer',
    'DriveVideoHandler', 
    'VideoMetadata',
    'VideoTimestamp'
] 