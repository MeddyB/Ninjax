"""
Trading bots module for automated trading strategies.
"""

from .base_bot import BaseBot, BotConfig, BotStatus, BotPerformance
from .scalping_bot import ScalpingBot
from .arbitrage_bot import ArbitrageBot

__all__ = [
    'BaseBot',
    'BotConfig',
    'BotStatus',
    'BotPerformance',
    'ScalpingBot',
    'ArbitrageBot'
]