"""
Configuration system for AI models.
Centralized configuration management for all AI model types.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from .llm.base_llm import LLMConfig
from .whisper.whisper_client import WhisperConfig
from .vision.chart_analyzer import ChartAnalysisConfig
from .embeddings.text_embeddings import EmbeddingsConfig


@dataclass
class AIModelsConfig:
    """
    Centralized configuration for all AI models.
    
    Manages configuration for LLM, Whisper, Vision, and Embeddings models
    with environment-based settings and validation.
    """
    
    # LLM Configuration
    llm_enabled: bool = True
    llm_provider: str = "openai"  # openai, local
    llm_model_name: str = "gpt-4"
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_max_tokens: int = 1000
    llm_temperature: float = 0.7
    llm_timeout: int = 30
    
    # Whisper Configuration
    whisper_enabled: bool = True
    whisper_model_size: str = "base"
    whisper_language: Optional[str] = None
    whisper_task: str = "transcribe"
    whisper_temperature: float = 0.0
    
    # Vision Configuration
    vision_enabled: bool = True
    vision_model_name: str = "gpt-4-vision-preview"
    vision_confidence_threshold: float = 0.7
    vision_analysis_depth: str = "standard"
    vision_max_image_size: int = 1024 * 1024
    
    # Embeddings Configuration
    embeddings_enabled: bool = True
    embeddings_provider: str = "openai"
    embeddings_model_name: str = "text-embedding-ada-002"
    embeddings_api_key: Optional[str] = None
    embeddings_max_input_length: int = 8192
    embeddings_batch_size: int = 100
    
    # General Configuration
    ai_models_cache_dir: str = "data/ai_models_cache"
    ai_models_log_level: str = "INFO"
    ai_models_retry_attempts: int = 3
    ai_models_timeout: int = 30
    
    # Model-specific feature flags
    enable_market_analysis: bool = True
    enable_trading_signals: bool = True
    enable_voice_commands: bool = True
    enable_chart_analysis: bool = True
    enable_semantic_search: bool = True
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        # Ensure cache directory exists
        Path(self.ai_models_cache_dir).mkdir(parents=True, exist_ok=True)
        
        # Validate configurations
        self._validate_config()
    
    @classmethod
    def from_env(cls, env_prefix: str = "AI_") -> 'AIModelsConfig':
        """
        Create configuration from environment variables.
        
        Args:
            env_prefix: Prefix for environment variables
            
        Returns:
            AIModelsConfig instance
        """
        config_dict = {}
        
        # Map environment variables to config fields
        env_mappings = {
            # LLM settings
            f"{env_prefix}LLM_ENABLED": ("llm_enabled", bool),
            f"{env_prefix}LLM_PROVIDER": ("llm_provider", str),
            f"{env_prefix}LLM_MODEL_NAME": ("llm_model_name", str),
            f"{env_prefix}LLM_API_KEY": ("llm_api_key", str),
            f"{env_prefix}LLM_BASE_URL": ("llm_base_url", str),
            f"{env_prefix}LLM_MAX_TOKENS": ("llm_max_tokens", int),
            f"{env_prefix}LLM_TEMPERATURE": ("llm_temperature", float),
            f"{env_prefix}LLM_TIMEOUT": ("llm_timeout", int),
            
            # Whisper settings
            f"{env_prefix}WHISPER_ENABLED": ("whisper_enabled", bool),
            f"{env_prefix}WHISPER_MODEL_SIZE": ("whisper_model_size", str),
            f"{env_prefix}WHISPER_LANGUAGE": ("whisper_language", str),
            f"{env_prefix}WHISPER_TASK": ("whisper_task", str),
            f"{env_prefix}WHISPER_TEMPERATURE": ("whisper_temperature", float),
            
            # Vision settings
            f"{env_prefix}VISION_ENABLED": ("vision_enabled", bool),
            f"{env_prefix}VISION_MODEL_NAME": ("vision_model_name", str),
            f"{env_prefix}VISION_CONFIDENCE_THRESHOLD": ("vision_confidence_threshold", float),
            f"{env_prefix}VISION_ANALYSIS_DEPTH": ("vision_analysis_depth", str),
            f"{env_prefix}VISION_MAX_IMAGE_SIZE": ("vision_max_image_size", int),
            
            # Embeddings settings
            f"{env_prefix}EMBEDDINGS_ENABLED": ("embeddings_enabled", bool),
            f"{env_prefix}EMBEDDINGS_PROVIDER": ("embeddings_provider", str),
            f"{env_prefix}EMBEDDINGS_MODEL_NAME": ("embeddings_model_name", str),
            f"{env_prefix}EMBEDDINGS_API_KEY": ("embeddings_api_key", str),
            f"{env_prefix}EMBEDDINGS_MAX_INPUT_LENGTH": ("embeddings_max_input_length", int),
            f"{env_prefix}EMBEDDINGS_BATCH_SIZE": ("embeddings_batch_size", int),
            
            # General settings
            f"{env_prefix}MODELS_CACHE_DIR": ("ai_models_cache_dir", str),
            f"{env_prefix}MODELS_LOG_LEVEL": ("ai_models_log_level", str),
            f"{env_prefix}MODELS_RETRY_ATTEMPTS": ("ai_models_retry_attempts", int),
            f"{env_prefix}MODELS_TIMEOUT": ("ai_models_timeout", int),
            
            # Feature flags
            f"{env_prefix}ENABLE_MARKET_ANALYSIS": ("enable_market_analysis", bool),
            f"{env_prefix}ENABLE_TRADING_SIGNALS": ("enable_trading_signals", bool),
            f"{env_prefix}ENABLE_VOICE_COMMANDS": ("enable_voice_commands", bool),
            f"{env_prefix}ENABLE_CHART_ANALYSIS": ("enable_chart_analysis", bool),
            f"{env_prefix}ENABLE_SEMANTIC_SEARCH": ("enable_semantic_search", bool),
        }
        
        # Load values from environment
        for env_var, (field_name, field_type) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if field_type == bool:
                        config_dict[field_name] = value.lower() in ('true', '1', 'yes', 'on')
                    elif field_type == int:
                        config_dict[field_name] = int(value)
                    elif field_type == float:
                        config_dict[field_name] = float(value)
                    else:
                        config_dict[field_name] = value
                except (ValueError, TypeError) as e:
                    logging.warning(f"Invalid value for {env_var}: {value} ({e})")
        
        return cls(**config_dict)
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration."""
        return LLMConfig(
            model_name=self.llm_model_name,
            api_key=self.llm_api_key,
            base_url=self.llm_base_url,
            max_tokens=self.llm_max_tokens,
            temperature=self.llm_temperature,
            timeout=self.llm_timeout,
            retry_attempts=self.ai_models_retry_attempts
        )
    
    def get_whisper_config(self) -> WhisperConfig:
        """Get Whisper configuration."""
        return WhisperConfig(
            model_size=self.whisper_model_size,
            language=self.whisper_language,
            task=self.whisper_task,
            temperature=self.whisper_temperature
        )
    
    def get_vision_config(self) -> ChartAnalysisConfig:
        """Get Vision configuration."""
        return ChartAnalysisConfig(
            model_name=self.vision_model_name,
            confidence_threshold=self.vision_confidence_threshold,
            analysis_depth=self.vision_analysis_depth,
            max_image_size=self.vision_max_image_size
        )
    
    def get_embeddings_config(self) -> EmbeddingsConfig:
        """Get Embeddings configuration."""
        return EmbeddingsConfig(
            model_name=self.embeddings_model_name,
            provider=self.embeddings_provider,
            api_key=self.embeddings_api_key or self.llm_api_key,  # Fallback to LLM API key
            max_input_length=self.embeddings_max_input_length,
            batch_size=self.embeddings_batch_size,
            timeout=self.ai_models_timeout,
            retry_attempts=self.ai_models_retry_attempts
        )
    
    def get_enabled_models(self) -> List[str]:
        """Get list of enabled AI models."""
        enabled = []
        if self.llm_enabled:
            enabled.append("llm")
        if self.whisper_enabled:
            enabled.append("whisper")
        if self.vision_enabled:
            enabled.append("vision")
        if self.embeddings_enabled:
            enabled.append("embeddings")
        return enabled
    
    def get_enabled_features(self) -> List[str]:
        """Get list of enabled AI features."""
        features = []
        if self.enable_market_analysis:
            features.append("market_analysis")
        if self.enable_trading_signals:
            features.append("trading_signals")
        if self.enable_voice_commands:
            features.append("voice_commands")
        if self.enable_chart_analysis:
            features.append("chart_analysis")
        if self.enable_semantic_search:
            features.append("semantic_search")
        return features
    
    def _validate_config(self):
        """Validate configuration settings."""
        errors = []
        
        # Validate LLM configuration
        if self.llm_enabled:
            if self.llm_provider == "openai" and not self.llm_api_key:
                errors.append("LLM API key required for OpenAI provider")
            
            if self.llm_temperature < 0 or self.llm_temperature > 2:
                errors.append("LLM temperature must be between 0 and 2")
            
            if self.llm_max_tokens <= 0:
                errors.append("LLM max_tokens must be positive")
        
        # Validate Whisper configuration
        if self.whisper_enabled:
            valid_sizes = ["tiny", "base", "small", "medium", "large"]
            if self.whisper_model_size not in valid_sizes:
                errors.append(f"Invalid Whisper model size: {self.whisper_model_size}")
            
            valid_tasks = ["transcribe", "translate"]
            if self.whisper_task not in valid_tasks:
                errors.append(f"Invalid Whisper task: {self.whisper_task}")
        
        # Validate Vision configuration
        if self.vision_enabled:
            if self.vision_confidence_threshold < 0 or self.vision_confidence_threshold > 1:
                errors.append("Vision confidence threshold must be between 0 and 1")
            
            valid_depths = ["basic", "standard", "detailed"]
            if self.vision_analysis_depth not in valid_depths:
                errors.append(f"Invalid vision analysis depth: {self.vision_analysis_depth}")
        
        # Validate Embeddings configuration
        if self.embeddings_enabled:
            if self.embeddings_provider == "openai" and not (self.embeddings_api_key or self.llm_api_key):
                errors.append("Embeddings API key required for OpenAI provider")
            
            if self.embeddings_max_input_length <= 0:
                errors.append("Embeddings max_input_length must be positive")
            
            if self.embeddings_batch_size <= 0:
                errors.append("Embeddings batch_size must be positive")
        
        # Validate general settings
        if self.ai_models_retry_attempts < 0:
            errors.append("Retry attempts must be non-negative")
        
        if self.ai_models_timeout <= 0:
            errors.append("Timeout must be positive")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            # LLM settings
            'llm_enabled': self.llm_enabled,
            'llm_provider': self.llm_provider,
            'llm_model_name': self.llm_model_name,
            'llm_api_key': '***' if self.llm_api_key else None,
            'llm_base_url': self.llm_base_url,
            'llm_max_tokens': self.llm_max_tokens,
            'llm_temperature': self.llm_temperature,
            'llm_timeout': self.llm_timeout,
            
            # Whisper settings
            'whisper_enabled': self.whisper_enabled,
            'whisper_model_size': self.whisper_model_size,
            'whisper_language': self.whisper_language,
            'whisper_task': self.whisper_task,
            'whisper_temperature': self.whisper_temperature,
            
            # Vision settings
            'vision_enabled': self.vision_enabled,
            'vision_model_name': self.vision_model_name,
            'vision_confidence_threshold': self.vision_confidence_threshold,
            'vision_analysis_depth': self.vision_analysis_depth,
            'vision_max_image_size': self.vision_max_image_size,
            
            # Embeddings settings
            'embeddings_enabled': self.embeddings_enabled,
            'embeddings_provider': self.embeddings_provider,
            'embeddings_model_name': self.embeddings_model_name,
            'embeddings_api_key': '***' if self.embeddings_api_key else None,
            'embeddings_max_input_length': self.embeddings_max_input_length,
            'embeddings_batch_size': self.embeddings_batch_size,
            
            # General settings
            'ai_models_cache_dir': self.ai_models_cache_dir,
            'ai_models_log_level': self.ai_models_log_level,
            'ai_models_retry_attempts': self.ai_models_retry_attempts,
            'ai_models_timeout': self.ai_models_timeout,
            
            # Feature flags
            'enable_market_analysis': self.enable_market_analysis,
            'enable_trading_signals': self.enable_trading_signals,
            'enable_voice_commands': self.enable_voice_commands,
            'enable_chart_analysis': self.enable_chart_analysis,
            'enable_semantic_search': self.enable_semantic_search,
            
            # Computed values
            'enabled_models': self.get_enabled_models(),
            'enabled_features': self.get_enabled_features()
        }