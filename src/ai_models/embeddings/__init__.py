"""
Embeddings module for text similarity and semantic search capabilities.
"""

from .text_embeddings import TextEmbeddingsClient, EmbeddingsConfig, EmbeddingsResponse

__all__ = [
    'TextEmbeddingsClient',
    'EmbeddingsConfig',
    'EmbeddingsResponse'
]