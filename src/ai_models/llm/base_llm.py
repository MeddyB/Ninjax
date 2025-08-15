"""
Base interface for Large Language Model implementations.
Provides a common interface for different LLM providers and local models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging


@dataclass
class LLMConfig:
    """Configuration for LLM models."""
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30
    retry_attempts: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'model_name': self.model_name,
            'api_key': self.api_key,
            'base_url': self.base_url,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'timeout': self.timeout,
            'retry_attempts': self.retry_attempts
        }


@dataclass
class LLMResponse:
    """Response from LLM model."""
    content: str
    model: str
    usage: Dict[str, int]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'content': self.content,
            'model': self.model,
            'usage': self.usage,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }


class BaseLLM(ABC):
    """
    Abstract base class for Large Language Model implementations.
    
    This interface provides a common API for different LLM providers
    including OpenAI, local models, and other cloud providers.
    """
    
    def __init__(self, config: LLMConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the LLM client.
        
        Args:
            config: LLM configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the LLM client.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text based on the given prompt.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            **kwargs: Additional model-specific parameters
            
        Returns:
            LLMResponse containing the generated text and metadata
        """
        pass
    
    @abstractmethod
    async def analyze_market_data(
        self, 
        market_data: Dict[str, Any],
        analysis_type: str = "general"
    ) -> LLMResponse:
        """
        Analyze market data and provide insights.
        
        Args:
            market_data: Market data to analyze
            analysis_type: Type of analysis (general, technical, sentiment, etc.)
            
        Returns:
            LLMResponse containing the analysis
        """
        pass
    
    @abstractmethod
    async def generate_trading_signals(
        self,
        market_context: Dict[str, Any],
        strategy_params: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Generate trading signals based on market context.
        
        Args:
            market_context: Current market context and data
            strategy_params: Optional strategy parameters
            
        Returns:
            LLMResponse containing trading signals and reasoning
        """
        pass
    
    @abstractmethod
    async def explain_trade_decision(
        self,
        trade_data: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> LLMResponse:
        """
        Explain a trading decision in natural language.
        
        Args:
            trade_data: Information about the trade
            market_context: Market context at time of trade
            
        Returns:
            LLMResponse containing the explanation
        """
        pass
    
    async def health_check(self) -> bool:
        """
        Check if the LLM service is healthy and responsive.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            test_response = await self.generate_text(
                "Test prompt for health check",
                system_prompt="Respond with 'OK' if you can process this request."
            )
            return "OK" in test_response.content.upper()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            'model_name': self.config.model_name,
            'initialized': self._initialized,
            'config': self.config.to_dict()
        }
    
    def is_initialized(self) -> bool:
        """Check if the LLM client is initialized."""
        return self._initialized