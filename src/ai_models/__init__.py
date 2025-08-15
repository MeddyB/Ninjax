"""
AI Models module for comprehensive AI-powered trading capabilities.

This module provides a unified interface for various AI models including:
- Large Language Models (LLM) for market analysis and trading insights
- Whisper for speech recognition and voice commands
- Vision models for chart analysis and pattern recognition
- Embeddings for semantic search and similarity analysis
"""

# LLM imports
from .llm import BaseLLM, LLMConfig, LLMResponse, OpenAIClient, LocalLLMClient

# Whisper imports
from .whisper import WhisperClient, WhisperConfig, WhisperResponse

# Vision imports
from .vision import ChartAnalyzer, ChartAnalysisConfig, ChartAnalysisResponse

# Embeddings imports
from .embeddings import TextEmbeddingsClient, EmbeddingsConfig, EmbeddingsResponse

# Configuration
from .config import AIModelsConfig

__all__ = [
    # LLM
    'BaseLLM',
    'LLMConfig',
    'LLMResponse',
    'OpenAIClient',
    'LocalLLMClient',
    
    # Whisper
    'WhisperClient',
    'WhisperConfig',
    'WhisperResponse',
    
    # Vision
    'ChartAnalyzer',
    'ChartAnalysisConfig',
    'ChartAnalysisResponse',
    
    # Embeddings
    'TextEmbeddingsClient',
    'EmbeddingsConfig',
    'EmbeddingsResponse',
    
    # Configuration
    'AIModelsConfig'
]