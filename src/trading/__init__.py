"""
Trading module for comprehensive algorithmic trading capabilities.

This module provides a complete trading framework including:
- Trading bots for automated execution
- Strategy development and backtesting
- Technical indicators and analysis tools
- Performance measurement and optimization
"""

# Bots
from .bots import BaseBot, BotConfig, BotStatus, BotPerformance, ScalpingBot, ArbitrageBot

# Strategies
from .strategies import BaseStrategy, StrategyConfig, StrategySignal, StrategyResult
from .strategies import TechnicalStrategy, MovingAverageStrategy, RSIStrategy

# Backtesting
from .backtesting import BacktestEngine, BacktestConfig, BacktestResult
from .backtesting import StrategyTester, PerformanceAnalyzer, PerformanceMetrics

# Indicators
from .indicators import TechnicalIndicators, CustomIndicators
from .indicators import sma, ema, rsi, macd, bollinger_bands, vwap, ichimoku_cloud

__all__ = [
    # Bots
    'BaseBot',
    'BotConfig',
    'BotStatus', 
    'BotPerformance',
    'ScalpingBot',
    'ArbitrageBot',
    
    # Strategies
    'BaseStrategy',
    'StrategyConfig',
    'StrategySignal',
    'StrategyResult',
    'TechnicalStrategy',
    'MovingAverageStrategy',
    'RSIStrategy',
    
    # Backtesting
    'BacktestEngine',
    'BacktestConfig',
    'BacktestResult',
    'StrategyTester',
    'PerformanceAnalyzer',
    'PerformanceMetrics',
    
    # Indicators
    'TechnicalIndicators',
    'CustomIndicators',
    'sma', 'ema', 'rsi', 'macd', 'bollinger_bands',
    'vwap', 'ichimoku_cloud'
]